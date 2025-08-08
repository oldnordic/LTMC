"""Chunking service for LTMC text splitting."""

import re
from typing import List


class TextChunker:
    """Text chunker for splitting text into semantically coherent chunks."""
    
    def __init__(self, chunk_size: int, chunk_overlap: int):
        """Initialize the text chunker.
        
        Args:
            chunk_size: Maximum size of each chunk in characters
            chunk_overlap: Number of characters to overlap between chunks
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def split_text(self, text: str) -> List[str]:
        """Split text into chunks.
        
        Args:
            text: Text to split into chunks
            
        Returns:
            List of text chunks
        """
        if not text:
            return []
        
        # If text is shorter than chunk size, return as single chunk
        if len(text) <= self.chunk_size:
            return [text]
        
        # Split text into sentences first
        sentences = self._split_into_sentences(text)
        
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            # If adding this sentence would exceed chunk size
            if len(current_chunk) + len(sentence) > self.chunk_size:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    # Start new chunk with overlap
                    overlap_start = max(0, len(current_chunk) - self.chunk_overlap)
                    current_chunk = current_chunk[overlap_start:] + sentence
                else:
                    # If single sentence is too long, split it
                    if len(sentence) > self.chunk_size:
                        sentence_chunks = self._split_long_sentence(sentence)
                        chunks.extend(sentence_chunks)
                        current_chunk = ""
                    else:
                        current_chunk = sentence
            else:
                current_chunk += " " + sentence if current_chunk else sentence
        
        # Add the last chunk if it exists
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences using regex."""
        # Simple sentence splitting - can be improved with NLP libraries
        sentences = re.split(r'([.!?]+)', text)
        result = []
        for i in range(0, len(sentences) - 1, 2):
            if i + 1 < len(sentences):
                sentence = sentences[i] + sentences[i + 1]
                if sentence.strip():
                    result.append(sentence.strip())
        return result
    
    def _split_long_sentence(self, sentence: str) -> List[str]:
        """Split a long sentence into smaller chunks."""
        words = sentence.split()
        chunks = []
        current_chunk = ""
        
        for word in words:
            if len(current_chunk) + len(word) + 1 > self.chunk_size:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = word
                else:
                    # If single word is too long, truncate it
                    chunks.append(word[:self.chunk_size])
                    current_chunk = ""
            else:
                current_chunk += " " + word if current_chunk else word
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks


def create_chunker(chunk_size: int, chunk_overlap: int) -> TextChunker:
    """Create a text chunker.
    
    Args:
        chunk_size: Maximum size of each chunk in characters
        chunk_overlap: Number of characters to overlap between chunks
        
    Returns:
        TextChunker instance
    """
    return TextChunker(chunk_size, chunk_overlap)


def split_text_into_chunks(chunker: TextChunker, text: str) -> List[str]:
    """Split text into chunks using the provided chunker.
    
    Args:
        chunker: TextChunker instance
        text: Text to split into chunks
        
    Returns:
        List of text chunks
    """
    return chunker.split_text(text)


def merge_small_chunks(chunks: List[str], min_chunk_size: int) -> List[str]:
    """Merge chunks that are smaller than the minimum size.
    
    Args:
        chunks: List of text chunks
        min_chunk_size: Minimum size for a chunk in characters
        
    Returns:
        List of merged chunks
    """
    if not chunks:
        return []
    
    merged_chunks = []
    current_chunk = ""
    
    for chunk in chunks:
        if len(current_chunk) + len(chunk) < min_chunk_size:
            # Merge with current chunk
            current_chunk += " " + chunk if current_chunk else chunk
        else:
            # Add current chunk to results and start new one
            if current_chunk:
                merged_chunks.append(current_chunk.strip())
            current_chunk = chunk
    
    # Add the last chunk
    if current_chunk:
        merged_chunks.append(current_chunk.strip())
    
    return merged_chunks
