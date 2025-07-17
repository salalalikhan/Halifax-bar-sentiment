"""Database service layer for API operations."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple

import psycopg2
from psycopg2.extras import RealDictCursor

from src.core.config import settings
from src.models.api import (
    BarSummary, MentionDetail, SentimentTrend, AnalyticsSummary,
    QualityMetrics, SearchRequest, TrendRequest, ComparisonRequest
)

logger = logging.getLogger(__name__)


class DatabaseService:
    """Database service for API operations."""
    
    def __init__(self):
        self._connection = None
    
    def get_connection(self):
        """Get database connection with error handling."""
        if self._connection is None or self._connection.closed:
            try:
                self._connection = psycopg2.connect(
                    dbname=settings.postgres_dbname,
                    user=settings.postgres_user,
                    password=settings.postgres_password,
                    host=settings.postgres_host,
                    port=settings.postgres_port,
                    cursor_factory=RealDictCursor
                )
                logger.debug("Database connection established")
            except Exception as e:
                logger.error(f"Failed to connect to database: {e}")
                raise
        
        return self._connection
    
    def close_connection(self):
        """Close database connection."""
        if self._connection and not self._connection.closed:
            self._connection.close()
            logger.debug("Database connection closed")
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get database health status."""
        try:
            conn = self.get_connection()
            with conn.cursor() as cur:
                # Test database connection
                cur.execute("SELECT 1")
                
                # Get last data update
                cur.execute("""
                    SELECT MAX(created_at_db) as last_update,
                           COUNT(*) as total_mentions
                    FROM mentions
                """)
                result = cur.fetchone()
                
                return {
                    "database_connected": True,
                    "last_data_update": result["last_update"],
                    "total_mentions": result["total_mentions"]
                }
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                "database_connected": False,
                "last_data_update": None,
                "total_mentions": 0
            }
    
    def get_all_bars(self, limit: Optional[int] = None) -> List[BarSummary]:
        """Get all bars with summary statistics."""
        conn = self.get_connection()
        
        try:
            with conn.cursor() as cur:
                query = """
                    SELECT 
                        name, total_mentions, avg_sentiment, avg_confidence,
                        positive_mentions, negative_mentions, neutral_mentions,
                        first_mention, last_mention, top_emotions, specialties
                    FROM bars 
                    WHERE total_mentions > 0
                    ORDER BY total_mentions DESC
                """
                
                if limit:
                    query += f" LIMIT {limit}"
                
                cur.execute(query)
                results = cur.fetchall()
                
                return [
                    BarSummary(
                        name=row["name"],
                        total_mentions=row["total_mentions"] or 0,
                        avg_sentiment=row["avg_sentiment"] or 0.0,
                        avg_confidence=row["avg_confidence"] or 0.0,
                        positive_mentions=row["positive_mentions"] or 0,
                        negative_mentions=row["negative_mentions"] or 0,
                        neutral_mentions=row["neutral_mentions"] or 0,
                        first_mention=row["first_mention"],
                        last_mention=row["last_mention"],
                        top_emotions=row["top_emotions"] or {},
                        specialties=row["specialties"] or []
                    )
                    for row in results
                ]
        
        except Exception as e:
            logger.error(f"Error fetching bars: {e}")
            raise
    
    def get_bar_by_name(self, bar_name: str) -> Optional[BarSummary]:
        """Get specific bar by name."""
        conn = self.get_connection()
        
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT 
                        name, total_mentions, avg_sentiment, avg_confidence,
                        positive_mentions, negative_mentions, neutral_mentions,
                        first_mention, last_mention, top_emotions, specialties
                    FROM bars 
                    WHERE name = %s
                """, (bar_name,))
                
                row = cur.fetchone()
                if not row:
                    return None
                
                return BarSummary(
                    name=row["name"],
                    total_mentions=row["total_mentions"] or 0,
                    avg_sentiment=row["avg_sentiment"] or 0.0,
                    avg_confidence=row["avg_confidence"] or 0.0,
                    positive_mentions=row["positive_mentions"] or 0,
                    negative_mentions=row["negative_mentions"] or 0,
                    neutral_mentions=row["neutral_mentions"] or 0,
                    first_mention=row["first_mention"],
                    last_mention=row["last_mention"],
                    top_emotions=row["top_emotions"] or {},
                    specialties=row["specialties"] or []
                )
        
        except Exception as e:
            logger.error(f"Error fetching bar {bar_name}: {e}")
            raise
    
    def get_mentions(
        self, 
        bar_name: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        sentiment_filter: Optional[str] = None
    ) -> List[MentionDetail]:
        """Get mentions with optional filtering."""
        conn = self.get_connection()
        
        try:
            with conn.cursor() as cur:
                # Build dynamic query
                conditions = []
                params = []
                
                if bar_name:
                    conditions.append("bar_name = %s")
                    params.append(bar_name)
                
                if start_date:
                    conditions.append("created_at >= %s")
                    params.append(start_date)
                
                if end_date:
                    conditions.append("created_at <= %s")
                    params.append(end_date)
                
                if sentiment_filter:
                    conditions.append("sentiment_label = %s")
                    params.append(sentiment_filter)
                
                where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
                
                query = f"""
                    SELECT 
                        id, bar_name, post_id, post_title, post_text, created_at,
                        sentiment_score, sentiment_confidence, sentiment_label,
                        model_scores, emotion_scores, food_mentions, url, is_comment
                    FROM mentions
                    {where_clause}
                    ORDER BY created_at DESC
                    LIMIT %s OFFSET %s
                """
                
                params.extend([limit, offset])
                cur.execute(query, params)
                results = cur.fetchall()
                
                return [
                    MentionDetail(
                        id=row["id"],
                        bar_name=row["bar_name"],
                        post_id=row["post_id"],
                        post_title=row["post_title"],
                        post_text=row["post_text"] or "",
                        created_at=row["created_at"],
                        sentiment_score=row["sentiment_score"],
                        sentiment_confidence=row["sentiment_confidence"] or 0.0,
                        sentiment_label=row["sentiment_label"],
                        model_scores=row["model_scores"] or {},
                        emotion_scores=row["emotion_scores"],
                        food_mentions=row["food_mentions"] or [],
                        url=row["url"],
                        is_comment=row["is_comment"] or False
                    )
                    for row in results
                ]
        
        except Exception as e:
            logger.error(f"Error fetching mentions: {e}")
            raise
    
    def search_mentions(self, search_request: SearchRequest) -> Tuple[List[MentionDetail], int]:
        """Search mentions with full-text search."""
        conn = self.get_connection()
        
        try:
            with conn.cursor() as cur:
                # Build search conditions
                conditions = []
                params = []
                
                # Text search
                conditions.append("(post_title ILIKE %s OR post_text ILIKE %s)")
                search_term = f"%{search_request.query}%"
                params.extend([search_term, search_term])
                
                # Bar filter
                if search_request.bars:
                    conditions.append("bar_name = ANY(%s)")
                    params.append(search_request.bars)
                
                # Sentiment filter
                if search_request.sentiment:
                    conditions.append("sentiment_label = %s")
                    params.append(search_request.sentiment)
                
                # Date filters
                if search_request.start_date:
                    conditions.append("created_at >= %s")
                    params.append(search_request.start_date)
                
                if search_request.end_date:
                    conditions.append("created_at <= %s")
                    params.append(search_request.end_date)
                
                where_clause = " WHERE " + " AND ".join(conditions)
                
                # Get total count
                count_query = f"SELECT COUNT(*) FROM mentions {where_clause}"
                cur.execute(count_query, params)
                total_count = cur.fetchone()["count"]
                
                # Get results
                query = f"""
                    SELECT 
                        id, bar_name, post_id, post_title, post_text, created_at,
                        sentiment_score, sentiment_confidence, sentiment_label,
                        model_scores, emotion_scores, food_mentions, url, is_comment
                    FROM mentions
                    {where_clause}
                    ORDER BY created_at DESC
                    LIMIT %s
                """
                
                params.append(search_request.limit)
                cur.execute(query, params)
                results = cur.fetchall()
                
                mentions = [
                    MentionDetail(
                        id=row["id"],
                        bar_name=row["bar_name"],
                        post_id=row["post_id"],
                        post_title=row["post_title"],
                        post_text=row["post_text"] or "",
                        created_at=row["created_at"],
                        sentiment_score=row["sentiment_score"],
                        sentiment_confidence=row["sentiment_confidence"] or 0.0,
                        sentiment_label=row["sentiment_label"],
                        model_scores=row["model_scores"] or {},
                        emotion_scores=row["emotion_scores"],
                        food_mentions=row["food_mentions"] or [],
                        url=row["url"],
                        is_comment=row["is_comment"] or False
                    )
                    for row in results
                ]
                
                return mentions, total_count
        
        except Exception as e:
            logger.error(f"Error searching mentions: {e}")
            raise
    
    def get_sentiment_trends(self, trend_request: TrendRequest) -> List[SentimentTrend]:
        """Get sentiment trends over time."""
        conn = self.get_connection()
        
        try:
            with conn.cursor() as cur:
                # Calculate date range
                end_date = datetime.now()
                start_date = end_date - timedelta(days=trend_request.days)
                
                # Build query based on granularity
                if trend_request.granularity == "daily":
                    date_trunc = "day"
                elif trend_request.granularity == "weekly":
                    date_trunc = "week"
                else:  # monthly
                    date_trunc = "month"
                
                conditions = []
                params = []
                
                # Date range
                conditions.append("created_at >= %s AND created_at <= %s")
                params.extend([start_date, end_date])
                
                # Bar filter
                if trend_request.bars:
                    conditions.append("bar_name = ANY(%s)")
                    params.append(trend_request.bars)
                
                where_clause = " WHERE " + " AND ".join(conditions)
                
                query = f"""
                    SELECT 
                        DATE_TRUNC('{date_trunc}', created_at) as date,
                        bar_name,
                        COUNT(*) as mention_count,
                        AVG(sentiment_score) as avg_sentiment,
                        AVG(sentiment_confidence) as avg_confidence,
                        SUM(CASE WHEN sentiment_label = 'positive' THEN 1 ELSE 0 END) as positive_count,
                        SUM(CASE WHEN sentiment_label = 'negative' THEN 1 ELSE 0 END) as negative_count,
                        SUM(CASE WHEN sentiment_label = 'neutral' THEN 1 ELSE 0 END) as neutral_count
                    FROM mentions
                    {where_clause}
                    GROUP BY DATE_TRUNC('{date_trunc}', created_at), bar_name
                    ORDER BY date DESC, mention_count DESC
                """
                
                cur.execute(query, params)
                results = cur.fetchall()
                
                return [
                    SentimentTrend(
                        date=row["date"],
                        bar_name=row["bar_name"],
                        mention_count=row["mention_count"],
                        avg_sentiment=float(row["avg_sentiment"]),
                        avg_confidence=float(row["avg_confidence"] or 0.0),
                        positive_count=row["positive_count"],
                        negative_count=row["negative_count"],
                        neutral_count=row["neutral_count"]
                    )
                    for row in results
                ]
        
        except Exception as e:
            logger.error(f"Error fetching sentiment trends: {e}")
            raise
    
    def get_analytics_summary(self) -> Optional[AnalyticsSummary]:
        """Get latest analytics summary."""
        conn = self.get_connection()
        
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT 
                        total_mentions, unique_bars, avg_sentiment_score,
                        sentiment_distribution, top_bars, trending_foods,
                        data_quality_score, analysis_date
                    FROM mention_analytics
                    ORDER BY analysis_date DESC
                    LIMIT 1
                """)
                
                row = cur.fetchone()
                if not row:
                    return None
                
                return AnalyticsSummary(
                    total_mentions=row["total_mentions"],
                    unique_bars=row["unique_bars"],
                    avg_sentiment_score=row["avg_sentiment_score"],
                    sentiment_distribution=row["sentiment_distribution"] or {},
                    top_bars=row["top_bars"] or [],
                    trending_foods=row["trending_foods"] or [],
                    data_quality_score=row["data_quality_score"],
                    analysis_date=row["analysis_date"]
                )
        
        except Exception as e:
            logger.error(f"Error fetching analytics summary: {e}")
            raise
    
    def get_quality_metrics(self, limit: int = 10) -> List[QualityMetrics]:
        """Get recent quality metrics."""
        conn = self.get_connection()
        
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT 
                        processing_date, total_posts_processed, valid_posts, invalid_posts,
                        spam_filtered, mentions_found, unique_bars_mentioned,
                        average_confidence, data_quality_score
                    FROM data_quality_metrics
                    ORDER BY processing_date DESC
                    LIMIT %s
                """, (limit,))
                
                results = cur.fetchall()
                
                return [
                    QualityMetrics(
                        processing_date=row["processing_date"],
                        total_posts_processed=row["total_posts_processed"],
                        valid_posts=row["valid_posts"],
                        invalid_posts=row["invalid_posts"],
                        spam_filtered=row["spam_filtered"],
                        mentions_found=row["mentions_found"],
                        unique_bars_mentioned=row["unique_bars_mentioned"],
                        average_confidence=row["average_confidence"],
                        data_quality_score=row["data_quality_score"]
                    )
                    for row in results
                ]
        
        except Exception as e:
            logger.error(f"Error fetching quality metrics: {e}")
            raise
    
    def compare_bars(self, comparison_request: ComparisonRequest) -> Dict[str, Any]:
        """Compare multiple bars across different metrics."""
        conn = self.get_connection()
        
        try:
            with conn.cursor() as cur:
                # Calculate date range
                end_date = datetime.now()
                start_date = end_date - timedelta(days=comparison_request.days)
                
                # Get comparison data
                cur.execute("""
                    SELECT 
                        bar_name,
                        COUNT(*) as mentions,
                        AVG(sentiment_score) as avg_sentiment,
                        AVG(sentiment_confidence) as avg_confidence,
                        SUM(CASE WHEN sentiment_label = 'positive' THEN 1 ELSE 0 END) as positive_count,
                        SUM(CASE WHEN sentiment_label = 'negative' THEN 1 ELSE 0 END) as negative_count,
                        SUM(CASE WHEN sentiment_label = 'neutral' THEN 1 ELSE 0 END) as neutral_count
                    FROM mentions
                    WHERE bar_name = ANY(%s) 
                    AND created_at >= %s AND created_at <= %s
                    GROUP BY bar_name
                """, (comparison_request.bars, start_date, end_date))
                
                results = cur.fetchall()
                
                # Format comparison data
                comparison_data = {}
                for row in results:
                    bar_name = row["bar_name"]
                    comparison_data[bar_name] = {
                        "mentions": row["mentions"],
                        "sentiment": float(row["avg_sentiment"]),
                        "confidence": float(row["avg_confidence"] or 0.0),
                        "positive_count": row["positive_count"],
                        "negative_count": row["negative_count"],
                        "neutral_count": row["neutral_count"]
                    }
                
                # Calculate rankings
                rankings = {}
                for metric in comparison_request.metrics:
                    if metric in ["mentions", "positive_count", "negative_count", "neutral_count"]:
                        # Higher is better
                        rankings[metric] = sorted(
                            comparison_data.keys(),
                            key=lambda x: comparison_data[x].get(metric, 0),
                            reverse=True
                        )
                    elif metric in ["sentiment", "confidence"]:
                        # Higher is better
                        rankings[metric] = sorted(
                            comparison_data.keys(),
                            key=lambda x: comparison_data[x].get(metric, 0.0),
                            reverse=True
                        )
                
                return {
                    "comparison_data": comparison_data,
                    "rankings": rankings
                }
        
        except Exception as e:
            logger.error(f"Error comparing bars: {e}")
            raise