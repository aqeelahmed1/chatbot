from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI
from config import MODEL_NAME, OPENAI_API_KEY
import logging
import time
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


def setup_rag_chain(retriever):
    """
    Set up RAG chain with rate limit handling and token optimization
    """
    try:
        # Optimized prompt to reduce token usage
        template = """Answer concisely (1-2 sentences max) using this context:
        {context}

        Question: {question}

        If unsure, say "Not found in website". No formatting."""
        prompt = ChatPromptTemplate.from_template(template)

        # Configure LLM with rate limit handling
        llm = ChatOpenAI(
            model_name=MODEL_NAME,
            temperature=0,
            openai_api_key=OPENAI_API_KEY,
            max_tokens=150,  # Limit response length
            max_retries=3,  # Built-in retries
            request_timeout=30  # Fail fast if rate limited
        )

        # Create the RAG chain
        return (
                {"context": retriever, "question": RunnablePassthrough()}
                | prompt
                | llm
                | StrOutputParser()
        )

    except Exception as e:
        logger.error(f"RAG setup failed: {str(e)}")
        raise RuntimeError("Failed to initialize chatbot. Please try again later.")


def handle_rate_limit(fn):
    """Decorator to handle rate limits with exponential backoff"""

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            if "rate_limit" in str(e).lower():
                logger.warning("Rate limited - retrying...")
                raise
            raise

    return wrapper