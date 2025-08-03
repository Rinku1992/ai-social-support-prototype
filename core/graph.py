from langgraph.graph import StateGraph, END
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from typing import Dict
import json

from core.schemas import GraphState, ExtractedData, ValidationResult, Decision
from core.tools import extract_text_from_image, read_document_content, predict_eligibility

# Initialize LLM
llm = ChatOpenAI(model="phi3", base_url="http://localhost:11434/v1", api_key="ollama", temperature=0)

# --- Define Graph Nodes ---

def data_extraction_node(state: GraphState) -> Dict:
    """
    Extracts information from uploaded documents using tools.
    """
    print("---NODE: DATA EXTRACTION---")
    doc_paths = state.document_paths
    
    id_text = extract_text_from_image.invoke({"image_path": doc_paths['emirates_id']})
    resume_text = read_document_content.invoke({"file_path": doc_paths['resume']})
    bank_statement_text = read_document_content.invoke({"file_path": doc_paths['bank_statement']})
    
    extraction_prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an expert data extraction assistant. Extract the required information and format it as the requested JSON object."),
        ("human", "Emirates ID Text: {id_text}\n\nBank Statement Text: {bank_text}\n\nResume Text: {resume_text}")
    ])
    
    extraction_chain = extraction_prompt | llm.with_structured_output(ExtractedData)
    extracted_data = extraction_chain.invoke({
        "id_text": id_text, "bank_text": bank_statement_text, "resume_text": resume_text
    })
    
    return {"extracted_data": extracted_data}

def data_validation_node(state: GraphState) -> Dict:
    """
    Validates extracted data against the application form data.
    """
    print("---NODE: DATA VALIDATION---")
    app_data = state.application_data
    ext_data = state.extracted_data
    notes = []
    
    name_matches = False
    if ext_data and ext_data.name_from_id:
        name_matches = app_data.name.lower() in ext_data.name_from_id.lower()
    if not name_matches:
        notes.append(f"Name mismatch: Form says '{app_data.name}', ID says '{ext_data.name_from_id if ext_data else 'N/A'}'.")
        
    income_consistent = False
    if ext_data and ext_data.income_from_statement:
        income_consistent = abs(app_data.monthly_income - ext_data.income_from_statement) < 1000
    if not income_consistent:
        notes.append(f"Income inconsistent: Form says {app_data.monthly_income}, Bank statement suggests {ext_data.income_from_statement if ext_data else 'N/A'}.")
    
    validation_passed = name_matches and income_consistent
    validation_result = ValidationResult(
        name_matches=name_matches, income_consistent=income_consistent,
        validation_passed=validation_passed, validation_notes=notes
    )
    
    return {"validation_result": validation_result}

def ml_eligibility_node(state: GraphState) -> Dict:
    """
    Runs the pre-trained ML model for an initial eligibility check.
    """
    print("---NODE: ML ELIGIBILITY CHECK---")
    app_data = state.application_data
    
    # CORRECTED: The input dictionary must have a key "data" that matches the
    # tool's argument name.
    tool_input = {"data": app_data.dict()}
    prediction = predict_eligibility.invoke(tool_input)
    
    decision = Decision(
        ml_eligibility_prediction=prediction,
        final_decision="",
        decision_reason=""
    )
    
    return {"decision": decision}

def decision_recommendation_node(state: GraphState) -> Dict:
    """
    Makes the final decision and generates recommendations using an LLM.
    """
    print("---NODE: DECISION & RECOMMENDATION---")
    app_data = state.application_data
    ext_data = state.extracted_data
    validation = state.validation_result
    decision = state.decision

    if not validation.validation_passed:
        decision.final_decision = "Review Required"
        decision.decision_reason = "Data inconsistencies found. Manual review is necessary."
        decision.enablement_recommendations = ["Applicant should be contacted to clarify information."]
        return {"decision": decision}
        
    prompt = ChatPromptTemplate.from_template(
        """You are a social support case officer. Based on the applicant's profile, make a final decision and provide recommendations.

        Profile:
        - Name: {name}, Age: {age}
        - Income: {income} AED, Family: {family_size}
        - Experience: {experience}
        - ML Model Check: {ml_prediction}

        Your task:
        1.  Final Decision: 'Approve' or 'Soft Decline'.
        2.  Decision Reason: A concise justification.
        3.  Enablement Recommendations: 2-3 concrete upskilling or job matching ideas.

        Respond with a JSON object with keys 'final_decision', 'decision_reason', and 'enablement_recommendations'.
        """
    )
    decision_chain = prompt | llm
    
    experience_summary = ext_data.experience_from_resume if ext_data else "Not available"
    
    response_str = decision_chain.invoke({
        "name": app_data.name, "age": app_data.age,
        "income": app_data.monthly_income, "family_size": app_data.family_size,
        "experience": experience_summary,
        "ml_prediction": decision.ml_eligibility_prediction
    }).content

    try:
        cleaned_str = response_str.strip().replace("```json", "").replace("```", "").strip()
        response_json = json.loads(cleaned_str)
        decision.final_decision = response_json.get('final_decision', "Error parsing")
        decision.decision_reason = response_json.get('decision_reason', "Error parsing")
        decision.enablement_recommendations = response_json.get('enablement_recommendations', [])
    except json.JSONDecodeError:
        decision.final_decision = "Error"
        decision.decision_reason = "Failed to parse the LLM's decision response."
        print(f"LLM JSON parsing failed. Response was: {response_str}")

    return {"decision": decision}

def get_graph():
    """Compiles and returns the LangGraph agentic workflow."""
    workflow = StateGraph(GraphState)
    workflow.add_node("data_extraction", data_extraction_node)
    workflow.add_node("data_validation", data_validation_node)
    workflow.add_node("ml_eligibility_check", ml_eligibility_node)
    workflow.add_node("decision_recommendation", decision_recommendation_node)
    workflow.set_entry_point("data_extraction")
    workflow.add_edge("data_extraction", "data_validation")
    workflow.add_edge("data_validation", "ml_eligibility_check")
    workflow.add_edge("ml_eligibility_check", "decision_recommendation")
    workflow.add_edge("decision_recommendation", END)
    return workflow.compile()