"""
Image analysis module for apartment listing photos using Gemini Vision.
Identifies photo quality issues, misleading images, and visual red flags.
"""

import json
from PIL import Image
from utils.gemini_client import GeminiClient

class ImageAnalyzer:
    def __init__(self):
        """Initialize image analyzer with Gemini Vision client."""
        self.client = GeminiClient()

    def analyze_photos(self, image_files):
        """
        Analyze apartment listing photos for red flags and quality issues.

        Args:
            image_files (list): List of file paths or PIL Image objects

        Returns:
            dict: Analysis results with photo_issues, positive_observations, and quality_score
        """
        if not image_files:
            return {
                'photo_issues': [],
                'positive_observations': [],
                'quality_score': 0,
                'summary': 'No photos provided'
            }

        # Load images if they're file paths
        images = []
        for img in image_files:
            if isinstance(img, str):
                images.append(Image.open(img))
            else:
                images.append(img)

        prompt = self._build_analysis_prompt()

        try:
            response = self.client.analyze_images(prompt, images)
            analysis = self._parse_response(response)
            return analysis
        except Exception as e:
            return {
                'error': str(e),
                'photo_issues': [],
                'positive_observations': [],
                'quality_score': 0
            }

    def _build_analysis_prompt(self):
        """Build the prompt for Gemini Vision analysis."""
        prompt = """You are analyzing apartment listing photos for college students. Identify visual red flags, quality issues, and assess photo authenticity.

Analyze these listing photos and respond in JSON format:
{
  "photo_issues": [
    {
      "issue": "description of the problem",
      "severity": "low/medium/high",
      "photo_number": 1,
      "explanation": "why this is concerning"
    }
  ],
  "positive_observations": [
    {
      "observation": "what looks good",
      "photo_number": 1
    }
  ],
  "quality_score": 0-10,
  "summary": "Overall assessment of the photos"
}

RED FLAGS TO IDENTIFY:
- Wide-angle lens distortion making spaces look bigger
- Strategic camera angles hiding issues
- Heavy filters or photo editing
- Stock photos or photos from other listings
- Poor lighting hiding damage or dirt
- Missing key areas (bathroom, kitchen, bedroom)
- Photos taken during staging vs actual condition
- Inconsistent photo quality (mix of professional and amateur)
- Clutter or mess visible in background
- Signs of damage (cracks, stains, peeling paint)
- Misleading photos (showing amenities not in unit)
- Too few photos (< 3 photos is suspicious)
- Blurry or low-quality images
- Photos don't match description

POSITIVE SIGNS:
- Well-lit, clear photos
- Multiple angles of each room
- Honest representation of space
- Shows important details (appliances, storage, fixtures)
- Recent photos (can tell by furnishings/style)
- Consistent quality across all photos
- Natural lighting
- Shows actual condition, not staged

Be specific about which photo number has which issue. Quality score: 10 = excellent, honest photos; 0 = major red flags or missing photos.
"""
        return prompt

    def _parse_response(self, response_text):
        """
        Parse Gemini Vision response into structured format.

        Args:
            response_text (str): Raw response from Gemini

        Returns:
            dict: Parsed analysis results
        """
        try:
            # Extract JSON from response (might be wrapped in markdown)
            if '```json' in response_text:
                json_start = response_text.find('```json') + 7
                json_end = response_text.find('```', json_start)
                json_str = response_text[json_start:json_end].strip()
            elif '```' in response_text:
                json_start = response_text.find('```') + 3
                json_end = response_text.find('```', json_start)
                json_str = response_text[json_start:json_end].strip()
            else:
                json_str = response_text.strip()

            analysis = json.loads(json_str)

            # Ensure required fields exist
            if 'photo_issues' not in analysis:
                analysis['photo_issues'] = []
            if 'positive_observations' not in analysis:
                analysis['positive_observations'] = []
            if 'quality_score' not in analysis:
                analysis['quality_score'] = 5

            return analysis

        except json.JSONDecodeError as e:
            # If JSON parsing fails, return basic structure
            return {
                'photo_issues': [
                    {
                        'issue': 'Unable to parse structured analysis',
                        'severity': 'low',
                        'photo_number': 0,
                        'explanation': 'Analysis format error'
                    }
                ],
                'positive_observations': [],
                'quality_score': 5,
                'summary': response_text[:200] + '...' if len(response_text) > 200 else response_text,
                'parse_error': str(e)
            }
