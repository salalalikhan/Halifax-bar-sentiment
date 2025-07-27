"""Unit tests for API endpoints."""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
from fastapi.testclient import TestClient
from fastapi import HTTPException

from src.api.main import app
from src.models.api import (
    BarSummary, MentionDetail, AnalyticsSummary, 
    QualityMetrics, HealthResponse
)


class TestAPIEndpoints:
    """Test cases for API endpoints."""

    def setup_method(self):
        """Set up test client."""
        self.client = TestClient(app)

    def test_root_endpoint(self):
        """Test root endpoint returns HTML."""
        response = self.client.get("/")
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/html; charset=utf-8"
        assert "Halifax Bar Sentiment Analysis API" in response.text

    @patch('src.api.main.get_database_service')
    def test_health_endpoint_healthy(self, mock_get_db):
        """Test health endpoint when system is healthy."""
        mock_db = Mock()
        mock_db.get_health_status.return_value = {
            "database_connected": True,
            "last_data_update": datetime.now().isoformat(),
            "total_mentions": 1000
        }
        mock_get_db.return_value = mock_db
        
        response = self.client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["database_connected"] is True
        assert data["total_mentions"] == 1000

    @patch('src.api.main.get_database_service')
    def test_health_endpoint_unhealthy(self, mock_get_db):
        """Test health endpoint when system is unhealthy."""
        mock_db = Mock()
        mock_db.get_health_status.side_effect = Exception("Database error")
        mock_get_db.return_value = mock_db
        
        response = self.client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "unhealthy"
        assert data["database_connected"] is False

    @patch('src.api.main.get_database_service')
    def test_get_bars_endpoint(self, mock_get_db):
        """Test get bars endpoint."""
        mock_db = Mock()
        mock_db.get_all_bars.return_value = [
            {
                "name": "Test Bar",
                "total_mentions": 100,
                "avg_sentiment": 0.5,
                "avg_confidence": 0.8,
                "positive_mentions": 60,
                "negative_mentions": 20,
                "neutral_mentions": 20,
                "first_mention": datetime.now(),
                "last_mention": datetime.now(),
                "top_emotions": {"joy": 0.7},
                "specialties": ["wings", "beer"]
            }
        ]
        mock_get_db.return_value = mock_db
        
        response = self.client.get("/bars")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Test Bar"
        assert data[0]["total_mentions"] == 100

    @patch('src.api.main.get_database_service')
    def test_get_bars_with_limit(self, mock_get_db):
        """Test get bars endpoint with limit parameter."""
        mock_db = Mock()
        mock_db.get_all_bars.return_value = []
        mock_get_db.return_value = mock_db
        
        response = self.client.get("/bars?limit=5")
        
        assert response.status_code == 200
        mock_db.get_all_bars.assert_called_once_with(limit=5)

    @patch('src.api.main.get_database_service')
    def test_get_bars_invalid_limit(self, mock_get_db):
        """Test get bars endpoint with invalid limit."""
        response = self.client.get("/bars?limit=0")
        
        assert response.status_code == 422  # Validation error

    @patch('src.api.main.get_database_service')
    def test_get_bar_by_name(self, mock_get_db):
        """Test get specific bar by name."""
        mock_db = Mock()
        mock_db.get_bar_by_name.return_value = {
            "name": "Test Bar",
            "total_mentions": 50,
            "avg_sentiment": 0.3,
            "avg_confidence": 0.7,
            "positive_mentions": 30,
            "negative_mentions": 10,
            "neutral_mentions": 10,
            "first_mention": datetime.now(),
            "last_mention": datetime.now(),
            "top_emotions": {"joy": 0.6},
            "specialties": ["food"]
        }
        mock_get_db.return_value = mock_db
        
        response = self.client.get("/bars/Test%20Bar")
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Bar"
        assert data["total_mentions"] == 50

    @patch('src.api.main.get_database_service')
    def test_get_bar_not_found(self, mock_get_db):
        """Test get bar that doesn't exist."""
        mock_db = Mock()
        mock_db.get_bar_by_name.return_value = None
        mock_get_db.return_value = mock_db
        
        response = self.client.get("/bars/NonExistent%20Bar")
        
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Bar not found"

    @patch('src.api.main.get_database_service')
    def test_get_bar_mentions(self, mock_get_db):
        """Test get mentions for a specific bar."""
        mock_db = Mock()
        mock_db.get_mentions.return_value = [
            {
                "id": 1,
                "bar_name": "Test Bar",
                "post_id": "abc123",
                "post_title": "Great experience",
                "post_text": "Had a wonderful time",
                "created_at": datetime.now(),
                "sentiment_score": 0.8,
                "sentiment_confidence": 0.9,
                "sentiment_label": "positive",
                "model_scores": {"vader": 0.7},
                "emotion_scores": {"joy": 0.8},
                "food_mentions": ["wings"],
                "url": "https://reddit.com/test",
                "is_comment": False
            }
        ]
        mock_get_db.return_value = mock_db
        
        response = self.client.get("/bars/Test%20Bar/mentions")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["bar_name"] == "Test Bar"
        assert data[0]["sentiment_score"] == 0.8

    @patch('src.api.main.get_database_service')
    def test_get_mentions_with_filters(self, mock_get_db):
        """Test get mentions with filtering parameters."""
        mock_db = Mock()
        mock_db.get_mentions.return_value = []
        mock_get_db.return_value = mock_db
        
        response = self.client.get("/mentions?limit=10&sentiment=positive")
        
        assert response.status_code == 200
        mock_db.get_mentions.assert_called_once_with(
            limit=10,
            offset=0,
            start_date=None,
            end_date=None,
            sentiment_filter="positive"
        )

    @patch('src.api.main.get_database_service')
    def test_search_mentions(self, mock_get_db):
        """Test search mentions endpoint."""
        mock_db = Mock()
        mock_db.search_mentions.return_value = ([], 0)
        mock_get_db.return_value = mock_db
        
        search_request = {
            "query": "great food",
            "limit": 20
        }
        
        response = self.client.post("/search", json=search_request)
        
        assert response.status_code == 200
        data = response.json()
        assert data["query"] == "great food"
        assert data["total_results"] == 0

    @patch('src.api.main.get_database_service')
    def test_get_sentiment_trends(self, mock_get_db):
        """Test get sentiment trends endpoint."""
        mock_db = Mock()
        mock_db.get_sentiment_trends.return_value = [
            {
                "date": datetime.now(),
                "bar_name": "Test Bar",
                "mention_count": 10,
                "avg_sentiment": 0.5,
                "avg_confidence": 0.8,
                "positive_count": 6,
                "negative_count": 2,
                "neutral_count": 2
            }
        ]
        mock_get_db.return_value = mock_db
        
        trend_request = {
            "days": 30,
            "granularity": "daily"
        }
        
        response = self.client.post("/analytics/trends", json=trend_request)
        
        assert response.status_code == 200
        data = response.json()
        assert "trends" in data
        assert data["granularity"] == "daily"

    @patch('src.api.main.get_database_service')
    def test_compare_bars(self, mock_get_db):
        """Test compare bars endpoint."""
        mock_db = Mock()
        mock_db.compare_bars.return_value = {
            "comparison_data": {
                "Bar A": {"avg_sentiment": 0.5, "total_mentions": 100},
                "Bar B": {"avg_sentiment": 0.3, "total_mentions": 80}
            },
            "rankings": {
                "avg_sentiment": ["Bar A", "Bar B"],
                "total_mentions": ["Bar A", "Bar B"]
            }
        }
        mock_get_db.return_value = mock_db
        
        comparison_request = {
            "bars": ["Bar A", "Bar B"],
            "metrics": ["avg_sentiment", "total_mentions"],
            "days": 30
        }
        
        response = self.client.post("/analytics/compare", json=comparison_request)
        
        assert response.status_code == 200
        data = response.json()
        assert "comparison_data" in data
        assert "rankings" in data

    @patch('src.api.main.get_database_service')
    def test_get_analytics_summary(self, mock_get_db):
        """Test get analytics summary endpoint."""
        mock_db = Mock()
        mock_db.get_analytics_summary.return_value = {
            "total_mentions": 1000,
            "unique_bars": 50,
            "avg_sentiment_score": 0.4,
            "sentiment_distribution": {
                "positive": 400,
                "negative": 300,
                "neutral": 300
            },
            "top_bars": [
                {"name": "Bar A", "mentions": 100},
                {"name": "Bar B", "mentions": 80}
            ],
            "trending_foods": [
                {"food": "wings", "count": 200},
                {"food": "beer", "count": 150}
            ],
            "data_quality_score": 0.85,
            "analysis_date": datetime.now()
        }
        mock_get_db.return_value = mock_db
        
        response = self.client.get("/analytics/summary")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_mentions"] == 1000
        assert data["unique_bars"] == 50

    @patch('src.api.main.get_database_service')
    def test_get_analytics_summary_not_found(self, mock_get_db):
        """Test get analytics summary when no data available."""
        mock_db = Mock()
        mock_db.get_analytics_summary.return_value = None
        mock_get_db.return_value = mock_db
        
        response = self.client.get("/analytics/summary")
        
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "No analytics data available"

    @patch('src.api.main.get_database_service')
    def test_get_quality_metrics(self, mock_get_db):
        """Test get quality metrics endpoint."""
        mock_db = Mock()
        mock_db.get_quality_metrics.return_value = [
            {
                "processing_date": datetime.now(),
                "total_posts_processed": 100,
                "valid_posts": 90,
                "invalid_posts": 10,
                "spam_filtered": 5,
                "mentions_found": 50,
                "unique_bars_mentioned": 20,
                "average_confidence": 0.8,
                "data_quality_score": 0.85
            }
        ]
        mock_get_db.return_value = mock_db
        
        response = self.client.get("/quality/metrics")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["total_posts_processed"] == 100

    @patch('src.api.main.get_database_service')
    def test_trigger_processing(self, mock_get_db):
        """Test trigger processing endpoint."""
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        
        job_request = {
            "limit": 100,
            "mode": "advanced"
        }
        
        response = self.client.post("/process", json=job_request)
        
        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        assert data["status"] == "queued"

    def test_get_job_status(self):
        """Test get job status endpoint."""
        response = self.client.get("/process/test-job-id")
        
        assert response.status_code == 200
        data = response.json()
        assert data["job_id"] == "test-job-id"
        assert "status" in data

    @patch('src.api.main.get_database_service')
    def test_database_error_handling(self, mock_get_db):
        """Test database error handling."""
        mock_db = Mock()
        mock_db.get_all_bars.side_effect = Exception("Database connection failed")
        mock_get_db.return_value = mock_db
        
        response = self.client.get("/bars")
        
        assert response.status_code == 500
        data = response.json()
        assert data["detail"] == "Internal server error"

    def test_invalid_json_request(self):
        """Test invalid JSON request handling."""
        response = self.client.post("/search", data="invalid json")
        
        assert response.status_code == 422  # Validation error

    def test_missing_required_fields(self):
        """Test missing required fields in request."""
        response = self.client.post("/search", json={})
        
        assert response.status_code == 422  # Validation error

    def test_invalid_sentiment_filter(self):
        """Test invalid sentiment filter."""
        response = self.client.get("/mentions?sentiment=invalid")
        
        assert response.status_code == 422  # Validation error

    def test_cors_headers(self):
        """Test CORS headers are present."""
        response = self.client.get("/")
        
        # Check that CORS middleware is applied
        assert response.status_code == 200


class TestAPIDependencies:
    """Test cases for API dependencies."""

    @patch('src.api.dependencies.DatabaseService')
    def test_get_database_service(self, mock_db_service):
        """Test database service dependency."""
        from src.api.dependencies import get_database_service
        
        mock_instance = Mock()
        mock_db_service.return_value = mock_instance
        
        # Test dependency injection
        db_gen = get_database_service()
        db_service = next(db_gen)
        
        assert db_service == mock_instance
        
        # Test cleanup
        try:
            next(db_gen)
        except StopIteration:
            pass  # Expected behavior
        
        mock_instance.close_connection.assert_called_once()

    @patch('src.api.dependencies.DatabaseService')
    def test_get_global_database_service(self, mock_db_service):
        """Test global database service dependency."""
        from src.api.dependencies import get_global_database_service, close_global_database_service
        
        mock_instance = Mock()
        mock_db_service.return_value = mock_instance
        
        # Test getting global service
        db_service = get_global_database_service()
        assert db_service == mock_instance
        
        # Test getting same instance
        db_service2 = get_global_database_service()
        assert db_service2 == mock_instance
        
        # Test cleanup
        close_global_database_service()
        mock_instance.close_connection.assert_called_once()


class TestAPIModels:
    """Test cases for API models."""

    def test_bar_summary_model(self):
        """Test BarSummary model validation."""
        bar_data = {
            "name": "Test Bar",
            "total_mentions": 100,
            "avg_sentiment": 0.5,
            "avg_confidence": 0.8,
            "positive_mentions": 60,
            "negative_mentions": 20,
            "neutral_mentions": 20,
            "first_mention": datetime.now(),
            "last_mention": datetime.now(),
            "top_emotions": {"joy": 0.7},
            "specialties": ["wings", "beer"]
        }
        
        bar_summary = BarSummary(**bar_data)
        
        assert bar_summary.name == "Test Bar"
        assert bar_summary.total_mentions == 100
        assert bar_summary.avg_sentiment == 0.5
        assert "wings" in bar_summary.specialties

    def test_mention_detail_model(self):
        """Test MentionDetail model validation."""
        mention_data = {
            "id": 1,
            "bar_name": "Test Bar",
            "post_id": "abc123",
            "post_title": "Great experience",
            "post_text": "Had a wonderful time",
            "created_at": datetime.now(),
            "sentiment_score": 0.8,
            "sentiment_confidence": 0.9,
            "sentiment_label": "positive",
            "model_scores": {"vader": 0.7},
            "emotion_scores": {"joy": 0.8},
            "food_mentions": ["wings"],
            "url": "https://reddit.com/test",
            "is_comment": False
        }
        
        mention_detail = MentionDetail(**mention_data)
        
        assert mention_detail.bar_name == "Test Bar"
        assert mention_detail.sentiment_score == 0.8
        assert mention_detail.sentiment_label == "positive"
        assert not mention_detail.is_comment

    def test_analytics_summary_model(self):
        """Test AnalyticsSummary model validation."""
        analytics_data = {
            "total_mentions": 1000,
            "unique_bars": 50,
            "avg_sentiment_score": 0.4,
            "sentiment_distribution": {
                "positive": 400,
                "negative": 300,
                "neutral": 300
            },
            "top_bars": [
                {"name": "Bar A", "mentions": 100}
            ],
            "trending_foods": [
                {"food": "wings", "count": 200}
            ],
            "data_quality_score": 0.85,
            "analysis_date": datetime.now()
        }
        
        analytics_summary = AnalyticsSummary(**analytics_data)
        
        assert analytics_summary.total_mentions == 1000
        assert analytics_summary.unique_bars == 50
        assert analytics_summary.data_quality_score == 0.85

    def test_quality_metrics_model(self):
        """Test QualityMetrics model validation."""
        metrics_data = {
            "processing_date": datetime.now(),
            "total_posts_processed": 100,
            "valid_posts": 90,
            "invalid_posts": 10,
            "spam_filtered": 5,
            "mentions_found": 50,
            "unique_bars_mentioned": 20,
            "average_confidence": 0.8,
            "data_quality_score": 0.85
        }
        
        quality_metrics = QualityMetrics(**metrics_data)
        
        assert quality_metrics.total_posts_processed == 100
        assert quality_metrics.valid_posts == 90
        assert quality_metrics.data_quality_score == 0.85

    def test_health_response_model(self):
        """Test HealthResponse model validation."""
        health_data = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": "2.0.0",
            "database_connected": True,
            "last_data_update": datetime.now().isoformat(),
            "total_mentions": 1000
        }
        
        health_response = HealthResponse(**health_data)
        
        assert health_response.status == "healthy"
        assert health_response.database_connected is True
        assert health_response.total_mentions == 1000


@pytest.mark.integration
class TestAPIIntegration:
    """Integration tests for API endpoints."""

    def setup_method(self):
        """Set up test client."""
        self.client = TestClient(app)

    def test_api_workflow(self):
        """Test complete API workflow."""
        # Test health check
        health_response = self.client.get("/health")
        assert health_response.status_code == 200
        
        # Test root endpoint
        root_response = self.client.get("/")
        assert root_response.status_code == 200
        
        # Test API documentation
        docs_response = self.client.get("/docs")
        assert docs_response.status_code == 200

    def test_error_handling_consistency(self):
        """Test consistent error handling across endpoints."""
        # Test 404 errors
        response = self.client.get("/nonexistent")
        assert response.status_code == 404
        
        # Test validation errors
        response = self.client.post("/search", json={"invalid": "data"})
        assert response.status_code == 422

    def test_response_format_consistency(self):
        """Test consistent response format across endpoints."""
        # All endpoints should return JSON (except root)
        endpoints = [
            "/health",
            "/bars",
            "/quality/metrics"
        ]
        
        for endpoint in endpoints:
            response = self.client.get(endpoint)
            # Should either be successful or have consistent error format
            assert response.status_code in [200, 500]
            if response.status_code == 200:
                assert response.headers["content-type"] == "application/json"