

from typing_extensions import TypeVar
from pydantic import BaseModel, Field
from typing import Dict, List, Optional


CarModelName = TypeVar("CarModelName", str, int)

class AvailableCarModels(BaseModel):
    car_models: List[CarModelName]

class Query(BaseModel):
    question: str

class Response(BaseModel):
    answer: str
    source: str
    confidence: float


class QueryBreakdownLLM(BaseModel):
    query: str = Field(description="The question the user asked for the car manual.")
    document_id: Optional[CarModelName] = Field(description="The car model the user is asking about.", default=None)
    vehicle_related_section: Optional[str] = Field(description="The section of the manual that the user's question is related to Ex. Vehicle operations (e.g., How to turn on indicator in MG Astor?) Maintenance requirements (e.g., Which engine oil to use in Tiago?) Technical specifications Safety features Troubleshooting guidance", default=None)

class ListQueryBreakdownLLM(BaseModel):
    queries: List[QueryBreakdownLLM]

class QueryResultLLM(BaseModel):
    answer: str = Field(description="The answer to the user's question.")
    sources: List[int] = Field(description="The indices of the sources of the answer.")

class QueryResult(QueryResultLLM):
    coordinates: List[Dict[str, float]] = Field(description="The coordinates of the answer on the PDF page.")
    page_numbers: List[int] = Field(description="The page numbers of the retrieved documents that contain the answer.")
    retrieved_documents: List[str] = Field(description="The retrieved documents that contain the answer.")
    document_id: CarModelName = Field(description="The document id of the retrieved document that contains the answer.")
    filename: str = Field(description="The filename of the retrieved document that contains the answer.")

class ChunkMetadata(BaseModel):
    start_index: int
    end_index: int
    page_number: int
    coordinates: Dict[str, float]  # x0, y0, x1, y1 coordinates on PDF page
    document_id: CarModelName

class TextChunk(BaseModel):
    text: str
    metadata: ChunkMetadata

class DocumentMetadata(BaseModel):
    filename: str
    document_id: CarModelName

class ProcessedDocument(BaseModel):
    full_text: str
    chunks: List[TextChunk]
    metadata: DocumentMetadata
