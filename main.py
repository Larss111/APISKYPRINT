import asyncio 
from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from pdf2docx import Converter
import shutil
import uuid
import subprocess
from pathlib import Path

app = FastAPI()
conversion_lock = asyncio.Lock() 

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

TO_PDF_EXT = {'.doc', '.docx', '.odt', '.rtf', '.xls', '.xlsx', '.ods', '.ppt', '.pptx', '.odp'}
MAX_FILE_SIZE = 10 * 1024 * 1024

def remove_file(path: Path):
    try:
        if path.exists():
            path.unlink()
    except Exception as e:
        print(f"Error borrando archivo: {e}")

@app.post("/convert")
async def convert_to_pdf(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    if file.size and file.size > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="Archivo demasiado grande.")
    
    ext = Path(file.filename).suffix.lower()
    if ext not in TO_PDF_EXT:
        raise HTTPException(status_code=400, detail="Extensión no soportada.")

    file_id = uuid.uuid4().hex
    input_path = UPLOAD_DIR / f"{file_id}{ext}"
    output_path = input_path.with_suffix('.pdf')

    # Usamos el LOCK 
    async with conversion_lock: 
        try:
            with input_path.open("wb") as f:
                shutil.copyfileobj(file.file, f)

            # Ejecutamos LibreOffice
            result = subprocess.run([
                "soffice", "--headless", "--convert-to", "pdf", 
                "--outdir", str(UPLOAD_DIR), str(input_path)
            ], check=True, capture_output=True)

            if not output_path.exists():
                raise Exception("LibreOffice no generó el archivo.")

            background_tasks.add_task(remove_file, output_path)

            return FileResponse(
                path=output_path,
                media_type="application/pdf",
                filename=f"SkyPrint_{file.filename.rsplit('.', 1)[0]}.pdf"
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
        finally:
            remove_file(input_path)

@app.post("/convert-to-word")
async def convert_to_word(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    file_id = uuid.uuid4().hex
    input_path = UPLOAD_DIR / f"{file_id}.pdf"
    output_path = UPLOAD_DIR / f"{file_id}.docx"

    async with conversion_lock:
        try:
            with input_path.open("wb") as f:
                shutil.copyfileobj(file.file, f)

            cv = Converter(str(input_path))
            cv.convert(str(output_path), start=0, end=None)
            cv.close()

            background_tasks.add_task(remove_file, output_path)

            return FileResponse(
                path=output_path,
                media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                filename=f"SkyPrint_{file.filename.rsplit('.', 1)[0]}.docx"
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
        finally:
            remove_file(input_path)