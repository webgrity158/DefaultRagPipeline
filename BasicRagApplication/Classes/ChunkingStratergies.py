from langchain_text_splitters import RecursiveCharacterTextSplitter

class ChunkingStratergies:
    def __init__(self, strategy: str):
        self.strategy = strategy

    def split_documents_into_chunks(documents, chunk_size=1000, chunk_overlap=200):
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        
        split_documents = text_splitter.split_documents(documents)
        print(f"Split {len(documents)} documents into {len(split_documents)} chunks.")

        if split_documents:
            print("\n Example of a chunk:")
            print(f"Content: {split_documents[0].page_content[:100]}...")
            print(f"Metadata: {split_documents[0].metadata}")
        return split_documents