import json
import logging
import os
from urllib.parse import unquote_plus

import boto3

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

ssm = boto3.client("ssm")

EC2_INSTANCE_ID  = os.environ["EC2_INSTANCE_ID"]
MASTER_CHROMA_DIR = os.environ.get("MASTER_CHROMA_DIR", "/opt/chroma_master")
MERGE_SCRIPT_PATH = os.environ.get("MERGE_SCRIPT_PATH", "/opt/chroma_agent/ec2_merge_agent.py")
PYTHON_BIN        = os.environ.get("PYTHON_BIN", "/opt/chroma_agent/venv/bin/python")


def lambda_handler(event, context):
    for record in event.get("Records", []):
        bucket = record["s3"]["bucket"]["name"]
        key    = unquote_plus(record["s3"]["object"]["key"])

        if not key.endswith("_chroma.zip"):
            logger.info("Skipping: %s", key)
            continue

        logger.info("New chroma zip: s3://%s/%s", bucket, key)

        command = (
            f"{PYTHON_BIN} {MERGE_SCRIPT_PATH} "
            f"--bucket '{bucket}' "
            f"--key '{key}' "
            f"--master-dir '{MASTER_CHROMA_DIR}'"
        )

        resp = ssm.send_command(
            InstanceIds=[EC2_INSTANCE_ID],
            DocumentName="AWS-RunShellScript",
            Parameters={
                "commands": [command],
                "executionTimeout": ["600"],
            },
            Comment=f"Chroma merge: {key}",
        )

        cmd_id = resp["Command"]["CommandId"]
        logger.info("SSM command dispatched: %s", cmd_id)

    return {"statusCode": 200}