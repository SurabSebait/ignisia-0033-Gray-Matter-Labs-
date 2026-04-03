import pandas as pd
import logging
import os
from pathlib import Path
from typing import List

from langchain.schema import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


logger = logging.getLogger(__name__)

CHUNK_SIZE = int(os.environ.get("CHUNK_SIZE", "1000"))
CHUNK_OVERLAP = int(os.environ.get("CHUNK_OVERLAP", "200"))

ROW_BASED_SOURCE_EXT = {"excel", "csv"}

def parse_file(filepath: str, ext:str) -> list[Document]:
    parsers = {
        ".pdf":  _parse_pdf,
        ".docx": _parse_docx,
        ".xlsx": _parse_excel,
        ".txt":  _parse_txt,
        ".csv":  _parse_csv,
    }

    parser = parsers.get(ext)
    
    if parser is None:
        raise ValueError(f"No parser registered for the file format '{ext}`")
    
    raw_docs : List[Document] = parser(filepath)
    logger.info("Raw document count before splitting: %d", len(raw_docs))

    return _split(raw_docs)

def _parse_pdf(path: Path) -> List[Document]:
    from langchain_community.document_loaders import PyPDFLoader
 
    loader = PyPDFLoader(str(path))
    docs = loader.load()
    for doc in docs:
        doc.metadata["source"] = "pdf"
        doc.metadata["filename"] = path.name
    return docs
 
 
def _parse_docx(path: Path) -> List[Document]:
    from langchain_community.document_loaders import Docx2txtLoader
 
    loader = Docx2txtLoader(str(path))
    docs = loader.load()
    for doc in docs:
        doc.metadata["source"] = "docx"
        doc.metadata["filename"] = path.name
    return docs
 
 
def _parse_excel(path: Path) -> List[Document]:
    xls = pd.ExcelFile(str(path))
    docs: List[Document] = []
 
    for sheet in xls.sheet_names:
        df = xls.parse(sheet)
        for i, row in df.iterrows():
            content = _clean_row(row)
            if not content.strip():
                continue
            docs.append(
                Document(
                    page_content=content,
                    metadata={
                        "source": "excel",
                        "filename": path.name,
                        "sheet": sheet,
                        "row": i,
                    },
                )
            )
    return docs
 
 
def _parse_txt(path: Path) -> List[Document]:
    text = path.read_text(encoding="utf-8", errors="replace")
    return [
        Document(
            page_content=text,
            metadata={"source": "txt", "filename": path.name},
        )
    ]
 
 
def _parse_csv(path: Path) -> List[Document]:
    """Each CSV row becomes its own Document (like Excel rows)."""
    try:
        df = pd.read_csv(str(path), dtype=str)
    except Exception as exc:
        logger.warning("CSV read failed with default settings (%s); retrying with latin-1.", exc)
        df = pd.read_csv(str(path), dtype=str, encoding="latin-1")
 
    docs: List[Document] = []
    for i, row in df.iterrows():
        content = _clean_row(row)
        if not content.strip():
            continue
        docs.append(
            Document(
                page_content=content,
                metadata={
                    "source": "csv",
                    "filename": path.name,
                    "row": i,
                },
            )
        )
    return docs

def _clean_row(row: pd.Series) -> str:
    """Serialise a DataFrame row into a readable key: value string."""
    return " | ".join(
        f"{col}: {row[col]}"
        for col in row.index
        if "Unnamed" not in str(col) and pd.notna(row[col]) and str(row[col]).strip()
    )


def _split(docs: List[Document]) -> List[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size = CHUNK_SIZE,
        chunk_overlap = CHUNK_OVERLAP
    )

    chunks: List[Document] = []

    for doc in docs:
        if doc.metadata.get("source") in ROW_BASED_SOURCE_EXT:
            chunks.append(doc)
        else:
            chunks.extend(splitter.split_documents([doc]))

        
    logger.info("Total chunks after splitting: %d", len(chunks))
    return chunks


