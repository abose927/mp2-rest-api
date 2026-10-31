import io
import json
import logging
from pathlib import Path
import pandas as pd
from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from src import DatasetInfo, DatasetStorage, HealthResponse, setup_logging

setup_logging(verbose=True)
logger = logging.getLogger(__name__)

app = FastAPI(title="Data Processing API", version="1.0.0")
storage = DatasetStorage()

@app.get("/health", response_model=HealthResponse)
def health_check():
    """Return the application status and version."""
    return {"status": "ok", "version": "1.0.0"}

@app.post("/upload", response_model=DatasetInfo)
async def upload_dataset(file: UploadFile = File(...)):
    """Read and store a CSV upload."""
    file_name = file.filename
    suffix = Path(file.filename or "").suffix.lower()
    if suffix != ".csv":
        logger.warning(f"Unsupported file format: {suffix}")
        raise HTTPException(status_code=400, detail="Unsupported file format")
    try:
        contents = await file.read()
        df = pd.read_csv(io.BytesIO(contents))
    
    except pd.errors.EmptyDataError:
        logger.warning(f"File is empty: {file_name}")
        raise HTTPException(status_code=400, detail="File is empty")
    except pd.errors.ParserError:
        logger.warning(f"Failed to parse the file: {file_name}")
        raise HTTPException(status_code=400, detail="Failed to parse the file")
    except UnicodeDecodeError:
        logger.warning(f"Decoding failed: {file_name}")
        raise HTTPException(status_code=400, detail="Decoding failed")

    dataset_id = storage.save(df, file_name)
    logger.info(f"Uploaded dataset: id={dataset_id}, filename={file_name}, rows={len(df)}")
    return storage.get_metadata(dataset_id)



@app.get("/datasets/{dataset_id}")
def get_dataset(dataset_id: int, limit: int = Query(default=100, ge=1)):
    """Return up to limit rows from a stored dataset."""
    df = storage.get(dataset_id)
    if df is None:
        logger.warning(f"Dataset not found: {dataset_id}")
        raise HTTPException(status_code=404, detail="Dataset not found")

    records = json.loads(df.head(limit).to_json(orient="records"))
    logger.info(f"Retrieved dataset: id={dataset_id}, returned_rows={len(records)}")
    return {"id": dataset_id, "data": records, "total_rows": len(df)}