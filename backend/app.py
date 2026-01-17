"""
Apartment Hunter - Flask Backend API
Analyzes apartment listings using AI and student feedback data.
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from PIL import Image
import io

from analyzers.text_analyzer import TextAnalyzer
from analyzers.image_analyzer import ImageAnalyzer
from analyzers.student_context import StudentContextAnalyzer
from utils.question_generator import generate_questions

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend communication

# Initialize analyzers
text_analyzer = TextAnalyzer()
image_analyzer = ImageAnalyzer()
student_analyzer = StudentContextAnalyzer()


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'message': 'Apartment Hunter API is running'
    }), 200


@app.route('/analyze', methods=['POST'])
def analyze_listing():
    """
    Main endpoint for analyzing apartment listings.

    Expected input:
    - listing_text (form field): Apartment description
    - address (form field): Apartment address
    - university (form field): University name (e.g., "UIUC")
    - images (files): Up to 5 photos

    Returns:
    - Comprehensive analysis with text, image, and student insights
    - Questions to ask the landlord
    """
    try:
        # Extract form data
        listing_text = request.form.get('listing_text', '')
        address = request.form.get('address', '')
        university = request.form.get('university', 'UIUC')

        # Validate inputs
        if not listing_text:
            return jsonify({
                'error': 'Missing required field: listing_text'
            }), 400

        # Extract images from request
        images = []
        if 'images' in request.files:
            files = request.files.getlist('images')
            for file in files[:5]:  # Limit to 5 images
                if file and _allowed_file(file.filename):
                    img = Image.open(io.BytesIO(file.read()))
                    images.append(img)

        # Run parallel analyses
        print(f"Analyzing listing for {address} near {university}...")

        # 1. Text analysis
        print("Running text analysis...")
        text_analysis = text_analyzer.analyze_listing(listing_text, address)

        # 2. Image analysis
        print("Running image analysis...")
        image_analysis = image_analyzer.analyze_photos(images)

        # 3. Student context
        print("Fetching student insights...")
        student_reviews = student_analyzer.get_student_insights(address, university)

        # 4. Generate questions
        print("Generating questions...")
        questions = generate_questions(text_analysis, image_analysis, student_reviews)

        # Build comprehensive response
        response = {
            'text_analysis': text_analysis,
            'image_analysis': image_analysis,
            'student_reviews': student_reviews,
            'questions': questions,
            'overall_assessment': _calculate_overall_assessment(
                text_analysis,
                image_analysis,
                student_reviews
            )
        }

        print("Analysis complete!")
        return jsonify(response), 200

    except Exception as e:
        print(f"Error during analysis: {str(e)}")
        return jsonify({
            'error': f'Analysis failed: {str(e)}'
        }), 500


def _allowed_file(filename):
    """Check if file extension is allowed."""
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions


def _calculate_overall_assessment(text_analysis, image_analysis, student_reviews):
    """
    Calculate an overall risk assessment based on all analyses.

    Args:
        text_analysis (dict): Text analysis results
        image_analysis (dict): Image analysis results
        student_reviews (dict): Student review data

    Returns:
        dict: Overall assessment with risk level and summary
    """
    risk_scores = {
        'low': 1,
        'medium': 2,
        'high': 3
    }

    # Calculate text risk
    text_risk = risk_scores.get(text_analysis.get('overall_risk', 'medium'), 2)

    # Calculate image risk (quality_score: 10 = low risk, 0 = high risk)
    quality_score = image_analysis.get('quality_score', 5)
    if quality_score >= 7:
        image_risk = 1
    elif quality_score >= 4:
        image_risk = 2
    else:
        image_risk = 3

    # Calculate student sentiment risk
    sentiment = student_reviews.get('sentiment_breakdown', {})
    negative_ratio = sentiment.get('negative', 0) / 100.0 if sentiment else 0.5
    if negative_ratio < 0.3:
        student_risk = 1
    elif negative_ratio < 0.6:
        student_risk = 2
    else:
        student_risk = 3

    # Average risk
    avg_risk = (text_risk + image_risk + student_risk) / 3

    if avg_risk <= 1.5:
        overall_risk = 'low'
        recommendation = 'This listing looks relatively safe. Still ask the suggested questions!'
    elif avg_risk <= 2.5:
        overall_risk = 'medium'
        recommendation = 'Proceed with caution. Make sure to ask all the suggested questions and schedule a tour.'
    else:
        overall_risk = 'high'
        recommendation = 'Major red flags detected. Consider other options or investigate thoroughly before proceeding.'

    # Count red flags
    red_flag_count = len(text_analysis.get('red_flags', []))
    photo_issue_count = len(image_analysis.get('photo_issues', []))

    return {
        'risk_level': overall_risk,
        'recommendation': recommendation,
        'red_flag_count': red_flag_count,
        'photo_issue_count': photo_issue_count,
        'student_score': student_reviews.get('overall_score', 0),
        'summary': _generate_summary(text_risk, image_risk, student_risk, red_flag_count)
    }


def _generate_summary(text_risk, image_risk, student_risk, red_flag_count):
    """Generate a human-readable summary."""
    concerns = []

    if text_risk >= 3:
        concerns.append("listing description has serious issues")
    elif text_risk >= 2:
        concerns.append("listing description raises some concerns")

    if image_risk >= 3:
        concerns.append("photos are misleading or poor quality")
    elif image_risk >= 2:
        concerns.append("photo quality could be better")

    if student_risk >= 3:
        concerns.append("student reviews are largely negative")
    elif student_risk >= 2:
        concerns.append("student reviews are mixed")

    if concerns:
        summary = f"Found {red_flag_count} red flag(s). " + ", ".join(concerns).capitalize() + "."
    else:
        summary = "This listing looks relatively solid. No major red flags detected."

    return summary


if __name__ == '__main__':
    print("Starting Apartment Hunter API...")
    print("Initializing analyzers...")
    print("Server ready at http://localhost:5001")
    app.run(debug=True, host='0.0.0.0', port=5001)
