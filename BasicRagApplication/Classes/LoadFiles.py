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

    def validate_file(self, file: Path) -> bool:
        supported_types = {
            "pdf": {".pdf"},
            "docx": {".docx"},
            "txt": {".txt"},
            "csv": {".csv"},
            "json": {".json"},
            "xlsx": {".xlsx"},
            "xls": {".xls"},
            "excel": {".xlsx", ".xls"},
            "sql": {".sql"},
        }

        file_type = self.file_type.lower()
        file_name = file.name

        if not file.is_file():
            print(f"File '{file_name}' does not exist or is not a regular file.")
            return False

        allowed_extensions = supported_types.get(file_type)
        if allowed_extensions is None:
            print(f"Unsupported file type: {file_type}")
            return False

        if file.suffix.lower() not in allowed_extensions:
            print(
                f"Invalid file '{file_name}'. "
                f"Expected: {', '.join(sorted(allowed_extensions))}"
            )
            return False
        return True

    def get_loader(self, file_type):
        match file_type.strip().lower().lstrip("."):
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
            case "xlsx" | "xls":
                return UnstructuredExcelLoader
            case _:
                return None


    def load_files(self):
        if self.is_single_file:
            file = Path(self.single_file_path)
            files = (file,)
        else:
            directory = Path(self.directory_path)
            if not directory.is_dir():
                print(f"Directory not found: {directory}")
                return False
            # Iterate through files without building a list of every path.
            files = directory.rglob("*")

        all_documents = []
        processed_files = 0

        for file in files:
            if not file.is_file():
                continue

            file_type = file.suffix.lower().lstrip(".")
            loader_class = self.get_loader(file_type)

            if loader_class is None:
                if self.is_single_file:
                    print(f"Unsupported file type: {file.suffix}")
                    return False
                continue

            if not self.validate_file(file):
                if self.is_single_file:
                    return False
                continue

            print(f"Processing file: {file}")

            try:
                loader_options = {}
                if file_type == "json":
                    # Load the entire JSON value as document content.
                    loader_options = {
                        "jq_schema": ".",
                        "text_content": False,
                    }
                elif file_type in ("txt", "sql", "csv"):
                    loader_options = {
                        "encoding": "utf-8",
                    }

                loader = loader_class(str(file), **loader_options)
                documents = loader.load()

                for doc in documents:
                    doc.metadata["source_file"] = file.name
                    doc.metadata["file_type"] = file_type

                all_documents.extend(documents)
                processed_files += 1

                print(f"Loaded {len(documents)} documents from {file.name}.")
            except Exception as e:
                print(f"Error processing {file}: {e}")
                return False

        print(
            f"Loaded {len(all_documents)} documents "
            f"from {processed_files} files."
        )
        return all_documents