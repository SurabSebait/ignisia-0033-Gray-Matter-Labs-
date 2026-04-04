"""
ec2_merge_agent.py — runs ON the EC2 instance via SSM.

Downloads new *_chroma.zip from S3, extracts it, and merges every
collection into the master ChromaDB using pre-computed embeddings
(no model/torch needed on EC2).
"""

import argparse
import logging
import sys
import tempfile
import zipfile
from pathlib import Path

import boto3
import chromadb

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

s3 = boto3.client("s3")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--bucket",      required=True)
    parser.add_argument("--key",         required=True)
    parser.add_argument("--master-dir",  required=True)
    args = parser.parse_args()

    master_dir = Path(args.master_dir)
    master_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)

        # 1. Download zip from S3
        zip_path = tmp / Path(args.key).name
        logger.info("Downloading s3://%s/%s", args.bucket, args.key)
        s3.download_file(args.bucket, args.key, str(zip_path))

        # 2. Extract
        extract_dir = tmp / "new_chroma"
        extract_dir.mkdir()
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(extract_dir)
        logger.info("Extracted to %s", extract_dir)

        # 3. Merge into master
        source_client = chromadb.PersistentClient(path=str(extract_dir))
        master_client = chromadb.PersistentClient(path=str(master_dir))

        for col_meta in source_client.list_collections():
            source_col = source_client.get_collection(col_meta.name)
            master_col = master_client.get_or_create_collection(
                name=col_meta.name,
                metadata=source_col.metadata or {},
            )

            total = source_col.count()
            logger.info("Merging collection '%s' (%d docs)", col_meta.name, total)

            # Batch copy with pre-computed embeddings — no re-embedding needed
            batch_size = 500
            for offset in range(0, total, batch_size):
                batch = source_col.get(
                    limit=batch_size,
                    offset=offset,
                    include=["documents", "metadatas", "embeddings"],
                )
                master_col.upsert(
                    ids=batch["ids"],
                    documents=batch["documents"],
                    metadatas=batch["metadatas"],
                    embeddings=batch["embeddings"],
                )
                logger.info("  Upserted %d/%d", min(offset + batch_size, total), total)

        logger.info("Done — master index at %s", master_dir)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.exception("Merge failed: %s", e)
        sys.exit(1)