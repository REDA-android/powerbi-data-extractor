"""
MoMoA: Mixture of Mixture of Agents Engine.
Provides a multi-agent swarm with 4 specialized roles + 1 Consensus Master.
"""

import os
import json
import requests
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

load_dotenv()


class MoMoASwarm:
    """Orchestrates multi-agent deliberation and consensus synthesis."""

    BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"

    def __init__(self, model_name: str = "gemini-3.5-flash-lite"):
        self.model_name = model_name
        self.api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")

    def _call_llm(self, system_prompt: str, user_prompt: str, temperature: float = 0.2) -> str:
        """Helper to invoke Gemini."""
        url = f"{self.BASE_URL}/{self.model_name}:generateContent?key={self.api_key}"
        payload = {
            "contents": [
                {"parts": [{"text": f"{system_prompt}\n\nUser Request:\n{user_prompt}"}]}
            ],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": 2048,
            }
        }
        try:
            res = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=30)
            if res.status_code == 200:
                data = res.json()
                parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])
                return "".join(p.get("text", "") for p in parts).strip()
        except Exception as e:
            print(f"[MoMoA] Error calling LLM: {e}")
        return "Erreur lors de la génération de l'agent."

    def solve(self, task: str, context_data: Optional[str] = None) -> Dict[str, Any]:
        """Runs the 5-agent MoMoA swarm on a given task."""
        context_str = f"\nDonnées contextuelles disponibles :\n{context_data[:3000]}" if context_data else ""

        # 1. Aria - The System Architect
        aria_system = "Tu es Aria, Architecte Logiciel & BI Senior. Propose une conception claire, modulaire et structurée pour résoudre ce problème."
        aria_proposal = self._call_llm(aria_system, f"{task}{context_str}", temperature=0.3)

        # 2. Devon - The Core Engineer
        devon_system = "Tu es Devon, Ingénieur Principal en Développement & DAX. Écris le code source complet, robuste et fonctionnel sans placeholders."
        devon_code = self._call_llm(devon_system, f"Tâche: {task}\nConception d'Aria:\n{aria_proposal}{context_str}", temperature=0.1)

        # 3. Vigil - Security & Edge Cases Auditor
        vigil_system = "Tu es Vigil, Auditeur en Sécurité et Robustesse. Identifie les failles potentielles, cas limites, injections ou divisions par zéro."
        vigil_review = self._call_llm(vigil_system, f"Code de Devon:\n{devon_code}", temperature=0.2)

        # 4. Volt - Performance Optimizer
        volt_system = "Tu es Volt, Expert en Optimisation et Performance (Vitesse, Mémoire, DAX Engine). Propose des gains d'efficacité."
        volt_suggestions = self._call_llm(volt_system, f"Code de Devon:\n{devon_code}", temperature=0.2)

        # 5. Nexus - Master Arbiter & Consensus Synthesizer
        nexus_system = """Tu es Nexus, Arbitre Suprême MoMoA. 
Synthétise les avis des 4 spécialistes (Aria, Devon, Vigil, Volt) pour produire le code final parfait et une brève synthèse claire."""
        nexus_prompt = f"""Tâche originale : {task}
- Proposition d'Aria (Architecte) : {aria_proposal}
- Code de Devon (Ingénieur) : {devon_code}
- Audit de Vigil (Sécurité) : {vigil_review}
- Optimisations de Volt : {volt_suggestions}

Fournis la synthèse finale avec le code définitif prêt à l'emploi."""
        final_consensus = self._call_llm(nexus_system, nexus_prompt, temperature=0.1)

        return {
            "success": True,
            "task": task,
            "agents": {
                "aria": {"role": "Architecte Système", "avatar": "📐", "response": aria_proposal},
                "devon": {"role": "Ingénieur Développeur", "avatar": "💻", "response": devon_code},
                "vigil": {"role": "Auditeur Sécurité", "avatar": "🛡️", "response": vigil_review},
                "volt": {"role": "Optimiseur Performance", "avatar": "⚡", "response": volt_suggestions},
            },
            "nexus_consensus": final_consensus,
        }
