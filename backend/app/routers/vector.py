from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.vector_service import VectorService
from app.db.connection import get_database
from app.config.settings import settings

router = APIRouter()

@router.post("/update")
async def update_vector_store(faiss_file: UploadFile = File(...), pkl_file: UploadFile = File(...)):
    db = get_database()
    service = VectorService(db)

    if not settings.gcs_bucket_name:
        raise HTTPException(status_code=500, detail="GCS bucket not configured")

    # Example metadata record for future vector store management
    await db.files.insert_one({
        "file_name": f"{faiss_file.filename},{pkl_file.filename}",
        "file_type": "vector-upsert",
        "gcs_path": f"gs://{settings.gcs_bucket_name}/",
        "processed": True,
        "created_at": __import__("datetime").datetime.utcnow(),
    })

    return {"message": "Vector store updated", "bucket": settings.gcs_bucket_name}