"""Chargement et utilisation du paquet d'inférence exporté par le notebook."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import tensorflow as tf


@dataclass(frozen=True)
class Prediction:
    """Sortie interne avant sérialisation HTTP."""

    predicted_class: int
    predicted_label: str
    probability: float


class ModelBundle:
    """Réseau, TF-IDF et métadonnées chargés une seule fois."""

    def __init__(
        self,
        *,
        model: tf.keras.Model,
        vectorizer: Any,
        metrics: dict[str, Any],
    ) -> None:
        self.model = model
        self.vectorizer = vectorizer
        self.metrics = metrics
        self.model_version = str(metrics["model_version"])
        self.decision_threshold = float(metrics["decision_threshold"])
        self.probability_class = int(metrics["probability_class"])
        self.label_mapping = {
            int(label): str(name)
            for label, name in metrics["label_mapping"].items()
        }

    @classmethod
    def load(cls, model_dir: Path) -> "ModelBundle":
        """Charger des artefacts locaux de confiance et contrôler leur cohérence."""

        metrics_path = model_dir / "metrics.json"
        if not metrics_path.is_file():
            raise FileNotFoundError(f"Métriques introuvables : {metrics_path}")

        with metrics_path.open("r", encoding="utf-8") as file:
            metrics = json.load(file)

        required_keys = {
            "model_version",
            "model_file",
            "vectorizer_file",
            "label_mapping",
            "probability_class",
            "decision_threshold",
            "tfidf_features",
        }
        missing_keys = sorted(required_keys - metrics.keys())
        if missing_keys:
            raise ValueError(
                "Clés absentes de metrics.json : " + ", ".join(missing_keys)
            )

        model_file = Path(str(metrics["model_file"]))
        vectorizer_file = Path(str(metrics["vectorizer_file"]))
        if model_file.name != str(model_file) or vectorizer_file.name != str(
            vectorizer_file
        ):
            raise ValueError("Les noms d'artefacts doivent être de simples noms de fichiers.")

        model_path = model_dir / model_file
        vectorizer_path = model_dir / vectorizer_file
        if not model_path.is_file():
            raise FileNotFoundError(f"Réseau introuvable : {model_path}")
        if not vectorizer_path.is_file():
            raise FileNotFoundError(f"Vectoriseur introuvable : {vectorizer_path}")

        # joblib ne doit charger que des artefacts produits et versionnés par ce projet.
        vectorizer = joblib.load(vectorizer_path)
        model = tf.keras.models.load_model(model_path, compile=False)

        expected_features = int(metrics["tfidf_features"])
        vectorizer_features = len(vectorizer.get_feature_names_out())
        model_features = int(model.input_shape[-1])
        if vectorizer_features != expected_features or model_features != expected_features:
            raise ValueError(
                "Dimensions incompatibles : "
                f"metrics={expected_features}, TF-IDF={vectorizer_features}, "
                f"réseau={model_features}."
            )
        if int(metrics["probability_class"]) != 1:
            raise ValueError("La probabilité exportée doit correspondre à la classe 1.")
        threshold = float(metrics["decision_threshold"])
        if not 0.0 <= threshold <= 1.0:
            raise ValueError("Le seuil de décision doit être compris entre 0 et 1.")
        if set(str(key) for key in metrics["label_mapping"]) != {"0", "1"}:
            raise ValueError("Le mapping des classes doit contenir exactement 0 et 1.")

        return cls(model=model, vectorizer=vectorizer, metrics=metrics)

    def predict(self, text: str) -> Prediction:
        """Appliquer exactement le TF-IDF sérialisé puis le réseau dense."""

        sparse_features = self.vectorizer.transform([text])
        dense_features = sparse_features.toarray()
        probability = float(
            np.asarray(self.model(dense_features, training=False)).reshape(-1)[0]
        )
        if not np.isfinite(probability) or not 0.0 <= probability <= 1.0:
            raise RuntimeError(f"Probabilité invalide produite par le modèle : {probability}")

        predicted_class = int(probability >= self.decision_threshold)
        return Prediction(
            predicted_class=predicted_class,
            predicted_label=self.label_mapping[predicted_class],
            probability=probability,
        )
