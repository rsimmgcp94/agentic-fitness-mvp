import unittest
from unittest.mock import patch, MagicMock
from app.llm import generate_workout_plan
import os
import json


class TestLLM(unittest.TestCase):
    @patch("app.llm.genai")
    @patch.dict(os.environ, {"GEMINI_API_KEY": "test_api_key"})
    def test_generate_workout_plan_uses_system_instruction(self, mock_genai):
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Generated workout plan"
        mock_model.generate_content.return_value = mock_response
        mock_genai.GenerativeModel.return_value = mock_model

        goals = "Build muscle"
        height = "180cm"
        weight = "80kg"
        pose_analysis = {
            "front": {"detected": True},
            "side": {"detected": True},
            "back": {"detected": True},
        }

        result = generate_workout_plan(goals, height, weight, pose_analysis)

        self.assertEqual(result, "Generated workout plan")

        # Verify GenerativeModel was initialized with system_instruction
        mock_genai.GenerativeModel.assert_called_once()
        _, kwargs = mock_genai.GenerativeModel.call_args
        self.assertIn("system_instruction", kwargs)

        # Verify generate_content was called with only user content
        mock_model.generate_content.assert_called_once()
        user_content_arg = mock_model.generate_content.call_args[0][0]

        self.assertIn(goals, user_content_arg)
        self.assertIn(height, user_content_arg)
        self.assertIn(weight, user_content_arg)
        self.assertIn(
            json.dumps(
                {k: v for k, v in pose_analysis.items() if v.get("detected")}, indent=2
            ),
            user_content_arg,
        )


if __name__ == "__main__":
    unittest.main()
