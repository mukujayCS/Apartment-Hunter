# Mock Reddit Data Processor for Apartment Hunter
#
# Processes mock student comments from JSON data files to simulate Reddit API responses.
#
# WHY MOCK DATA:
# Reddit API access changed in November 2025 to require pre-approval with undefined wait times. 
# This mock data demonstrates the feature while maintaining production-ready architecture similar to reddit data outputs

# ARCHITECTURE:
# - Raw data stored in backend/data/reddit_comments.json
# - University mappings in backend/data/university_subreddits.json
# - This file provides processing logic and API-compatible interface to process the mock Reddit data
# - SENTIMENT INFERENCE: Analyzes text to infer sentiment
# - TEMPORAL WEIGHTING: Newer comments weighted higher in scoring
#
# Production Note: Replace this module with real PRAW integration once Reddit API credentials are obtained. 
# The interface remains the same - just swap the implementation.

import json
import random
from pathlib import Path
from datetime import datetime
from utils.gemini_client import GeminiClient

# Get the directory where this script is located
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"

# Global Gemini client for LLM-assisted sentiment analysis
_gemini_client = None

def get_gemini_client():
    """Lazy-load Gemini client to avoid initialization cost if not needed."""
    global _gemini_client
    if _gemini_client is None:
        _gemini_client = GeminiClient()
    return _gemini_client


def infer_sentiment_llm(text):
    """
    Use Gemini LLM for nuanced sentiment analysis.
    Called only for borderline cases where rules-based is uncertain.

    Args:
        text: Comment text to analyze

    Returns:
        str: "positive", "negative", "neutral", or "unknown"
    """
    try:
        client = get_gemini_client()

        # Context-aware prompt for college apartment reviews
        prompt = f"""
You are analyzing Reddit comments written by college students about apartments.

Classify the sentiment as EXACTLY one of:
positive
neutral
negative

Rules:
- Complaints about noise, walls, neighbors, studying conditions, safety, landlords, or maintenance are NEGATIVE.
- Phrases like "would not recommend", numeric ratings below 5/10, or warnings to others are NEGATIVE.
- Mixed or descriptive comments without clear satisfaction or dissatisfaction are NEUTRAL.
- Praise or recommendations are POSITIVE.
- Do NOT default to neutral if the comment clearly harms quality of life.

Return only ONE word.

Comment:
{text}
"""

        # Use lightweight sentiment model for fast classification
        response = client.analyze_sentiment(prompt)
        sentiment = response.strip().lower()

        # Extract first word if response has multiple words
        first_word = sentiment.split()[0] if sentiment else 'unknown'

        # Validate response
        if first_word in ['positive', 'negative', 'neutral']:
            return first_word
        # Handle variations
        elif 'positive' in sentiment:
            return 'positive'
        elif 'negative' in sentiment:
            return 'negative'
        else:
            # If LLM gives weird response, flag as unknown for debugging
            print(f"LLM gave unexpected response: {sentiment[:50]}")
            return 'unknown'

    except Exception as e:
        # If LLM fails, flag as unknown for debugging
        print(f"LLM sentiment analysis failed: {e}")
        return 'unknown'


def infer_sentiment(text, use_hybrid=True):
    """
    HYBRID sentiment inference: Rules-based + LLM for borderline cases.

    This approach is used when:
    1. Saves API costs by using rules for clear-cut cases (most common)
    2. Leverages LLM intelligence for nuanced/sarcastic/complex cases and not for simple obvious cases

    Args:
        text: Comment text to analyze
        use_hybrid: If True, use LLM for borderline cases. If False, rules only.

    Returns:
        str: "positive", "negative", or "neutral"
    """
    text_lower = text.lower()

    # College-specific phrases (common in student apartment reviews)
    college_negative = [
        'sketchy', 'loud parties', 'thin walls', 'far from campus',
        'overpriced', 'landlord sucks', 'avoid', 'scam', 'dirty',
        'roaches', 'mold', 'broken ac', 'parking nightmare'
    ]

    college_positive = [
        'close to campus', 'quiet', 'great location', 'worth it',
        'responsive landlord', 'clean', 'spacious', 'good deal',
        'highly recommend', 'love living here', 'clutch'
    ]

    # Strong negative indicators (high weight)
    strong_negative = [
        'worst', 'terrible', 'awful', 'disgusting', 'avoid', 'nightmare',
        'scam', 'shady', 'broken', 'horrible', 'trash', 'sucks', 'hate',
        'miserable', 'brutal', 'never again', 'rip off'
    ]

    # Moderate negative indicators
    negative = [
        'bad', 'issue', 'problem', 'annoying', 'inconvenient', 'sketchy',
        'loud', 'noisy', 'far', 'expensive', 'old', 'small',
        'complaint', 'disappointing', 'meh', 'mediocre'
    ]

    # Strong positive indicators (high weight)
    strong_positive = [
        'best', 'amazing', 'perfect', 'excellent', 'love', 'great',
        'wonderful', 'fantastic', 'highly recommend', 'awesome', 'clutch',
        'gem', 'steal', 'couldn\'t be happier'
    ]

    # Moderate positive indicators
    positive = [
        'good', 'nice', 'clean', 'safe', 'convenient', 'happy', 'worth',
        'solid', 'recommend', 'impressed', 'comfortable', 'spacious',
        'decent', 'satisfied'
    ]

    # Negation words that flip sentiment
    negations = ['not', 'no', 'never', 'don\'t', 'didn\'t', 'won\'t', 'barely']

    # Calculate scores
    college_neg_count = sum(1 for phrase in college_negative if phrase in text_lower)
    college_pos_count = sum(1 for phrase in college_positive if phrase in text_lower)
    strong_neg_count = sum(1 for word in strong_negative if word in text_lower)
    neg_count = sum(1 for word in negative if word in text_lower)
    strong_pos_count = sum(1 for word in strong_positive if word in text_lower)
    pos_count = sum(1 for word in positive if word in text_lower)
    negation_count = sum(1 for word in negations if word in text_lower)

    # Weighted scoring (college phrases get extra weight)
    sentiment_score = (
        (college_pos_count * 3) +  # College-specific positive (highest weight)
        (strong_pos_count * 2) +   # Strong positive
        pos_count -                # Moderate positive
        (college_neg_count * 3) -  # College-specific negative (highest weight)
        (strong_neg_count * 2) -   # Strong negative
        neg_count                  # Moderate negative
    )

    # Adjust for negations (reduces confidence)
    confidence_penalty = 0
    if negation_count > 0:
        sentiment_score *= 0.7
        confidence_penalty = negation_count * 0.5

    # Calculate confidence (how sure are we about the rules-based result?)
    total_signals = (college_pos_count + college_neg_count +
                     strong_pos_count + strong_neg_count +
                     pos_count + neg_count)

    confidence = total_signals - confidence_penalty

    # ============================================================================
    # TIER 1: OBVIOUS CASES - Use rules-based ONLY (NO LLM call needed)
    # ============================================================================
    # For clear positive/negative cases, we don't need expensive LLM calls.
    # Examples: "Terrible place, avoid!", "Amazing location, highly recommend!"
    #
    # WHY: Saves API costs by handling obvious cases with simple rules
    # ============================================================================

    if sentiment_score >= 3:
        return 'positive'  # Clear positive (e.g., "great location, highly recommend")
    elif sentiment_score <= -3:
        return 'negative'  # Clear negative (e.g., "terrible, avoid at all costs")

    # ============================================================================
    # TIER 2: BORDERLINE CASES - Try LLM first, fallback to rules if LLM fails
    # ============================================================================
    # For nuanced/sarcastic/mixed sentiment, LLM is better at understanding context.
    # Examples: "Not bad, but could be better", "It's fine I guess"
    #
    # WHY: LLM handles sarcasm, negations, and subtle sentiment better than rules
    # FALLBACK: If LLM fails (API error, safety block), use rules as backup
    # ============================================================================

    if use_hybrid and confidence < 2:
        # Low confidence - this is a borderline/complex case
        llm_result = infer_sentiment_llm(text)

        # If LLM succeeds, trust it (better at nuance than rules)
        if llm_result != 'unknown':
            return llm_result

        # If LLM fails, continue to rules-based fallback below
        # (This happens on API errors, safety blocks, or invalid responses)

    # ============================================================================
    # TIER 3: MODERATE CASES - Use rules-based (LLM fallback for Tier 2)
    # ============================================================================
    # Moderate signals OR LLM failed in Tier 2, so we use rules as final decision
    # ============================================================================

    if sentiment_score >= 1:
        return 'positive'  # Moderately positive
    elif sentiment_score <= -1:
        return 'negative'  # Moderately negative
    else:
        return 'neutral'  # Balanced or factual statement


def calculate_recency_weight(time_posted):
    """
    Calculate weight multiplier based on comment recency.
    Newer comments are weighted higher than older ones.

    Args:
        time_posted: String in format "YYYY-MM"

    Returns:
        float: Weight multiplier (0.5 to 1.5)
    """
    try:
        # Parse the time_posted field (format: "2024-11")
        comment_date = datetime.strptime(time_posted, "%Y-%m")
        current_date = datetime(2025, 1, 1)  # Reference date for mock data

        # Calculate months difference
        months_old = (current_date.year - comment_date.year) * 12
        months_old += current_date.month - comment_date.month

        # Recency weighting: newer = higher weight
        if months_old <= 2:
            return 1.5  # Very recent (last 2 months)
        elif months_old <= 6:
            return 1.2  # Recent (2-6 months)
        elif months_old <= 12:
            return 1.0  # Moderately recent (6-12 months)
        else:
            return 0.7  # Older than a year

    except Exception:
        # If parsing fails, default weight
        return 1.0


class MockRedditDataLoader:
    """Loads and processes mock Reddit data from JSON files."""

    def __init__(self):
        self.comments_data = None
        self.university_mappings = None
        self._load_data()

    def _load_data(self):
        """Load data from JSON files on initialization."""

        # Load comments
        comments_path = DATA_DIR / "reddit_comments.json"
        if comments_path.exists():
            with open(comments_path, 'r') as f:
                data = json.load(f)
                self.comments_data = data
        else:
            raise FileNotFoundError(
                f"Could not find reddit_comments.json at {comments_path}"
            )

        # Load university mappings
        uni_path = DATA_DIR / "university_subreddits.json"
        if uni_path.exists():
            with open(uni_path, 'r') as f:
                data = json.load(f)
                self.university_mappings = data['mappings']
        else:
            raise FileNotFoundError(
                f"Could not find university_subreddits.json at {uni_path}"
            )

    def get_subreddit_for_university(self, university):
        """
        Map university name to appropriate subreddit.

        Args:
            university: University name (e.g., "UIUC", "Berkeley")

        Returns:
            Subreddit name (e.g., "UIUC", "berkeley")
        """
        uni_lower = university.lower().strip()
        return self.university_mappings.get(uni_lower, "college")

    def get_comments_by_category(self, subreddit, category, num_comments=None):
        """
        Get comments from a specific university subreddit and category.

        Args:
            subreddit: Subreddit name (e.g., "UIUC", "jhu")
            category: Category name (e.g., "noise", "location")
            num_comments: Number of comments to return (None = all)

        Returns:
            List of comment dicts
        """
        print(f"   Loading comments: subreddit=r/{subreddit}, category={category}")

        # Check if subreddit exists in data
        if subreddit not in self.comments_data:
            print(f"        Subreddit '{subreddit}' not found in data")
            # Fallback to UIUC if subreddit not found - Placeholder as mock Reddit data only contains cases for UIUC and Johns Hopkins
            if 'UIUC' in self.comments_data:
                print(f"       Using fallback: UIUC")
                subreddit = 'UIUC'
            else:
                print(f"       No fallback available, returning empty list")
                return []

        # Skip metadata
        if subreddit == 'metadata':
            return []

        # Check if category exists for this subreddit
        if category not in self.comments_data[subreddit]:
            print(f"        Category '{category}' not found in r/{subreddit}")
            return []

        comments = self.comments_data[subreddit][category]
        print(f"      ✅ Found {len(comments)} comments for r/{subreddit}/{category}")

        if num_comments and num_comments < len(comments):
            return random.sample(comments, num_comments)

        return comments.copy()

    def get_diverse_comments(self, subreddit, num_comments=10):
        """
        Get a diverse selection of comments across all categories for a specific university.

        Args:
            subreddit: Subreddit name (e.g., "UIUC", "jhu")
            num_comments: Total number of comments to return

        Returns:
            List of comment dicts with diverse categories
        """
        print(f"    Getting diverse comments from r/{subreddit}")

        # Check if subreddit exists
        if subreddit not in self.comments_data:
            print(f"        Subreddit '{subreddit}' not found")
            # Fallback to UIUC
            if 'UIUC' in self.comments_data:
                print(f"       Using fallback: UIUC")
                subreddit = 'UIUC'
            else:
                print(f"       No fallback available, returning empty list")
                return []

        # Skip metadata
        if subreddit == 'metadata':
            return []

        all_comments = []

        # Categories to sample from (excluding description/note keys)
        categories = [
            "location", "safety", "noise", "landlord",
            "transit", "condition", "price", "overall", "social"
        ]

        # Get 1-2 comments from each category for variety
        for category in categories:
            if category in self.comments_data[subreddit]:
                cat_comments = self.comments_data[subreddit][category]
                sample_size = min(2, len(cat_comments))
                sampled = random.sample(cat_comments, sample_size)

                # Add category label to each comment
                for comment in sampled:
                    comment['category'] = category
                    all_comments.append(comment)

        print(f"      ✅ Retrieved {len(all_comments)} diverse comments from r/{subreddit}")

        # Shuffle and limit to requested number
        random.shuffle(all_comments)
        return all_comments[:num_comments]


# Global loader instance
_loader = None

def get_loader():
    """Get or create the global data loader instance."""
    global _loader
    if _loader is None:
        _loader = MockRedditDataLoader()
    return _loader


def get_mock_student_reviews(address, university, num_comments=10):
    """
    Generate realistic mock Reddit comments for an apartment listing.

    This function simulates what a real Reddit API integration would return,
    using pre-loaded mock data from JSON files.

    Args:
        address: Apartment address (used for future context-aware filtering)
        university: University name (determines subreddit)
        num_comments: Number of comments to return (default 10)

    Returns:
        Dict with comments list and metadata

    Example:
        >>> results = get_mock_student_reviews("123 Main St", "UIUC", 8)
        >>> print(results['subreddit'])  # "UIUC"
        >>> print(len(results['comments']))  # 8
    """

    loader = get_loader()

    # Determine subreddit from university name
    subreddit = loader.get_subreddit_for_university(university)
    print(f"\n🎓 University: {university} → Subreddit: r/{subreddit}")

    # Get diverse comments across categories for this university
    selected_comments = loader.get_diverse_comments(subreddit, num_comments)

    # Format for return (simulating Reddit API structure)
    formatted_comments = []

    for comment in selected_comments:
        # Infer sentiment from text (not pre-labeled!)
        sentiment = infer_sentiment(comment["text"])

        # Calculate recency weight
        recency_weight = calculate_recency_weight(comment.get("time_posted", "2024-06"))

        formatted_comments.append({
            "text": comment["text"],
            "score": comment["score"],
            "subreddit": subreddit,
            "category": comment.get("category", "general"),
            "sentiment": sentiment,  # INFERRED from text
            "time_posted": comment.get("time_posted", "unknown"),
            "user_type": comment.get("user_type", "student"),
            "recency_weight": recency_weight,
            # PRIVACY: NO username field (intentionally excluded)
            # In production with real Reddit API:
            # "permalink": f"https://reddit.com/r/{subreddit}/comments/{post_id}/..."
            "permalink": f"https://reddit.com/r/{subreddit}/comments/mock_{hash(comment['text'][:20])}/apartment_discussion"
        })

    # Calculate aggregate metrics using INFERRED sentiment
    sentiments = [c["sentiment"] for c in formatted_comments]
    positive_count = sentiments.count("positive")
    negative_count = sentiments.count("negative")
    neutral_count = sentiments.count("neutral")

    # Weighted sentiment scoring (1-5 stars) with recency consideration
    total_weight = sum(c["recency_weight"] for c in formatted_comments)
    weighted_positive = sum(c["recency_weight"] for c in formatted_comments if c["sentiment"] == "positive")
    weighted_negative = sum(c["recency_weight"] for c in formatted_comments if c["sentiment"] == "negative")

    # Calculate score based on weighted sentiment
    if total_weight > 0:
        pos_ratio = weighted_positive / total_weight
        neg_ratio = weighted_negative / total_weight

        if neg_ratio > 0.5:
            overall_score = 2.0  # Mostly negative
        elif pos_ratio > 0.5:
            overall_score = 4.5  # Mostly positive
        elif pos_ratio > neg_ratio:
            overall_score = 3.5  # Slightly positive
        elif neg_ratio > pos_ratio:
            overall_score = 2.5  # Slightly negative
        else:
            overall_score = 3.0  # Balanced
    else:
        overall_score = 3.0

    return {
        "comments": formatted_comments,
        "total_mentions": len(formatted_comments),
        "subreddit": subreddit,
        "overall_score": overall_score,
        "sentiment_breakdown": {
            "positive": positive_count,
            "negative": negative_count,
            "neutral": neutral_count
        },
        "source": "mock_data",
        "note": "Mock data - Reddit API requires pre-approval as of Nov 2025",
        # Note: address parameter reserved for future context-aware filtering
        # e.g., filtering comments that mention specific streets/neighborhoods
    }


def get_comments_by_category(university, category, num_comments=3):
    """
    Get specific category of comments (useful for targeted analysis).

    Args:
        university: University name
        category: Category to filter by (location, safety, noise, etc.)
        num_comments: Number to return

    Returns:
        List of formatted comments in that category
    """
    loader = get_loader()
    subreddit = loader.get_subreddit_for_university(university)
    print(f"\n🎓 University: {university} → Subreddit: r/{subreddit}")

    comments = loader.get_comments_by_category(subreddit, category, num_comments)

    formatted = []
    for comment in comments:
        # Infer sentiment from text
        sentiment = infer_sentiment(comment["text"])
        recency_weight = calculate_recency_weight(comment.get("time_posted", "2024-06"))

        formatted.append({
            "text": comment["text"],
            "score": comment["score"],
            "subreddit": subreddit,
            "category": category,
            "sentiment": sentiment,  # INFERRED
            "time_posted": comment.get("time_posted", "unknown"),
            "user_type": comment.get("user_type", "student"),
            "recency_weight": recency_weight,
            "permalink": f"https://reddit.com/r/{subreddit}/comments/mock_{hash(comment['text'][:20])}/..."
        })

    return formatted


def get_available_categories():
    """
    Get list of available comment categories.

    Returns:
        List of category names
    """
    loader = get_loader()

    # Get categories from first university (all universities have same categories)
    # Skip metadata
    universities = [k for k in loader.comments_data.keys() if k != 'metadata']

    if not universities:
        return []

    # Use first university to get category list
    first_uni = universities[0]
    return [
        key for key in loader.comments_data[first_uni].keys()
        if key not in ['description', 'note']
    ]


def get_data_stats():
    """
    Get statistics about the mock data.

    Returns:
        Dict with data statistics
    """
    loader = get_loader()

    # Get universities (skip metadata)
    universities = [k for k in loader.comments_data.keys() if k != 'metadata']

    # Count total comments across all universities and categories
    total_comments = 0
    for uni in universities:
        categories = get_available_categories()
        for cat in categories:
            if cat in loader.comments_data[uni]:
                total_comments += len(loader.comments_data[uni][cat])

    return {
        "total_comments": total_comments,
        "categories": get_available_categories(),
        "universities_in_data": universities,
        "universities_supported": len(loader.university_mappings),
        "source": "Mock data (Reddit API requires pre-approval)"
    }


# Example usage and testing
if __name__ == "__main__":
    print("=== Testing Mock Reddit Data Processor ===\n")

    # Test data loading
    print(" Data Statistics:")
    stats = get_data_stats()
    print(f"   Total comments: {stats['total_comments']}")
    print(f"   Categories: {len(stats['categories'])}")
    print(f"   Universities in data: {stats['universities_in_data']}")
    print(f"   Universities supported (mappings): {stats['universities_supported']}")
    print()

    # Test getting reviews for UIUC
    print("=" * 60)
    print(" Testing UIUC:")
    print("=" * 60)
    results_uiuc = get_mock_student_reviews(
        address="123 Main St, Champaign IL",
        university="UIUC",
        num_comments=5
    )

    print(f"\nSubreddit: r/{results_uiuc['subreddit']}")
    print(f"Total mentions: {results_uiuc['total_mentions']}")
    print(f"Overall score: {results_uiuc['overall_score']}/5.0")
    print(f"Sentiment: {results_uiuc['sentiment_breakdown']}\n")

    print("Sample comments:\n")
    for i, comment in enumerate(results_uiuc['comments'][:2], 1):
        print(f"{i}. [{comment['category'].upper()}] ({comment['sentiment']} - INFERRED)")
        print(f"   \"{comment['text'][:80]}...\"")
        print(f"   From: r/{comment['subreddit']}\n")

    # Test getting reviews for Johns Hopkins
    print("=" * 60)
    print(" Testing Johns Hopkins:")
    print("=" * 60)
    results_jhu = get_mock_student_reviews(
        address="456 Charles St, Baltimore MD",
        university="Johns Hopkins",
        num_comments=5
    )

    print(f"\nSubreddit: r/{results_jhu['subreddit']}")
    print(f"Total mentions: {results_jhu['total_mentions']}")
    print(f"Overall score: {results_jhu['overall_score']}/5.0")
    print(f"Sentiment: {results_jhu['sentiment_breakdown']}\n")

    print("Sample comments:\n")
    for i, comment in enumerate(results_jhu['comments'][:2], 1):
        print(f"{i}. [{comment['category'].upper()}] ({comment['sentiment']} - INFERRED)")
        print(f"   \"{comment['text'][:80]}...\"")
        print(f"   From: r/{comment['subreddit']}\n")

    print("✅ All tests passed!")
    print(f"✅ Data loaded from: {DATA_DIR}")
