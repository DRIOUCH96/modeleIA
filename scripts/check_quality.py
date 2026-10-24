"""Vérifier les métriques avant d'autoriser un déploiement."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml


def load_metrics(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def load_config(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as file:
        config = yaml.safe_load(file)

    if not isinstance(config, dict):
        raise ValueError("La configuration YAML doit contenir un objet.")
    return config


def evaluate_quality(
    metrics: dict[str, Any],
    config: dict[str, Any],
) -> tuple[list[str], float, int, float, int]:
    try:
        actual_f1 = float(metrics["metrics"]["f1"])
        actual_test_rows = int(metrics["test_rows"])
        minimum_f1 = float(config["quality_gate"]["minimum_f1"])
        minimum_test_rows = int(
            config["quality_gate"]["minimum_test_rows"]
        )
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError(
            "Structure de métriques ou de configuration invalide."
        ) from error

    if not 0.0 <= actual_f1 <= 1.0:
        raise ValueError("Le F1 observé doit être compris entre 0 et 1.")
    if actual_test_rows <= 0:
        raise ValueError("La taille du test doit être strictement positive.")
    if not 0.0 <= minimum_f1 <= 1.0:
        raise ValueError("Le F1 minimal doit être compris entre 0 et 1.")
    if minimum_test_rows <= 0:
        raise ValueError(
            "La taille minimale du test doit être strictement positive."
        )

    failures = []

    if actual_f1 < minimum_f1:
        failures.append(
            f"F1 insuffisant : {actual_f1:.6f} < {minimum_f1:.6f}"
        )

    if actual_test_rows < minimum_test_rows:
        failures.append(
            "Test trop petit : "
            f"{actual_test_rows} < {minimum_test_rows}"
        )

    return (
        failures,
        actual_f1,
        actual_test_rows,
        minimum_f1,
        minimum_test_rows,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Contrôler le F1 et la taille du test."
    )
    parser.add_argument(
        "--metrics",
        type=Path,
        required=True,
        help="Chemin du fichier metrics.json à contrôler.",
    )
    parser.add_argument(
        "--config",
        type=Path,
        required=True,
        help="Chemin de la configuration YAML.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        metrics = load_metrics(args.metrics)
        config = load_config(args.config)
        (
            failures,
            actual_f1,
            actual_test_rows,
            minimum_f1,
            minimum_test_rows,
        ) = evaluate_quality(metrics, config)
    except (OSError, json.JSONDecodeError, yaml.YAMLError, ValueError) as error:
        print(f"Barrière qualité : ERREUR\n- {error}")
        return 2

    f1_status = "OK" if actual_f1 >= minimum_f1 else "ÉCHEC"
    rows_status = (
        "OK"
        if actual_test_rows >= minimum_test_rows
        else "ÉCHEC"
    )

    print(
        f"F1 : {actual_f1:.6f} "
        f"(minimum {minimum_f1:.6f}) -> {f1_status}"
    )
    print(
        f"Taille du test : {actual_test_rows} "
        f"(minimum {minimum_test_rows}) -> {rows_status}"
    )

    if failures:
        print("Barrière qualité : ÉCHEC")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Barrière qualité : OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())