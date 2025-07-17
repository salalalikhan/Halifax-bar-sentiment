"""Data transformation layer for Reddit content."""

from __future__ import annotations

import logging
import re
from typing import Dict, List, Any, Set, Tuple
from datetime import datetime

from textblob import TextBlob

from src.core.constants import BAR_NAMES

logger = logging.getLogger(__name__)

# Common food and drink terms to look for
FOOD_TERMS = {
    'wings', 'nachos', 'burger', 'pizza', 'fries', 'poutine',
    'fish and chips', 'tacos', 'appetizers', 'menu', 'food',
    'dinner', 'lunch', 'brunch', 'snacks', 'platter'
}

DRINK_TERMS = {
    'beer', 'craft beer', 'wine', 'cocktail', 'drinks', 'draft',
    'ale', 'lager', 'stout', 'ipa', 'cider', 'happy hour'
}

def _normalize_text(text: str) -> str:
    """Normalize text for matching by removing special characters and extra spaces."""
    text = text.lower()
    text = re.sub(r'[^\w\s]', ' ', text)  # Replace special chars with space
    text = re.sub(r'\s+', ' ', text)  # Replace multiple spaces with single space
    return text.strip()

def _extract_bar_mentions(text: str) -> Set[str]:
    """Extract bar mentions using flexible matching."""
    normalized_text = _normalize_text(text)
    
    matches = set()
    for bar in BAR_NAMES:
        # Try exact match first
        if bar.lower() in normalized_text:
            matches.add(bar)
            continue
            
        # Try matching without special characters
        bar_normalized = _normalize_text(bar)
        if bar_normalized in normalized_text:
            matches.add(bar)
            continue
            
        # Try matching just the distinctive parts (e.g., "Durty" for "Durty Nelly's")
        bar_parts = bar_normalized.split()
        if len(bar_parts) > 1:
            distinctive_part = bar_parts[0] if len(bar_parts[0]) > 3 else bar_parts[-1]
            if distinctive_part in normalized_text:
                matches.add(bar)
    
    return matches

def _extract_food_mentions(text: str) -> Set[str]:
    """Extract food and drink mentions from text."""
    normalized_text = _normalize_text(text)
    
    food_mentions = set()
    for term in FOOD_TERMS:
        if term in normalized_text:
            food_mentions.add(term)
    
    for term in DRINK_TERMS:
        if term in normalized_text:
            food_mentions.add(term)
    
    return food_mentions

def _analyze_sentiment(text: str) -> float:
    """Analyze sentiment of text, returns score between -1 (negative) and 1 (positive)."""
    try:
        blob = TextBlob(text)
        return blob.sentiment.polarity
    except Exception as e:
        logger.warning(f"Error analyzing sentiment: {e}")
        return 0.0

def transform_posts(posts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Transform Reddit posts to extract bar mentions, food mentions, and sentiment."""
    transformed_data = []
    
    for post in posts:
        # Combine title and content for analysis
        full_text = f"{post['title']} {post['selftext']}"
        
        # Extract bar mentions
        bar_mentions = _extract_bar_mentions(full_text)
        
        # If we found bar mentions, process the post
        if bar_mentions:
            # Get food mentions
            food_mentions = _extract_food_mentions(full_text)
            
            # Analyze sentiment
            sentiment = _analyze_sentiment(full_text)
            
            # Process each bar mention
            for bar in bar_mentions:
                transformed_data.append({
                    "bar_name": bar,
                    "post_id": post["id"],
                    "post_title": post["title"],
                    "post_text": post["selftext"],
                    "created_at": datetime.fromtimestamp(post["created_utc"]),
                    "sentiment": sentiment,
                    "food_mentions": list(food_mentions),
                    "url": post["url"]
                })
            
            # Process comments for additional mentions
            for comment in post.get("comments", []):
                comment_text = comment["body"]
                comment_bar_mentions = _extract_bar_mentions(comment_text)
                
                if comment_bar_mentions:
                    comment_food = _extract_food_mentions(comment_text)
                    comment_sentiment = _analyze_sentiment(comment_text)
                    
                    for bar in comment_bar_mentions:
                        transformed_data.append({
                            "bar_name": bar,
                            "post_id": comment["id"],
                            "post_title": f"Comment on: {post['title']}",
                            "post_text": comment_text,
                            "created_at": datetime.fromtimestamp(comment["created_utc"]),
                            "sentiment": comment_sentiment,
                            "food_mentions": list(comment_food),
                            "url": post["url"]
                        })
    
    logger.info(f"Transformed {len(transformed_data)} posts with bar mentions")
    return transformed_data
