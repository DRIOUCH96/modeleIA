import json
from pathlib import Path

import numpy as np

from src.inference import ModelBundle


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODEL_DIR = PROJECT_ROOT / "model"
REFERENCE_PATH = MODEL_DIR / "reference_sample.json"


def test_reloaded_artifacts_reproduce_reference_predictions():
    bundle = ModelBundle.load(MODEL_DIR)

    with REFERENCE_PATH.open("r", encoding="utf-8") as file:
        reference = json.load(file)

    assert reference["model_version"] == bundle.model_version
    assert reference["provenance"]["not_for_performance_evaluation"] is True
    assert bundle.metrics["production_holdout_evaluated"] is False

    observed_probabilities = []
    observed_classes = []
    expected_probabilities = []
    expected_classes = []

    for sample in reference["samples"]:
        prediction = bundle.predict(sample["resume"])

        observed_probabilities.append(prediction.probability)
        observed_classes.append(prediction.predicted_class)
        expected_probabilities.append(
            sample["expected_probability_class_1"]
        )
        expected_classes.append(sample["expected_class"])

    np.testing.assert_allclose(
        observed_probabilities,
        expected_probabilities,
        rtol=1e-6,
        atol=1e-7,
    )
    np.testing.assert_array_equal(
        observed_classes,
        expected_classes,
    )