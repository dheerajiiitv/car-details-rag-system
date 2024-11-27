import os
from typing import Dict, List
import uuid
import chromadb
from langchain_openai import OpenAIEmbeddings
from app.models import QueryBreakdownLLM
from pdf_processor import ProcessedDocument


class DocumentIndexer:
    def __init__(self):
        self.client = chromadb.Client()
        self.collection = self.client.get_or_create_collection("car_manuals")
        self.embedder = OpenAIEmbeddings(openai_api_key=os.getenv("OPENAI_API_KEY"), model="text-embedding-3-small")

    def _create_where_clause(self, query_config: QueryBreakdownLLM):
        where_clause = {"document_id": query_config.document_id.lower()}
        
        # TODO: Leave section out for now
        # if query_config.metadata:
        #     where_clause["section"] = query_config.metadata.section
        return where_clause
    
    def query_database(self, query_config: QueryBreakdownLLM):
        results = self.collection.query(
            query_texts=[query_config.query],
            query_embeddings=[self._embed_query(query_config.query)],
            n_results=3,
            where=self._create_where_clause(query_config)
        )
        results["metadatas"] = [[self._unflatten_metadata(metadata) for metadata in results["metadatas"][0]]]
        return results
    
    def _flatten_metadata(self, metadata: Dict):
        """
        Flatten the metadata dictionary to a list of strings

        dict to key@key1:value1,key2:value2
        """
        # This is a hack to get around the fact that chroma doesn't support nested dictionaries in metadata
        # TODO: Fetch data from the normal database, also handles for lists
        flattened_metadata = {}
        for key, value in metadata.items():
            if isinstance(value, dict):
                for k, v in value.items():
                    flattened_metadata[f"{key}@{k}"] = v
            else:
                flattened_metadata[key] = value
        return flattened_metadata
    
    def _unflatten_metadata(self, metadata: Dict):
        """
        Unflatten the metadata dictionary from a list of strings
        """
        unflattened_metadata = {}
        for key, value in metadata.items():
            if "@" in key:
                key, subkey = key.split("@")
                if key not in unflattened_metadata:
                    unflattened_metadata[key] = {}
                unflattened_metadata[key][subkey] = value
            else:
                unflattened_metadata[key] = value
        return unflattened_metadata

    def index_document(self, document: ProcessedDocument):
        # Add all chunks to the database together
        embeddings = self._embed_documents([chunk.text for chunk in document.chunks])
        self.collection.add(
            documents=[chunk.text for chunk in document.chunks],
            ids=[str(uuid.uuid4()) for _ in document.chunks], 
            metadatas=[self._flatten_metadata(chunk.metadata.model_dump() | {"filename": document.metadata.filename}) for chunk in document.chunks],
            embeddings=embeddings
        )
        return {"message": "Document indexed successfully"}

    def _embed_query(self, query: str):
        # return [0] * 1536
        return self.embedder.embed_query(query)
    
    def _embed_documents(self, documents: List[str]):
        # return [[0] * 1536] * len(documents)
        return self.embedder.embed_documents(documents)
    