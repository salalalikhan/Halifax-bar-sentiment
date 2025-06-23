"""Sentiment analysis module for Halifax Bar mentions."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Dict, List, Any
from collections import defaultdict

import psycopg2

from config import settings

logger = logging.getLogger(__name__)


def get_sentiment_trends(start_date: datetime = None, end_date: datetime = None) -> List[Dict[str, Any]]:
    """Retrieve sentiment trends for Halifax bars from the database."""
    conn = psycopg2.connect(
        dbname=settings.postgres_dbname,
        user=settings.postgres_user,
        password=settings.postgres_password,
        host=settings.postgres_host,
        port=settings.postgres_port,
    )

    query = """
        SELECT 
            b.name,
            COUNT(*) as mention_count,
            AVG(m.post_sentiment) as avg_post_sentiment,
            AVG(m.post_subjectivity) as avg_post_subjectivity,
            AVG(m.avg_comment_sentiment) as avg_comment_sentiment,
            AVG(m.avg_comment_subjectivity) as avg_comment_subjectivity,
            SUM(m.num_comments) as total_comments
        FROM bars b
        JOIN mentions m ON b.id = m.bar_id
        WHERE 1=1
    """
    params = []

    if start_date:
        query += " AND m.created_at >= %s"
        params.append(start_date)
    if end_date:
        query += " AND m.created_at <= %s"
        params.append(end_date)

    query += """
        GROUP BY b.name
        ORDER BY mention_count DESC, avg_post_sentiment DESC
    """

    with conn.cursor() as cur:
        cur.execute(query, params)
        columns = [desc[0] for desc in cur.description]
        results = [dict(zip(columns, row)) for row in cur.fetchall()]

    conn.close()
    return results


def print_sentiment_report(trends: List[Dict[str, Any]], data: List[Dict[str, Any]] = None) -> None:
    """Display a formatted report of bar sentiment trends and food mentions."""
    if not trends:
        logger.warning("No sentiment data available for analysis")
        return

    # Collect food mentions if data is provided
    food_mentions: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
    if data:
        for post in data:
            for bar, foods in post.get("food_mentions", {}).items():
                for food in foods:
                    food_mentions[bar][food] += 1

    logger.info("\n📊 Halifax Bar Sentiment Analysis Report")
    logger.info("=" * 50)

    for bar in trends:
        logger.info(f"\n🍺 {bar['name']}")
        logger.info("-" * 30)
        logger.info(f"Total Mentions: {bar['mention_count']}")
        logger.info(f"Total Comments: {bar['total_comments']}")
        logger.info(f"Post Sentiment: {bar['avg_post_sentiment']:.2f}")
        logger.info(f"Comment Sentiment: {bar['avg_comment_sentiment']:.2f}")
        logger.info(f"Subjectivity: {bar['avg_post_subjectivity']:.2f}")
        
        # Add food mentions if available
        if bar['name'] in food_mentions and food_mentions[bar['name']]:
            logger.info("\nPopular Food Items:")
            sorted_foods = sorted(
                food_mentions[bar['name']].items(),
                key=lambda x: x[1],
                reverse=True
            )
            for food, count in sorted_foods[:5]:  # Show top 5 food items
                logger.info(f"  • {food}: {count} mentions")

    logger.info("\n" + "=" * 50)
