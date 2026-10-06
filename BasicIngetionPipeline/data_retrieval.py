from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from dotenv import load_dotenv
import os

load_dotenv()

persistant_directory = "db/chroma_db"

embedding_model = OpenAIEmbeddings(model='text-embedding-3-small', openai_api_key=os.getenv("OPENAI_API_KEY"))

db = Chroma(
    persist_directory=persistant_directory, 
    embedding_function=embedding_model,
    collection_metadata={"hnsw:space": "cosine"}
)


retriever = db.as_retriever(
    search_type="similarity_score_threshold",
    search_kwargs={
        "k": 3,
        "score_threshold": 0.3,
    },
)

# results = db.similarity_search_with_score(
#     "Who is the CEO of BMW?",
#     k=5
# )

# print(results)

queries = [
    "What is the current best model offered by OpenAI?",
]
relevant_docs = retriever.invoke(queries[0])

print(f"User Query: {queries[0]}")
print("--- Context ---")

for i, doc in enumerate(relevant_docs):
    print(f"\nDocument {i+1}:")
    print(f"Source: {doc.metadata['source']}")
    print(f"Content Preview: {doc.page_content}...")  # Displaying only the first 500 characters for brevity
    print("-"*20)
