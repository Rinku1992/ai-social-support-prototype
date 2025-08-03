from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
import uvicorn
import os
import shutil
from typing import Annotated
from pydantic import BaseModel

from core.graph import get_graph
from core.schemas import ApplicationData, GraphState

app = FastAPI(title="Social Support AI API")
app_graph = get_graph()

UPLOAD_DIR = "temp_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/process_application/")
async def process_application(
    name: Annotated[str, Form()],
    age: Annotated[int, Form()],
    monthly_income: Annotated[int, Form()],
    family_size: Annotated[int, Form()],
    employment_years: Annotated[int, Form()],
    address_form: Annotated[str, Form()],
    emirates_id: Annotated[UploadFile, File()],
    resume: Annotated[UploadFile, File()],
    bank_statement: Annotated[UploadFile, File()],
):
    """
    Receives application data and files, processes them through the AI workflow,
    and returns the final decision.
    """
    try:
        # Save uploaded files temporarily
        id_path = os.path.join(UPLOAD_DIR, emirates_id.filename)
        resume_path = os.path.join(UPLOAD_DIR, resume.filename)
        bank_statement_path = os.path.join(UPLOAD_DIR, bank_statement.filename)

        with open(id_path, "wb") as buffer:
            shutil.copyfileobj(emirates_id.file, buffer)
        with open(resume_path, "wb") as buffer:
            shutil.copyfileobj(resume.file, buffer)
        with open(bank_statement_path, "wb") as buffer:
            shutil.copyfileobj(bank_statement.file, buffer)

        # Prepare initial state for the graph
        initial_state = GraphState(
            application_data=ApplicationData(
                name=name, age=age, monthly_income=monthly_income,
                family_size=family_size, employment_years=employment_years,
                address_form=address_form
            ),
            document_paths={
                "emirates_id": id_path, "resume": resume_path, "bank_statement": bank_statement_path
            }
        )

        # Run the graph
        final_state_dict = app_graph.invoke(initial_state)
        
        # Clean up temp files
        os.remove(id_path)
        os.remove(resume_path)
        os.remove(bank_statement_path)

        # FINAL FIX: Manually build a serializable dictionary.
        # This loop checks each value in the state dictionary. If a value is a
        # Pydantic model (like ApplicationData), it calls .dict() on it.
        # Otherwise, it uses the value as-is.
        serializable_content = {}
        for key, value in final_state_dict.items():
            if isinstance(value, BaseModel):
                serializable_content[key] = value.dict()
            else:
                serializable_content[key] = value

        return JSONResponse(content=serializable_content)

    except Exception as e:
        import traceback
        print(f"An error occurred: {e}")
        traceback.print_exc() # Print full traceback for better debugging
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)