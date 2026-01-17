"""
Text analysis module for apartment listings using Gemini AI.
Identifies red flags, missing information, and generates concerns.
"""

import json
from utils.gemini_client import GeminiClient

class TextAnalyzer:
    def __init__(self):
        """Initialize text analyzer with Gemini client."""
        self.client = GeminiClient()

    def analyze_listing(self, listing_text, address=None):
        """
        Analyze apartment listing text for red flags and missing info.

        Args:
            listing_text (str): The apartment listing description
            address (str, optional): Listing address for context

        Returns:
            dict: Analysis results with red_flags, missing_info, and overall_risk
        """
        prompt = self._build_analysis_prompt(listing_text, address)

        try:
            response = self.client.analyze_text(prompt)
            analysis = self._parse_response(response)
            return analysis
        except Exception as e:
            return {
                'error': str(e),
                'red_flags': [],
                'missing_info': [],
                'overall_risk': 'unknown'
            }

    def _build_analysis_prompt(self, listing_text, address):
        """Build the prompt for Gemini text analysis."""
        context = f"Address: {address}\n\n" if address else ""

        prompt = f"""You are analyzing an apartment listing for college students. Identify red flags, missing information, and assess risk.

{context}Listing Description:
{listing_text}

Analyze this listing and respond in JSON format with the following structure:
{{
  "red_flags": [
    {{"flag": "description of red flag", "severity": "low/medium/high", "reason": "why this is concerning"}}
  ],
  "missing_info": [
    {{"item": "what's missing", "importance": "low/medium/high", "why": "why this matters"}}
  ],
  "overall_risk": "low/medium/high",
  "summary": "2-3 sentence summary of the listing quality"
}}

RED FLAGS TO LOOK FOR:
- Vague or evasive language about property condition
- Missing essential details (lease terms, utilities, deposit)
- Too-good-to-be-true pricing
- Pressure tactics ("won't last long", "act now")
- Photo inconsistencies or stock photos
- Unclear contact information
- Requests for payment before viewing
- "As-is" conditions without explanation
- No mention of landlord/property management
- Excessive emphasis on "cozy" (possibly small)

MISSING INFORMATION:
- Lease length and terms
- Utilities included/excluded
- Deposit and fees
- Pet policy
- Parking availability
- Laundry facilities
- Move-in date flexibility
- Maintenance contact
- Subletting policy
- Internet/cable included

Be thorough but fair. Only flag genuine concerns, not minor style issues.
"""
        return prompt

    def _parse_response(self, response_text):
        """
        Parse Gemini response into structured format.

        Args:
            response_text (str): Raw response from Gemini

        Returns:
            dict: Parsed analysis results
        """
        try:
            # Try to extract JSON from the response
            # Gemini might wrap JSON in markdown code blocks
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
            if 'red_flags' not in analysis:
                analysis['red_flags'] = []
            if 'missing_info' not in analysis:
                analysis['missing_info'] = []
            if 'overall_risk' not in analysis:
                analysis['overall_risk'] = 'medium'

            return analysis

        except json.JSONDecodeError as e:
            # If JSON parsing fails, return a basic structure with the raw response
            return {
                'red_flags': [
                    {
                        'flag': 'Unable to parse structured analysis',
                        'severity': 'low',
                        'reason': 'Analysis format error'
                    }
                ],
                'missing_info': [],
                'overall_risk': 'medium',
                'summary': response_text[:200] + '...' if len(response_text) > 200 else response_text,
                'parse_error': str(e)
            }
