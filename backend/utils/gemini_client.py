"""
Gemini API client wrapper for text and image analysis.
"""

import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from config import GEMINI_API_KEY

class GeminiClient:
    def __init__(self):
        """Initialize Gemini client with API key."""
        genai.configure(api_key=GEMINI_API_KEY)

        # Safety settings - allow more content for apartment analysis
        # Apartment descriptions may mention safety concerns, which shouldn't be blocked
        self.safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }

        # Use Gemini 3 Flash Preview for multi-modal analysis (text + images)
        self.text_model = genai.GenerativeModel(
            'gemini-3-flash-preview',
            safety_settings=self.safety_settings
        )
        self.vision_model = genai.GenerativeModel(
            'gemini-3-flash-preview',
            safety_settings=self.safety_settings
        )

        # Lightweight model for simple sentiment classification (cheaper, faster)
        self.sentiment_model = genai.GenerativeModel(
            'gemini-2.5-flash-lite',
            safety_settings=self.safety_settings
        )

        # Lightweight model for question generation (cheaper, faster)
        self.question_model = genai.GenerativeModel(
            'gemini-2.5-flash-lite',
            safety_settings=self.safety_settings
        )

    def analyze_text(self, prompt):
        """
        Analyze text using Gemini.

        Args:
            prompt (str): The prompt to send to Gemini

        Returns:
            str: Model response text
        """
        try:
            response = self.text_model.generate_content(prompt)

            # Check if response has valid parts before accessing .text
            if not response.candidates:
                raise Exception("No response candidates returned")

            candidate = response.candidates[0]

            # Check finish_reason and safety ratings
            if not candidate.content or not candidate.content.parts:
                # Response was blocked or empty
                finish_reason = candidate.finish_reason if hasattr(candidate, 'finish_reason') else 'unknown'
                safety_ratings = candidate.safety_ratings if hasattr(candidate, 'safety_ratings') else []

                # Check if blocked by safety
                blocked_reasons = [r.category for r in safety_ratings if hasattr(r, 'blocked') and r.blocked]
                if blocked_reasons:
                    raise Exception(f"Response blocked by safety filters: {blocked_reasons}")
                else:
                    raise Exception(f"Empty response (finish_reason: {finish_reason})")

            return response.text

        except Exception as e:
            raise Exception(f"Gemini text analysis error: {str(e)}")

    def analyze_sentiment(self, prompt):
        """
        Analyze sentiment using lightweight Gemini model (optimized for speed/cost).

        Args:
            prompt (str): The sentiment classification prompt

        Returns:
            str: Model response text
        """
        try:
            response = self.sentiment_model.generate_content(prompt)

            # Check if response has valid parts before accessing .text
            if not response.candidates:
                raise Exception("No response candidates returned")

            candidate = response.candidates[0]

            # Check finish_reason and safety ratings
            if not candidate.content or not candidate.content.parts:
                # Response was blocked or empty
                finish_reason = candidate.finish_reason if hasattr(candidate, 'finish_reason') else 'unknown'
                safety_ratings = candidate.safety_ratings if hasattr(candidate, 'safety_ratings') else []

                # Check if blocked by safety
                blocked_reasons = [r.category for r in safety_ratings if hasattr(r, 'blocked') and r.blocked]
                if blocked_reasons:
                    raise Exception(f"Response blocked by safety filters: {blocked_reasons}")
                else:
                    raise Exception(f"Empty response (finish_reason: {finish_reason})")

            return response.text

        except Exception as e:
            raise Exception(f"Gemini sentiment analysis error: {str(e)}")

    def generate_questions(self, prompt):
        """
        Generate questions using lightweight Gemini model (optimized for Q&A generation).

        Args:
            prompt (str): The question generation prompt

        Returns:
            str: Model response text (JSON format with questions)
        """
        try:
            response = self.question_model.generate_content(prompt)

            # Check if response has valid parts before accessing .text
            if not response.candidates:
                raise Exception("No response candidates returned")

            candidate = response.candidates[0]

            # Check finish_reason and safety ratings
            if not candidate.content or not candidate.content.parts:
                # Response was blocked or empty
                finish_reason = candidate.finish_reason if hasattr(candidate, 'finish_reason') else 'unknown'
                safety_ratings = candidate.safety_ratings if hasattr(candidate, 'safety_ratings') else []

                # Check if blocked by safety
                blocked_reasons = [r.category for r in safety_ratings if hasattr(r, 'blocked') and r.blocked]
                if blocked_reasons:
                    raise Exception(f"Response blocked by safety filters: {blocked_reasons}")
                else:
                    raise Exception(f"Empty response (finish_reason: {finish_reason})")

            return response.text

        except Exception as e:
            raise Exception(f"Gemini question generation error: {str(e)}")

    def analyze_images(self, prompt, images):
        """
        Analyze images using Gemini Vision (NEW API).

        Args:
            prompt (str): The prompt describing what to analyze
            images (list): List of PIL Image objects

        Returns:
            str: Model response text (JSON format)
        """
        try:
            if not images:
                return '''{{
  "photo_issues": [],
  "positive_observations": [],
  "quality_score": 0,
  "summary": "No photos provided"
}}'''

            # Gemini 1.5 can analyze multiple images in one request
            content = [prompt] + images
            response = self.vision_model.generate_content(content)

            # Check if response has valid parts before accessing .text
            if not response.candidates:
                raise Exception("No response candidates returned")

            candidate = response.candidates[0]

            # Check finish_reason and safety ratings
            if not candidate.content or not candidate.content.parts:
                # Response was blocked or empty
                finish_reason = candidate.finish_reason if hasattr(candidate, 'finish_reason') else 'unknown'
                safety_ratings = candidate.safety_ratings if hasattr(candidate, 'safety_ratings') else []

                # Check if blocked by safety
                blocked_reasons = [r.category for r in safety_ratings if hasattr(r, 'blocked') and r.blocked]
                if blocked_reasons:
                    raise Exception(f"Response blocked by safety filters: {blocked_reasons}")
                else:
                    raise Exception(f"Empty response (finish_reason: {finish_reason})")

            return response.text
        except Exception as e:
            # If image analysis fails, return graceful error
            num_images = len(images) if images else 0
            return f'''{{
  "photo_issues": [
    {{
      "issue": "Image analysis error: {str(e)[:100]}",
      "severity": "low",
      "photo_number": 0,
      "explanation": "{num_images} photo(s) provided but analysis failed."
    }}
  ],
  "positive_observations": [],
  "quality_score": 5,
  "summary": "Image analysis encountered an error."
}}'''
