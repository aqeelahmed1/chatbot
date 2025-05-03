import os

# Configuration constants
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

# Best available models as of 2024
EMBEDDING_MODEL = "text-embedding-3-large"  # Highest quality embeddings
MODEL_NAME = "gpt-4-turbo-preview"         # Most capable GPT-4 version
# Add this to your existing config.py
MAX_PAGES_TO_SCRAPE = 100  # Control how many pages to crawl
# Number of chunks to retrieve as context
NUM_RETRIEVED_CHUNKS = 8  # Change this value to control context size

# Get OpenAI API key from environment variable
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("Please set the OPENAI_API_KEY environment variable")

TEMPERATURE = 0.3
PERSIST_DIRECTORY = "chroma_db"  # Directory to store ChromaDB data
# Chat History Settings
MAX_HISTORY_LENGTH = 20  # Number of messages to retain