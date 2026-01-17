"""
Test script for backend components.
Tests analyzers and mock data without making actual API calls.
"""

import sys
from pathlib import Path

# Add backend directory to path for imports
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

def test_config():
    """Test configuration loading."""
    print("\n=== Testing Configuration ===")
    try:
        import config
        print(f"✓ Config loaded successfully")
        print(f"✓ Gemini API key: {'Set' if config.GEMINI_API_KEY else 'NOT SET'}")
        print(f"✓ Reddit mock mode: {config.REDDIT_MOCK_MODE}")
        return True
    except Exception as e:
        print(f"✗ Config error: {e}")
        return False


def test_mock_reddit():
    """Test mock Reddit data."""
    print("\n=== Testing Mock Reddit Data ===")
    try:
        from mock_reddit_data import get_mock_student_reviews, get_comments_by_category

        # Test getting reviews
        reviews = get_mock_student_reviews("123 Main St", "UIUC", 5)
        print(f"✓ Got {len(reviews['comments'])} mock comments")
        print(f"✓ Overall score: {reviews['overall_score']}/5.0")
        print(f"✓ Sentiment breakdown: {reviews['sentiment_breakdown']}")

        # Test category comments
        noise_comments = get_comments_by_category("UIUC", "noise", 3)
        print(f"✓ Got {len(noise_comments)} noise-related comments")

        return True
    except Exception as e:
        print(f"✗ Mock Reddit error: {e}")
        return False


def test_student_analyzer():
    """Test student context analyzer."""
    print("\n=== Testing Student Context Analyzer ===")
    try:
        from analyzers.student_context import StudentContextAnalyzer

        analyzer = StudentContextAnalyzer()

        # Test getting insights
        insights = analyzer.get_student_insights("456 Green St", "UIUC", 5)
        print(f"✓ Got student insights with {len(insights['comments'])} comments")

        # Test getting concerns
        concerns = analyzer.get_key_concerns(insights)
        print(f"✓ Extracted {len(concerns)} key concerns")

        # Test getting highlights
        highlights = analyzer.get_positive_highlights(insights)
        print(f"✓ Extracted {len(highlights)} positive highlights")

        return True
    except Exception as e:
        print(f"✗ Student analyzer error: {e}")
        return False


def test_question_generator():
    """Test question generator."""
    print("\n=== Testing Question Generator ===")
    try:
        from utils.question_generator import generate_questions

        # Mock analysis data
        text_analysis = {
            'red_flags': [
                {
                    'flag': 'Vague language about property condition',
                    'severity': 'high',
                    'reason': 'No specific details'
                }
            ],
            'missing_info': [
                {
                    'item': 'Lease terms',
                    'importance': 'high',
                    'why': 'Essential information'
                }
            ]
        }

        image_analysis = {
            'photo_issues': [
                {
                    'issue': 'Wide angle lens distortion',
                    'severity': 'medium',
                    'explanation': 'Room may appear larger'
                }
            ]
        }

        student_reviews = {
            'comments': [
                {
                    'text': 'Walls are paper thin',
                    'category': 'noise',
                    'sentiment': 'negative'
                }
            ]
        }

        questions = generate_questions(text_analysis, image_analysis, student_reviews)
        print(f"✓ Generated {len(questions)} questions")

        if questions:
            print(f"✓ Sample question: {questions[0]['question']}")

        return True
    except Exception as e:
        print(f"✗ Question generator error: {e}")
        return False


def test_validators():
    """Test input validators."""
    print("\n=== Testing Validators ===")
    try:
        from utils.validators import (
            validate_listing_text,
            validate_university,
            validate_address,
            validate_images
        )

        # Test listing text validation
        valid, error = validate_listing_text("This is a nice apartment with 2 bedrooms and a large kitchen. Close to campus.")
        print(f"✓ Listing text validation: {valid}")

        # Test university validation
        valid, error = validate_university("UIUC")
        print(f"✓ University validation: {valid}")

        # Test address validation
        valid, error = validate_address("123 Main St, Champaign, IL")
        print(f"✓ Address validation: {valid}")

        # Test images validation
        valid, error = validate_images([])
        print(f"✓ Images validation: {valid}")

        return True
    except Exception as e:
        print(f"✗ Validators error: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 50)
    print("APARTMENT HUNTER - BACKEND TESTS")
    print("=" * 50)

    results = []

    results.append(("Configuration", test_config()))
    results.append(("Mock Reddit Data", test_mock_reddit()))
    results.append(("Student Analyzer", test_student_analyzer()))
    results.append(("Question Generator", test_question_generator()))
    results.append(("Validators", test_validators()))

    # Summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed! Backend is ready.")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please check errors above.")
        return 1


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
