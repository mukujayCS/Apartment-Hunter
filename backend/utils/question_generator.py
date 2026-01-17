"""
Question Generator - LLM-powered with Hallucination Prevention

OVERALL DESIGN:
- Primary: Use LLM to generate contextual, specific questions
- Guardrails: Strict validation prevents hallucinations - using cross reference checks with issue flags
- Fallback: Simple comprehensive list if LLM fails - list out all the generated issues
"""

import json
from utils.gemini_client import GeminiClient

# Lazy-load Gemini client
_gemini_client = None

def get_gemini_client():
    """Lazy-load Gemini client to avoid initialization cost if not needed."""
    global _gemini_client
    if _gemini_client is None:
        _gemini_client = GeminiClient()
    return _gemini_client


def generate_questions(text_analysis, image_analysis, student_reviews):
    """
    Generate questions for students to ask landlords.

    APPROACH:
    1. Try LLM generation with strict guardrails (contextual questions)
    2. If LLM fails or hallucinates → simple fallback (list all flags)

    Args:
        text_analysis (dict): Results from text analyzer
        image_analysis (dict): Results from image analyzer
        student_reviews (dict): Student context from Reddit

    Returns:
        list: Questions to ask the landlord
    """

    # Step 1: Prepare all flags with unique IDs (prevents hallucination)
    tagged_flags, valid_flag_ids = _prepare_flags_with_ids(
        text_analysis, image_analysis, student_reviews
    )

    # Calculate expectations based on actual flags found
    total_flags = len(tagged_flags)

    print(f"\n Question Generation: Found {total_flags} flags/issues")

    # Edge case: Perfect listing (no flags) = no questions needed
    if total_flags == 0:
        print("   ✅ No issues found - no questions needed")
        return []

    # Step 2: Try LLM generation with guardrails
    try:
        print(f"   Attempting LLM generation with anti-hallucination guardrails...")

        llm_questions = _generate_with_llm(
            tagged_flags,
            text_analysis.get('listing_text', ''),
            total_flags
        )

        # Step 3: Validate LLM output (catch hallucinations)
        validated_questions, should_fallback, reason = _validate_llm_output(
            llm_questions, valid_flag_ids, total_flags
        )

        if not should_fallback:
            print(f"   ✅ LLM generated {len(validated_questions)} valid questions")
            return validated_questions
        else:
            print(f"   ⚠️  LLM validation failed: {reason}")
            print(f"   → Using simple fallback approach")

    except Exception as e:
        print(f"   LLM generation error: {str(e)[:100]}")
        print(f"   Using simple fallback approach")

    # Step 4: Fallback - simple comprehensive list
    return _generate_fallback_questions(tagged_flags)


def _prepare_flags_with_ids(text_analysis, image_analysis, student_reviews):
    """
    Tag all flags with unique IDs for hallucination prevention.

    Returns:
        (tagged_flags, valid_flag_ids)
    """
    tagged_flags = []
    valid_flag_ids = set()

    # Tag red flags from text analysis
    for i, flag in enumerate(text_analysis.get('red_flags', [])):
        flag_id = f"text_flag_{i}"
        tagged_flags.append({
            'id': flag_id,
            'type': 'red_flag',
            'description': flag.get('flag', ''),
            'severity': flag.get('severity', 'medium'),
            'reason': flag.get('reason', '')
        })
        valid_flag_ids.add(flag_id)

    # Tag missing information
    for i, info in enumerate(text_analysis.get('missing_info', [])):
        flag_id = f"missing_info_{i}"
        tagged_flags.append({
            'id': flag_id,
            'type': 'missing_info',
            'description': f"Missing: {info.get('item', '')}",
            'severity': info.get('importance', 'medium'),
            'reason': info.get('why', '')
        })
        valid_flag_ids.add(flag_id)

    # Tag photo issues
    for i, issue in enumerate(image_analysis.get('photo_issues', [])):
        flag_id = f"photo_issue_{i}"
        tagged_flags.append({
            'id': flag_id,
            'type': 'photo_issue',
            'description': issue.get('issue', ''),
            'severity': issue.get('severity', 'medium'),
            'reason': issue.get('explanation', '')
        })
        valid_flag_ids.add(flag_id)

    # Tag student concerns (top 3 negative)
    negative_concerns = [c for c in student_reviews.get('comments', [])
                         if c.get('sentiment') == 'negative'][:3]
    for i, concern in enumerate(negative_concerns):
        flag_id = f"student_concern_{i}"
        tagged_flags.append({
            'id': flag_id,
            'type': 'student_concern',
            'description': f"Student feedback: {concern.get('category', 'general')} concerns",
            'severity': 'medium',
            'reason': concern.get('text', '')[:100]
        })
        valid_flag_ids.add(flag_id)

    return tagged_flags, valid_flag_ids


def _generate_with_llm(tagged_flags, listing_text, total_flags):
    """
    Generate questions using LLM with strict anti-hallucination guardrails.
    """
    client = get_gemini_client()

    # Build prompt with strict guardrails
    prompt = f"""You are helping a college student prepare questions to ask a landlord about an apartment listing.

AVAILABLE FLAGS/ISSUES (you MUST ONLY use these - DO NOT invent new issues):
{json.dumps(tagged_flags, indent=2)}

ORIGINAL LISTING TEXT (for context only - do NOT create questions about things not flagged above):
{listing_text[:500]}...

CRITICAL RULES:
1. Generate questions ONLY about the specific flags/issues listed above
2. Each question MUST reference at least one flag by its exact ID in the "flag_ids" field
3. DO NOT include flag IDs (like "text_flag_0" or "missing_info_3") in the question text - keep questions clean and professional
4. DO NOT invent new concerns or issues not in the flags list above
5. Use specific details from the flag descriptions to make questions contextual
6. Combine related flags into single questions when appropriate
7. Prioritize high-severity flags over medium/low
8. If few flags exist, generate fewer questions (quality over quantity)

Expected: {max(1, int(total_flags * 0.7))}-{total_flags} questions (you may combine related flags)

OUTPUT FORMAT (must be valid JSON):
{{
  "questions": [
    {{
      "question": "The specific question text to ask the landlord",
      "flag_ids": ["text_flag_0"],
      "priority": "high",
      "reasoning": "Brief explanation of why this matters"
    }}
  ]
}}

EXAMPLES:

Good output (clean, professional, grounded):
Input flag: {{"id": "text_flag_0", "description": "Vague pricing - mentions 'affordable' without specific amount"}}
Output: {{"question": "You mention the rent is 'affordable' - what is the exact monthly rent amount?", "flag_ids": ["text_flag_0"], "priority": "high", "reasoning": "Need specific pricing to evaluate affordability"}}

Bad output #1 (includes flag ID in question text):
{{"question": "What is the rent amount? (text_flag_0)", "flag_ids": ["text_flag_0"], ...}}  ❌ WRONG - don't put flag IDs in question text!

Bad output #2 (hallucination):
{{"question": "Is there a gym?", "flag_ids": ["amenity_gym"], ...}}  ❌ WRONG - no such flag exists!

Generate questions now (JSON only):"""

    # Call LLM using dedicated lightweight question model
    response_text = client.generate_questions(prompt)

    # Parse JSON response
    # Handle potential code block wrapping
    response_text = response_text.strip()
    if response_text.startswith('```'):
        # Remove markdown code blocks
        lines = response_text.split('\n')
        response_text = '\n'.join(lines[1:-1]) if len(lines) > 2 else response_text

    response = json.loads(response_text)
    return response.get('questions', [])


def _determine_category(flag_ids):
    """
    Determine question category based on flag IDs.

    Args:
        flag_ids (list): List of flag IDs referenced by the question

    Returns:
        str: Category name for frontend display
    """
    if not flag_ids:
        return 'general'

    # Check first flag ID to determine category
    first_id = flag_ids[0]

    if first_id.startswith('text_flag'):
        return 'listing_description'
    elif first_id.startswith('missing_info'):
        return 'missing_details'
    elif first_id.startswith('photo_issue'):
        return 'photos'
    elif first_id.startswith('student_concern'):
        return 'student_concerns'
    else:
        return 'general'


def _validate_llm_output(questions, valid_flag_ids, total_flags):
    """
    Validate LLM output and detect hallucinations.

    Returns:
        (validated_questions, should_fallback, reason)
    """

    validated = []
    hallucination_count = 0

    # Validate each question
    for q in questions:
        referenced_ids = q.get('flag_ids', [])

        # CRITICAL: Check that ALL referenced flag IDs actually exist
        if all(flag_id in valid_flag_ids for flag_id in referenced_ids):
            # keeps it grounded in real flags
            # Determine category from flag_ids (for frontend compatibility)
            category = _determine_category(referenced_ids)
            q['category'] = category  # Add category field for frontend
            validated.append(q)
        else:
            # Hallucination detected - LLM invented a flag
            invalid_ids = [fid for fid in referenced_ids if fid not in valid_flag_ids]
            hallucination_count += 1
            print(f"      ⚠️  Rejected hallucinated question: {q.get('question', '')[:50]}...")
            print(f"         Invalid flag_ids: {invalid_ids}")

    # DECISION LOGIC: Fallback cases

    # Case 1: Complete failure - no valid questions at all
    if len(validated) == 0 and total_flags > 0:
        return [], True, "LLM generated 0 valid questions"

    # Case 2: Too many hallucinations (>50% rejected)
    if hallucination_count > len(validated):
        return [], True, f"Too many hallucinations ({hallucination_count} rejected vs {len(validated)} valid)"

    # Case 3: Suspiciously low coverage (<50% of flags addressed)
    coverage = len(validated) / max(1, total_flags)
    if coverage < 0.5 and total_flags >= 3:
        return [], True, f"Low coverage: {len(validated)} questions for {total_flags} flags"

    # Validation passed - use LLM questions
    return validated, False, None


def _generate_fallback_questions(tagged_flags):
    """
    FALLBACK: Simple approach - just list all the flags we found.

    This is used when LLM fails or hallucinates. It's intentionally simple:
    - Can't hallucinate (just lists what we found)
    - Covers ALL flags (guaranteed completeness)
    - Clear and honest (doesn't pretend to be smart)
    """

    if len(tagged_flags) == 0:
        return []

    # Group flags by severity for better organization
    high_priority = [f for f in tagged_flags if f['severity'] == 'high']
    medium_priority = [f for f in tagged_flags if f['severity'] == 'medium']
    low_priority = [f for f in tagged_flags if f['severity'] == 'low']

    # Build the comprehensive question
    concerns = []

    if high_priority:
        concerns.append("High Priority Issues:")
        for flag in high_priority:
            concerns.append(f"  • {flag['description']}")

    if medium_priority:
        if high_priority:
            concerns.append("")  # Blank line for separation
        concerns.append("Additional Concerns:")
        for flag in medium_priority:
            concerns.append(f"  • {flag['description']}")

    if low_priority:
        if high_priority or medium_priority:
            concerns.append("")
        concerns.append("Other Items:")
        for flag in low_priority:
            concerns.append(f"  • {flag['description']}")

    concerns_text = "\n".join(concerns)

    question_text = f"""I reviewed the listing and noticed the following points I'd like to address:

{concerns_text}

Could you please provide clarification on each of these items?"""

    return [{
        'question': question_text,
        'priority': 'high' if high_priority else 'medium',
        'category': 'comprehensive_review',
        'reason': f'{len(tagged_flags)} concerns identified during listing analysis'
    }]
