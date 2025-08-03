from pydantic import BaseModel, Field
from typing import List, Optional

class ApplicationData(BaseModel):
    """Schema for the initial application form data."""
    name: str = Field(description="Applicant's full name")
    age: int = Field(description="Applicant's age")
    monthly_income: int = Field(description="Applicant's monthly income in AED from the form")
    family_size: int = Field(description="Number of family members")
    employment_years: int = Field(description="Total years of employment")
    address_form: str = Field(description="Address provided in the application form")

class ExtractedData(BaseModel):
    """Schema for data extracted from documents."""
    name_from_id: Optional[str] = Field(None, description="Name extracted from Emirates ID")
    income_from_statement: Optional[int] = Field(None, description="Income extracted from bank statement")
    experience_from_resume: Optional[str] = Field(None, description="Work experience summary from resume")

class ValidationResult(BaseModel):
    """Schema for data validation checks."""
    name_matches: Optional[bool] = Field(None, description="True if name on form matches ID")
    income_consistent: Optional[bool] = Field(None, description="True if income on form is consistent with bank statement")
    validation_passed: bool = Field(False, description="Overall validation status")
    validation_notes: List[str] = Field([], description="List of validation discrepancies")

class Decision(BaseModel):
    """Schema for the final decision and recommendations."""
    ml_eligibility_prediction: str = Field(description="Initial prediction from the ML model (Approve/Decline)")
    final_decision: str = Field(description="Final decision after LLM review (Approve/Soft Decline)")
    decision_reason: str = Field(description="Justification for the final decision")
    enablement_recommendations: List[str] = Field([], description="List of upskilling or job matching recommendations")

class GraphState(BaseModel):
    """Represents the state of our workflow."""
    application_data: ApplicationData
    document_paths: dict
    extracted_data: Optional[ExtractedData] = None
    validation_result: Optional[ValidationResult] = None
    decision: Optional[Decision] = None