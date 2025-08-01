import os
import json
import shutil
import tempfile
from typing import List

from fastapi import FastAPI, UploadFile, File, HTTPException, Request, Form
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from processing.pdf_parser import extract_pdf_lines_cleaned_and_merged
from processing.outliner import extract_outline
from processing.ranker import run_persona_ranking

app = FastAPI(
    title="Persona-Based Document Intelligence API",
    description="Uploads PDFs and a persona job, returns ranked sections.",
    version="1.0.0"
)

templates = Jinja2Templates(directory="templates")

BASE_CONTENT_DIR = "content"

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("upload.html", {"request": request})

@app.get("/results", response_class=HTMLResponse)
async def results_page(request: Request):
    return templates.TemplateResponse("results.html", {"request": request})

@app.post("/process/", response_class=JSONResponse)
async def process_documents(
    input_json_file: UploadFile = File(...),
    pdf_files: List[UploadFile] = File(...)
):
    """
    This endpoint processes uploaded PDFs based on a persona and job description.

    - **input_json_file**: The JSON file containing the persona and job.
    - **pdf_files**: A list of PDF files to be analyzed.
    """
    
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            content_path = os.path.join(temp_dir, BASE_CONTENT_DIR)
            pdfs_path = os.path.join(content_path, "pdfs")
            parsed_outlines_path = os.path.join(content_path, "parsed_outlines")

            os.makedirs(pdfs_path)
            os.makedirs(parsed_outlines_path)

            input_json_path = os.path.join(content_path, "challenge1b_input.json")
            with open(input_json_path, "wb") as f:
                shutil.copyfileobj(input_json_file.file, f)

            for pdf in pdf_files:
                pdf_location = os.path.join(pdfs_path, pdf.filename)
                with open(pdf_location, "wb") as f:
                    shutil.copyfileobj(pdf.file, f)

        
            with open(input_json_path, 'r') as f:
                input_data = json.load(f)
            
            pdf_filenames_in_order = [doc['filename'] for doc in input_data.get('documents', [])]

            for i, pdf_filename in enumerate(pdf_filenames_in_order):
                pdf_path = os.path.join(pdfs_path, pdf_filename)
                
                if not os.path.exists(pdf_path):
                    print(f"Warning: PDF file {pdf_filename} listed in JSON but not uploaded. Skipping.")
                    continue

                print(f"Processing PDF: {pdf_filename}...")

                parsed_data = extract_pdf_lines_cleaned_and_merged(pdf_path)
                
                temp_parsed_json_path = os.path.join(temp_dir, f"temp_parsed_{i}.json")
                with open(temp_parsed_json_path, "w", encoding="utf-8") as f:
                    json.dump(parsed_data, f, ensure_ascii=False, indent=2)

                final_outline_path = os.path.join(parsed_outlines_path, f"file{i}_outline.json")
                extract_outline(temp_parsed_json_path, final_outline_path)

            print("All PDFs parsed. Running final ranking...")
            final_ranked_output = run_persona_ranking(content_path)
            
            if not final_ranked_output:
                raise HTTPException(status_code=500, detail="Failed to generate final ranking.")

            return JSONResponse(content=final_ranked_output, status_code=200)

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
