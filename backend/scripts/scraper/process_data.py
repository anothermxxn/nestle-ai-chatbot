#!/usr/bin/env python3
"""
Data Processing Script for Nestle AI Chatbot

This script processes the scraped markdown files into chunks suitable for vector storage.
It removes boilerplate content and prepares data for the search index.
"""

import os
import sys
import argparse
import logging

# Add src to the path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from scraper.data_processor import (
    process_all_content,
    remove_content_duplicates,
    create_content_index
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def run_duplicate_removal():
    """Remove duplicate content files."""
    logger.info("Checking and removing duplicate files...")
    report = remove_content_duplicates()
    
    if "error" in report:
        logger.error(f"Error removing duplicates: {report['error']}")
        return False
    
    duplicates_count = len(report.get('duplicates', {}))
    logger.info(f"Removed {duplicates_count} sets of duplicate files")
    
    for kept_url, info in report.get('duplicates', {}).items():
        logger.info(f"Kept: {info['kept']}, Removed: {info['removed']}")
    
    return True

def run_content_processing():
    """Process all content into chunks."""
    logger.info("Processing content into chunks...")
    results = process_all_content()
    
    logger.info(f"Processing completed:")
    logger.info(f"  - Files processed: {results['total_files']}")
    logger.info(f"  - Chunks created: {results['total_chunks']}")
    logger.info(f"  - Content types: {dict(results['content_types'])}")
    logger.info(f"  - Brands found: {dict(results['brands'])}")
    
    return True

def run_content_indexing():
    """Create content index."""
    logger.info("Creating content index...")
    index = create_content_index()
    
    logger.info(f"Content index created:")
    logger.info(f"  - Total files: {index['total_files']}")
    logger.info(f"  - Timestamp: {index['timestamp']}")
    
    return True

def main():
    """Main entry point with command line argument parsing."""
    parser = argparse.ArgumentParser(description="Nestle AI Chatbot Data Processor")
    
    parser.add_argument(
        "--step",
        choices=["duplicates", "process", "index", "all"],
        default="all",
        help="Which processing step to run"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Run specified steps
    success = True
    
    if args.step in ["duplicates", "all"]:
        logger.info("=" * 50)
        logger.info("STEP 1: REMOVING DUPLICATES")
        logger.info("=" * 50)
        success &= run_duplicate_removal()
    
    if args.step in ["process", "all"]:
        logger.info("\n" + "=" * 50)
        logger.info("STEP 2: PROCESSING CONTENT")
        logger.info("=" * 50)
        success &= run_content_processing()
    
    if args.step in ["index", "all"]:
        logger.info("\n" + "=" * 50)
        logger.info("STEP 3: CREATING INDEX")
        logger.info("=" * 50)
        success &= run_content_indexing()
    
    if success:
        logger.info("\n🎉 All processing steps completed successfully!")
    else:
        logger.error("\n❌ Some processing steps failed. Check logs for details.")
        sys.exit(1)

if __name__ == "__main__":
    main() 