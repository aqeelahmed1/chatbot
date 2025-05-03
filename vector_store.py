from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from config import PERSIST_DIRECTORY, OPENAI_API_KEY
import logging
import os

logger = logging.getLogger(__name__)


def create_vector_store(documents):
    """Create ChromaDB vector store with OpenAI embeddings"""
    try:
        # Initialize OpenAI embeddings (will use default settings)
        embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)

        # Create or load ChromaDB
        if os.path.exists(PERSIST_DIRECTORY):
            logger.info("Loading existing ChromaDB")
            return Chroma(
                persist_directory=PERSIST_DIRECTORY,
                embedding_function=embeddings
            )
        else:
            logger.info("Creating new ChromaDB")
            vectorstore = Chroma.from_documents(
                documents=documents,
                embedding=embeddings,
                persist_directory=PERSIST_DIRECTORY
            )
            vectorstore.persist()
            return vectorstore

    except Exception as e:
        logger.error(f"Error creating vector store: {str(e)}")
        raise


def get_retriever(vectorstore, top_k=10):
    """Create ChromaDB retriever with optimized settings"""
    try:
        return vectorstore.as_retriever(
            search_type="similarity_score_threshold",
            search_kwargs={
                "k": top_k,
                "score_threshold": 0.7
            }
        )
    except Exception as e:
        logger.error(f"Error creating retriever: {str(e)}")
        raise