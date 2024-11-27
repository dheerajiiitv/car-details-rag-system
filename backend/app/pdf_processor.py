import os
from typing import BinaryIO, List, Tuple, TypeVar
import pdfplumber

from pydantic import BaseModel
from typing import List, Dict, Optional
from app.models import ChunkMetadata, TextChunk, ProcessedDocument, DocumentMetadata, CarModelName
from app.utils.logger import get_logger
import re

logger = get_logger(__name__)

class PDFProcessor:
    def __init__(self):
        self.chunk_size = 1000
        self.chunk_overlap = 100

    def preprocess_text(self, text: str) -> str:
        """
        Preprocess text after conversion, from pypdf client
        1. not able to detect paragraph, each line as separate entity so fixing with regex based pattern
        2. extra new lines with a single new line.
        3. Remove extra space
        4. remove space around new line
        """
        converted_text = re.sub(r"(\t)", " ", text)
        converted_text = re.sub(r"(\r| *\n *)", "\n", converted_text)
        # Fix some new line issue for PDF conversion
        converted_text = re.sub(" +", " ", converted_text)
        converted_text = re.sub("\n+", "\n", converted_text) 
        converted_text = re.sub(r"([0-9a-z,-])\n", r"\g<1> ", converted_text) 
        converted_text = converted_text.strip()
        return converted_text

    def extract_text(self, file: BinaryIO, filename: str, id: CarModelName) -> ProcessedDocument:
        """Extract and process text from PDF file"""
        logger.info(f"Extracting text from {filename}")
        full_text = ""
        word_chunks = []
        
        with pdfplumber.open(file) as pdf: 
            for page_num, page in enumerate(pdf.pages, 1):
                page_text, page_chunks = self._process_page(page, page_num, len(full_text), id)
                if page_text:
                    full_text += page_text + "\n"
                    word_chunks.extend(page_chunks)

        return self._create_processed_document(full_text, word_chunks, filename, id)

    def _process_page(self, page, page_num: int, text_offset: int, id: CarModelName) -> Tuple[str, List[TextChunk]]:
        """Process a single PDF page and extract text with coordinates"""
        page_text = page.extract_text()
        if not page_text:
            return "", []
            
        page_text = self.preprocess_text(page_text)
        words = page.extract_words()
        chunks = [self._create_word_chunk(word, text_offset, page_num, id) 
                 for word in words]
        
        return page_text, chunks

    def _create_word_chunk(self, word_data: Dict, text_offset: int, page_num: int, id: CarModelName) -> TextChunk:
        """Create a TextChunk from word data"""
        metadata = ChunkMetadata(
            start_index=text_offset,
            end_index=text_offset + len(word_data["text"]),
            page_number=page_num,
            coordinates=self._extract_coordinates(word_data),
            document_id=id
        )
        return TextChunk(
            text=word_data["text"],
            metadata=metadata
        )

    def _extract_coordinates(self, word_data: Dict) -> Dict[str, float]:
        """Extract coordinates from word data"""
        return {
            "x0": word_data["x0"],
            "y0": word_data["top"],
            "x1": word_data["x1"],
            "y1": word_data["bottom"]
        }

    def _create_processed_document(self, full_text: str, word_chunks: List[TextChunk], filename: str, id: CarModelName) -> ProcessedDocument:
        """Create ProcessedDocument from extracted text and chunks"""
        return ProcessedDocument(
            full_text=full_text,
            chunks=self.split_text(full_text, word_chunks, id),
            metadata=DocumentMetadata(filename=filename, document_id=id),
        )

    def split_text(self, text: str, word_chunks: List[TextChunk], id: CarModelName) -> List[TextChunk]:
        """
        Split text into chunks while preserving word boundaries and coordinates
        """
        text_chunks = []
        current_pos = 0
        
        while current_pos < len(text):
            chunk_end = self._find_chunk_boundary(text, current_pos)
            chunk = self._create_text_chunk(text, current_pos, chunk_end, word_chunks, id)
            if chunk:
                text_chunks.append(chunk)
            current_pos = chunk_end + 1
            
        return text_chunks

    def _find_chunk_boundary(self, text: str, current_pos: int) -> int:
        """Find the next chunk boundary position"""
        chunk_end = min(current_pos + self.chunk_size, len(text))
        
        if chunk_end < len(text):
            while chunk_end > current_pos and text[chunk_end] != ' ':
                chunk_end -= 1
                
        return chunk_end

    def _create_text_chunk(self, text: str, start: int, end: int, word_chunks: List[TextChunk], id: CarModelName) -> Optional[TextChunk]:
        """Create a TextChunk for the given text span"""
        relevant_chunks = [
            chunk for chunk in word_chunks 
            if chunk.metadata.start_index >= start and chunk.metadata.end_index <= end 
        ]
        
        if not relevant_chunks:
            return None
            
        metadata = ChunkMetadata(
            start_index=start,
            end_index=end,
            page_number=relevant_chunks[0].metadata.page_number,
            coordinates=self._merge_coordinates(relevant_chunks),
            document_id=id
        )
        return TextChunk(
            text=text[start:end],
            metadata=metadata
        )

    def _merge_coordinates(self, chunks: List[TextChunk]) -> Dict[str, float]:
        """Merge coordinates from multiple chunks"""
        return {
            "x0": min(c.metadata.coordinates["x0"] for c in chunks),
            "y0": min(c.metadata.coordinates["y0"] for c in chunks),
            "x1": max(c.metadata.coordinates["x1"] for c in chunks),
            "y1": max(c.metadata.coordinates["y1"] for c in chunks)
        }

