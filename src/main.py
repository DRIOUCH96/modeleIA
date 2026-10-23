"""Application FastAPI exposant le classifieur NLP."""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request

from src.inference import ModelBundle
from src.schemas import HealthResponse, PredictionRequest, PredictionResponse


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MODEL_DIR = PROJECT_ROOT / "model"
DEFAULT_APP_VERSION = "development"


def create_app(
    *,
    model_dir: Path | None = None,
    app_version: str | None = None,
) -> FastAPI:
    """Créer l'application avec une configuration injectable pour les tests."""

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        resolved_model_dir = model_dir or Path(
            os.getenv("MODEL_DIR", str(DEFAULT_MODEL_DIR))
        )
        resolved_app_version = app_version or os.getenv(
            "APP_VERSION", DEFAULT_APP_VERSION
        )

        app.state.model_bundle = ModelBundle.load(resolved_model_dir)
        app.state.app_version = resolved_app_version
        yield
        app.state.model_bundle = None

    application = FastAPI(
        title="Classifieur de résumés de films",
        description=(
            "Classe un résumé en comédie (0) ou horreur (1). "
            "La probabilité retournée correspond à la classe 1."
        ),
        version="1.0.0",
        lifespan=lifespan,
    )

    @application.get("/health", response_model=HealthResponse)
    def health(request: Request) -> HealthResponse:
        bundle: ModelBundle = request.app.state.model_bundle
        return HealthResponse(
            status="ok",
            model_loaded=bundle is not None,
            model_version=bundle.model_version,
            app_version=request.app.state.app_version,
        )

    @application.post("/predict", response_model=PredictionResponse)
    def predict(
        payload: PredictionRequest,
        request: Request,
    ) -> PredictionResponse:
        bundle: ModelBundle = request.app.state.model_bundle
        result = bundle.predict(payload.text)
        return PredictionResponse(
            predicted_class=result.predicted_class,
            predicted_label=result.predicted_label,
            probability=result.probability,
            probability_class=bundle.probability_class,
            model_version=bundle.model_version,
        )

    return application


app = create_app()
