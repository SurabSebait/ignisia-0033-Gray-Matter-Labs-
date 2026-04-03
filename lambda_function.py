import os
import json
import boto3
import tempfile
import logging
import shutil
import zipfile
from pathlib import Path
from urllib.parse import unquote_plus

import pandas as pd

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS, Chroma

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Destination bucket where the updated embeddings are to be populated
DEST_BUCKET = os.environ["DEST_BUCKET"]

# Chroma vector database file prefix
CHROMA_COLLECTION_PREFIX = os.environ.get("CHROMA_COLLECTION_PREFIX", "docs")


EMBED_MODEL      = os.environ.get("EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
CHUNK_SIZE       = int(os.environ.get("CHUNK_SIZE", "1000"))
CHUNK_OVERLAP    = int(os.environ.get("CHUNK_OVERLAP", "200"))

SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".xlsx", ".txt", ".csv"}


# S3 client initialization
s3 = boto3.client("s3")


def lambda_handler(event, context):
    """Process every new S3 object listed in the event records."""
    results = []
 
    for record in event.get("Records", []):
        source_bucket = record["s3"]["bucket"]["name"]
        object_key = unquote_plus(record["s3"]["object"]["key"])
 
        ext = Path(object_key).suffix.lower()
        if ext not in SUPPORTED_EXTENSIONS:
            logger.info("Skipping unsupported file type '%s': %s", ext, object_key)
            results.append({"key": object_key, "status": "skipped", "reason": f"unsupported extension {ext}"})
            continue
 
        logger.info("Processing s3://%s/%s", source_bucket, object_key)
        try:
            dest_key = process_object(source_bucket, object_key, ext)
            logger.info("Uploaded ChromaDB zip → s3://%s/%s", DEST_BUCKET, dest_key)
            results.append({"key": object_key, "status": "success", "dest_key": dest_key})
        except Exception as exc:
            logger.exception("Failed to process %s: %s", object_key, exc)
            results.append({"key": object_key, "status": "error", "error": str(exc)})
            # Re-raise so Lambda marks this invocation as failed and SQS/DLQ
            # can retry / capture the message.
            raise
 
    return {"statusCode": 200, "body": json.dumps(results)}


def process_object(source_bucket: str, object_key: str, ext: str) -> str:
  """
  Download → parse → embed → persist ChromaDB → zip → upload.

  Returns the S3 key of the uploaded zip.
  """
  # Lazy imports keep cold-start latency manageable and isolate heavy deps.
  from document_parser import parse_file
  from embedder import build_chroma_index

  with tempfile.TemporaryDirectory(dir="/tmp") as work_dir:
      work_dir = Path(work_dir)

      # 1. Download the source file
      local_file = work_dir / Path(object_key).name
      logger.info("Downloading to %s", local_file)

      # Commenting following line for local testing
    #   s3.download_file(source_bucket, object_key, str(local_file))

      local_test_file = "test.pdf"
      shutil.copy(local_test_file, local_file)




      # 2. Parse into LangChain Documents
      docs = parse_file(local_file, ext)
      logger.info("Parsed %d document chunks from %s", len(docs), object_key)

      # 3. Build & persist a ChromaDB collection
      #    Collection name: prefix + sanitised filename stem
      stem = Path(object_key).stem
      safe_stem = "".join(c if c.isalnum() or c in "-_" else "_" for c in stem)
      collection_name = f"{CHROMA_COLLECTION_PREFIX}_{safe_stem}"[:63]  # Chroma limit

      chroma_dir = work_dir / "chroma_index"
      build_chroma_index(docs, collection_name, str(chroma_dir))

      # 4. Zip the ChromaDB directory
      zip_path = work_dir / f"{safe_stem}_chroma.zip"
      _zip_directory(chroma_dir, zip_path)
      logger.info("Zipped ChromaDB to %s (%.1f MB)", zip_path, zip_path.stat().st_size / 1e6)

      # 5. Upload zip to destination bucket
      #    Mirror the source key path, swap extension → _chroma.zip
      dest_key = _build_dest_key(object_key)

      # Commenting out following upload for local testing
    #   s3.upload_file(str(zip_path), DEST_BUCKET, dest_key)
    
      local_output_dir = Path("local_output")
      local_output_dir.mkdir(exist_ok=True)

      local_output_path = local_output_dir / Path(dest_key).name
      shutil.copy(zip_path, local_output_path)

      logger.info("Saved locally %s", local_output_path)

  return dest_key

def _build_dest_key(source_key: str) -> str:
    """
    Convert a source S3 key into the destination key.
 
    Example:
        raw/reports/Q1_financials.pdf  →  embeddings/reports/Q1_financials_chroma.zip
    """

    p = Path(source_key)
    # Replace leading path segment (if any) with 'embeddings/'
    parts = p.parts
    if len(parts) > 1:
        new_parts = ("embeddings",) + parts[1:-1] + (p.stem + "_chroma.zip",)
    else:
        new_parts = ("embeddings", p.stem + "_chroma.zip")
    return "/".join(new_parts)


def _zip_directory(source_dir: Path, output_path: Path) -> None:
    """Recursively zip *source_dir* into *output_path*."""
    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for file in source_dir.rglob("*"):
            if file.is_file():
                zf.write(file, file.relative_to(source_dir))
