"""
main.py — API FastAPI principale — Plateforme MCO NetApp
CG CONSEIL — Plateforme MCO NetApp

Point d'entrée de l'API REST. Expose les endpoints de santé, alertes
et rapports consommés par les workflows n8n et les outils externes.
"""

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import alerts, health, reports

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Démarrage Plateforme MCO NetApp API")
    yield
    logger.info("Arrêt Plateforme MCO NetApp API")


app = FastAPI(
    title="CG CONSEIL — Plateforme MCO NetApp",
    description=(
        "API de supervision intelligente NetApp.\n"
        "Collecte EMS, qualification événements, RAG et génération de rapports."
    ),
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS — restreindre en production
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:5678").split(","),
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Routes
app.include_router(health.router, prefix="/api", tags=["Infrastructure"])
app.include_router(alerts.router, prefix="/api", tags=["Alertes"])
app.include_router(reports.router, prefix="/api", tags=["Rapports"])


@app.get("/", include_in_schema=False)
async def root():
    return {"service": "CG CONSEIL MCO NetApp API", "status": "running", "version": "0.1.0"}
