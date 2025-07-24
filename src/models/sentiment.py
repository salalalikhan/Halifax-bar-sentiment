
"""Advanced sentiment analysis models and ensemble methods."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np
from sklearn.preprocessing import MinMaxScaler
from textblob import TextBlob
from transformers import pipeline
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

logger = logging.getLogger(__name__)


@dataclass
class SentimentResult:
    """Structured sentiment analysis result."""
    
    score: float  # Normalized score between -1 and 1
    confidence: float  # Confidence score between 0 and 1
    model_scores: Dict[str, float]  # Individual model scores
    sentiment_label: str  # "positive", "negative", "neutral"
    emotion_scores: Optional[Dict[str, float]] = None  # Detailed emotions


class SentimentAnalyzer:
    """Advanced multi-model sentiment analyzer with ensemble methods."""
    
    def __init__(self):
        """Initialize sentiment analyzer with multiple models."""
        self.vader = SentimentIntensityAnalyzer()
        self.scaler = MinMaxScaler(feature_range=(-1, 1))
        self._roberta_pipeline = None
        self._emotion_pipeline = None
        self._models_loaded = False
        
    def _load_models(self) -> None:
        """Lazy load advanced analytics models to avoid startup delays."""
        if self._models_loaded:
            return
            
        try:
            logger.info("Loading advanced analytics models for sentiment analysis...")
            
            # RoBERTa model fine-tuned for sentiment
            self._roberta_pipeline = pipeline(
                "sentiment-analysis",
                model="cardiffnlp/twitter-roberta-base-sentiment-latest",
                return_all_scores=True
            )
            
            # Emotion classification model
            self._emotion_pipeline = pipeline(
                "text-classification",
                model="j-hartmann/emotion-english-distilroberta-base",
                return_all_scores=True
            )
            
            self._models_loaded = True
            logger.info("Advanced analytics models loaded successfully")
            
        except Exception as e:
            logger.warning(f"Failed to load advanced analytics models: {e}")
            logger.info("Falling back to VADER and TextBlob only")
    
    def _get_vader_sentiment(self, text: str) -> Dict[str, float]:
        """Get VADER sentiment scores."""
        scores = self.vader.polarity_scores(text)
        return {
            "compound": scores["compound"],
            "positive": scores["pos"],
            "negative": scores["neg"],
            "neutral": scores["neu"]
        }
    
    def _get_textblob_sentiment(self, text: str) -> float:
        """Get TextBlob sentiment polarity."""
        try:
            blob = TextBlob(text)
            return blob.sentiment.polarity
        except Exception as e:
            logger.warning(f"TextBlob sentiment analysis failed: {e}")
            return 0.0
    
    def _get_roberta_sentiment(self, text: str) -> Optional[Dict[str, float]]:
        """Get RoBERTa sentiment scores."""
        if not self._roberta_pipeline:
            return None
            
        try:
            results = self._roberta_pipeline(text[:512])  # RoBERTa max length
            scores = {}
            for result in results[0]:
                label = result["label"].lower()
                score = result["score"]
                
                # Convert to standardized labels
                if "negative" in label:
                    scores["negative"] = score
                elif "positive" in label:
                    scores["positive"] = score
                else:
                    scores["neutral"] = score
                    
            return scores
            
        except Exception as e:
            logger.warning(f"RoBERTa sentiment analysis failed: {e}")
            return None
    
    def _get_emotion_scores(self, text: str) -> Optional[Dict[str, float]]:
        """Get detailed emotion scores."""
        if not self._emotion_pipeline:
            return None
            
        try:
            results = self._emotion_pipeline(text[:512])
            return {result["label"]: result["score"] for result in results[0]}
            
        except Exception as e:
            logger.warning(f"Emotion analysis failed: {e}")
            return None
    
    def _ensemble_scoring(self, model_scores: Dict[str, float]) -> Tuple[float, float]:
        """
        Combine multiple model scores using weighted ensemble.
        
        Returns:
            Tuple of (final_score, confidence)
        """
        scores = []
        weights = []
        
        # VADER (weight: 0.3) - good for social media text
        if "vader" in model_scores:
            scores.append(model_scores["vader"])
            weights.append(0.3)
        
        # TextBlob (weight: 0.2) - baseline sentiment
        if "textblob" in model_scores:
            scores.append(model_scores["textblob"])
            weights.append(0.2)
        
        # RoBERTa (weight: 0.5) - most sophisticated if available
        if "roberta" in model_scores:
            scores.append(model_scores["roberta"])
            weights.append(0.5)
        
        if not scores:
            return 0.0, 0.0
        
        # Normalize weights
        weights = np.array(weights)
        weights = weights / weights.sum()
        
        # Calculate weighted average
        final_score = np.average(scores, weights=weights)
        
        # Calculate confidence based on agreement between models
        if len(scores) > 1:
            std_dev = np.std(scores)
            max_std = 2.0  # Maximum expected standard deviation
            confidence = max(0.0, 1.0 - (std_dev / max_std))
        else:
            confidence = 0.7  # Default confidence for single model
        
        return float(final_score), float(confidence)
    
    def _convert_roberta_to_polarity(self, roberta_scores: Dict[str, float]) -> float:
        """Convert RoBERTa classification scores to polarity score."""
        positive = roberta_scores.get("positive", 0.0)
        negative = roberta_scores.get("negative", 0.0)
        neutral = roberta_scores.get("neutral", 0.0)
        
        # Convert to polarity: positive - negative, weighted by confidence
        polarity = (positive - negative) * (1 - neutral)
        return np.clip(polarity, -1.0, 1.0)
    
    def analyze_sentiment(self, text: str) -> SentimentResult:
        """
        Perform comprehensive sentiment analysis using ensemble of models.
        
        Args:
            text: Input text to analyze
            
        Returns:
            SentimentResult with comprehensive analysis
        """
        if not text or not text.strip():
            return SentimentResult(
                score=0.0,
                confidence=0.0,
                model_scores={},
                sentiment_label="neutral"
            )
        
        # Load models if not already loaded
        self._load_models()
        
        model_scores = {}
        
        # Get VADER sentiment
        vader_scores = self._get_vader_sentiment(text)
        model_scores["vader"] = vader_scores["compound"]
        
        # Get TextBlob sentiment
        textblob_score = self._get_textblob_sentiment(text)
        model_scores["textblob"] = textblob_score
        
        # Get RoBERTa sentiment if available
        roberta_scores = self._get_roberta_sentiment(text)
        if roberta_scores:
            roberta_polarity = self._convert_roberta_to_polarity(roberta_scores)
            model_scores["roberta"] = roberta_polarity
        
        # Ensemble scoring
        final_score, confidence = self._ensemble_scoring(model_scores)
        
        # Determine sentiment label
        if final_score > 0.1:
            sentiment_label = "positive"
        elif final_score < -0.1:
            sentiment_label = "negative"
        else:
            sentiment_label = "neutral"
        
        # Get emotion scores
        emotion_scores = self._get_emotion_scores(text)
        
        return SentimentResult(
            score=final_score,
            confidence=confidence,
            model_scores=model_scores,
            sentiment_label=sentiment_label,
            emotion_scores=emotion_scores
        )
    
    def analyze_batch(self, texts: List[str]) -> List[SentimentResult]:
        """Analyze sentiment for a batch of texts efficiently."""
        return [self.analyze_sentiment(text) for text in texts]


class HospitalitySentimentAnalyzer(SentimentAnalyzer):
    """Specialized sentiment analyzer for hospitality/restaurant domain."""
    
    def __init__(self):
        """Initialize with hospitality-specific enhancements."""
        super().__init__()
        
        # Domain-specific sentiment modifiers
        self.positive_indicators = {
            "amazing", "excellent", "outstanding", "delicious", "fantastic",
            "love", "perfect", "incredible", "awesome", "best", "great",
            "wonderful", "impressive", "tasty", "fresh", "friendly",
            "attentive", "quick", "fast", "clean", "cozy", "atmosphere"
        }
        
        self.negative_indicators = {
            "terrible", "awful", "horrible", "disgusting", "worst", "hate",
            "slow", "rude", "dirty", "expensive", "overpriced", "cold",
            "burnt", "stale", "soggy", "bland", "salty", "dry", "greasy",
            "waiting", "wait", "delayed", "mistake", "wrong", "poor"
        }
    
    def _apply_domain_adjustment(self, text: str, base_score: float) -> float:
        """Apply hospitality domain-specific sentiment adjustments."""
        text_lower = text.lower()
        
        # Count positive and negative indicators
        positive_count = sum(1 for word in self.positive_indicators if word in text_lower)
        negative_count = sum(1 for word in self.negative_indicators if word in text_lower)
        
        # Calculate adjustment factor
        net_indicators = positive_count - negative_count
        adjustment = net_indicators * 0.1  # 0.1 adjustment per indicator
        
        # Apply adjustment with bounds
        adjusted_score = base_score + adjustment
        return np.clip(adjusted_score, -1.0, 1.0)
    
    def analyze_sentiment(self, text: str) -> SentimentResult:
        """Analyze sentiment with hospitality domain adjustments."""
        result = super().analyze_sentiment(text)
        
        # Apply domain-specific adjustments
        adjusted_score = self._apply_domain_adjustment(text, result.score)
        
        # Update sentiment label if score changed significantly
        if abs(adjusted_score - result.score) > 0.15:
            if adjusted_score > 0.1:
                sentiment_label = "positive"
            elif adjusted_score < -0.1:
                sentiment_label = "negative"
            else:
                sentiment_label = "neutral"
        else:
            sentiment_label = result.sentiment_label
        
        return SentimentResult(
            score=adjusted_score,
            confidence=result.confidence,
            model_scores=result.model_scores,
            sentiment_label=sentiment_label,
            emotion_scores=result.emotion_scores
        )