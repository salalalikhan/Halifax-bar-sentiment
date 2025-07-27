"""Unit tests for validation module."""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch

from src.models.validation import (
    RedditPost,
    RedditComment,
    BarMention,
    DataQualityMetrics,
    ContentFilter,
    DataValidator,
    ValidationError
)


class TestRedditPost:
    """Test cases for RedditPost validation."""

    def test_valid_reddit_post(self):
        """Test valid Reddit post creation."""
        post_data = {
            "id": "abc123",
            "title": "Great bar in Halifax",
            "selftext": "Had an amazing experience at this bar.",
            "created_utc": datetime(2023, 1, 1).timestamp(),
            "score": 10,
            "url": "https://reddit.com/r/halifax/comments/abc123",
            "comments": []
        }
        
        post = RedditPost(**post_data)
        
        assert post.id == "abc123"
        assert post.title == "Great bar in Halifax"
        assert post.score == 10
        assert len(post.comments) == 0

    def test_invalid_reddit_post_id(self):
        """Test invalid Reddit post ID."""
        post_data = {
            "id": "ABC123!",  # Invalid characters
            "title": "Test",
            "created_utc": datetime(2023, 1, 1).timestamp(),
            "url": "https://reddit.com/test"
        }
        
        with pytest.raises(ValueError, match="Invalid Reddit post ID format"):
            RedditPost(**post_data)

    def test_invalid_url_format(self):
        """Test invalid URL format."""
        post_data = {
            "id": "abc123",
            "title": "Test",
            "created_utc": datetime(2023, 1, 1).timestamp(),
            "url": "not-a-url"
        }
        
        with pytest.raises(ValueError, match="URL must start with"):
            RedditPost(**post_data)

    def test_invalid_timestamp(self):
        """Test invalid timestamp validation."""
        post_data = {
            "id": "abc123",
            "title": "Test",
            "created_utc": datetime(2000, 1, 1).timestamp(),  # Before Reddit launch
            "url": "https://reddit.com/test"
        }
        
        with pytest.raises(ValueError, match="Timestamp outside reasonable range"):
            RedditPost(**post_data)

    def test_title_length_validation(self):
        """Test title length validation."""
        post_data = {
            "id": "abc123",
            "title": "",  # Empty title
            "created_utc": datetime(2023, 1, 1).timestamp(),
            "url": "https://reddit.com/test"
        }
        
        with pytest.raises(ValueError):
            RedditPost(**post_data)


class TestRedditComment:
    """Test cases for RedditComment validation."""

    def test_valid_reddit_comment(self):
        """Test valid Reddit comment creation."""
        comment_data = {
            "id": "def456",
            "body": "This is a valid comment",
            "created_utc": datetime(2023, 1, 1).timestamp(),
            "score": 5
        }
        
        comment = RedditComment(**comment_data)
        
        assert comment.id == "def456"
        assert comment.body == "This is a valid comment"
        assert comment.score == 5

    def test_deleted_comment_validation(self):
        """Test deleted comment validation."""
        comment_data = {
            "id": "def456",
            "body": "[deleted]",
            "created_utc": datetime(2023, 1, 1).timestamp(),
            "score": 0
        }
        
        with pytest.raises(ValueError, match="Comment content is deleted"):
            RedditComment(**comment_data)

    def test_removed_comment_validation(self):
        """Test removed comment validation."""
        comment_data = {
            "id": "def456",
            "body": "[removed]",
            "created_utc": datetime(2023, 1, 1).timestamp(),
            "score": 0
        }
        
        with pytest.raises(ValueError, match="Comment content is deleted"):
            RedditComment(**comment_data)


class TestBarMention:
    """Test cases for BarMention validation."""

    def test_valid_bar_mention(self):
        """Test valid bar mention creation."""
        mention_data = {
            "bar_name": "The Halifax Pub",
            "post_id": "abc123",
            "post_title": "Great bar experience",
            "post_text": "Had a wonderful time at this bar.",
            "created_at": datetime(2023, 1, 1),
            "sentiment_score": 0.8,
            "sentiment_confidence": 0.9,
            "sentiment_label": "positive",
            "food_mentions": ["wings", "beer"],
            "url": "https://reddit.com/test",
            "model_scores": {"vader": 0.7, "textblob": 0.9}
        }
        
        mention = BarMention(**mention_data)
        
        assert mention.bar_name == "The Halifax Pub"
        assert mention.sentiment_score == 0.8
        assert mention.sentiment_label == "positive"
        assert "wings" in mention.food_mentions

    def test_invalid_sentiment_score(self):
        """Test invalid sentiment score."""
        mention_data = {
            "bar_name": "Test Bar",
            "post_id": "abc123",
            "post_title": "Test",
            "created_at": datetime(2023, 1, 1),
            "sentiment_score": 1.5,  # Invalid score > 1
            "sentiment_confidence": 0.8,
            "sentiment_label": "positive",
            "url": "https://reddit.com/test"
        }
        
        with pytest.raises(ValueError):
            BarMention(**mention_data)

    def test_invalid_sentiment_label(self):
        """Test invalid sentiment label."""
        mention_data = {
            "bar_name": "Test Bar",
            "post_id": "abc123",
            "post_title": "Test",
            "created_at": datetime(2023, 1, 1),
            "sentiment_score": 0.5,
            "sentiment_confidence": 0.8,
            "sentiment_label": "invalid",  # Invalid label
            "url": "https://reddit.com/test"
        }
        
        with pytest.raises(ValueError):
            BarMention(**mention_data)

    def test_model_scores_validation(self):
        """Test model scores validation."""
        mention_data = {
            "bar_name": "Test Bar",
            "post_id": "abc123",
            "post_title": "Test",
            "created_at": datetime(2023, 1, 1),
            "sentiment_score": 0.5,
            "sentiment_confidence": 0.8,
            "sentiment_label": "positive",
            "url": "https://reddit.com/test",
            "model_scores": {"invalid_model": 0.5}  # Invalid model name
        }
        
        with pytest.raises(ValueError, match="Unknown model"):
            BarMention(**mention_data)

    def test_food_mentions_normalization(self):
        """Test food mentions normalization."""
        mention_data = {
            "bar_name": "Test Bar",
            "post_id": "abc123",
            "post_title": "Test",
            "created_at": datetime(2023, 1, 1),
            "sentiment_score": 0.5,
            "sentiment_confidence": 0.8,
            "sentiment_label": "positive",
            "url": "https://reddit.com/test",
            "food_mentions": ["  Wings  ", "BEER", "wings", ""]  # Should normalize
        }
        
        mention = BarMention(**mention_data)
        
        # Should remove duplicates, normalize case, and filter empty strings
        assert "wings" in mention.food_mentions
        assert "beer" in mention.food_mentions
        assert len(mention.food_mentions) == 2  # No duplicates


class TestDataQualityMetrics:
    """Test cases for DataQualityMetrics validation."""

    def test_valid_quality_metrics(self):
        """Test valid quality metrics creation."""
        metrics_data = {
            "total_posts_processed": 100,
            "valid_posts": 90,
            "invalid_posts": 10,
            "total_mentions_found": 50,
            "unique_bars_mentioned": 20,
            "duplicate_posts_filtered": 5,
            "spam_posts_filtered": 3,
            "average_sentiment_confidence": 0.85
        }
        
        metrics = DataQualityMetrics(**metrics_data)
        
        assert metrics.total_posts_processed == 100
        assert metrics.valid_posts == 90
        assert metrics.data_quality_score > 0

    def test_data_quality_score_calculation(self):
        """Test data quality score calculation."""
        metrics = DataQualityMetrics(
            total_posts_processed=100,
            valid_posts=80,
            invalid_posts=20,
            total_mentions_found=50,
            unique_bars_mentioned=15,
            duplicate_posts_filtered=5,
            spam_posts_filtered=3,
            average_sentiment_confidence=0.9
        )
        
        expected_score = (0.8 * 0.7) + (0.9 * 0.3)  # 80% validity, 90% confidence
        assert abs(metrics.data_quality_score - expected_score) < 0.01

    def test_invalid_post_count(self):
        """Test invalid post count validation."""
        metrics_data = {
            "total_posts_processed": 100,
            "valid_posts": 120,  # More than total
            "invalid_posts": 10,
            "total_mentions_found": 50,
            "unique_bars_mentioned": 20,
            "duplicate_posts_filtered": 5,
            "spam_posts_filtered": 3,
            "average_sentiment_confidence": 0.85
        }
        
        with pytest.raises(ValueError, match="Count cannot exceed total"):
            DataQualityMetrics(**metrics_data)


class TestContentFilter:
    """Test cases for ContentFilter validation."""

    def test_spam_detection(self):
        """Test spam detection functionality."""
        filter_obj = ContentFilter()
        
        # Test legitimate content
        assert not filter_obj.is_spam("Great food at this bar!")
        
        # Test spam content
        assert filter_obj.is_spam("BUY NOW! LIMITED TIME OFFER! CLICK HERE!")
        assert filter_obj.is_spam("Visit our website for promo code discount code")

    def test_length_validation(self):
        """Test text length validation."""
        filter_obj = ContentFilter(min_text_length=5, max_text_length=100)
        
        assert not filter_obj.is_valid_length("Hi")  # Too short
        assert filter_obj.is_valid_length("This is a good length")
        assert not filter_obj.is_valid_length("x" * 101)  # Too long

    def test_relevance_calculation(self):
        """Test relevance score calculation."""
        filter_obj = ContentFilter()
        bar_names = {"Halifax Pub", "The Bitter End"}
        
        # High relevance
        high_relevance = filter_obj.calculate_relevance(
            "Great food and drinks at Halifax Pub with excellent service",
            bar_names
        )
        
        # Low relevance
        low_relevance = filter_obj.calculate_relevance(
            "I went to the store yesterday to buy groceries",
            bar_names
        )
        
        assert high_relevance > low_relevance
        assert 0 <= high_relevance <= 1
        assert 0 <= low_relevance <= 1

    def test_empty_text_relevance(self):
        """Test relevance calculation with empty text."""
        filter_obj = ContentFilter()
        
        relevance = filter_obj.calculate_relevance("", {"Halifax Pub"})
        assert relevance == 0.0


class TestDataValidator:
    """Test cases for DataValidator class."""

    def test_validator_initialization(self):
        """Test validator initialization."""
        validator = DataValidator()
        
        assert validator.content_filter is not None
        assert validator.metrics is not None
        assert validator.metrics.total_posts_processed == 0

    def test_validate_reddit_post_success(self):
        """Test successful Reddit post validation."""
        validator = DataValidator()
        
        post_data = {
            "id": "abc123",
            "title": "Test post",
            "created_utc": datetime(2023, 1, 1).timestamp(),
            "url": "https://reddit.com/test"
        }
        
        post = validator.validate_reddit_post(post_data)
        assert isinstance(post, RedditPost)
        assert post.id == "abc123"

    def test_validate_reddit_post_failure(self):
        """Test failed Reddit post validation."""
        validator = DataValidator()
        
        invalid_post_data = {
            "id": "INVALID!",
            "title": "Test",
            "created_utc": datetime(2023, 1, 1).timestamp(),
            "url": "https://reddit.com/test"
        }
        
        with pytest.raises(ValidationError, match="Invalid Reddit post"):
            validator.validate_reddit_post(invalid_post_data)

    def test_validate_bar_mention_success(self):
        """Test successful bar mention validation."""
        validator = DataValidator()
        
        mention_data = {
            "bar_name": "Test Bar",
            "post_id": "abc123",
            "post_title": "Test",
            "created_at": datetime(2023, 1, 1),
            "sentiment_score": 0.5,
            "sentiment_confidence": 0.8,
            "sentiment_label": "positive",
            "url": "https://reddit.com/test"
        }
        
        mention = validator.validate_bar_mention(mention_data)
        assert isinstance(mention, BarMention)
        assert mention.bar_name == "Test Bar"

    def test_filter_content_valid(self):
        """Test content filtering with valid content."""
        validator = DataValidator()
        bar_names = {"Halifax Pub"}
        
        is_valid, reason = validator.filter_content(
            "Great food and atmosphere at Halifax Pub",
            bar_names
        )
        
        assert is_valid is True
        assert reason == ""

    def test_filter_content_spam(self):
        """Test content filtering with spam content."""
        validator = DataValidator()
        bar_names = {"Halifax Pub"}
        
        is_valid, reason = validator.filter_content(
            "BUY NOW! CLICK HERE! Halifax Pub promo code",
            bar_names
        )
        
        assert is_valid is False
        assert "spam" in reason.lower()

    def test_filter_content_low_relevance(self):
        """Test content filtering with low relevance."""
        validator = DataValidator(ContentFilter(required_relevance_score=0.5))
        bar_names = {"Halifax Pub"}
        
        is_valid, reason = validator.filter_content(
            "I went shopping yesterday",
            bar_names
        )
        
        assert is_valid is False
        assert "relevance" in reason.lower()

    def test_update_metrics(self):
        """Test metrics updating."""
        validator = DataValidator()
        
        validator.update_metrics(
            valid_posts=50,
            invalid_posts=10,
            total_mentions_found=30
        )
        
        assert validator.metrics.valid_posts == 50
        assert validator.metrics.invalid_posts == 10
        assert validator.metrics.total_mentions_found == 30

    def test_quality_report_generation(self):
        """Test quality report generation."""
        validator = DataValidator()
        
        validator.update_metrics(
            total_posts_processed=100,
            valid_posts=90,
            invalid_posts=10,
            total_mentions_found=50,
            unique_bars_mentioned=20,
            spam_posts_filtered=5,
            average_sentiment_confidence=0.85
        )
        
        report = validator.get_quality_report()
        
        assert report["total_processed"] == 100
        assert report["valid_posts"] == 90
        assert report["data_quality_score"] > 0
        assert "timestamp" in report


class TestValidationError:
    """Test cases for ValidationError exception."""

    def test_validation_error_creation(self):
        """Test validation error creation."""
        error = ValidationError("Test error", field="test_field", value="test_value")
        
        assert str(error) == "Test error"
        assert error.field == "test_field"
        assert error.value == "test_value"

    def test_validation_error_minimal(self):
        """Test validation error with minimal parameters."""
        error = ValidationError("Simple error")
        
        assert str(error) == "Simple error"
        assert error.field is None
        assert error.value is None


@pytest.mark.integration
class TestValidationIntegration:
    """Integration tests for validation system."""

    def test_full_validation_pipeline(self):
        """Test complete validation pipeline."""
        validator = DataValidator()
        
        # Test complete flow
        post_data = {
            "id": "abc123",
            "title": "Amazing experience at Halifax Pub",
            "selftext": "Great food and friendly service",
            "created_utc": datetime(2023, 1, 1).timestamp(),
            "url": "https://reddit.com/r/halifax/comments/abc123"
        }
        
        # Validate post
        post = validator.validate_reddit_post(post_data)
        assert isinstance(post, RedditPost)
        
        # Filter content
        is_valid, reason = validator.filter_content(
            f"{post.title} {post.selftext}",
            {"Halifax Pub"}
        )
        assert is_valid is True
        
        # Validate mention
        mention_data = {
            "bar_name": "Halifax Pub",
            "post_id": post.id,
            "post_title": post.title,
            "post_text": post.selftext,
            "created_at": datetime.fromtimestamp(post.created_utc),
            "sentiment_score": 0.7,
            "sentiment_confidence": 0.9,
            "sentiment_label": "positive",
            "url": post.url
        }
        
        mention = validator.validate_bar_mention(mention_data)
        assert isinstance(mention, BarMention)
        
        # Update metrics
        validator.update_metrics(
            total_posts_processed=1,
            valid_posts=1,
            invalid_posts=0,
            total_mentions_found=1,
            unique_bars_mentioned=1,
            spam_posts_filtered=0,
            average_sentiment_confidence=0.9
        )
        
        report = validator.get_quality_report()
        assert report["data_quality_score"] > 0.8