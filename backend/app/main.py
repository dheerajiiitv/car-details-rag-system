from fastapi import FastAPI, HTTPException, Depends, File, UploadFile
from fastapi.params import Form
from pydantic import BaseModel
from pydantic_settings import BaseSettings
import uvicorn
from app.database import DocumentIndexer
from app.models import CarModelName, Query, Response, AvailableCarModels
from app.pdf_processor import PDFProcessor
from app.qna_service import QNAService

app = FastAPI()
available_car_models = AvailableCarModels(car_models=[]) # TODO: Will be fetched from the database

class Settings(BaseSettings):
    openai_api_key: str

def get_db_manager():
    return DocumentIndexer()

def get_pdf_processor():
    return PDFProcessor()

@app.post("/query")
async def query_manual(query: Query):
    qna_service = QNAService(available_car_models)
    return qna_service.answer_question(query.question)

    
@app.post("/index")
async def index_document(file: UploadFile = File(...),
                        id: CarModelName = Form(...),
                        db_manager: DocumentIndexer = Depends(get_db_manager),
                        processor: PDFProcessor = Depends(get_pdf_processor)):
    document = processor.extract_text(file.file, file.filename, id)
    result = db_manager.index_document(document)
    available_car_models.car_models.append(id)
    return result

if __name__ == "__main__":
    # TODO: Remove reload=True in production
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)