"""
Unit and Integration Tests for PowerBI Scraper & Extractor.
"""

import os
import sys
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from exporter import PowerBIExporter
from vision_extractor import PowerBIVisionExtractor
from server import app

client = TestClient(app)


def test_exporter_excel():
    records = [
        {"Région": "Nord", "Ventes (€)": 150000, "Marge (%)": "24.5%"},
        {"Région": "Sud", "Ventes (€)": 210000, "Marge (%)": "28.0%"},
    ]
    excel_bytes = PowerBIExporter.to_excel_bytes(records)
    assert isinstance(excel_bytes, bytes)
    assert len(excel_bytes) > 500


def test_exporter_csv():
    records = [
        {"Région": "Nord", "Ventes": 150000},
        {"Région": "Sud", "Ventes": 210000},
    ]
    csv_bytes = PowerBIExporter.to_csv_bytes(records)
    assert isinstance(csv_bytes, bytes)
    assert b"Nord" in csv_bytes
    assert b"150000" in csv_bytes


def test_health_endpoint():
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json()["status"] == "online"


def test_vision_json_parser():
    vision = PowerBIVisionExtractor()
    json_text = '[{"Région": "Nord", "Chiffre_Affaires": 45000}]'
    res = vision._parse_json_safely(json_text)
    assert isinstance(res, list)
    assert len(res) == 1
    assert res[0]["Région"] == "Nord"


def test_pbix_generator():
    from pbix_generator import PBIXGenerator
    records = [{"Produit": "Laptop", "Prix": 1200, "EnStock": True}]
    pbix_bytes = PBIXGenerator.generate_pbix_bytes(records)
    assert isinstance(pbix_bytes, bytes)
    assert len(pbix_bytes) > 200
    
    # Verify valid zip containing DataModelSchema and Report/Layout
    import zipfile, io
    zf = zipfile.ZipFile(io.BytesIO(pbix_bytes))
    assert "DataModelSchema" in zf.namelist()
    assert "Report/Layout" in zf.namelist()
    assert "[Content_Types].xml" in zf.namelist()


def test_pbix_export_route():
    res = client.post(
        "/api/export/pbix",
        json={"records": [{"a": "test", "b": 123}]},
    )
    assert res.status_code == 200
    assert "application/octet-stream" in res.headers["content-type"]


def test_chatbot_endpoint():
    res = client.post(
        "/api/chat",
        json={
            "messages": [{"role": "user", "content": "Hello"}],
            "current_data": [{"col1": "A", "col2": 100}],
        }
    )
    assert res.status_code == 200
    assert "reply" in res.json()


def test_momoa_endpoint():
    res = client.post(
        "/api/momoa/solve",
        json={"task": "Calculer la TVA"},
    )
    assert res.status_code == 200
    data = res.json()
    assert "agents" in data
    assert "aria" in data["agents"]
    assert "nexus_consensus" in data
