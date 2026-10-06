import os
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage


load_dotenv()

persistent_directory = "db/chroma_db"
embedding_model = OpenAIEmbeddings(model='text-embedding-3-small', openai_api_key=os.getenv("TAA_OPENAI_API_KEY"))
db = Chroma(
    persist_directory=persistent_directory,
    embedding_function=embedding_model
)
llm_model = ChatOpenAI(model_name="gpt-4o-mini", openai_api_key=os.getenv("TAA_OPENAI_API_KEY"))

chat_history = []

def ask_question(question):
    print("\n You asked: ", question)

    if chat_history:
        messages = [
            SystemMessage(content="Given the chat history, rewrite the new question to be a standalone and searchable. just return the rewritten question."),
        ] + chat_history + [
            HumanMessage(content=f"New question: {question}")
        ]

        result = llm_model.invoke(messages)
        searchable_question = result.content.strip()
        print(f"Searching for relevant documents using the rewritten question: {searchable_question}")
    else:
        searchable_question = question

    retriever = db.as_retriever(search_kwargs={"k": 3})
    docs = retriever.invoke(searchable_question)

    print(f"\nFound {len(docs)} relevant documents.")
    for i, doc in enumerate(docs):
        lines = doc.page_content.split("\n")[:2]
        preview = "\n".join(lines)
        print(f" Doc {i}: {preview}...")


    combined_input = f"""
    based on the following documents, please answer the question: {searchable_question}

    Documents:
    {"\n".join(f"- {doc.page_content}" for doc in docs)}

    Please Provide a clear, helpful answer using only the information from the documents. If the answer is not present, respond with 'I don't have information from the provided documents'."
    """

    messages = [
        SystemMessage(content="You are a helpful assistant that answers questions based on the provided documents. If the answer is not present in the documents, respond with 'I don't have information from the provided documents'."),
    ] + chat_history + [   
        HumanMessage(content=combined_input)
    ]   

    result = llm_model.invoke(messages)
    answer = result.content

    chat_history.append(HumanMessage(content=question))
    chat_history.append(AIMessage(content=answer))

    print("\nAnswer:")
    print(answer)
    return answer 


def start_chat():
    print("Welcome to the Chatbot! Type 'exit' to end the chat.")
    while True:
        question = input("\n Enter your question: ")
        if question.lower() == 'exit':
            print("Exiting the chat. Goodbye!")
            break
        ask_question(question)

if __name__ == "__main__":
    start_chat()

