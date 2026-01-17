"""
Student context analyzer - integrates mock Reddit data to provide
student perspectives on apartments, areas, and landlords.

This module wraps the mock_reddit_data functionality to provide
a clean interface for the main Flask app.
"""

from mock_reddit_data import get_mock_student_reviews, get_comments_by_category

class StudentContextAnalyzer:
    def __init__(self):
        """Initialize student context analyzer."""
        pass

    def get_student_insights(self, address, university, num_comments=10):
        """
        Get student reviews and insights about the apartment/area.

        Args:
            address (str): Apartment address
            university (str): University name (e.g., "UIUC")
            num_comments (int): Number of comments to retrieve

        Returns:
            dict: Student reviews with comments, overall_score, sentiment breakdown
        """
        try:
            reviews = get_mock_student_reviews(address, university, num_comments)

            # Add helpful context
            reviews['data_source'] = 'mock_reddit'
            reviews['disclaimer'] = (
                'This data is simulated for demonstration purposes. '
                'Real Reddit API integration requires pre-approval (as of Nov 2025).'
            )

            return reviews

        except Exception as e:
            return {
                'error': str(e),
                'comments': [],
                'overall_score': 0,
                'sentiment_breakdown': {
                    'positive': 0,
                    'neutral': 0,
                    'negative': 0
                },
                'data_source': 'mock_reddit'
            }

    def get_category_insights(self, university, category, num_comments=5):
        """
        Get student comments about a specific category.

        Args:
            university (str): University name
            category (str): Category (location, safety, noise, landlord, etc.)
            num_comments (int): Number of comments to retrieve

        Returns:
            list: Comments about the category
        """
        try:
            comments = get_comments_by_category(university, category, num_comments)
            return comments

        except Exception as e:
            return []

    def get_key_concerns(self, student_reviews):
        """
        Extract key concerns from student reviews based on sentiment.

        Args:
            student_reviews (dict): Student reviews from get_student_insights()

        Returns:
            list: Key concerns extracted from negative/neutral comments
        """
        if 'comments' not in student_reviews:
            return []

        concerns = []
        for comment in student_reviews['comments']:
            if comment.get('sentiment') in ['negative', 'neutral']:
                # Extract concern from comment
                concern = {
                    'text': comment['text'][:150] + '...' if len(comment['text']) > 150 else comment['text'],
                    'category': comment.get('category', 'general'),
                    'sentiment': comment['sentiment']
                }
                concerns.append(concern)

        return concerns[:5]  # Return top 5 concerns

    def get_positive_highlights(self, student_reviews):
        """
        Extract positive highlights from student reviews.

        Args:
            student_reviews (dict): Student reviews from get_student_insights()

        Returns:
            list: Positive highlights from reviews
        """
        if 'comments' not in student_reviews:
            return []

        highlights = []
        for comment in student_reviews['comments']:
            if comment.get('sentiment') == 'positive':
                highlight = {
                    'text': comment['text'][:150] + '...' if len(comment['text']) > 150 else comment['text'],
                    'category': comment.get('category', 'general')
                }
                highlights.append(highlight)

        return highlights[:5]  # Return top 5 highlights
