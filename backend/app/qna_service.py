from typing import List, Dict, Optional
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from app.query_processing import QueryProcessor
from app.database import DocumentIndexer
from app.models import QueryResult, QueryResultLLM, AvailableCarModels
from app.utils.logger import get_logger

logger = get_logger(__name__)

class QNAService:
    def __init__(self, available_car_models: AvailableCarModels):
        self.available_car_models = available_car_models
        self.processor = QueryProcessor()
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        self.json_llm = self.llm.bind(response_format={"type": "json_object"})
        self.query_prompt = """
            You are a helpful assistant that can answer a user's question, please provide a detailed answer with citations.
            The output should be a JSON object with the following keys:
            {query_result_schema}

            Few shot examples:

            question: How to turn on indicator in MG Astor?
            document:
            Content: MG astor owner's manual is a comprehensive guide to the operation and maintenance of the MG Astor.
            Source: 0
            Content: To turn on indicator in MG Astor, press the indicator button on the steering wheel.
            Source: 1
            output:
            {{
                "answer": "To turn on indicator in MG Astor, press the indicator button on the steering wheel.",
                "sources": [1]
            }}

            The user's question is: {question}
            The document is: {document}
            output:
        """

    def answer_question(self, question: str) -> List[QueryResult]:
        queries = self.processor.query_breakdown(question, self.available_car_models)
        query_results = []
        
        for query in queries:
            logger.info(f"Processing query: {query.query}")
            result = self._process_single_query(query)
            if result:
                query_results.append(result)
                
        logger.info(f"Query results: {query_results}")
        return query_results

    def _process_single_query(self, query) -> Optional[QueryResult]:
        if query.document_id is None:
            # If the query is not related to any document, return answer "Manual not available"
            return QueryResult(
                answer="Manual not available",
                sources=[],
                coordinates=[],
                retrieved_documents=[],
                page_numbers=[],
                document_id=None,
                filename=None
            )
        docs = self.processor.indexer.query_database(query)
        logger.info(f"Retrieved documents: {docs}")
        
        if len(docs["documents"][0]) == 0:
            return None
            
        logger.info(f"Total documents retrieved: {len(docs['documents'][0])}")
        llm_result = self._get_llm_response(query, docs["documents"][0])
        coordinates = self._get_coordinates(llm_result.sources, docs["metadatas"][0])
        page_numbers = self._get_page_numbers(llm_result.sources, docs["metadatas"][0])
        return QueryResult(
            answer=llm_result.answer,
            sources=llm_result.sources,
            coordinates=coordinates,
            retrieved_documents=docs["documents"][0],
            page_numbers=page_numbers,
            document_id=query.document_id,
            filename=docs["metadatas"][0][0]["filename"]
        )

    def _get_llm_response(self, query, documents) -> QueryResultLLM:
        formatted_document = self._format_document(documents)
        qna_prompt = self.query_prompt.format(
            question=query.query,
            document=formatted_document,
            query_result_schema=QueryResultLLM.model_json_schema()
        )
        response = self.json_llm.invoke(qna_prompt)
        logger.info(f"Response: {response}")
        return QueryResultLLM.parse_raw(response.content)

    def _get_coordinates(self, sources, metadata) -> List[Dict[str, float]]:
        coordinates = []
        for source in sources:
            coordinates.append(self._replace_index_with_coordinates(source, metadata))
        return coordinates
    
    def _get_page_numbers(self, sources, metadata) -> List[int]:
        page_numbers = []
        for source in sources:
            page_numbers.append(metadata[source]["page_number"])
        return page_numbers

    def _format_document(self, retrieved_chunks: List[str]) -> str:
        """Format the retrieved chunks with source information."""
        formatted_document = ""
        for index, chunk in enumerate(retrieved_chunks):
            formatted_document += f"Content: {chunk}\n"
            formatted_document += f"Source: {index}\n\n"
        return formatted_document

    def _replace_index_with_coordinates(self, index: int, metadata: Dict[str, float]) -> Dict[str, float]:
        return metadata[index]["coordinates"]