from unittest import case

from langchain_community.document_loaders import (
    CSVLoader,
    Docx2txtLoader,
    JSONLoader,
    PyMuPDFLoader,
    TextLoader,
    UnstructuredExcelLoader,
)
from pathlib import Path
from config import DIRECTORY_PATH, FILE_TYPE, IS_SINGLE_FILE, SINGLE_FILE_PATH

class LoadFiles:
    def __init__(
        self, 
        directory_path: str = DIRECTORY_PATH, 
        file_type: str = FILE_TYPE, 
        is_single_file: bool = IS_SINGLE_FILE, 
        single_file_path: str = SINGLE_FILE_PATH
    ):
        self.directory_path = directory_path
        self.file_type = file_type
        self.is_single_file = is_single_file
        self.single_file_path = single_file_path

        # If it's a single file, process that file; otherwise, process all files in the directory
        if not self.is_single_file:
            if self.file_type == "pdf":
                self.load_pdf()

    def validate_file(self, file: Path):
        file_name = file.name
        file_path = file.parent
        file_type = file.suffix.lower()

        if not file.exists():
            print(f"File {file_name} does not exist on {file_path}.")
            return False

        if not file.is_file():
            print(f"File {file_name} is not a valid regular {self.file_type} file.")
            return False

        if self.file_type == "pdf" and file_type != ".pdf":
            print(f"File {file_name} is not a PDF file.")
            return False

        if self.file_type == "docx" and file_type != ".docx":
            print(f"File {file_name} is not a DOCX file.")
            return False

        if self.file_type == "txt" and file_type != ".txt":
            print(f"File {file_name} is not a TXT file.")
            return False

        if self.file_type == "csv" and file_type != ".csv":
            print(f"File {file_name} is not a CSV file.")
            return False

        if self.file_type == "json" and file_type != ".json":
            print(f"File {file_name} is not a JSON file.")
            return False

        if (self.file_type == "xlsx" or self.file_type == "xls" or self.file_type == "excel") and (file_type != ".xlsx" and file_type != ".xls"):
            print(f"File {file_name} is not a Excel file.")
            return False

        if self.file_type == "sql" and file_type != ".sql":
            print(f"File {file_name} is not a SQL file.")
            return False

        return True

    def get_loader(self):
        file_type = self.file_type.strip().lower().lstrip(".")

        match file_type:
            case "pdf":
                return PyMuPDFLoader

            case "docx":
                return Docx2txtLoader

            case "txt" | "sql":
                return TextLoader

            case "csv":
                return CSVLoader

            case "json":
                return JSONLoader

            case "xlsx":
                return UnstructuredExcelLoader

            case _:
                return None


    def load_files(self):
        if self.is_single_file:
            file = Path(self.single_file_path)
            if not self.validate_file(file):
                return False
            
            print(f"Found {file.name} in the directory {file.parent}.")
            try:
                loader = self.get_loader()(self.single_file_path)
                documents = loader.load()

                # Add source Metadata to each document
                for doc in documents:
                    doc.metadata["source_file"] = file.name
                    doc.metadata["file_type"] = "pdf"

                print(f"Loaded {len(documents)} pages from the single file.")
                return documents
            except Exception as e:
                print(f"Error processing {self.single_file_path}: {e}")
                return False
        else:
            all_documents = []
            pdf_dir =  Path(self.directory_path)

            #Find all PDF files in the directory and its subdirectories
            pdf_files = list(pdf_dir.glob("**/*.pdf"))

            print(f"Found {len(pdf_files)} PDF files in the directory and its subdirectories.")

            for pdf_file in pdf_files:
                print(f"Processing file: {pdf_file.name}")
                if not self.validate_file(pdf_file):
                    continue

                try: 
                    loader = self.get_loader()(str(pdf_file))
                    documents = loader.load()
                    #Add source Metadata to each document
                    for doc in documents:
                        doc.metadata["source_file"] = pdf_file.name
                        doc.metadata["file_type"] = "pdf"

                    all_documents.extend(documents)
                    print(f"Loaded {len(documents)} pages from {pdf_file.name}.")
                except Exception as e:
                    print(f"Error processing {pdf_file.name}: {e}")
                    return False

            print(f"Processed {len(all_documents)} documents from {len(pdf_files)} PDF files.")
            return all_documents
