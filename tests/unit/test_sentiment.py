"""Unit tests for sentiment analysis module."""

import pytest
from unittest.mock import Mock, patch

from src.models.sentiment import (
    SentimentAnalyzer,
    HospitalitySentimentAnalyzer,
    SentimentResult
)


class TestSentimentAnalyzer:
    """Test cases for SentimentAnalyzer class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.analyzer = SentimentAnalyzer()

    def test_init(self):
        """Test analyzer initialization."""
        assert self.analyzer.vader is not None
        assert self.analyzer.scaler is not None
        assert self.analyzer._models_loaded is False
        assert self.analyzer._roberta_pipeline is None
        assert self.analyzer._emotion_pipeline is None

    def test_analyze_sentiment_empty_text(self):
        """Test sentiment analysis with empty text."""
        result = self.analyzer.analyze_sentiment("")
        
        assert isinstance(result, SentimentResult)
        assert result.score == 0.0
        assert result.confidence == 0.0
        assert result.sentiment_label == "neutral"
        assert result.model_scores == {}

    def test_analyze_sentiment_none_text(self):
        """Test sentiment analysis with None text."""
        result = self.analyzer.analyze_sentiment(None)
        
        assert isinstance(result, SentimentResult)
        assert result.score == 0.0
        assert result.confidence == 0.0
        assert result.sentiment_label == "neutral"

    @patch('src.models.sentiment.TextBlob')
    def test_get_textblob_sentiment(self, mock_textblob):
        """Test TextBlob sentiment extraction."""
        mock_blob = Mock()
        mock_blob.sentiment.polarity = 0.5
        mock_textblob.return_value = mock_blob
        
        result = self.analyzer._get_textblob_sentiment("Great food!")
        assert result == 0.5

    @patch('src.models.sentiment.TextBlob')
    def test_get_textblob_sentiment_error(self, mock_textblob):
        """Test TextBlob sentiment with error handling."""
        mock_textblob.side_effect = Exception("TextBlob error")
        
        result = self.analyzer._get_textblob_sentiment("Test text")
        assert result == 0.0

    def test_get_vader_sentiment(self):
        """Test VADER sentiment extraction."""
        result = self.analyzer._get_vader_sentiment("This is great!")
        
        assert isinstance(result, dict)
        assert "compound" in result
        assert "positive" in result
        assert "negative" in result
        assert "neutral" in result
        assert -1 <= result["compound"] <= 1

    def test_convert_roberta_to_polarity(self):
        """Test RoBERTa score conversion to polarity."""
        roberta_scores = {
            "positive": 0.8,
            "negative": 0.1,
            "neutral": 0.1
        }
        
        polarity = self.analyzer._convert_roberta_to_polarity(roberta_scores)
        
        assert isinstance(polarity, float)
        assert -1 <= polarity <= 1
        assert polarity > 0  # Should be positive

    def test_ensemble_scoring_single_model(self):
        """Test ensemble scoring with single model."""
        model_scores = {"vader": 0.5}
        
        score, confidence = self.analyzer._ensemble_scoring(model_scores)
        
        assert score == 0.5
        assert confidence == 0.7  # Default confidence for single model

    def test_ensemble_scoring_multiple_models(self):
        """Test ensemble scoring with multiple models."""
        model_scores = {
            "vader": 0.3,
            "textblob": 0.5,
            "roberta": 0.4
        }
        
        score, confidence = self.analyzer._ensemble_scoring(model_scores)
        
        assert isinstance(score, float)
        assert isinstance(confidence, float)
        assert 0 <= confidence <= 1
        assert -1 <= score <= 1

    def test_ensemble_scoring_empty(self):
        """Test ensemble scoring with empty scores."""
        model_scores = {}
        
        score, confidence = self.analyzer._ensemble_scoring(model_scores)
        
        assert score == 0.0
        assert confidence == 0.0

    def test_sentiment_label_classification(self):
        """Test sentiment label classification."""
        # Test positive
        result = self.analyzer.analyze_sentiment("This is absolutely amazing!")
        assert result.sentiment_label in ["positive", "neutral", "negative"]
        
        # Test negative
        result = self.analyzer.analyze_sentiment("This is terrible and awful!")
        assert result.sentiment_label in ["positive", "neutral", "negative"]

    def test_analyze_batch(self):
        """Test batch sentiment analysis."""
        texts = [
            "Great food and service!",
            "Terrible experience",
            "It was okay"
        ]
        
        results = self.analyzer.analyze_batch(texts)
        
        assert len(results) == 3
        assert all(isinstance(r, SentimentResult) for r in results)
        assert all(hasattr(r, 'score') for r in results)
        assert all(hasattr(r, 'confidence') for r in results)


class TestHospitalitySentimentAnalyzer:
    """Test cases for HospitalitySentimentAnalyzer class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.analyzer = HospitalitySentimentAnalyzer()

    def test_init(self):
        """Test hospitality analyzer initialization."""
        assert isinstance(self.analyzer, SentimentAnalyzer)
        assert hasattr(self.analyzer, 'positive_indicators')
        assert hasattr(self.analyzer, 'negative_indicators')
        assert "amazing" in self.analyzer.positive_indicators
        assert "terrible" in self.analyzer.negative_indicators

    def test_apply_domain_adjustment_positive(self):
        """Test domain adjustment for positive indicators."""
        text = "The food was amazing and delicious with great service"
        base_score = 0.3
        
        adjusted_score = self.analyzer._apply_domain_adjustment(text, base_score)
        
        # Should be more positive due to hospitality indicators
        assert adjusted_score >= base_score
        assert -1 <= adjusted_score <= 1

    def test_apply_domain_adjustment_negative(self):
        """Test domain adjustment for negative indicators."""
        text = "The food was terrible and the service was slow and rude"
        base_score = -0.3
        
        adjusted_score = self.analyzer._apply_domain_adjustment(text, base_score)
        
        # Should be more negative due to hospitality indicators
        assert adjusted_score <= base_score
        assert -1 <= adjusted_score <= 1

    def test_apply_domain_adjustment_neutral(self):
        """Test domain adjustment with neutral text."""
        text = "I went to the restaurant yesterday"
        base_score = 0.0
        
        adjusted_score = self.analyzer._apply_domain_adjustment(text, base_score)
        
        # Should remain close to base score
        assert abs(adjusted_score - base_score) < 0.2

    def test_analyze_sentiment_with_domain_adjustment(self):
        """Test sentiment analysis with domain-specific adjustments."""
        # Test with hospitality-specific positive terms
        result = self.analyzer.analyze_sentiment("The atmosphere was cozy and the food was delicious")
        
        assert isinstance(result, SentimentResult)
        assert result.sentiment_label in ["positive", "neutral", "negative"]
        assert -1 <= result.score <= 1
        assert 0 <= result.confidence <= 1

    def test_domain_indicators_coverage(self):
        """Test that domain indicators cover expected hospitality terms."""
        # Test positive indicators
        positive_terms = ["amazing", "delicious", "friendly", "cozy", "fresh"]
        for term in positive_terms:
            assert term in self.analyzer.positive_indicators
        
        # Test negative indicators
        negative_terms = ["terrible", "slow", "rude", "expensive", "cold"]
        for term in negative_terms:
            assert term in self.analyzer.negative_indicators


class TestSentimentResult:
    """Test cases for SentimentResult dataclass."""

    def test_sentiment_result_creation(self):
        """Test SentimentResult creation."""
        result = SentimentResult(
            score=0.5,
            confidence=0.8,
            model_scores={"vader": 0.4, "textblob": 0.6},
            sentiment_label="positive",
            emotion_scores={"joy": 0.7, "anger": 0.1}
        )
        
        assert result.score == 0.5
        assert result.confidence == 0.8
        assert result.sentiment_label == "positive"
        assert result.model_scores == {"vader": 0.4, "textblob": 0.6}
        assert result.emotion_scores == {"joy": 0.7, "anger": 0.1}

    def test_sentiment_result_optional_fields(self):
        """Test SentimentResult with optional fields."""
        result = SentimentResult(
            score=0.0,
            confidence=0.5,
            model_scores={},
            sentiment_label="neutral"
        )
        
        assert result.emotion_scores is None


@pytest.fixture
def mock_pipeline():
    """Mock pipeline for testing."""
    mock_pipe = Mock()
    mock_pipe.return_value = [[
        {"label": "POSITIVE", "score": 0.8},
        {"label": "NEGATIVE", "score": 0.1},
        {"label": "NEUTRAL", "score": 0.1}
    ]]
    return mock_pipe


@pytest.mark.integration
class TestSentimentIntegration:
    """Integration tests for sentiment analysis."""

    def test_full_sentiment_pipeline(self):
        """Test complete sentiment analysis pipeline."""
        analyzer = HospitalitySentimentAnalyzer()
        
        test_cases = [
            ("The food was amazing and the service was excellent!", "positive"),
            ("Terrible food and rude waiters", "negative"),
            ("It was okay", "neutral"),
            ("", "neutral"),
        ]
        
        for text, _ in test_cases:
            result = analyzer.analyze_sentiment(text)
            
            assert isinstance(result, SentimentResult)
            assert result.sentiment_label in ["positive", "negative", "neutral"]
            assert -1 <= result.score <= 1
            assert 0 <= result.confidence <= 1
            assert isinstance(result.model_scores, dict)

    def test_batch_processing_consistency(self):
        """Test batch processing produces consistent results."""
        analyzer = SentimentAnalyzer()
        
        texts = [
            "Great experience at this restaurant!",
            "Food was cold and service was slow",
            "Average meal, nothing special"
        ]
        
        # Process individually
        individual_results = [analyzer.analyze_sentiment(text) for text in texts]
        
        # Process as batch
        batch_results = analyzer.analyze_batch(texts)
        
        # Results should be identical
        assert len(individual_results) == len(batch_results)
        for individual, batch in zip(individual_results, batch_results):
            assert individual.score == batch.score
            assert individual.confidence == batch.confidence
            assert individual.sentiment_label == batch.sentiment_label