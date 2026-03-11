"""
embeddings.py — Génération d'embeddings pour la base de connaissances RAG
CG CONSEIL — Plateforme MCO NetApp

Génère et stocke les embeddings vectoriels des documents de la knowledge base
(articles KB NetApp, procédures techniques, historique incidents).
Utilise l'API Claude/Anthropic pour les embeddings ou un modèle local.
"""

import json
import logging
from pathlib import Path
from dataclasses import dataclass

import anthropic

logger = logging.getLogger(__name__)

KB_DIR = Path(__file__).parent / "knowledge_base"
EMBED_CACHE = Path(__file__).parent / ".embed_cache.json"

# Modèle d'embedding — peut être remplacé par un modèle local (sentence-transformers)
EMBED_MODEL = "voyage-3"  # Via Anthropic / Voyage AI


@dataclass
class Document:
    doc_id: str
    source: str        # netapp_kb | working_instructions | incident_history
    title: str
    content: str
    metadata: dict


class EmbeddingsManager:
    """Gère la génération et le cache des embeddings de la knowledge base."""

    def __init__(self, api_key: str | None = None):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.cache: dict[str, list[float]] = self._load_cache()

    def index_knowledge_base(self, force_reindex: bool = False) -> int:
        """
        Indexe tous les documents de la knowledge base.

        Returns:
            Nombre de documents indexés
        """
        docs = self._load_documents()
        indexed = 0

        for doc in docs:
            if doc.doc_id in self.cache and not force_reindex:
                continue
            try:
                embedding = self._embed(doc.content)
                self.cache[doc.doc_id] = embedding
                indexed += 1
                logger.debug(f"Indexé : {doc.doc_id}")
            except Exception as e:
                logger.error(f"Erreur embedding {doc.doc_id} : {e}")

        self._save_cache()
        logger.info(f"Indexation terminée : {indexed} nouveaux documents")
        return indexed

    def _embed(self, text: str) -> list[float]:
        """Génère un embedding via l'API (placeholder — adapter selon provider)."""
        # TODO: Implémenter avec Voyage AI via anthropic client ou sentence-transformers local
        # Exemple avec sentence-transformers (sans coût API) :
        # from sentence_transformers import SentenceTransformer
        # model = SentenceTransformer("all-MiniLM-L6-v2")
        # return model.encode(text).tolist()
        raise NotImplementedError("Configurer le provider d'embedding dans .env")

    def _load_documents(self) -> list[Document]:
        """Charge tous les fichiers Markdown de la knowledge base."""
        docs = []
        for source_dir in ("netapp_kb", "working_instructions", "incident_history"):
            source_path = KB_DIR / source_dir
            for md_file in source_path.glob("**/*.md"):
                content = md_file.read_text(encoding="utf-8", errors="replace")
                docs.append(Document(
                    doc_id=str(md_file.relative_to(KB_DIR)),
                    source=source_dir,
                    title=md_file.stem.replace("_", " "),
                    content=content,
                    metadata={"path": str(md_file), "source": source_dir},
                ))
        return docs

    def _load_cache(self) -> dict:
        if EMBED_CACHE.exists():
            return json.loads(EMBED_CACHE.read_text())
        return {}

    def _save_cache(self) -> None:
        EMBED_CACHE.write_text(json.dumps(self.cache, indent=2))
