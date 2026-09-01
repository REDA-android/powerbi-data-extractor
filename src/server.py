"""
PowerBI Extractor - FastAPI Server.
Provides endpoints for Vision-based screenshot extraction and Playwright URL scraping.
"""

import os
import sys
import time
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Response
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Ensure src is on Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from vision_extractor import PowerBIVisionExtractor
from network_interceptor import PowerBINetworkInterceptor
from exporter import PowerBIExporter
from pbix_generator import PBIXGenerator
from momoa_engine import MoMoASwarm
from chatbot_engine import PowerBIChatbot

app = FastAPI(title="PowerBI Data Extractor", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static")
os.makedirs(STATIC_DIR, exist_ok=True)

vision = PowerBIVisionExtractor()
interceptor = PowerBINetworkInterceptor(vision)
momoa = MoMoASwarm()
chatbot = PowerBIChatbot()


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    current_data: Optional[List[Dict[str, Any]]] = None


class MoMoARequest(BaseModel):
    task: str
    context_data: Optional[str] = None


class URLExtractRequest(BaseModel):
    url: str
    timeout_sec: Optional[int] = 25


class ExportRequest(BaseModel):
    records: List[Dict[str, Any]]
    filename: Optional[str] = "powerbi_extracted_data"


@app.get("/", response_class=HTMLResponse)
async def serve_ui():
    index_file = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_file):
        with open(index_file, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>PowerBI Extractor UI Loading...</h1>"


@app.get("/api/health")
async def health():
    return {
        "status": "online",
        "vision_model": vision.model_name,
        "api_configured": bool(vision.api_key),
    }


@app.post("/api/extract/screenshot")
async def extract_screenshot(
    file: UploadFile = File(...),
    instructions: Optional[str] = Form(None),
):
    """
    Méthode 1: Extrait les données tabulaires d'une capture d'écran Power BI via Gemini Vision.
    """
    start = time.time()
    contents = await file.read()
    mime_type = file.content_type or "image/png"

    records = vision.extract_from_image_bytes(
        image_bytes=contents,
        mime_type=mime_type,
        custom_instructions=instructions,
    )

    elapsed = round(time.time() - start, 2)
    columns = []
    if records:
        for r in records:
            for k in r.keys():
                if k not in columns:
                    columns.append(k)

    return {
        "success": True,
        "method": "vision_multimodal_ia",
        "filename": file.filename,
        "count": len(records),
        "columns": columns,
        "records": records,
        "execution_time_sec": elapsed,
    }


@app.post("/api/extract/url")
async def extract_url(req: URLExtractRequest):
    """
    Méthode 2: Intercepte les requêtes réseau Power BI ou capture la vue avec Playwright.
    """
    start = time.time()
    result = await interceptor.scrape_powerbi_url(req.url, timeout_sec=req.timeout_sec or 25)
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Impossible d'extraire les données du rapport"))

    records = result.get("records", [])
    elapsed = round(time.time() - start, 2)

    columns = []
    if records:
        for r in records:
            for k in r.keys():
                if k not in columns:
                    columns.append(k)

    return {
        "success": True,
        "method": result.get("method"),
        "url": req.url,
        "count": len(records),
        "columns": columns,
        "records": records,
        "execution_time_sec": elapsed,
    }


@app.post("/api/export/excel")
async def export_excel(req: ExportRequest):
    filename = f"{req.filename or 'powerbi_data'}.xlsx"
    excel_bytes = PowerBIExporter.to_excel_bytes(req.records)
    return Response(
        content=excel_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@app.post("/api/export/csv")
async def export_csv(req: ExportRequest):
    filename = f"{req.filename or 'powerbi_data'}.csv"
    csv_bytes = PowerBIExporter.to_csv_bytes(req.records)
    return Response(
        content=csv_bytes,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@app.post("/api/export/pbix")
async def export_pbix(req: ExportRequest):
    """Génère et télécharge une archive Power BI Template (.pbit / .pbix) complète."""
    filename = f"{req.filename or 'powerbi_report'}.pbit"
    pbix_bytes = PBIXGenerator.generate_pbix_bytes(req.records, report_title="Rapport Power BI Extrait")
    return Response(
        content=pbix_bytes,
        media_type="application/octet-stream",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@app.post("/api/chat")
async def chat_endpoint(req: ChatRequest):
    """Assistant Chatbot contextuel pour poser des questions ou générer des formules DAX/Python."""
    raw_messages = [{"role": m.role, "content": m.content} for m in req.messages]
    response_text = chatbot.reply(messages=raw_messages, current_data=req.current_data)
    return {"reply": response_text}


@app.post("/api/momoa/solve")
async def momoa_solve_endpoint(req: MoMoARequest):
    """Essaim multi-agents MoMoA (Aria, Devon, Vigil, Volt, Nexus)."""
    res = momoa.solve(task=req.task, context_data=req.context_data)
    return res
