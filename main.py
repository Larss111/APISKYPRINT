from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from pdf2docx import Converter
import shutil
import uuid
import subprocess
from pathlib import Path


app = FastAPI()

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Separamos las extensiones para evitar confusiones
TO_PDF_EXT = {'.doc', '.docx', '.odt', '.rtf', '.xls', '.xlsx', '.ods', '.ppt', '.pptx', '.odp'}
TO_WORD_EXT = {'.pdf'}

# Función para borrar archivos después de enviarlos
def remove_file(path: Path):
    if path.exists():
        path.unlink()

@app.post("/convert")
async def convert_to_pdf(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    ext = Path(file.filename).suffix.lower()
    if ext not in TO_PDF_EXT:
        raise HTTPException(status_code=400, detail="Extensión no soportada para PDF.")

    file_id = uuid.uuid4().hex
    input_path = UPLOAD_DIR / f"{file_id}{ext}"
    output_path = input_path.with_suffix('.pdf')

    try:
        with input_path.open("wb") as f:
            shutil.copyfileobj(file.file, f)

        subprocess.run([
            "soffice", "--headless", "--convert-to", "pdf", 
            "--outdir", str(UPLOAD_DIR), str(input_path)
        ], check=True, capture_output=True)

        # Agregamos la tarea de borrar el PDF después de enviarlo
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
    ext = Path(file.filename).suffix.lower()
    if ext != '.pdf':
        raise HTTPException(status_code=400, detail="Solo se permiten archivos PDF.")

    file_id = uuid.uuid4().hex
    input_path = UPLOAD_DIR / f"{file_id}.pdf"
    output_path = UPLOAD_DIR / f"{file_id}.docx"

    try:
        # Guardar archivo subido
        with input_path.open("wb") as f:
            shutil.copyfileobj(file.file, f)

        # Conversión ligera (usa menos RAM que LibreOffice)
        cv = Converter(str(input_path))
        cv.convert(str(output_path), start=0, end=None)
        cv.close()

        if not output_path.exists():
            raise HTTPException(status_code=500, detail="Error en la conversión")

        background_tasks.add_task(remove_file, output_path)

        return FileResponse(
            path=output_path,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            filename=f"SkyPrint_{file.filename.rsplit('.', 1)[0]}.docx"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if input_path.exists():
            input_path.unlink()