"""Data loading layer for PostgreSQL database."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Dict, List, Any

import psycopg2
from psycopg2.extras import execute_values

from src.core.config import settings

logger = logging.getLogger(__name__)


def _get_db_connection():
    return psycopg2.connect(
        dbname=settings.db_database,
        user=settings.db_user,
        password=settings.db_password,
        host=settings.db_host,
        port=settings.db_port,
    )


def _create_tables(conn):
    with conn.cursor() as cur:
        # Drop existing tables if they exist to ensure clean schema
        cur.execute("DROP TABLE IF EXISTS mentions")
        cur.execute("DROP TABLE IF EXISTS bars")
        
        # Create bars table
        cur.execute("""
            CREATE TABLE bars (
                name VARCHAR(255) PRIMARY KEY,
                total_mentions INTEGER DEFAULT 0,
                avg_sentiment FLOAT DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create mentions table
        cur.execute("""
            CREATE TABLE mentions (
                id SERIAL PRIMARY KEY,
                bar_name VARCHAR(255) REFERENCES bars(name),
                post_id VARCHAR(255),
                post_title TEXT,
                post_text TEXT,
                created_at TIMESTAMP,
                sentiment FLOAT,
                food_mentions TEXT[],
                url TEXT,
                created_at_db TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
    
    conn.commit()


def load_to_postgres(data: List[Dict[str, Any]]) -> None:
    """Load transformed data into PostgreSQL database."""
    if not data:
        logger.info("No data to load")
        return

    conn = _get_db_connection()
    _create_tables(conn)

    try:
        with conn.cursor() as cur:
            # Insert unique bars
            bars = {item["bar_name"] for item in data}
            bar_values = [(bar,) for bar in bars]
            execute_values(
                cur,
                "INSERT INTO bars (name) VALUES %s ON CONFLICT DO NOTHING",
                bar_values
            )

            # Insert mentions
            mention_values = [
                (
                    item["bar_name"],
                    item["post_id"],
                    item["post_title"],
                    item["post_text"],
                    item["created_at"],
                    item["sentiment"],
                    item["food_mentions"],
                    item["url"]
                )
                for item in data
            ]
            execute_values(
                cur,
                """
                INSERT INTO mentions (
                    bar_name, post_id, post_title, post_text,
                    created_at, sentiment, food_mentions, url
                ) VALUES %s
                """,
                mention_values
            )

            # Update bar statistics
            cur.execute("""
                UPDATE bars b
                SET 
                    total_mentions = m.mention_count,
                    avg_sentiment = m.avg_sentiment
                FROM (
                    SELECT 
                        bar_name,
                        COUNT(*) as mention_count,
                        AVG(sentiment) as avg_sentiment
                    FROM mentions
                    GROUP BY bar_name
                ) m
                WHERE b.name = m.bar_name
            """)

        conn.commit()
        logger.info("Successfully loaded data into PostgreSQL")

    except Exception as e:
        conn.rollback()
        logger.error(f"Error loading data into PostgreSQL: {e}")
        raise

    finally:
        conn.close()


def summarize_sentiment(start_date: datetime = None, end_date: datetime = None) -> None:
    """Print a summary of sentiment analysis results."""
    if not start_date and not end_date:
        logger.warning("No data to summarize")
        return

    conn = _get_db_connection()
    try:
        with conn.cursor() as cur:
            # Get overall statistics
            cur.execute("""
                SELECT 
                    COUNT(DISTINCT bar_name) as unique_bars,
                    COUNT(*) as total_mentions,
                    AVG(sentiment) as avg_sentiment
                FROM mentions
                WHERE ($1::timestamp IS NULL OR created_at >= $1)
                AND ($2::timestamp IS NULL OR created_at <= $2)
            """, (start_date, end_date))
            
            stats = cur.fetchone()
            if not stats or stats[1] == 0:
                logger.warning("No data to summarize")
                return
                
            print("\n=== Sentiment Analysis Summary ===")
            print(f"Period: {start_date or 'All time'} to {end_date or 'Present'}")
            print(f"Unique Bars: {stats[0]}")
            print(f"Total Mentions: {stats[1]}")
            print(f"Average Sentiment: {stats[2]:.2f}")
            
            # Get top mentioned bars with their stats
            cur.execute("""
                SELECT 
                    bar_name,
                    COUNT(*) as mentions,
                    AVG(sentiment) as avg_sentiment,
                    array_agg(DISTINCT unnest(food_mentions)) as food_items
                FROM mentions
                WHERE ($1::timestamp IS NULL OR created_at >= $1)
                AND ($2::timestamp IS NULL OR created_at <= $2)
                GROUP BY bar_name
                ORDER BY mentions DESC
                LIMIT 10
            """, (start_date, end_date))
            
            print("\nTop 10 Most Mentioned Bars:")
            print("----------------------------")
            for bar in cur.fetchall():
                print(f"\n{bar[0]}:")
                print(f"  Mentions: {bar[1]}")
                print(f"  Avg Sentiment: {bar[2]:.2f}")
                print(f"  Popular Items: {', '.join(bar[3][:5])}")  # Show top 5 food items

    except Exception as e:
        logger.error(f"Error summarizing data: {e}")
        raise

    finally:
        conn.close() 