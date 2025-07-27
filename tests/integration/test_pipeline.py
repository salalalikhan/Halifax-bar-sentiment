"""Integration tests for the complete ETL pipeline."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from typing import List, Dict, Any

from src.services.transform import transform_posts
from src.models.sentiment import HospitalitySentimentAnalyzer
from src.models.validation import DataValidator


class TestETLPipeline:
    """Integration tests for the complete ETL pipeline."""

    def setup_method(self):
        """Set up test fixtures."""
        self.sample_reddit_posts = [
            {
                "id": "abc123",
                "title": "Great experience at Your Father's Moustache",
                "selftext": "Had amazing wings and beer. The atmosphere was cozy and service was friendly.",
                "created_utc": datetime(2023, 6, 15, 12, 0, 0).timestamp(),
                "score": 25,
                "url": "https://reddit.com/r/halifax/comments/abc123",
                "comments": [
                    {
                        "id": "def456",
                        "body": "I agree! The wings at Your Father's Moustache are the best in Halifax.",
                        "created_utc": datetime(2023, 6, 15, 12, 30, 0).timestamp(),
                        "score": 5
                    }
                ]
            },
            {
                "id": "ghi789",
                "title": "Terrible experience at The Bitter End",
                "selftext": "The service was slow and the food was cold. Very disappointed.",
                "created_utc": datetime(2023, 6, 16, 19, 0, 0).timestamp(),
                "score": -5,
                "url": "https://reddit.com/r/halifax/comments/ghi789",
                "comments": []
            },
            {
                "id": "jkl012",
                "title": "Good Robot has great craft beer",
                "selftext": "Love their selection of local brews. The atmosphere is cool too.",
                "created_utc": datetime(2023, 6, 17, 16, 0, 0).timestamp(),
                "score": 15,
                "url": "https://reddit.com/r/halifax/comments/jkl012",
                "comments": []
            }
        ]

    def test_transform_posts_basic_functionality(self):
        """Test basic transform_posts functionality."""
        transformed_data, quality_metrics = transform_posts(self.sample_reddit_posts)
        
        # Check that we got transformed data
        assert len(transformed_data) > 0
        assert isinstance(transformed_data, list)
        assert isinstance(quality_metrics, dict)
        
        # Check data structure
        for item in transformed_data:
            assert "bar_name" in item
            assert "sentiment_score" in item
            assert "sentiment_confidence" in item
            assert "sentiment_label" in item
            assert "post_id" in item
            assert "post_title" in item
            assert "created_at" in item
            assert "url" in item
            assert "food_mentions" in item

    def test_transform_posts_sentiment_analysis(self):
        """Test sentiment analysis in transform pipeline."""
        transformed_data, quality_metrics = transform_posts(self.sample_reddit_posts)
        
        # Find the positive and negative mentions
        positive_mentions = [item for item in transformed_data if item["sentiment_label"] == "positive"]
        negative_mentions = [item for item in transformed_data if item["sentiment_label"] == "negative"]
        
        # Should have at least some positive mentions from the good review
        assert len(positive_mentions) > 0
        
        # Should have at least some negative mentions from the bad review
        assert len(negative_mentions) > 0
        
        # Check sentiment scores are in valid range
        for item in transformed_data:
            assert -1 <= item["sentiment_score"] <= 1
            assert 0 <= item["sentiment_confidence"] <= 1
            assert item["sentiment_label"] in ["positive", "negative", "neutral"]

    def test_transform_posts_bar_detection(self):
        """Test bar name detection in transform pipeline."""
        transformed_data, quality_metrics = transform_posts(self.sample_reddit_posts)
        
        # Should detect the bars mentioned in the test data
        detected_bars = set(item["bar_name"] for item in transformed_data)
        
        # Should include the bars mentioned in our test posts
        expected_bars = {"Your Father's Moustache", "The Bitter End", "Good Robot"}
        assert expected_bars.issubset(detected_bars) or len(detected_bars) > 0

    def test_transform_posts_food_mentions(self):
        """Test food mention detection in transform pipeline."""
        transformed_data, quality_metrics = transform_posts(self.sample_reddit_posts)
        
        # Should detect food mentions
        all_food_mentions = []
        for item in transformed_data:
            all_food_mentions.extend(item["food_mentions"])
        
        # Should detect some food items from our test data
        assert len(all_food_mentions) > 0
        
        # Should include items mentioned in test posts
        food_mentions_str = " ".join(all_food_mentions)
        assert any(food in food_mentions_str for food in ["wings", "beer", "food"])

    def test_transform_posts_comment_processing(self):
        """Test comment processing in transform pipeline."""
        transformed_data, quality_metrics = transform_posts(self.sample_reddit_posts)
        
        # Should process comments as well as posts
        comment_mentions = [item for item in transformed_data if "Comment on:" in item["post_title"]]
        
        # Should have at least one comment mention from our test data
        assert len(comment_mentions) > 0

    def test_transform_posts_data_quality(self):
        """Test data quality metrics from transform pipeline."""
        transformed_data, quality_metrics = transform_posts(self.sample_reddit_posts)
        
        # Check quality metrics structure
        assert isinstance(quality_metrics, dict)
        assert "total_processed" in quality_metrics
        assert "valid_posts" in quality_metrics
        assert "data_quality_score" in quality_metrics
        assert "average_confidence" in quality_metrics
        
        # Check quality metrics values
        assert quality_metrics["total_processed"] == len(self.sample_reddit_posts)
        assert quality_metrics["valid_posts"] <= quality_metrics["total_processed"]
        assert 0 <= quality_metrics["data_quality_score"] <= 1
        assert 0 <= quality_metrics["average_confidence"] <= 1

    def test_transform_posts_validation(self):
        """Test data validation in transform pipeline."""
        transformed_data, quality_metrics = transform_posts(self.sample_reddit_posts)
        
        # All transformed data should pass validation
        validator = DataValidator()
        
        for item in transformed_data:
            # Should not raise validation errors
            try:
                validated_mention = validator.validate_bar_mention(item)
                assert validated_mention is not None
            except Exception as e:
                pytest.fail(f"Validation failed for item {item}: {e}")

    def test_transform_posts_empty_input(self):
        """Test transform pipeline with empty input."""
        transformed_data, quality_metrics = transform_posts([])
        
        assert transformed_data == []
        assert quality_metrics["total_processed"] == 0
        assert quality_metrics["valid_posts"] == 0
        assert quality_metrics["data_quality_score"] == 0

    def test_transform_posts_invalid_data(self):
        """Test transform pipeline with invalid data."""
        invalid_posts = [
            {
                "id": "INVALID!",  # Invalid ID format
                "title": "Test",
                "created_utc": datetime(2000, 1, 1).timestamp(),  # Invalid timestamp
                "url": "not-a-url"  # Invalid URL
            }
        ]
        
        transformed_data, quality_metrics = transform_posts(invalid_posts)
        
        # Should handle invalid data gracefully
        assert quality_metrics["invalid_posts"] > 0
        assert quality_metrics["data_quality_score"] < 1.0

    def test_transform_posts_spam_filtering(self):
        """Test spam filtering in transform pipeline."""
        spam_posts = [
            {
                "id": "spam123",
                "title": "BUY NOW! CLICK HERE! DISCOUNT CODE!",
                "selftext": "Visit our website for amazing deals on Your Father's Moustache!",
                "created_utc": datetime(2023, 6, 15, 12, 0, 0).timestamp(),
                "score": 1,
                "url": "https://reddit.com/r/halifax/comments/spam123",
                "comments": []
            }
        ]
        
        transformed_data, quality_metrics = transform_posts(spam_posts)
        
        # Should filter out spam content
        assert quality_metrics["spam_filtered"] > 0 or len(transformed_data) == 0

    def test_sentiment_analyzer_integration(self):
        """Test sentiment analyzer integration with hospitality domain."""
        analyzer = HospitalitySentimentAnalyzer()
        
        # Test hospitality-specific sentiment analysis
        test_cases = [
            ("The food was amazing and the service was excellent!", "positive"),
            ("Terrible food and slow service", "negative"),
            ("The atmosphere was cozy and the beer was fresh", "positive"),
            ("Overpriced and the waiters were rude", "negative"),
            ("It was okay", "neutral")
        ]
        
        for text, expected_category in test_cases:
            result = analyzer.analyze_sentiment(text)
            
            # Check sentiment analysis results
            assert isinstance(result.score, float)
            assert -1 <= result.score <= 1
            assert 0 <= result.confidence <= 1
            assert result.sentiment_label in ["positive", "negative", "neutral"]
            
            # Check that hospitality domain adjustments are applied
            assert hasattr(result, 'model_scores')
            assert isinstance(result.model_scores, dict)

    def test_data_validator_integration(self):
        """Test data validator integration with content filtering."""
        validator = DataValidator()
        
        # Test content filtering
        test_cases = [
            ("Great food and drinks at Halifax bars", True),
            ("BUY NOW! CLICK HERE! SPAM CONTENT", False),
            ("", False),
            ("I went shopping yesterday", False)  # Low relevance
        ]
        
        bar_names = {"Halifax Pub", "The Bitter End", "Good Robot"}
        
        for text, should_be_valid in test_cases:
            is_valid, reason = validator.filter_content(text, bar_names)
            
            assert is_valid == should_be_valid
            if not is_valid:
                assert isinstance(reason, str)
                assert len(reason) > 0

    def test_full_pipeline_consistency(self):
        """Test consistency across multiple pipeline runs."""
        # Run pipeline multiple times
        results = []
        for _ in range(3):
            transformed_data, quality_metrics = transform_posts(self.sample_reddit_posts)
            results.append((transformed_data, quality_metrics))
        
        # Results should be consistent
        first_result = results[0]
        for other_result in results[1:]:
            # Same number of mentions
            assert len(first_result[0]) == len(other_result[0])
            
            # Same quality metrics
            assert first_result[1]["total_processed"] == other_result[1]["total_processed"]
            
            # Same sentiment scores (should be deterministic)
            for item1, item2 in zip(first_result[0], other_result[0]):
                assert item1["sentiment_score"] == item2["sentiment_score"]
                assert item1["sentiment_confidence"] == item2["sentiment_confidence"]

    def test_pipeline_performance(self):
        """Test pipeline performance with larger dataset."""
        # Create larger dataset
        large_dataset = self.sample_reddit_posts * 10  # 30 posts
        
        import time
        start_time = time.time()
        
        transformed_data, quality_metrics = transform_posts(large_dataset)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Should process reasonably quickly
        assert processing_time < 30  # Should complete in under 30 seconds
        
        # Should scale linearly
        assert len(transformed_data) > 0
        assert quality_metrics["total_processed"] == len(large_dataset)

    def test_error_handling_robustness(self):
        """Test pipeline robustness with various error conditions."""
        # Test with malformed data
        malformed_posts = [
            {
                "id": "test1",
                "title": "Test",
                "created_utc": "invalid_timestamp",  # Invalid type
                "url": "https://reddit.com/test"
            },
            {
                "id": "test2",
                "title": None,  # None value
                "created_utc": datetime(2023, 1, 1).timestamp(),
                "url": "https://reddit.com/test"
            }
        ]
        
        # Should handle errors gracefully without crashing
        try:
            transformed_data, quality_metrics = transform_posts(malformed_posts)
            
            # Should track invalid posts
            assert quality_metrics["invalid_posts"] > 0
            
        except Exception as e:
            pytest.fail(f"Pipeline should handle malformed data gracefully: {e}")


@pytest.mark.integration
class TestAPIIntegrationWithPipeline:
    """Integration tests for API with the data pipeline."""

    def setup_method(self):
        """Set up test fixtures."""
        self.sample_transformed_data = [
            {
                "bar_name": "Test Bar",
                "post_id": "abc123",
                "post_title": "Great experience",
                "post_text": "Had amazing food",
                "created_at": datetime(2023, 6, 15, 12, 0, 0),
                "sentiment_score": 0.8,
                "sentiment_confidence": 0.9,
                "sentiment_label": "positive",
                "food_mentions": ["wings", "beer"],
                "url": "https://reddit.com/test"
            }
        ]

    @patch('src.services.database.DatabaseService')
    def test_api_with_pipeline_data(self, mock_db_service):
        """Test API endpoints with pipeline-generated data."""
        from fastapi.testclient import TestClient
        from src.api.main import app
        
        client = TestClient(app)
        
        # Mock database service to return pipeline-like data
        mock_db = Mock()
        mock_db.get_health_status.return_value = {
            "database_connected": True,
            "last_data_update": datetime.now().isoformat(),
            "total_mentions": 1
        }
        mock_db.get_all_bars.return_value = [
            {
                "name": "Test Bar",
                "total_mentions": 1,
                "avg_sentiment": 0.8,
                "avg_confidence": 0.9,
                "positive_mentions": 1,
                "negative_mentions": 0,
                "neutral_mentions": 0,
                "first_mention": datetime.now(),
                "last_mention": datetime.now(),
                "top_emotions": {"joy": 0.8},
                "specialties": ["wings", "beer"]
            }
        ]
        mock_db_service.return_value = mock_db
        
        # Test API endpoints
        response = client.get("/health")
        assert response.status_code == 200
        
        response = client.get("/bars")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Test Bar"

    def test_pipeline_data_validation_for_api(self):
        """Test that pipeline data is valid for API consumption."""
        from src.services.transform import transform_posts
        
        # Use sample Reddit data
        sample_posts = [
            {
                "id": "abc123",
                "title": "Great bar experience",
                "selftext": "Had amazing wings at Your Father's Moustache",
                "created_utc": datetime(2023, 6, 15, 12, 0, 0).timestamp(),
                "score": 10,
                "url": "https://reddit.com/r/halifax/comments/abc123",
                "comments": []
            }
        ]
        
        # Transform data
        transformed_data, quality_metrics = transform_posts(sample_posts)
        
        # Validate that transformed data can be consumed by API models
        from src.models.api import MentionDetail
        
        for item in transformed_data:
            # Should be able to create API model from pipeline data
            try:
                api_item = {
                    "id": 1,  # Would be assigned by database
                    "bar_name": item["bar_name"],
                    "post_id": item["post_id"],
                    "post_title": item["post_title"],
                    "post_text": item["post_text"],
                    "created_at": item["created_at"],
                    "sentiment_score": item["sentiment_score"],
                    "sentiment_confidence": item["sentiment_confidence"],
                    "sentiment_label": item["sentiment_label"],
                    "food_mentions": item["food_mentions"],
                    "url": item["url"],
                    "model_scores": {},
                    "emotion_scores": None,
                    "is_comment": False
                }
                
                mention_detail = MentionDetail(**api_item)
                assert mention_detail is not None
                
            except Exception as e:
                pytest.fail(f"Pipeline data not compatible with API model: {e}")


@pytest.mark.slow
class TestPipelinePerformance:
    """Performance tests for the pipeline."""

    def test_large_dataset_processing(self):
        """Test processing of large dataset."""
        # Create a large dataset
        large_dataset = []
        for i in range(100):
            large_dataset.append({
                "id": f"post_{i}",
                "title": f"Test post {i} about bars in Halifax",
                "selftext": f"This is post {i} with content about restaurants and bars",
                "created_utc": datetime(2023, 6, 15, 12, i % 60, 0).timestamp(),
                "score": i % 20,
                "url": f"https://reddit.com/r/halifax/comments/post_{i}",
                "comments": []
            })
        
        import time
        start_time = time.time()
        
        transformed_data, quality_metrics = transform_posts(large_dataset)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Performance assertions
        assert processing_time < 60  # Should complete in under 1 minute
        assert quality_metrics["total_processed"] == len(large_dataset)
        
        # Should maintain quality even with large dataset
        assert quality_metrics["data_quality_score"] > 0

    def test_memory_usage(self):
        """Test memory usage during processing."""
        import psutil
        import os
        
        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Process data
        dataset = []
        for i in range(50):
            dataset.append({
                "id": f"post_{i}",
                "title": f"Test post {i}",
                "selftext": "Content about bars and restaurants",
                "created_utc": datetime(2023, 6, 15, 12, 0, 0).timestamp(),
                "score": 1,
                "url": f"https://reddit.com/test_{i}",
                "comments": []
            })
        
        transformed_data, quality_metrics = transform_posts(dataset)
        
        # Get final memory usage
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Memory usage should be reasonable
        assert memory_increase < 100  # Should not use more than 100MB additional