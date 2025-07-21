from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
import os
import shutil
import uuid
import subprocess
from pathlib import Path

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "API SkyPrint activa. Usa /docs para probar."}

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {'.doc', '.docx', '.odt'}

@app.post("/convert")
async def convert_to_pdf(file: UploadFile = File(...)):
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Archivo no compatible. Usa .doc, .docx u .odt")

    file_id = uuid.uuid4().hex
    input_path = UPLOAD_DIR / f"{file_id}{ext}"
    output_path = input_path.with_suffix('.pdf')

    try:
        with input_path.open("wb") as f:
            shutil.copyfileobj(file.file, f)

        result = subprocess.run([
            "soffice", "--headless", "--convert-to", "pdf", "--outdir",
            str(UPLOAD_DIR), str(input_path)
        ], capture_output=True, text=True)

        if result.returncode != 0:
            raise HTTPException(status_code=500, detail=f"Error al convertir: {result.stderr.strip()}")

        if not output_path.exists():
            raise HTTPException(status_code=500, detail="No se generó el PDF")

        return FileResponse(
            path=output_path,
            media_type="application/pdf",
            filename=output_path.name
        )

    finally:
        if input_path.exists():
            input_path.unlink()