import os
import sys
import argparse
import logging

# Add src to the path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "src"))

# Import config
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
from config import (
    RAW_DATA_DIR,
    PROCESSED_DATA_DIR
)

from scraper.data_processor import (
    process_all_content,
    remove_content_duplicates,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def get_default_paths():
    """Get default data directory paths from config."""
    return {
        "raw_dir": RAW_DATA_DIR,
        "processed_dir": PROCESSED_DATA_DIR
    }

def run_duplicate_removal(raw_dir: str):
    """Remove duplicate content files."""
    logger.info("Checking and removing duplicate files...")
    report = remove_content_duplicates(raw_dir)
    
    if "error" in report:
        logger.error(f"Error removing duplicates: {report['error']}")
        return False
    
    duplicates_count = len(report.get('duplicates', {}))
    logger.info(f"Removed {duplicates_count} sets of duplicate files")
    
    for kept_url, info in report.get('duplicates', {}).items():
        logger.info(f"Kept: {info['kept']}, Removed: {info['removed']}")
    
    return True

def run_content_processing(raw_dir: str, processed_dir: str):
    """Process all content into chunks."""
    logger.info("Processing content into chunks...")
    results = process_all_content(raw_dir, processed_dir)
    
    logger.info(f"Processing completed:")
    logger.info(f"  - Files processed: {results['total_files']}")
    logger.info(f"  - Chunks created: {results['total_chunks']}")
    logger.info(f"  - Content types: {dict(results['content_types'])}")
    logger.info(f"  - Brands found: {dict(results['brands'])}")
    
    return True

def main():
    """Main entry point with command line argument parsing."""
    parser = argparse.ArgumentParser(description="Nestle AI Chatbot Data Processor")
    
    # Get default paths
    default_paths = get_default_paths()
    
    parser.add_argument(
        "--step",
        choices=["duplicates", "process", "all"],
        default="all",
        help="Which processing step to run"
    )
    
    parser.add_argument(
        "--raw-dir",
        default=default_paths["raw_dir"],
        help="Path to directory containing raw markdown files"
    )
    
    parser.add_argument(
        "--processed-dir", 
        default=default_paths["processed_dir"],
        help="Path to directory for processed output files"
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
    
    # Validate paths
    if not os.path.exists(args.raw_dir):
        logger.error(f"Raw data directory not found: {args.raw_dir}")
        sys.exit(1)
    
    # Create processed directory if it doesn't exist
    os.makedirs(args.processed_dir, exist_ok=True)
    
    logger.info(f"Raw data directory: {args.raw_dir}")
    logger.info(f"Processed data directory: {args.processed_dir}")
    
    # Run specified steps
    success = True
    
    if args.step in ["duplicates", "all"]:
        logger.info("\n" + "=" * 50)
        logger.info("STEP 1: REMOVING DUPLICATES")
        logger.info("=" * 50)
        success &= run_duplicate_removal(args.raw_dir)
    
    if args.step in ["process", "all"]:
        logger.info("\n" + "=" * 50)
        logger.info("STEP 2: CONTENT PROCESSING")
        logger.info("=" * 50)
        success &= run_content_processing(args.raw_dir, args.processed_dir)
    if success:
        logger.info("\n🎉 All processing steps completed successfully!")
    else:
        logger.error("\n❌ Some processing steps failed. Check logs for details.")
        sys.exit(1)

if __name__ == "__main__":
    main() 