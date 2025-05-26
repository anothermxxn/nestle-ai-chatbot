import os
import sys
import argparse
import logging

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "src"))
from utils.import_helper import setup_imports
setup_imports(__file__)
from config import (
    RAW_DATA_DIR,
    PROCESSED_DATA_DIR
)
from scrape.data_processor import (
    process_all_content,
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
    
    # Run content processing only
    logger.info("\n" + "=" * 50)
    logger.info("CONTENT PROCESSING")
    logger.info("=" * 50)
    
    success = run_content_processing(args.raw_dir, args.processed_dir)
    
    if success:
        logger.info("\nContent processing completed successfully!")
    else:
        logger.error("\nContent processing failed.")
        sys.exit(1)

if __name__ == "__main__":
    main() 