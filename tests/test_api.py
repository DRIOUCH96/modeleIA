from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.main import create_app


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODEL_DIR = PROJECT_ROOT / "model"


@pytest.fixture(scope="module")
def client():
    app = create_app(
        model_dir=MODEL_DIR,
        app_version="test-app-version",
    )

    # Le contexte démarre puis arrête le lifespan.
    # Les artefacts sont donc chargés une seule fois pour ces tests.
    with TestClient(app) as test_client:
        yield test_client


def test_health_expose_les_deux_versions(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "model_loaded": True,
        "model_version": "horror-comedy-tfidf-dnn-v1",
        "app_version": "test-app-version",
    }


def test_predict_accepte_un_resume_valide(client):
    response = client.post(
        "/predict",
        json={
            "text": (
                "Une famille découvre une présence terrifiante "
                "dans une maison abandonnée."
            )
        },
    )

    assert response.status_code == 200
    body = response.json()

    assert body["predicted_class"] in (0, 1)
    assert body["predicted_label"] == {
        0: "comédie",
        1: "horreur",
    }[body["predicted_class"]]
    assert 0.0 <= body["probability"] <= 1.0
    assert body["probability_class"] == 1
    assert body["model_version"] == "horror-comedy-tfidf-dnn-v1"


def test_predict_refuse_un_texte_vide(client):
    response = client.post("/predict", json={"text": "   "})

    assert response.status_code == 422
    errors = response.json()["detail"]
    assert any("vide" in error["msg"] for error in errors)


def test_predict_accepte_le_cas_limite_tres_court(client):
    response = client.post("/predict", json={"text": "x"})

    assert response.status_code == 200
    assert response.json()["predicted_class"] in (0, 1)