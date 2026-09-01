"""
Chatbot Assistant Engine for Power BI & Data Analytics.
Provides multi-turn intelligent conversation with contextual knowledge of extracted datasets.
"""

import os
import json
import requests
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()


class PowerBIChatbot:
    """Conversational assistant for Power BI, DAX formulas, and data analysis."""

    BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"

    def __init__(self, model_name: str = "gemini-3.5-flash-lite"):
        self.model_name = model_name
        self.api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")

    def reply(
        self,
        messages: List[Dict[str, str]],
        current_data: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        """
        Processes conversation history and returns an intelligent response.
        """
        system_instruction = """Tu es l'Assistant IA Expert de PowerBI Data Extractor & Analytics.
Tes capacités :
1. Analyser et interpréter les données du tableau actuellement extrait (statistiques, totaux, moyennes, anomalies, corrélations).
2. Rédiger et optimiser des formules DAX (CALCULATE, SUMX, FILTER, Time Intelligence, DATESYTD, etc.) pour Power BI.
3. Rédiger du code Python, SQL, ou des scripts Power Query (M) pour nettoyer et modéliser les données.
4. Répondre avec clarté, concision et formattage soigné (tableaux markdown, code blocks)."""

        if current_data:
            sample_data_str = json.dumps(current_data[:25], indent=2, ensure_ascii=False)
            system_instruction += f"\n\n[CONTEXTE DU TABLEAU EXTRAIT ({len(current_data)} lignes au total)] :\n{sample_data_str}"

        # Format Gemini contents
        contents = []
        for msg in messages:
            role = "user" if msg.get("role") == "user" else "model"
            contents.append({"role": role, "parts": [{"text": msg.get("content", "")}]})

        url = f"{self.BASE_URL}/{self.model_name}:generateContent?key={self.api_key}"
        payload = {
            "system_instruction": {"parts": [{"text": system_instruction}]},
            "contents": contents,
            "generationConfig": {
                "temperature": 0.3,
                "maxOutputTokens": 2048,
            }
        }

        try:
            res = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=25)
            if res.status_code == 200:
                data = res.json()
                parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])
                return "".join(p.get("text", "") for p in parts).strip()
            else:
                return f"Erreur Gemini ({res.status_code}): {res.text[:100]}"
        except Exception as e:
            return f"Erreur de communication avec l'assistant : {str(e)}"
