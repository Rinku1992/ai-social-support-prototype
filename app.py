import streamlit as st
import requests
import json
import pandas as pd

st.set_page_config(layout="wide")
st.title("🤖 AI-Powered Social Support Application (Enhanced)")

st.info("This prototype now accepts PDF, DOCX, and Excel files for a more flexible application process.")

# --- Form Section ---
with st.form("application_form"):
    st.header("Applicant Information")
    
    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("Full Name", "Jameela Al Falahi")
        age = st.number_input("Age", min_value=18, max_value=100, value=35)
        monthly_income = st.number_input("Monthly Income (AED)", min_value=0, value=4500)
    with col2:
        family_size = st.number_input("Family Size", min_value=1, max_value=20, value=4)
        employment_years = st.number_input("Years of Employment", min_value=0, max_value=50, value=10)
        address_form = st.text_area("Address", "123 Main St, Abu Dhabi, UAE")

    st.header("Upload Documents")
    col1_docs, col2_docs = st.columns(2)
    with col1_docs:
        # Allow multiple resume formats
        resume = st.file_uploader("Upload Resume (PDF, DOCX, TXT)", type=['pdf', 'docx', 'txt'])
        # Allow multiple bank statement formats
        bank_statement = st.file_uploader("Upload Bank Statement (PDF, XLSX, TXT)", type=['pdf', 'xlsx', 'txt'])
    with col2_docs:
        emirates_id = st.file_uploader("Upload Emirates ID (PNG, JPG)", type=['png', 'jpg'])
        assets_excel = st.file_uploader("Upload Assets/Liabilities File (Optional XLSX)", type=['xlsx'])
    
    submit_button = st.form_submit_button("Submit Application for AI Assessment")

# --- Processing and Results Section ---
if submit_button:
    # We only require the main documents for this demo
    if not all([emirates_id, resume, bank_statement, name, address_form]):
        st.error("Please fill in all fields and upload Resume, Bank Statement, and Emirates ID.")
    else:
        with st.spinner("🤖 AI agents are processing your documents... This may take a moment."):
            files = {
                'emirates_id': (emirates_id.name, emirates_id.getvalue(), emirates_id.type),
                'resume': (resume.name, resume.getvalue(), resume.type),
                'bank_statement': (bank_statement.name, bank_statement.getvalue(), bank_statement.type),
            }
            payload = {
                'name': name, 'age': age, 'monthly_income': monthly_income,
                'family_size': family_size, 'employment_years': employment_years,
                'address_form': address_form
            }
            
            try:
                api_url = "http://127.0.0.1:8000/process_application/"
                response = requests.post(api_url, data=payload, files=files)
                
                if response.status_code == 200:
                    st.success("Assessment Complete!")
                    results = response.json()
                    
                    st.subheader("Assessment Outcome")
                    decision = results.get('decision', {})
                    final_decision = decision.get('final_decision', 'N/A')
                    
                    if final_decision == "Approve":
                        st.balloons()
                        st.markdown(f"### <span style='color:green;'>Status: {final_decision}</span>", unsafe_allow_html=True)
                    elif final_decision == "Review Required":
                        st.markdown(f"### <span style='color:orange;'>Status: {final_decision}</span>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"### <span style='color:red;'>Status: {final_decision}</span>", unsafe_allow_html=True)
                    
                    st.write("**Reasoning:**", decision.get('decision_reason', 'N/A'))

                    st.subheader("Economic Enablement Recommendations")
                    recs = decision.get('enablement_recommendations', [])
                    if recs:
                        for rec in recs:
                            st.markdown(f"- {rec}")
                    
                    st.subheader("Data Verification Details")
                    validation = results.get('validation_result', {})
                    if not validation.get('validation_passed'):
                        st.warning("Discrepancies found in your documents:")
                        for note in validation.get('validation_notes', []):
                            st.markdown(f"- {note}")
                    else:
                        st.success("All document information is consistent.")

                    with st.expander("Show Full AI Agent State (JSON)"):
                        st.json(results)
                else:
                    st.error(f"Error from API: {response.status_code} - {response.text}")
            except requests.exceptions.RequestException as e:
                st.error(f"Could not connect to the backend API. Is it running? Error: {e}")