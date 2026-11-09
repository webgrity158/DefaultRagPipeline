# File Configurations
DIRECTORY_PATH = "Datasets/pdf_files"
FILE_TYPE = "pdf" # Options: "pdf", "docx", "txt", "csv", "json", "sql"
IS_SINGLE_FILE = True
SINGLE_FILE_PATH = "Datasets/pdf_files/gpt3_models.pdf"

#Chunking Configurations
CHUNKING_STRATEGY = "recursive" # Options: "sentence-based", "agentic", "recursive", "fixed-size", "semantic", "structured"
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
MIN_CHUNK_SIZE = 200

#Embedding Configurations
EMBEDDING_MODEL_TYPE = "sentence-transformers"
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"  # Options: "all-MiniLM-L6-v2"

# Vector Store Configurations
VECTOR_DATABASE = "chromadb"
VECTOR_STORE_PATH = "Database/vector_store"
VECTOR_STORE_COLLECTION_NAME = "pdf_documents_cosine_v1"

# Retrieval Configurations
TOP_K = 3
SCORE_THRESHOLD = 0.5


