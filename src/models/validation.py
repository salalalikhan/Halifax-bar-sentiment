"""Data validation models and schemas using Pydantic."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple

from pydantic import BaseModel, Field, validator


class RedditPost(BaseModel):
    """Validated Reddit post data model."""
    
    id: str = Field(..., min_length=1, max_length=10)
    title: str = Field(..., min_length=1, max_length=500)
    selftext: str = Field(default="", max_length=40000)
    created_utc: float = Field(..., gt=0)
    score: int = Field(default=0)
    url: str = Field(..., min_length=1)
    comments: List[RedditComment] = Field(default_factory=list)
    
    @validator('id')
    def validate_id(cls, v):
        """Validate Reddit post ID format."""
        if not re.match(r'^[a-z0-9]+$', v):
            raise ValueError('Invalid Reddit post ID format')
        return v
    
    @validator('url')
    def validate_url(cls, v):
        """Validate URL format."""
        if not v.startswith(('http://', 'https://')):
            raise ValueError('URL must start with http:// or https://')
        return v
    
    @validator('created_utc')
    def validate_timestamp(cls, v):
        """Validate timestamp is reasonable."""
        # Reddit launched in 2005
        reddit_launch = datetime(2005, 6, 23).timestamp()
        current_time = datetime.now().timestamp()
        
        if v < reddit_launch or v > current_time:
            raise ValueError('Timestamp outside reasonable range')
        return v


class RedditComment(BaseModel):
    """Validated Reddit comment data model."""
    
    id: str = Field(..., min_length=1, max_length=10)
    body: str = Field(..., min_length=1, max_length=10000)
    created_utc: float = Field(..., gt=0)
    score: int = Field(default=0)
    
    @validator('id')
    def validate_id(cls, v):
        """Validate Reddit comment ID format."""
        if not re.match(r'^[a-z0-9]+$', v):
            raise ValueError('Invalid Reddit comment ID format')
        return v
    
    @validator('body')
    def validate_body(cls, v):
        """Validate comment body content."""
        # Filter out deleted/removed comments
        if v.lower().strip() in ['[deleted]', '[removed]', '']:
            raise ValueError('Comment content is deleted or removed')
        return v


class BarMention(BaseModel):
    """Validated bar mention data model."""
    
    bar_name: str = Field(..., min_length=1, max_length=255)
    post_id: str = Field(..., min_length=1, max_length=10)
    post_title: str = Field(..., min_length=1, max_length=500)
    post_text: str = Field(default="", max_length=40000)
    created_at: datetime = Field(...)
    sentiment_score: float = Field(..., ge=-1.0, le=1.0)
    sentiment_confidence: float = Field(..., ge=0.0, le=1.0)
    sentiment_label: str = Field(..., regex=r'^(positive|negative|neutral)$')
    food_mentions: List[str] = Field(default_factory=list)
    url: str = Field(..., min_length=1)
    model_scores: Dict[str, float] = Field(default_factory=dict)
    emotion_scores: Optional[Dict[str, float]] = None
    
    @validator('bar_name')
    def validate_bar_name(cls, v):
        """Validate bar name format."""
        # Remove extra whitespace and validate length
        v = ' '.join(v.split())
        if len(v) < 2:
            raise ValueError('Bar name too short')
        return v
    
    @validator('food_mentions')
    def validate_food_mentions(cls, v):
        """Validate food mentions list."""
        # Remove duplicates and empty strings
        return list(set(mention.strip().lower() for mention in v if mention.strip()))
    
    @validator('model_scores')
    def validate_model_scores(cls, v):
        """Validate model scores dictionary."""
        valid_models = {'vader', 'textblob', 'roberta'}
        
        for model_name, score in v.items():
            if model_name not in valid_models:
                raise ValueError(f'Unknown model: {model_name}')
            if not isinstance(score, (int, float)) or score < -1 or score > 1:
                raise ValueError(f'Invalid score for {model_name}: {score}')
        
        return v


class DataQualityMetrics(BaseModel):
    """Data quality metrics for monitoring."""
    
    total_posts_processed: int = Field(..., ge=0)
    valid_posts: int = Field(..., ge=0)
    invalid_posts: int = Field(..., ge=0)
    total_mentions_found: int = Field(..., ge=0)
    unique_bars_mentioned: int = Field(..., ge=0)
    duplicate_posts_filtered: int = Field(..., ge=0)
    spam_posts_filtered: int = Field(..., ge=0)
    average_sentiment_confidence: float = Field(..., ge=0.0, le=1.0)
    processing_timestamp: datetime = Field(default_factory=datetime.now)
    
    @validator('valid_posts', 'invalid_posts')
    def validate_post_counts(cls, v, values):
        """Validate that post counts make sense."""
        if 'total_posts_processed' in values:
            total = values['total_posts_processed']
            if v > total:
                raise ValueError('Count cannot exceed total posts processed')
        return v
    
    @property
    def data_quality_score(self) -> float:
        """Calculate overall data quality score."""
        if self.total_posts_processed == 0:
            return 0.0
        
        validity_ratio = self.valid_posts / self.total_posts_processed
        confidence_score = self.average_sentiment_confidence
        
        # Weighted score: 70% validity, 30% confidence
        return (validity_ratio * 0.7) + (confidence_score * 0.3)


class ContentFilter(BaseModel):
    """Content filtering and spam detection model."""
    
    min_text_length: int = Field(default=10, ge=1)
    max_text_length: int = Field(default=10000, ge=100)
    spam_keywords: Set[str] = Field(default_factory=lambda: {
        'spam', 'bot', 'advertisement', 'promo code', 'discount code',
        'click here', 'visit our', 'buy now', 'limited time'
    })
    required_relevance_score: float = Field(default=0.1, ge=0.0, le=1.0)
    
    def is_spam(self, text: str) -> bool:
        """Detect if text is likely spam."""
        text_lower = text.lower()
        
        # Check for spam keywords
        spam_count = sum(1 for keyword in self.spam_keywords if keyword in text_lower)
        
        # Spam if multiple spam keywords or excessive capitalization
        if spam_count >= 2:
            return True
        
        # Check for excessive capitalization (more than 50% uppercase)
        if len(text) > 10:
            uppercase_ratio = sum(1 for c in text if c.isupper()) / len(text)
            if uppercase_ratio > 0.5:
                return True
        
        return False
    
    def is_valid_length(self, text: str) -> bool:
        """Check if text length is within acceptable range."""
        return self.min_text_length <= len(text) <= self.max_text_length
    
    def calculate_relevance(self, text: str, bar_names: Set[str]) -> float:
        """Calculate how relevant text is to bar/restaurant discussion."""
        text_lower = text.lower()
        
        # Keywords indicating restaurant/bar relevance
        restaurant_keywords = {
            'restaurant', 'bar', 'pub', 'brewery', 'cafe', 'food', 'drink',
            'beer', 'wine', 'cocktail', 'menu', 'service', 'server', 'waiter',
            'dinner', 'lunch', 'brunch', 'eat', 'ate', 'meal', 'taste', 'flavor',
            'atmosphere', 'ambiance', 'patio', 'reservation', 'kitchen'
        }
        
        # Count relevant keywords
        keyword_matches = sum(1 for keyword in restaurant_keywords if keyword in text_lower)
        
        # Count bar name mentions
        bar_matches = sum(1 for bar in bar_names if bar.lower() in text_lower)
        
        # Calculate relevance score
        total_words = len(text_lower.split())
        if total_words == 0:
            return 0.0
        
        relevance = (keyword_matches + bar_matches * 2) / total_words
        return min(relevance, 1.0)  # Cap at 1.0


class ValidationError(Exception):
    """Custom exception for validation errors."""
    
    def __init__(self, message: str, field: str = None, value=None):
        self.message = message
        self.field = field
        self.value = value
        super().__init__(self.message)


class DataValidator:
    """Main data validation class."""
    
    def __init__(self, content_filter: ContentFilter = None):
        self.content_filter = content_filter or ContentFilter()
        self.metrics = DataQualityMetrics(
            total_posts_processed=0,
            valid_posts=0,
            invalid_posts=0,
            total_mentions_found=0,
            unique_bars_mentioned=0,
            duplicate_posts_filtered=0,
            spam_posts_filtered=0,
            average_sentiment_confidence=0.0
        )
    
    def validate_reddit_post(self, post_data: dict) -> RedditPost:
        """Validate and return a Reddit post."""
        try:
            return RedditPost(**post_data)
        except Exception as e:
            raise ValidationError(f"Invalid Reddit post: {str(e)}")
    
    def validate_bar_mention(self, mention_data: dict) -> BarMention:
        """Validate and return a bar mention."""
        try:
            return BarMention(**mention_data)
        except Exception as e:
            raise ValidationError(f"Invalid bar mention: {str(e)}")
    
    def filter_content(self, text: str, bar_names: Set[str]) -> Tuple[bool, str]:
        """
        Filter content for quality and relevance.
        
        Returns:
            Tuple of (is_valid, reason_if_invalid)
        """
        if not self.content_filter.is_valid_length(text):
            return False, "Text length outside acceptable range"
        
        if self.content_filter.is_spam(text):
            return False, "Detected as spam content"
        
        relevance = self.content_filter.calculate_relevance(text, bar_names)
        if relevance < self.content_filter.required_relevance_score:
            return False, f"Low relevance score: {relevance:.2f}"
        
        return True, ""
    
    def update_metrics(self, **kwargs):
        """Update data quality metrics."""
        for key, value in kwargs.items():
            if hasattr(self.metrics, key):
                setattr(self.metrics, key, value)
    
    def get_quality_report(self) -> dict:
        """Generate data quality report."""
        return {
            "total_processed": self.metrics.total_posts_processed,
            "valid_posts": self.metrics.valid_posts,
            "invalid_posts": self.metrics.invalid_posts,
            "data_quality_score": self.metrics.data_quality_score,
            "average_confidence": self.metrics.average_sentiment_confidence,
            "unique_bars": self.metrics.unique_bars_mentioned,
            "spam_filtered": self.metrics.spam_posts_filtered,
            "timestamp": self.metrics.processing_timestamp
        }