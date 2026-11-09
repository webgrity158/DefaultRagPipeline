from config import CHUNKING_STRATEGY, CHUNK_SIZE, CHUNK_OVERLAP, MIN_CHUNK_SIZE, EMBEDDING_MODEL_NAME, EMBEDDING_MODEL_TYPE
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
import uuid
import re
import numpy as np
from sentence_transformers import SentenceTransformer


class DataChunking:
    def __init__(
        self,
        chunking_strategy:str = CHUNKING_STRATEGY,
        chunk_size:int = CHUNK_SIZE,
        chunk_overlap:int = CHUNK_OVERLAP,
        min_chunk_size:int = MIN_CHUNK_SIZE,
        embedding_model_name:str = EMBEDDING_MODEL_NAME,
        embedding_model_type:str = EMBEDDING_MODEL_TYPE,
    ):
        self.chunking_strategy = chunking_strategy
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.strategies = {
            "sentence-based": self.sentence_based_chunking,
            "agentic": self.agentic_chunking,
            "recursive": self.recursive_chunking,
            "fixed-size": self.fixed_size_chunking,
            "semantic": self.semantic_chunking,
            "structured": self.structured_chunking,
        }
        self.min_chunk_size = min(
            max(0, min_chunk_size),
            chunk_size,
        )
        self.embedding_model_name = embedding_model_name
        self.embedding_model_type = embedding_model_type


    def split_documents_into_chunks(self, documents):
        print("_" * 50)
        print(
            f"🔄 Started Generating chunks using "
            f"{self.chunking_strategy} chunking strategy"
        )
        self.documents = documents
        chunking_method = self.strategies.get(self.chunking_strategy)
        if chunking_method is None:
            raise ValueError(
                f"Unsupported chunking strategy: {self.chunking_strategy}"
            )

        split_documents = chunking_method()

        print(
            f"✅ Generated {len(documents)} documents "
            f"into {len(split_documents)} chunks."
        )
        print("_" * 50)
        print("\n")
        return split_documents

    def _create_documents(self, source_doc, chunks, strategy):
        """
        Preserve source metadata and attach chunk metadata.
        """
        result = []

        for index, text in enumerate(chunks):
            if not text.strip():
                continue

            metadata = dict(source_doc.metadata)
            metadata.update({
                "chunk_id": str(uuid.uuid4()),
                "chunk_index": index,
                "chunk_strategy": strategy,
                "content_length": len(text),
            })

            result.append(
                Document(
                    page_content=text,
                    metadata=metadata,
                )
            )

        return result

    def _get_sentences(self, text):
        """
        Lightweight sentence segmentation.
        """
        return [
            sentence.strip()
            for sentence in re.split(
                r'(?<=[.!?])\s+|\n+',
                text.strip(),
            )
            if sentence.strip()
        ]

    def _pack_text(self, units):
        """
        Pack sentences or topic groups into chunks
        without exceeding chunk_size.

        Oversized units are recursively split.
        """
        chunks = []
        current = ""

        for unit in units:
            unit = unit.strip()

            if not unit:
                continue

            if len(unit) > self.chunk_size:
                if current:
                    chunks.append(current)
                    current = ""

                splitter = RecursiveCharacterTextSplitter(
                    chunk_size=self.chunk_size,
                    chunk_overlap=0,
                    separators=["\n\n", "\n", " ", ""],
                )

                chunks.extend(splitter.split_text(unit))
                continue

            candidate = (
                f"{current} {unit}" if current else unit
            )

            if len(candidate) <= self.chunk_size:
                current = candidate
            else:
                if current:
                    chunks.append(current)

                current = unit

        if current:
            chunks.append(current)

        return chunks

    def _apply_overlap(self, chunks):
        """
        Add word-boundary overlap without
        exceeding chunk_size.
        """

        if self.chunk_overlap <= 0:
            return chunks

        result = []
        for index, chunk in enumerate(chunks):
            if index == 0:
                result.append(chunk)
                continue

            available = self.chunk_size - len(chunk)

            if available <= 1:
                result.append(chunk)
                continue

            max_overlap = min(
                self.chunk_overlap,
                available - 1
            )

            previous_words = chunks[index - 1].split()
            overlap_words = []
            overlap_length = 0

            for word in reversed(previous_words):
                added_length = len(word) + (
                    1 if overlap_words else 0
                )

                if overlap_length + added_length > max_overlap:
                    break

                overlap_words.insert(0, word)
                overlap_length += added_length

            if overlap_words:
                prefix = " ".join(overlap_words)
                result.append(f"{prefix} {chunk}")
            else:
                result.append(chunk)

        return result

    def _get_embedding_model(self):
        """
        Lazy-load the embedding model.
        """
        if self.embedding_model_type == "sentence-transformers":
            self.embedding_model = SentenceTransformer(
                self.embedding_model_name
            )
        else:
            raise ValueError(
                f"Unknown embedding model type: {self.embedding_model_type}"
            )

        return self.embedding_model
    
    def fixed_size_chunking(self):
        """
        Exact character-window chunking.

        Uses fixed-size windows with configurable
        character overlap.
        """
        all_chunks = []        
        step = self.chunk_size - self.chunk_overlap

        for doc in self.documents:
            text = doc.page_content
            chunks = []
            for start in range(0, len(text), step):
                chunk = text[start:start + self.chunk_size]
                if chunk:
                    chunks.append(chunk)

                if start + self.chunk_size >= len(text):
                    break

            all_chunks.extend(
                self._create_documents(
                    doc,
                    chunks,
                    "fixed-size",
                )
            )

        return all_chunks

    def recursive_chunking(self):
        """
        Hierarchical character splitting:

        Paragraph -> Line -> Word -> Character
        """
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""],
        )

        all_chunks = []

        for doc in self.documents:
            chunks = splitter.split_text(
                doc.page_content
            )

            all_chunks.extend(
                self._create_documents(
                    doc,
                    chunks,
                    "recursive",
                )
            )

        return all_chunks

    def sentence_based_chunking(self):
        """
        Split into sentences and group them into
        dynamically sized chunks.
        """
        all_chunks = []
        for doc in self.documents:
            sentences = self._get_sentences(
                doc.page_content
            )
            chunks = self._pack_text(sentences)
            chunks = self._apply_overlap(chunks)
            all_chunks.extend(
                self._create_documents(
                    doc,
                    chunks,
                    "sentence-based",
                )
            )

        return all_chunks

    def structured_chunking(self, documents):
        """
        Split based on detected headings and sections.

        Supports:
        - Markdown headings
        - Chapter headings
        - Section headings
        - Numbered headings

        This operates on extracted plain text.
        """
        all_chunks = []

        heading_pattern = re.compile(
            r"^(?:"
            r"#{1,6}\s+.+"
            r"|(?:Chapter|Section)\s+\d+.*"
            r"|\d+(?:\.\d+)*[.)]?\s+.+"
            r")$",
            re.IGNORECASE,
        )

        for doc in documents:
            sections = []
            current_lines = []

            for line in doc.page_content.splitlines():
                stripped = line.strip()

                if (
                    stripped
                    and heading_pattern.match(stripped)
                    and current_lines
                ):
                    sections.append(
                        "\n".join(current_lines).strip()
                    )
                    current_lines = []

                current_lines.append(line)

            if current_lines:
                sections.append(
                    "\n".join(current_lines).strip()
                )

            chunks = []

            for section in sections:
                splitter = RecursiveCharacterTextSplitter(
                    chunk_size=self.chunk_size,
                    chunk_overlap=self.chunk_overlap,
                    separators=["\n\n", "\n", " ", ""],
                )

                chunks.extend(
                    splitter.split_text(section)
                )

            all_chunks.extend(
                self._create_documents(
                    doc,
                    chunks,
                    "structured",
                )
            )

        return all_chunks
        
    def agentic_chunking(self):
        pass
    
    
    def semantic_chunking(self, documents):
        """
        Uses sentence embeddings and cosine similarity.

        Creates a new topic group when adjacent
        sentence similarity falls below threshold.
        """
        all_chunks = []
        model = self._get_embedding_model()

        for doc in documents:
            sentences = self._get_sentences(
                doc.page_content
            )

            if not sentences:
                continue

            if len(sentences) == 1:
                chunks = self._pack_text(sentences)

            else:
                embeddings = model.encode(
                    sentences,
                    batch_size=32,
                    normalize_embeddings=True,
                    show_progress_bar=False,
                )

                similarities = np.sum(
                    embeddings[:-1] * embeddings[1:],
                    axis=1,
                )

                groups = []
                current = [sentences[0]]

                for index, similarity in enumerate(similarities):
                    next_sentence = sentences[index + 1]
                    current_text = " ".join(current)

                    topic_changed = (
                        float(similarity)
                        < self.semantic_threshold
                    )

                    size_exceeded = (
                        len(current_text)
                        + len(next_sentence)
                        + 1
                        > self.chunk_size
                    )

                    if (
                        topic_changed
                        and len(current_text) >= self.min_chunk_size
                    ) or size_exceeded:
                        groups.append(" ".join(current))
                        current = [next_sentence]
                    else:
                        current.append(next_sentence)

                if current:
                    groups.append(" ".join(current))

                chunks = []

                for group in groups:
                    chunks.extend(
                        self._pack_text([group])
                    )

            chunks = self._apply_overlap(chunks)

            all_chunks.extend(
                self._create_documents(
                    doc,
                    chunks,
                    "semantic",
                )
            )

        return all_chunks