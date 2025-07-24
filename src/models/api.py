"""API data models for FastAPI endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional, Any

from pydantic import BaseModel, Field


class BarSummary(BaseModel):
    """Bar summary statistics model."""
    
    name: str = Field(..., description="Bar name")
    total_mentions: int = Field(..., description="Total number of mentions")
    avg_sentiment: float = Field(..., description="Average sentiment score (-1 to 1)")
    avg_confidence: float = Field(..., description="Average confidence score (0 to 1)")
    positive_mentions: int = Field(..., description="Number of positive mentions")
    negative_mentions: int = Field(..., description="Number of negative mentions")
    neutral_mentions: int = Field(..., description="Number of neutral mentions")
    first_mention: Optional[datetime] = Field(None, description="First mention timestamp")
    last_mention: Optional[datetime] = Field(None, description="Last mention timestamp")
    top_emotions: Optional[Dict[str, float]] = Field(None, description="Top emotion scores")
    specialties: List[str] = Field(default_factory=list, description="Food/drink specialties")


class MentionDetail(BaseModel):
    """Detailed mention model."""
    
    id: int = Field(..., description="Unique mention ID")
    bar_name: str = Field(..., description="Bar name")
    post_id: str = Field(..., description="Reddit post ID")
    post_title: str = Field(..., description="Post title")
    post_text: str = Field(..., description="Post content")
    created_at: datetime = Field(..., description="Post creation timestamp")
    sentiment_score: float = Field(..., description="Sentiment score (-1 to 1)")
    sentiment_confidence: float = Field(..., description="Confidence score (0 to 1)")
    sentiment_label: str = Field(..., description="Sentiment label")
    model_scores: Dict[str, float] = Field(default_factory=dict, description="Individual model scores")
    emotion_scores: Optional[Dict[str, float]] = Field(None, description="Emotion analysis scores")
    food_mentions: List[str] = Field(default_factory=list, description="Food/drink mentions")
    url: str = Field(..., description="Reddit post URL")
    is_comment: bool = Field(False, description="Whether this is a comment")


class SentimentTrend(BaseModel):
    """Sentiment trend data model."""
    
    date: datetime = Field(..., description="Date")
    bar_name: str = Field(..., description="Bar name")
    mention_count: int = Field(..., description="Number of mentions")
    avg_sentiment: float = Field(..., description="Average sentiment")
    avg_confidence: float = Field(..., description="Average confidence")
    positive_count: int = Field(..., description="Positive mentions")
    negative_count: int = Field(..., description="Negative mentions")
    neutral_count: int = Field(..., description="Neutral mentions")


class AnalyticsSummary(BaseModel):
    """Overall analytics summary model."""
    
    total_mentions: int = Field(..., description="Total mentions across all bars")
    unique_bars: int = Field(..., description="Number of unique bars mentioned")
    avg_sentiment_score: float = Field(..., description="Overall average sentiment")
    sentiment_distribution: Dict[str, int] = Field(..., description="Distribution of sentiment labels")
    top_bars: List[Dict[str, Any]] = Field(..., description="Top mentioned bars")
    trending_foods: List[Dict[str, Any]] = Field(..., description="Trending food/drink items")
    data_quality_score: Optional[float] = Field(None, description="Data quality score")
    analysis_date: datetime = Field(..., description="Analysis timestamp")


class QualityMetrics(BaseModel):
    """Data quality metrics model."""
    
    processing_date: datetime = Field(..., description="Processing timestamp")
    total_posts_processed: int = Field(..., description="Total posts processed")
    valid_posts: int = Field(..., description="Valid posts")
    invalid_posts: int = Field(..., description="Invalid posts")
    spam_filtered: int = Field(..., description="Spam posts filtered")
    mentions_found: int = Field(..., description="Total mentions found")
    unique_bars_mentioned: int = Field(..., description="Unique bars mentioned")
    average_confidence: float = Field(..., description="Average processing confidence")
    data_quality_score: float = Field(..., description="Overall data quality score")


class SearchRequest(BaseModel):
    """Search request model."""
    
    query: str = Field(..., min_length=1, max_length=200, description="Search query")
    bars: Optional[List[str]] = Field(None, description="Filter by specific bars")
    sentiment: Optional[str] = Field(None, regex="^(positive|negative|neutral)$", description="Filter by sentiment")
    start_date: Optional[datetime] = Field(None, description="Start date filter")
    end_date: Optional[datetime] = Field(None, description="End date filter")
    limit: int = Field(default=50, ge=1, le=500, description="Maximum results to return")


class SearchResponse(BaseModel):
    """Search response model."""
    
    query: str = Field(..., description="Original search query")
    total_results: int = Field(..., description="Total number of results")
    results: List[MentionDetail] = Field(..., description="Search results")
    filters_applied: Dict[str, Any] = Field(..., description="Applied filters")


class TrendRequest(BaseModel):
    """Trend analysis request model."""
    
    bars: Optional[List[str]] = Field(None, description="Specific bars to analyze")
    days: int = Field(default=30, ge=1, le=365, description="Number of days to analyze")
    granularity: str = Field(default="daily", regex="^(daily|weekly|monthly)$", description="Data granularity")


class TrendResponse(BaseModel):
    """Trend analysis response model."""
    
    period_start: datetime = Field(..., description="Analysis period start")
    period_end: datetime = Field(..., description="Analysis period end")
    granularity: str = Field(..., description="Data granularity")
    trends: List[SentimentTrend] = Field(..., description="Trend data")
    summary_stats: Dict[str, Any] = Field(..., description="Summary statistics")


class ComparisonRequest(BaseModel):
    """Bar comparison request model."""
    
    bars: List[str] = Field(..., min_items=2, max_items=10, description="Bars to compare")
    metrics: List[str] = Field(
        default=["sentiment", "mentions", "confidence"],
        description="Metrics to compare"
    )
    days: int = Field(default=30, ge=1, le=365, description="Analysis period in days")


class ComparisonResponse(BaseModel):
    """Bar comparison response model."""
    
    bars: List[str] = Field(..., description="Bars being compared")
    metrics: List[str] = Field(..., description="Metrics compared")
    analysis_period: int = Field(..., description="Analysis period in days")
    comparison_data: Dict[str, Dict[str, Any]] = Field(..., description="Comparison results")
    rankings: Dict[str, List[str]] = Field(..., description="Rankings by metric")


class ErrorResponse(BaseModel):
    """Error response model."""
    
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.now, description="Error timestamp")


class HealthResponse(BaseModel):
    """Health check response model."""
    
    status: str = Field(..., description="Service status")
    timestamp: datetime = Field(default_factory=datetime.now, description="Check timestamp")
    version: str = Field(default="2.0.0", description="API version")
    database_connected: bool = Field(..., description="Database connection status")
    last_data_update: Optional[datetime] = Field(None, description="Last data update timestamp")
    total_mentions: int = Field(default=0, description="Total mentions in database")


class ProcessingJobRequest(BaseModel):
    """Background processing job request model."""
    
    limit: int = Field(default=1000, ge=1, le=5000, description="Number of posts to process")
    mode: str = Field(default="advanced", regex="^(basic|advanced)$", description="Processing mode")
    priority: str = Field(default="normal", regex="^(low|normal|high)$", description="Job priority")


class ProcessingJobResponse(BaseModel):
    """Background processing job response model."""
    
    job_id: str = Field(..., description="Unique job identifier")
    status: str = Field(..., description="Job status")
    created_at: datetime = Field(default_factory=datetime.now, description="Job creation time")
    estimated_completion: Optional[datetime] = Field(None, description="Estimated completion time")
    progress: int = Field(default=0, ge=0, le=100, description="Job progress percentage")


class JobStatusResponse(BaseModel):
    """Job status response model."""
    
    job_id: str = Field(..., description="Job identifier")
    status: str = Field(..., description="Current status")
    progress: int = Field(..., description="Progress percentage")
    created_at: datetime = Field(..., description="Job creation time")
    started_at: Optional[datetime] = Field(None, description="Job start time")
    completed_at: Optional[datetime] = Field(None, description="Job completion time")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    result_summary: Optional[Dict[str, Any]] = Field(None, description="Job result summary")