"""Enhanced data loading layer with advanced schema and analytics."""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

import psycopg2
from psycopg2.extras import execute_values, Json

from src.core.config import settings

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Enhanced database management with connection pooling and advanced schema."""
    
    def __init__(self):
        self._connection = None
    
    def get_connection(self):
        """Get database connection with error handling."""
        if self._connection is None or self._connection.closed:
            try:
                self._connection = psycopg2.connect(
                    dbname=settings.db_database,
                    user=settings.db_user,
                    password=settings.db_password,
                    host=settings.db_host,
                    port=settings.db_port,
                    # Connection options for better performance
                    options="-c statement_timeout=30000"  # 30 second timeout
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


class EnhancedLoader:
    """Enhanced data loader with advanced schema and analytics."""
    
    def __init__(self):
        self.db_manager = DatabaseManager()
    
    def create_enhanced_schema(self) -> None:
        """Create enhanced database schema with additional analytics tables."""
        conn = self.db_manager.get_connection()
        
        try:
            with conn.cursor() as cur:
                # Drop existing tables for clean schema
                cur.execute("DROP TABLE IF EXISTS mention_analytics CASCADE")
                cur.execute("DROP TABLE IF EXISTS daily_sentiment CASCADE")
                cur.execute("DROP TABLE IF EXISTS mentions CASCADE")
                cur.execute("DROP TABLE IF EXISTS bars CASCADE")
                cur.execute("DROP TABLE IF EXISTS data_quality_metrics CASCADE")
                
                # Create bars table with enhanced metadata
                cur.execute("""
                    CREATE TABLE bars (
                        name VARCHAR(255) PRIMARY KEY,
                        total_mentions INTEGER DEFAULT 0,
                        avg_sentiment FLOAT DEFAULT 0,
                        avg_confidence FLOAT DEFAULT 0,
                        positive_mentions INTEGER DEFAULT 0,
                        negative_mentions INTEGER DEFAULT 0,
                        neutral_mentions INTEGER DEFAULT 0,
                        first_mention TIMESTAMP,
                        last_mention TIMESTAMP,
                        top_emotions JSONB,
                        specialties TEXT[],
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create enhanced mentions table
                cur.execute("""
                    CREATE TABLE mentions (
                        id SERIAL PRIMARY KEY,
                        bar_name VARCHAR(255) REFERENCES bars(name),
                        post_id VARCHAR(255) NOT NULL,
                        post_title TEXT NOT NULL,
                        post_text TEXT,
                        created_at TIMESTAMP NOT NULL,
                        sentiment_score FLOAT NOT NULL CHECK (sentiment_score >= -1 AND sentiment_score <= 1),
                        sentiment_confidence FLOAT CHECK (sentiment_confidence >= 0 AND sentiment_confidence <= 1),
                        sentiment_label VARCHAR(20) CHECK (sentiment_label IN ('positive', 'negative', 'neutral')),
                        model_scores JSONB,
                        emotion_scores JSONB,
                        food_mentions TEXT[],
                        url TEXT,
                        is_comment BOOLEAN DEFAULT FALSE,
                        created_at_db TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(post_id, bar_name)
                    )
                """)
                
                # Create daily sentiment aggregation table
                cur.execute("""
                    CREATE TABLE daily_sentiment (
                        date DATE,
                        bar_name VARCHAR(255) REFERENCES bars(name),
                        mention_count INTEGER DEFAULT 0,
                        avg_sentiment FLOAT DEFAULT 0,
                        avg_confidence FLOAT DEFAULT 0,
                        positive_count INTEGER DEFAULT 0,
                        negative_count INTEGER DEFAULT 0,
                        neutral_count INTEGER DEFAULT 0,
                        PRIMARY KEY (date, bar_name)
                    )
                """)
                
                # Create mention analytics table for trend analysis
                cur.execute("""
                    CREATE TABLE mention_analytics (
                        id SERIAL PRIMARY KEY,
                        analysis_date DATE DEFAULT CURRENT_DATE,
                        total_mentions INTEGER,
                        unique_bars INTEGER,
                        avg_sentiment_score FLOAT,
                        sentiment_distribution JSONB,
                        top_bars JSONB,
                        trending_foods JSONB,
                        data_quality_score FLOAT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create data quality metrics table
                cur.execute("""
                    CREATE TABLE data_quality_metrics (
                        id SERIAL PRIMARY KEY,
                        processing_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        total_posts_processed INTEGER,
                        valid_posts INTEGER,
                        invalid_posts INTEGER,
                        spam_filtered INTEGER,
                        mentions_found INTEGER,
                        unique_bars_mentioned INTEGER,
                        average_confidence FLOAT,
                        data_quality_score FLOAT,
                        metrics_details JSONB
                    )
                """)
                
                # Create indexes for better performance
                cur.execute("CREATE INDEX idx_mentions_bar_name ON mentions(bar_name)")
                cur.execute("CREATE INDEX idx_mentions_created_at ON mentions(created_at)")
                cur.execute("CREATE INDEX idx_mentions_sentiment ON mentions(sentiment_score)")
                cur.execute("CREATE INDEX idx_daily_sentiment_date ON daily_sentiment(date)")
                cur.execute("CREATE INDEX idx_bars_avg_sentiment ON bars(avg_sentiment)")
                cur.execute("CREATE INDEX idx_bars_total_mentions ON bars(total_mentions)")
                
                # Create trigger for updating bar statistics
                cur.execute("""
                    CREATE OR REPLACE FUNCTION update_bar_stats()
                    RETURNS TRIGGER AS $$
                    BEGIN
                        UPDATE bars 
                        SET 
                            total_mentions = (
                                SELECT COUNT(*) FROM bar_mentions WHERE bar_name = NEW.bar_name
                            ),
                            avg_sentiment = (
                                SELECT AVG(sentiment_score) FROM bar_mentions WHERE bar_name = NEW.bar_name
                            ),
                            avg_confidence = (
                                SELECT AVG(sentiment_confidence) FROM bar_mentions WHERE bar_name = NEW.bar_name
                            ),
                            positive_mentions = (
                                SELECT COUNT(*) FROM bar_mentions 
                                WHERE bar_name = NEW.bar_name AND sentiment_label = 'positive'
                            ),
                            negative_mentions = (
                                SELECT COUNT(*) FROM bar_mentions 
                                WHERE bar_name = NEW.bar_name AND sentiment_label = 'negative'
                            ),
                            neutral_mentions = (
                                SELECT COUNT(*) FROM bar_mentions 
                                WHERE bar_name = NEW.bar_name AND sentiment_label = 'neutral'
                            ),
                            last_mention = (
                                SELECT MAX(created_at) FROM bar_mentions WHERE bar_name = NEW.bar_name
                            ),
                            updated_at = CURRENT_TIMESTAMP
                        WHERE name = NEW.bar_name;
                        
                        RETURN NEW;
                    END;
                    $$ LANGUAGE plpgsql;
                """)
                
                cur.execute("""
                    CREATE TRIGGER trigger_update_bar_stats
                    AFTER INSERT ON mentions
                    FOR EACH ROW
                    EXECUTE FUNCTION update_bar_stats();
                """)
            
            conn.commit()
            logger.info("Enhanced database schema created successfully")
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Error creating enhanced schema: {e}")
            raise
    
    def load_enhanced_data(self, data: List[Dict[str, Any]], quality_metrics: Optional[Dict[str, Any]] = None) -> None:
        """Load data with enhanced schema and analytics."""
        if not data:
            logger.info("No data to load")
            return
        
        conn = self.db_manager.get_connection()
        
        try:
            with conn.cursor() as cur:
                # Insert unique bars first
                bars = {item["bar_name"] for item in data}
                bar_values = [(bar,) for bar in bars]
                
                execute_values(
                    cur,
                    """
                    INSERT INTO bars (name, first_mention) 
                    VALUES %s 
                    ON CONFLICT (name) DO UPDATE SET
                        first_mention = CASE 
                            WHEN bars.first_mention IS NULL THEN EXCLUDED.first_mention 
                            ELSE LEAST(bars.first_mention, EXCLUDED.first_mention)
                        END
                    """,
                    [(bar, min(item["created_at"] for item in data if item["bar_name"] == bar)) 
                     for bar in bars]
                )
                
                # Prepare mention data for insertion
                mention_values = []
                for item in data:
                    mention_values.append((
                        item["bar_name"],
                        item["post_id"],
                        item["post_title"],
                        item["post_text"],
                        item["created_at"],
                        item.get("sentiment_score", item.get("sentiment", 0.0)),
                        item.get("sentiment_confidence", 0.0),
                        item.get("sentiment_label", "neutral"),
                        Json(item.get("model_scores", {})),
                        Json(item.get("emotion_scores", {})),
                        item.get("food_mentions", []),
                        item["url"],
                        "Comment on:" in item.get("post_title", "")
                    ))
                
                # Insert mentions with conflict handling
                execute_values(
                    cur,
                    """
                    INSERT INTO mentions (
                        bar_name, post_id, post_title, post_text, created_at,
                        sentiment_score, sentiment_confidence, sentiment_label,
                        model_scores, emotion_scores, food_mentions, url, is_comment
                    ) VALUES %s
                    ON CONFLICT (post_id, bar_name) DO UPDATE SET
                        sentiment_score = EXCLUDED.sentiment_score,
                        sentiment_confidence = EXCLUDED.sentiment_confidence,
                        sentiment_label = EXCLUDED.sentiment_label,
                        model_scores = EXCLUDED.model_scores,
                        emotion_scores = EXCLUDED.emotion_scores
                    """,
                    mention_values
                )
                
                # Update daily sentiment aggregations
                cur.execute("""
                    INSERT INTO daily_sentiment (date, bar_name, mention_count, avg_sentiment, avg_confidence, positive_count, negative_count, neutral_count)
                    SELECT 
                        DATE(created_at) as date,
                        bar_name,
                        COUNT(*) as mention_count,
                        AVG(sentiment_score) as avg_sentiment,
                        AVG(sentiment_confidence) as avg_confidence,
                        SUM(CASE WHEN sentiment_label = 'positive' THEN 1 ELSE 0 END) as positive_count,
                        SUM(CASE WHEN sentiment_label = 'negative' THEN 1 ELSE 0 END) as negative_count,
                        SUM(CASE WHEN sentiment_label = 'neutral' THEN 1 ELSE 0 END) as neutral_count
                    FROM bar_mentions 
                    WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
                    GROUP BY DATE(created_at), bar_name
                    ON CONFLICT (date, bar_name) DO UPDATE SET
                        mention_count = EXCLUDED.mention_count,
                        avg_sentiment = EXCLUDED.avg_sentiment,
                        avg_confidence = EXCLUDED.avg_confidence,
                        positive_count = EXCLUDED.positive_count,
                        negative_count = EXCLUDED.negative_count,
                        neutral_count = EXCLUDED.neutral_count
                """)
                
                # Store quality metrics if provided
                if quality_metrics:
                    cur.execute("""
                        INSERT INTO data_quality_metrics (
                            total_posts_processed, valid_posts, invalid_posts, spam_filtered,
                            mentions_found, unique_bars_mentioned, average_confidence,
                            data_quality_score, metrics_details
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        quality_metrics.get("total_processed", 0),
                        quality_metrics.get("valid_posts", 0),
                        quality_metrics.get("invalid_posts", 0),
                        quality_metrics.get("spam_filtered", 0),
                        len(data),
                        len(bars),
                        quality_metrics.get("average_confidence", 0.0),
                        quality_metrics.get("data_quality_score", 0.0),
                        Json(quality_metrics)
                    ))
            
            conn.commit()
            logger.info(f"Successfully loaded {len(data)} mentions for {len(bars)} bars")
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Error loading enhanced data: {e}")
            raise
    
    def generate_analytics_summary(self) -> None:
        """Generate comprehensive analytics summary."""
        conn = self.db_manager.get_connection()
        
        try:
            with conn.cursor() as cur:
                # Store current analytics snapshot
                cur.execute("""
                    INSERT INTO mention_analytics (
                        total_mentions, unique_bars, avg_sentiment_score,
                        sentiment_distribution, top_bars, trending_foods, data_quality_score
                    )
                    SELECT 
                        (SELECT COUNT(*) FROM bar_mentions) as total_mentions,
                        (SELECT COUNT(*) FROM bars WHERE total_mentions > 0) as unique_bars,
                        (SELECT AVG(sentiment_score) FROM bar_mentions) as avg_sentiment_score,
                        (
                            SELECT jsonb_build_object(
                                'positive', COUNT(*) FILTER (WHERE sentiment_label = 'positive'),
                                'negative', COUNT(*) FILTER (WHERE sentiment_label = 'negative'),
                                'neutral', COUNT(*) FILTER (WHERE sentiment_label = 'neutral')
                            ) FROM mentions
                        ) as sentiment_distribution,
                        (
                            SELECT jsonb_agg(jsonb_build_object('name', name, 'mentions', total_mentions, 'sentiment', avg_sentiment))
                            FROM (
                                SELECT name, total_mentions, avg_sentiment 
                                FROM bars 
                                WHERE total_mentions > 0 
                                ORDER BY total_mentions DESC 
                                LIMIT 10
                            ) top_bars_query
                        ) as top_bars,
                        (
                            SELECT jsonb_agg(jsonb_build_object('food', food_item, 'count', mention_count))
                            FROM (
                                SELECT unnest(food_mentions) as food_item, COUNT(*) as mention_count
                                FROM bar_mentions 
                                WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
                                GROUP BY food_item
                                ORDER BY mention_count DESC
                                LIMIT 20
                            ) trending_foods_query
                        ) as trending_foods,
                        (
                            SELECT AVG(data_quality_score) 
                            FROM data_quality_metrics 
                            WHERE processing_date >= CURRENT_DATE - INTERVAL '7 days'
                        ) as data_quality_score
                """)
                
                conn.commit()
                logger.info("Analytics summary generated and stored")
        
        except Exception as e:
            logger.error(f"Error generating analytics summary: {e}")
            raise
    
    async def load_processed_data(self, processed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Load processed data and return results."""
        mentions = processed_data.get("mentions", [])
        quality_metrics = processed_data.get("quality_metrics", {})
        
        if mentions:
            import asyncio
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self.create_enhanced_schema)
            await loop.run_in_executor(None, self.load_enhanced_data, mentions, quality_metrics)
            await loop.run_in_executor(None, self.generate_analytics_summary)
        
        return {
            "mentions_loaded": len(mentions),
            "quality_score": quality_metrics.get("data_quality_score", 0),
            "new_bars": len(set(m["bar_name"] for m in mentions))
        }
    
    def close(self):
        """Close database connections."""
        self.db_manager.close_connection()


# Enhanced functions for backwards compatibility and new features
def load_to_postgres(data: List[Dict[str, Any]], quality_metrics: Optional[Dict[str, Any]] = None) -> None:
    """Enhanced data loading with backwards compatibility."""
    loader = EnhancedLoader()
    
    try:
        # Create schema if it doesn't exist
        loader.create_enhanced_schema()
        
        # Load data
        loader.load_enhanced_data(data, quality_metrics)
        
        # Generate analytics
        loader.generate_analytics_summary()
        
    finally:
        loader.close()


def summarize_sentiment(start_date: datetime = None, end_date: datetime = None) -> None:
    """Enhanced sentiment summary with advanced analytics."""
    db_manager = DatabaseManager()
    conn = db_manager.get_connection()
    
    try:
        with conn.cursor() as cur:
            # Get overall statistics
            cur.execute("""
                SELECT 
                    COUNT(DISTINCT bar_name) as unique_bars,
                    COUNT(*) as total_mentions,
                    AVG(sentiment_score) as avg_sentiment,
                    AVG(sentiment_confidence) as avg_confidence
                FROM mentions
                WHERE ($1::timestamp IS NULL OR created_at >= $1)
                AND ($2::timestamp IS NULL OR created_at <= $2)
            """, (start_date, end_date))
            
            stats = cur.fetchone()
            if not stats or stats[1] == 0:
                # Try to get data from any time period
                cur.execute("""
                    SELECT 
                        COUNT(DISTINCT bar_name) as unique_bars,
                        COUNT(*) as total_mentions,
                        AVG(sentiment_score) as avg_sentiment,
                        AVG(sentiment_confidence) as avg_confidence
                    FROM bar_mentions
                """)
                stats = cur.fetchone()
                
                if not stats or stats[1] == 0:
                    print("\n⚠️  No sentiment data found in database")
                    return
            
            print("\n" + "="*70)
            print(" HALIFAX BAR SENTIMENT ANALYSIS SUMMARY")
            print("="*70)
            print(f"Period: {start_date or 'All time'} to {end_date or 'Present'}")
            print(f"Unique Bars: {stats[0]:,}")
            print(f"Total Mentions: {stats[1]:,}")
            print(f"Average Sentiment: {stats[2]:.3f} ({_sentiment_label(stats[2])})")
            print(f"Average Confidence: {stats[3]:.1%}" if stats[3] else "Average Confidence: N/A")
            
            # Get sentiment distribution
            cur.execute("""
                SELECT 
                    sentiment_label,
                    COUNT(*) as count,
                    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) as percentage
                FROM mentions
                WHERE ($1::timestamp IS NULL OR created_at >= $1)
                AND ($2::timestamp IS NULL OR created_at <= $2)
                GROUP BY sentiment_label
                ORDER BY count DESC
            """, (start_date, end_date))
            
            sentiment_dist = cur.fetchall()
            if sentiment_dist:
                print("\nSentiment Distribution:")
                print("-" * 25)
                for label, count, percentage in sentiment_dist:
                    print(f"{label.capitalize():>10}: {count:>6,} ({percentage:>5.1f}%)")
            
            # Get top mentioned bars with enhanced stats
            cur.execute("""
                SELECT 
                    bar_name,
                    COUNT(*) as mentions,
                    AVG(sentiment_score) as avg_sentiment,
                    AVG(sentiment_confidence) as avg_confidence,
                    array_agg(DISTINCT unnest(food_mentions)) 
                        FILTER (WHERE food_mentions IS NOT NULL AND array_length(food_mentions, 1) > 0) as food_items
                FROM mentions
                WHERE ($1::timestamp IS NULL OR created_at >= $1)
                AND ($2::timestamp IS NULL OR created_at <= $2)
                GROUP BY bar_name
                ORDER BY mentions DESC
                LIMIT 15
            """, (start_date, end_date))
            
            print(f"\nTop 15 Most Mentioned Bars:")
            print("-" * 80)
            print(f"{'Bar Name':<30} {'Mentions':<10} {'Sentiment':<12} {'Confidence':<12} {'Top Items'}")
            print("-" * 80)
            
            for bar_data in cur.fetchall():
                bar_name, mentions, avg_sentiment, avg_confidence, food_items = bar_data
                sentiment_str = f"{avg_sentiment:.2f}" if avg_sentiment else "N/A"
                confidence_str = f"{avg_confidence:.1%}" if avg_confidence else "N/A"
                
                # Format food items
                if food_items and food_items[0]:  # Check if not empty
                    top_items = ', '.join(food_items[:3])
                    if len(top_items) > 25:
                        top_items = top_items[:22] + "..."
                else:
                    top_items = "N/A"
                
                print(f"{bar_name:<30} {mentions:<10,} {sentiment_str:<12} {confidence_str:<12} {top_items}")
            
            # Get recent data quality metrics
            cur.execute("""
                SELECT 
                    data_quality_score,
                    average_confidence,
                    processing_date
                FROM data_quality_metrics
                ORDER BY processing_date DESC
                LIMIT 1
            """)
            
            quality_data = cur.fetchone()
            if quality_data:
                quality_score, avg_conf, proc_date = quality_data
                print(f"\nData Quality Metrics (Last Run: {proc_date.strftime('%Y-%m-%d %H:%M')})")
                print("-" * 50)
                print(f"Data Quality Score: {quality_score:.1%}" if quality_score else "Data Quality Score: N/A")
                print(f"Processing Confidence: {avg_conf:.1%}" if avg_conf else "Processing Confidence: N/A")
            
            print("="*70)
            
    except Exception as e:
        logger.error(f"Error generating sentiment summary: {e}")
        raise
    finally:
        db_manager.close_connection()


def _sentiment_label(score: float) -> str:
    """Convert sentiment score to human-readable label."""
    if score is None:
        return "Unknown"
    elif score > 0.1:
        return "Positive"
    elif score < -0.1:
        return "Negative"
    else:
        return "Neutral"