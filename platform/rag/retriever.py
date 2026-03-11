"""
retriever.py — Retrieval augmenté pour la knowledge base NetApp
CG CONSEIL — Plateforme MCO NetApp

Recherche les documents les plus pertinents dans la knowledge base
en fonction d'un événement ou d'une question. Alimente le contexte
des prompts Claude pour la génération de rapports et d'analyses.
"""

import json
import logging
import math
from pathlib import Path

logger = logging.getLogger(__name__)

EMBED_CACHE = Path(__file__).parent / ".embed_cache.json"
KB_DIR = Path(__file__).parent / "knowledge_base"


class Retriever:
    """
    Recherche les documents pertinents par similarité cosinus.

    Pour une production réelle, remplacer par une base vectorielle
    (pgvector, Chroma, Qdrant) pour de meilleures performances.
    """

    def __init__(self):
        self.cache: dict[str, list[float]] = self._load_cache()
        self.documents: dict[str, str] = self._load_documents()

    def retrieve(self, query_embedding: list[float], top_k: int = 5) -> list[dict]:
        """
        Retourne les top_k documents les plus proches de la requête.

        Args:
            query_embedding: Vecteur de la requête
            top_k: Nombre de résultats à retourner

        Returns:
            Liste de documents triés par similarité décroissante
        """
        scores = []
        for doc_id, embedding in self.cache.items():
            score = self._cosine_similarity(query_embedding, embedding)
            scores.append((doc_id, score))

        scores.sort(key=lambda x: x[1], reverse=True)
        results = []
        for doc_id, score in scores[:top_k]:
            content = self.documents.get(doc_id, "")
            results.append({
                "doc_id": doc_id,
                "score": round(score, 4),
                "content": content[:2000],  # Tronqué pour le contexte
                "source": doc_id.split("/")[0],
            })

        logger.info(f"Retrieval : {len(results)} documents retournés (top {top_k})")
        return results

    def retrieve_by_event(self, event_name: str, severity: str, top_k: int = 3) -> list[dict]:
        """
        Recherche contextuelle par nom d'événement EMS et sévérité.
        Utilisé pour enrichir les alertes avec des KB articles pertinents.

        Returns:
            Documents KB correspondant à l'événement
        """
        # Recherche lexicale simple par nom d'événement (avant embedding)
        results = []
        for doc_id, content in self.documents.items():
            if event_name.lower() in content.lower() or severity.lower() in content.lower():
                results.append({
                    "doc_id": doc_id,
                    "score": 1.0 if event_name.lower() in content.lower() else 0.5,
                    "content": content[:2000],
                    "source": doc_id.split("/")[0],
                })
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

    def build_context(self, docs: list[dict], max_chars: int = 4000) -> str:
        """Construit un bloc de contexte formaté pour insertion dans un prompt Claude."""
        parts = []
        total = 0
        for doc in docs:
            snippet = f"### {doc['doc_id']} (score: {doc['score']})\n{doc['content']}\n"
            if total + len(snippet) > max_chars:
                break
            parts.append(snippet)
            total += len(snippet)
        return "\n---\n".join(parts)

    @staticmethod
    def _cosine_similarity(a: list[float], b: list[float]) -> float:
        if len(a) != len(b):
            return 0.0
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x ** 2 for x in a))
        norm_b = math.sqrt(sum(x ** 2 for x in b))
        return dot / (norm_a * norm_b) if norm_a and norm_b else 0.0

    def _load_cache(self) -> dict:
        if EMBED_CACHE.exists():
            return json.loads(EMBED_CACHE.read_text())
        return {}

    def _load_documents(self) -> dict[str, str]:
        docs = {}
        for md_file in KB_DIR.glob("**/*.md"):
            doc_id = str(md_file.relative_to(KB_DIR))
            docs[doc_id] = md_file.read_text(encoding="utf-8", errors="replace")
        return docs
