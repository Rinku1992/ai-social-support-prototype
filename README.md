Application Submission & Ingestion
The user fills out the application form and uploads their documents (ID, resume, etc.) via the Streamlit web interface.

Backend Orchestration
The FastAPI backend receives the data and files. It immediately invokes the LangGraph agentic workflow, passing the initial application data and file paths.

Multimodal Data Extraction
The first AI agent in the graph analyzes the uploaded documents. It uses OCR (via Pytesseract) to extract text from the image-based Emirates ID and specialized parsers to read content from .pdf, .docx, and .xlsx files.

Structured Data Generation
The raw text extracted from all documents is passed to the LLM (Large Language Model). The LLM's task is to understand this unstructured text and populate a structured Pydantic schema with the relevant information, such as name, income from a bank statement, and work experience from a resume.

Automated Validation
A validation agent takes over, programmatically comparing key data points from different sources. For example, it checks if the name on the application form matches the name extracted from the ID card, ensuring data consistency.

Baseline Eligibility Check
The applicant's tabular data (age, income, family size) is passed to the pre-trained Scikit-learn model. This model provides a fast, data-driven baseline prediction (Approve or Decline) for financial eligibility.

Final AI Review & Recommendation
The final and most sophisticated agent acts as an expert case officer. It synthesizes all the information gathered so far—the initial application, the structured data from documents, the validation flags, and the ML model's prediction. Based on this holistic view, the LLM makes a final, reasoned decision and generates personalized economic enablement recommendations, such as upskilling courses or job-matching advice.

🖥️ Displaying Results
The final, structured state containing the decision, reasoning, and recommendations is sent back to the Streamlit UI and presented to the user in a clear, easy-to-understand format.



