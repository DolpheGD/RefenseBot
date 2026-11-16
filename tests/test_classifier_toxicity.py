import asyncio
import unittest
from unittest.mock import patch

from bot.ml import classifier


class ToxicityClassificationTests(unittest.TestCase):
    def test_extracts_toxic_label_from_nested_model_output(self):
        score = classifier._extract_toxicity_score(
            [[
                {"label": "insult", "score": 0.8},
                {"label": "toxic", "score": 0.6},
            ]]
        )

        self.assertEqual(score, 0.6)

    def test_toxicity_score_contributes_to_hate_classification(self):
        model_scores = {label: 0.0 for label in classifier.CLASS_TERMS}
        with (
            patch.object(classifier, "USE_LOCAL_ML", False),
            patch.object(classifier, "HF_TOKEN", "test-token"),
            patch.object(classifier, "_REMOTE_USAGE_BLOCKED", False),
            patch.object(classifier, "_classify_general_remote", return_value=model_scores),
            patch.object(classifier, "_classify_toxicity_remote", return_value=0.8),
            patch.object(classifier, "identify_slurs", return_value={"count": 0}),
            patch.object(classifier, "identify_scam", return_value=0.0),
        ):
            scores = asyncio.run(classifier.classify_danger_level("toxic input"))

        self.assertAlmostEqual(scores["Hate"], 0.24)

    def test_local_mode_uses_local_toxicity_model(self):
        model_scores = {label: 0.0 for label in classifier.CLASS_TERMS}
        with (
            patch.object(classifier, "USE_LOCAL_ML", True),
            patch.object(classifier, "_local_model_available", return_value=True),
            patch.object(classifier, "_classify_general_local", return_value=model_scores),
            patch.object(classifier, "_classify_toxicity_local", return_value=0.5) as toxic_model,
            patch.object(classifier, "identify_slurs", return_value={"count": 0}),
            patch.object(classifier, "identify_scam", return_value=0.0),
        ):
            scores = asyncio.run(classifier.classify_danger_level("toxic input"))

        toxic_model.assert_called_once_with("toxic input")
        self.assertAlmostEqual(scores["Hate"], 0.15)


if __name__ == "__main__":
    unittest.main()
