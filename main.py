"""Command-line entrypoint for the Halifax Bar sentiment ETL pipeline."""

from __future__ import annotations

import logging
import sys
from argparse import ArgumentParser, Namespace

from extract import extract_reddit_data
from transform import transform_posts
from load import load_to_postgres, summarize_sentiment


def _configure_logging(verbose: bool = False) -> None:
    """Initialise basic console logging."""

    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        stream=sys.stdout,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def _parse_args() -> Namespace:
    parser = ArgumentParser(description="Reddit ETL sentiment pipeline for Halifax bars")
    parser.add_argument("--limit", type=int, default=1_000, help="Number of posts to fetch")
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging")
    return parser.parse_args()


def main() -> None:
    """Main entrypoint."""
    args = _parse_args()
    _configure_logging(args.verbose)

    logger = logging.getLogger()
    logger.info("🔄 Extracting data from Reddit …")
    posts = extract_reddit_data(limit=args.limit)

    if args.verbose:
        logger.debug("Sample of fetched posts:")
        for i, post in enumerate(posts[:5], 1):
            logger.debug(f"Post {i}: {post['title']}")
            if post['selftext']:
                logger.debug(f"Content: {post['selftext'][:200]}...")
            logger.debug("-" * 50)

    logger.info("🧠 Transforming data …")
    processed_data = transform_posts(posts)

    logger.info("📥 Loading into PostgreSQL …")
    load_to_postgres(processed_data)
    summarize_sentiment()  # Call without arguments to show all-time stats


if __name__ == "__main__":
    main()
