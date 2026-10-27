"""Contrats HTTP validés par Pydantic."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class PredictionRequest(BaseModel):
    """Texte brut envoyé au classifieur."""

    model_config = ConfigDict(extra="forbid")

    text: str = Field(
        min_length=1,
        max_length=10_000,
        description="Résumé de film à classer.",
        examples=["Une famille s'installe dans une maison hantée."],
    )

    @field_validator("text")
    @classmethod
    def strip_and_reject_blank_text(cls, value: str) -> str:
        """Normaliser les bords sans modifier le contenu linguistique."""

        stripped_value = value.strip()
        if not stripped_value:
            raise ValueError("Le texte ne peut pas être vide ou contenir seulement des espaces.")
        return stripped_value


class HealthResponse(BaseModel):
    """État observable de l'application et du modèle chargé."""

    status: Literal["ok"]
    model_loaded: bool
    model_version: str
    app_version: str
class HelloResponse(BaseModel):
    """Réponse de la route utilisée pour démontrer une évolution."""

    message: Literal["Bonjour depuis adriouch-modeleia-api"]
    app_version: str

class PredictionResponse(BaseModel):
    """Résultat d'une classification binaire."""

    predicted_class: Literal[0, 1]
    predicted_label: Literal["comédie", "horreur"]
    probability: float = Field(ge=0.0, le=1.0)
    probability_class: Literal[1]
    model_version: str
