from typing import List, Optional
from app.database import DocumentIndexer
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate

from app.models import CarModelName, QueryBreakdownLLM, ListQueryBreakdownLLM, AvailableCarModels
from app.utils.logger import get_logger

logger = get_logger(__name__)

class QueryProcessor:
    def __init__(self):
        """Initialize the QueryProcessor with the necessary components."""
        self.indexer = DocumentIndexer()
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        self.json_llm = self.llm.bind(response_format={"type": "json_object"})
        self.query_breakdown_prompt = """
            You are a helpful assistant that can break down a user's question.
            
            The output should be a JSON object with the following keys:
            {query_breakdown_schema}
            Example:

            question: How to turn on indicator in MG Astor? Safety and security section of Tiago? Brake system of Maruti 800?
            The available car models are: MG Astor, Tiago
            output:
            {{
                "queries": [
                    {{
                        "query": "How to turn on indicator in MG Astor?",
                        "vehicle_related_section": "Vehicle operations",
                        "document_id": "MG Astor"
                    }},
                    {{
                        "query": "What are the safety and security features of Tiago?",
                        "vehicle_related_section": "Safety and security",
                        "document_id": "Tiago"
                    }},
                    {{
                        "query": "What are the brake system features of Maruti 800?",
                        "vehicle_related_section": "Brake system"
                    }}
                ]
            }}


            The user's question is: {question}
            The available car models are: {available_car_models}, if the question is not related to any of the car models, do not include the document_id key.
            output:
        """

    def query_breakdown(self, question: str, available_car_models: AvailableCarModels) -> List[QueryBreakdownLLM]:
        """Break down a user's question into a list of queries."""
        prompt = PromptTemplate(
            template=self.query_breakdown_prompt,
            partial_variables={"query_breakdown_schema": ListQueryBreakdownLLM.model_json_schema()},
            input_variables=["question", "available_car_models"]
        )
        
        response = self.json_llm.invoke(prompt.format(question=question, available_car_models="\n".join(available_car_models.car_models)))
        logger.info(f"Query breakdown response: {response.content}")
        queries = ListQueryBreakdownLLM.parse_raw(response.content).queries
        for query in queries:
            query.document_id = self._validate_document_id(query.document_id, available_car_models)
        logger.info(f"Query breakdown queries: {queries}")
        return queries

    def _validate_document_id(self, document_id: Optional[CarModelName], available_car_models: AvailableCarModels) -> Optional[CarModelName]:
        if document_id is None:
            return None
        if document_id.lower() not in [car_model.lower() for car_model in available_car_models.car_models]:
            logger.warning(f"Document ID {document_id} not found in available car models")
            return None
        return document_id.lower()