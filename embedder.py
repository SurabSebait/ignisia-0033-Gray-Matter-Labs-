import os
import logging
from typing import List

from langchain.schema import Document

logger = logging.getLogger(__name__)

# Hugging-Face Transformer Cache 
os.environ.setdefault("TRANSFORMERS_CACHE", "/tmp/hf_cache")

os.environ.setdefault("HF_HOME", "/tmp/hf_cache")

EMBED_MODEL = os.environ.get(
    "EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
)

def build_chroma_index(
        docs: List[Document],
        collection_name: str,
        persistance_dir: str
) -> None:
    
    if not docs:
        raise ValueError("No documents to embed - aborting...")
    
    logger.info("Loading Embedding Model: %s", EMBED_MODEL)
    
    from langchain_huggingface import HuggingFaceEmbeddings

    embeddings = HuggingFaceEmbeddings(
        model_name = EMBED_MODEL,
        model_kwargs = {"device": "cpu"},
        encode_kwargs = {"normalize_embeddings" : True},
    )

    logger.info(
        "Building ChromaDB Collection '%s' -> '%s", collection_name, persistance_dir
    )

    import chromadb
    from langchain_chroma import Chroma

    chroma_client = chromadb.PersistentClient(path=persistance_dir)

    vectorstore = Chroma(
        client = chroma_client,
        collection_name=collection_name,
        embedding_function=embeddings
    )

    BATCH_SIZE = 500
    for i in range(0, len(docs), BATCH_SIZE):
        batch = docs[i : i + BATCH_SIZE]
        vectorstore.add_documents(batch)
        logger.info(
            "  Inserted batch %d/%d (%d docs)",
            i // BATCH_SIZE + 1,
            -(-len(docs) // BATCH_SIZE),  # ceiling division
            len(batch),
        )

    logger.info(
        "ChromaDB collection '%s' persisted with %d documents.", collection_name, len(docs)
    )