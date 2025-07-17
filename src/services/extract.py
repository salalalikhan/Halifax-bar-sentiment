"""Data extraction layer for Reddit content."""

from __future__ import annotations

import logging
from typing import List, Dict, Any

import praw
from prawcore.exceptions import PrawcoreException, RequestException, ResponseException

from src.core.config import settings
from src.core.constants import BAR_NAMES

logger = logging.getLogger(__name__)


def _get_reddit_client() -> praw.Reddit:
    logger.debug("Initialising Reddit API client")
    return praw.Reddit(
        client_id=settings.reddit_client_id,
        client_secret=settings.reddit_client_secret,
        user_agent=settings.reddit_user_agent,
        requestor_kwargs={"timeout": 20},  # 20-second network timeout per request
    )


def _build_search_query() -> str:
    """Build a simpler search query that works better with Reddit's search."""
    # Use a simpler query focusing on common terms
    terms = [
        "bar", "pub", "brewery", "beer",
        "wings", "trivia", "live music",
        "happy hour", "drinks"
    ]
    return " OR ".join(terms)


def extract_reddit_data(limit: int = 1_000) -> List[Dict[str, Any]]:
    """Fetch Reddit submissions and comments mentioning Halifax bars."""
    reddit = _get_reddit_client()
    subreddit = reddit.subreddit("halifax")
    
    logger.info(f"Fetching up to {limit} submissions from r/halifax matching search terms")
    
    try:
        # Search for submissions
        search_query = _build_search_query()
        logger.debug("Search query: %s", search_query)
        
        # Get posts from hot, new, and top
        posts = set()  # Use set to avoid duplicates
        
        # Get from different sort methods to increase coverage
        for sort_method in ['hot', 'new', 'top']:
            if sort_method == 'top':
                submissions = subreddit.top(limit=limit//3, time_filter='all')
            elif sort_method == 'hot':
                submissions = subreddit.hot(limit=limit//3)
            else:
                submissions = subreddit.new(limit=limit//3)
            
            for submission in submissions:
                # Check if post might be relevant
                text = f"{submission.title.lower()} {submission.selftext.lower()}"
                if any(term.lower() in text for term in search_query.split(" OR ")):
                    posts.add(submission)
        
        # Process each submission
        processed_data = []
        for submission in posts:
            # Get submission data
            data = {
                "id": submission.id,
                "title": submission.title,
                "selftext": submission.selftext,
                "created_utc": submission.created_utc,
                "score": submission.score,
                "url": submission.url,
                "comments": []
            }
            
            # Get comments
            submission.comments.replace_more(limit=0)  # Only get readily available comments
            for comment in submission.comments.list():
                data["comments"].append({
                    "id": comment.id,
                    "body": comment.body,
                    "created_utc": comment.created_utc,
                    "score": comment.score
                })
            
            processed_data.append(data)
        
        logger.info(f"Extracted {len(processed_data)} submissions")
        return processed_data
        
    except (PrawcoreException, RequestException, ResponseException) as e:
        logger.error(f"Error fetching Reddit data: {str(e)}")
        return []
