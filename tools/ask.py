"""Route queries through LLM with chosen context."""

from typing import Dict, Any
import openai
import os
# Handle import path for different execution contexts
try:
    from core.config import settings
except ImportError:
    # Fallback for when running from different directory
    import sys
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, project_root)
    from core.config import settings

from tools.retrieve import retrieve_with_metadata
from tools.context_builder import build_context_window, create_context_summary


def ask_with_context(query: str, max_tokens: int = 4000, top_k: int = 5) -> Dict[str, Any]:
    """Ask a question with context from LTMC memory using real LLM."""
    try:
        # Retrieve relevant documents
        documents = retrieve_with_metadata(query, top_k=top_k)
        
        if not documents:
            return {
                "success": False,
                "error": "No relevant documents found",
                "query": query,
                "context": "",
                "answer": "I don't have enough information to answer this question."
            }
        
        # Build context window
        context = build_context_window(documents, max_tokens)
        context_summary = create_context_summary(documents)
        
        # Create prompt with context
        prompt = f"""Based on the following context, please answer the question.

Context:
{context}

Question: {query}

Please provide a comprehensive answer based on the context provided."""

        # Use real OpenAI API if available
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if openai_api_key:
            try:
                openai.api_key = openai_api_key
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant that answers questions based on the provided context."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=max_tokens,
                    temperature=0.7
                )
                answer = response.choices[0].message['content']
            except Exception as e:
                # Fallback to simple answer if OpenAI fails
                answer = f"Based on the available context:\n\n{context_summary}\n\nThis is a fallback response due to API error: {str(e)}"
        else:
            # Fallback when no API key is available
            answer = f"Based on the available context:\n\n{context_summary}\n\nThis is a fallback response. Set OPENAI_API_KEY environment variable for full LLM integration."
        
        return {
            "success": True,
            "query": query,
            "context": context,
            "context_summary": context_summary,
            "answer": answer,
            "documents_used": len(documents),
            "top_documents": documents[:3]
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "query": query
        }


def ask_by_type(query: str, doc_type: str, max_tokens: int = 4000, top_k: int = 5) -> Dict[str, Any]:
    """Ask a question with context from a specific document type using real LLM."""
    try:
        # Retrieve documents of specific type
        documents = retrieve_with_metadata(query, top_k=top_k, source_filter=[doc_type])
        
        if not documents:
            return {
                "success": False,
                "error": f"No relevant {doc_type} documents found",
                "query": query,
                "context": "",
                "answer": f"I don't have enough {doc_type} information to answer this question."
            }
        
        # Build context window
        context = build_context_window(documents, max_tokens)
        context_summary = create_context_summary(documents)
        
        # Create prompt with context
        prompt = f"""Based on the following {doc_type} context, please answer the question.

Context:
{context}

Question: {query}

Please provide a comprehensive answer based on the {doc_type} context provided."""

        # Use real OpenAI API if available
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if openai_api_key:
            try:
                openai.api_key = openai_api_key
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": f"You are a helpful assistant that answers questions based on {doc_type} context."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=max_tokens,
                    temperature=0.7
                )
                answer = response.choices[0].message['content']
            except Exception as e:
                # Fallback to simple answer if OpenAI fails
                answer = f"Based on the available {doc_type} context:\n\n{context_summary}\n\nThis is a fallback response due to API error: {str(e)}"
        else:
            # Fallback when no API key is available
            answer = f"Based on the available {doc_type} context:\n\n{context_summary}\n\nThis is a fallback response. Set OPENAI_API_KEY environment variable for full LLM integration."
        
        return {
            "success": True,
            "query": query,
            "doc_type": doc_type,
            "context": context,
            "context_summary": context_summary,
            "answer": answer,
            "documents_used": len(documents),
            "top_documents": documents[:3]
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "query": query,
            "doc_type": doc_type
        }


def ask_with_custom_context(query: str, context: str) -> Dict[str, Any]:
    """Ask a question with custom provided context using real LLM."""
    try:
        # Create prompt with custom context
        prompt = f"""Based on the following context, please answer the question.

Context:
{context}

Question: {query}

Please provide a comprehensive answer based on the context provided."""

        # Use real OpenAI API if available
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if openai_api_key:
            try:
                openai.api_key = openai_api_key
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant that answers questions based on the provided context."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=4000,
                    temperature=0.7
                )
                answer = response.choices[0].message['content']
            except Exception as e:
                # Fallback to simple answer if OpenAI fails
                answer = f"Based on the provided context:\n\nThis is a fallback response due to API error: {str(e)}"
        else:
            # Fallback when no API key is available
            answer = f"Based on the provided context:\n\nThis is a fallback response. Set OPENAI_API_KEY environment variable for full LLM integration."
        
        return {
            "success": True,
            "query": query,
            "context": context,
            "answer": answer,
            "context_length": len(context)
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "query": query
        }
