import os 
from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from dotenv import load_dotenv

load_dotenv()
def main():
    documents = load_documents()
    print("Document loading completed successfully.")
    chunks = chunk_ducuments(documents)
    print("Documents loaded into chunks")
    create_vector_store(chunks)
    print("Vector store created successfully.")


if __name__ == "__main__":
    main()

def load_documents(document_path = "Datasets"):
    print(f"Loading documents from {document_path}... ")

    if not os.path.exists(document_path):
        raise FileNotFoundError(f"Document path {document_path} does not exist.")
    loader = DirectoryLoader(path = document_path, glob = "**/*.pdf", loader_cls=PyPDFLoader)
    documents = loader.load()

    if(len(documents) == 0):
        raise ValueError(f"No documents found in {document_path}. Please check the path and ensure it contains PDF files.")
    return documents

def chunk_ducuments(documents, chunk_size = 800, chunk_overlap = 150):
    print("Splitting documents into chunks...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    chunks = text_splitter.split_documents(documents)
    return chunks

def create_vector_store(chunks, persist_directory = "db/chroma_db"):
    print("Creating Embeddings and Vector Store...")
    embedding_model = OpenAIEmbeddings(model='text-embedding-3-small', openai_api_key=os.getenv("OPENAI_API_KEY"))

    print("--- Creating Chroma Vector Store ---")
    vectorStore =  Chroma.from_documents(
        documents=chunks, 
        embedding=embedding_model, 
        persist_directory=persist_directory,
        collection_metadata={"hnsw:space": "cosine"}
    )
    print("--- Finished Creating Chroma Vector Store ---")
    print(f"--- Vector store created and saved to directory {persist_directory} ---")
    return vectorStore


