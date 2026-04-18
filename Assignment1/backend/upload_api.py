from datetime import datetime
import os
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse

router = APIRouter()

UPLOAD_DIR = "uploads"

os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    if_exists: str = Form("reject", pattern="^(overwrite|reject)$")
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename cannot be empty")
    
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    action_taken = "created"

    if os.path.exists(file_path):
        if if_exists == "reject":
            raise HTTPException(
                status_code=409,
                detail=f"File '{file.filename}' already exists. Set if_exists to 'overwrite' to replace it."
            )
        action_taken = "overwritten"

    try:
        with open(file_path, "wb") as f:
            f.write(await file.read())
    except OSError as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")

    return JSONResponse({
        "status": "success",
        "filename": file.filename,
        "save_path": file_path,
        "action_taken": action_taken
    })
    
@router.get("/list-files")
async def list_uploaded_files():
    if not os.path.isdir(UPLOAD_DIR):
        raise HTTPException(status_code=404, detail="Upload directory not found")
    
    files = []
    for filename in os.listdir(UPLOAD_DIR):
        file_path = os.path.join(UPLOAD_DIR, filename)
        if os.path.isfile(file_path):
            stat = os.stat(file_path)
            files.append({
                "filename": filename,
                "file_size": stat.st_size,
                "last_modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
            })
    
    return {
        "status": "success",
        "count": len(files),
        "files": files
    }