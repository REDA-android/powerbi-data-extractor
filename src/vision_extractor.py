"""
Multimodal Vision Extractor for Power BI Dashboards & Screenshots.
Uses Gemini Vision models to extract structured tabular records from images.
"""

import base64
import json
import os
import re
import requests
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()


class PowerBIVisionExtractor:
    """Extracts tables, matrices, and visual metrics from Power BI screenshots."""

    BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"

    def __init__(self, model_name: str = "gemini-3.5-flash-lite"):
        self.model_name = model_name
        self.api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")

    def extract_from_image_bytes(
        self,
        image_bytes: bytes,
        mime_type: str = "image/png",
        custom_instructions: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Extracts structured tabular data from image bytes."""
        base64_img = base64.b64encode(image_bytes).decode("utf-8")

        prompt = f"""You are a specialized Power BI & Business Intelligence Data Extractor.
Analyze this Power BI dashboard/report screenshot with extreme precision.

Mission:
1. Identify all data tables, matrix visuals, KPI values, cards, bar/line chart data points, and lists.
2. Reconstruct the complete tabular data exactly as shown in the visual (preserve all columns, headers, numbers, percentages, dates, and category names).
3. If there are multiple visuals/tables, merge them logically or extract the primary data table.
4. Clean the data: trim spaces, preserve currency symbols or unit numbers, avoid truncation.
5. Return ONLY a valid JSON array of objects: `[ {{"col1": "val1", "col2": "val2"}}, ... ]`.

{f"Additional User Instruction: {custom_instructions}" if custom_instructions else ""}
"""

        models = [self.model_name, "gemini-3.5-flash", "gemini-flash-latest"]
        
        for model in models:
            url = f"{self.BASE_URL}/{model}:generateContent?key={self.api_key}"

            payload = {
                "contents": [
                    {
                        "parts": [
                            {"text": prompt},
                            {
                                "inlineData": {
                                    "mimeType": mime_type,
                                    "data": base64_img,
                                }
                            },
                        ]
                    }
                ],
                "generationConfig": {
                    "temperature": 0.1,
                    "maxOutputTokens": 4096,
                    "responseMimeType": "application/json",
                },
            }

            try:
                res = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=30)
                if res.status_code == 200:
                    data = res.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        raw_text = "".join(p.get("text", "") for p in parts).strip()
                        return self._parse_json_safely(raw_text)
                else:
                    print(f"[VisionExtractor] Model {model} HTTP {res.status_code}: {res.text[:100]}")
            except Exception as e:
                print(f"[VisionExtractor] Error calling {model}: {e}")

        return []

    def _parse_json_safely(self, text: str) -> List[Dict[str, Any]]:
        """Parses JSON array from text."""
        try:
            parsed = json.loads(text)
            if isinstance(parsed, list):
                return parsed
            elif isinstance(parsed, dict):
                for v in parsed.values():
                    if isinstance(v, list) and v and isinstance(v[0], dict):
                        return v
                return [parsed]
        except Exception:
            pass

        match = re.search(r"\[\s*\{.*\}\s*\]", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except Exception:
                pass
        return []
