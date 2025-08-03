import pandas as pd
import pytesseract
from PIL import Image
import joblib
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from core.schemas import ApplicationData
import os
import pypdf
import docx

# --- Tool Configuration ---
# Point pytesseract to the Tesseract executable if needed
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Load the trained ML model, encoder and features
model = joblib.load('models/eligibility_classifier.joblib')
label_encoder = joblib.load('models/label_encoder.joblib')
features_list = joblib.load('models/features.joblib')

# Initialize LLM
llm = ChatOpenAI(model="phi3", base_url="http://localhost:11434/v1", api_key="ollama")

# --- Tool Definitions ---

@tool
def read_document_content(file_path: str) -> str:
    """
    Reads the text content from a document file (PDF, DOCX, XLSX, TXT).
    """
    try:
        _, extension = os.path.splitext(file_path)
        extension = extension.lower()

        if extension == '.pdf':
            reader = pypdf.PdfReader(file_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() or ""
            return text
        
        elif extension == '.docx':
            doc = docx.Document(file_path)
            return "\n".join([para.text for para in doc.paragraphs])
            
        elif extension == '.xlsx':
            # Read all sheets and convert them to a string format
            xls = pd.ExcelFile(file_path)
            content = ""
            for sheet_name in xls.sheet_names:
                df = pd.read_excel(xls, sheet_name=sheet_name)
                content += f"--- Sheet: {sheet_name} ---\n"
                content += df.to_string() + "\n\n"
            return content

        elif extension == '.txt':
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        else:
            return f"Unsupported file type: {extension}"
            
    except Exception as e:
        return f"Error reading file {file_path}: {e}"

@tool
def extract_text_from_image(image_path: str) -> str:
    """Extracts text from an image file using OCR."""
    try:
        text = pytesseract.image_to_string(Image.open(image_path))
        return text
    except Exception as e:
        return f"Error processing image: {e}"

class MLInput(BaseModel):
    age: int = Field(description="Applicant's age")
    monthly_income: int = Field(description="Applicant's monthly income")
    family_size: int = Field(description="Number of family members")
    employment_years: int = Field(description="Total years of employment")

@tool
def predict_eligibility(data: MLInput) -> str:
    """
    Predicts financial support eligibility using a pre-trained machine learning model.
    """
    try:
        input_data = pd.DataFrame([data.dict()], columns=features_list, index=[0])
        input_data['income_per_person'] = input_data['monthly_income'] / input_data['family_size']
        input_data = input_data[features_list]

        prediction_encoded = model.predict(input_data)[0]
        prediction = label_encoder.inverse_transform([prediction_encoded])[0]
        return prediction
    except Exception as e:
        return f"Error during prediction: {e}"