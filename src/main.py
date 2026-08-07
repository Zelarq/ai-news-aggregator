import sys
import logging
import argparse
import datetime
from src.config import Config
from src.database import (
    init_db, save_raw_item, get_unsummarized_items,
    update_item_summary, get_summarized_unsent_items, mark_items_as_sent
)
from src.collectors.youtube import collect_youtube_news
from src.collectors.reddit import collect_reddit_news
from src.collectors.hackernews import collect_hn_news
from src.agent import summarize_and_categorize
from src.composer import build_html_digest, build_plain_text_digest
from src.mailer import send_email_digest

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("agent_run.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)

def run_pipeline(lookback_hours=24, dry_run=False, test_mode=False):
    """Executes the daily AI News Digest pipeline from collection to email delivery."""
    logging.info("=" * 50)
    logging.info(f"Starting pipeline execution (dry-run={dry_run}, test-mode={test_mode})")
    
    # 0. Validate Configuration
    try:
        Config.validate(dry_run=dry_run, test_mode=test_mode)
        logging.info("Configuration validation succeeded.")
    except ValueError as e:
        logging.error(f"Configuration validation failed:\n{e}")
        logging.error("Please configure your .env file before running. Exiting.")
        sys.exit(1)
        
    # 1. Initialize DB
    logging.info("Initializing database...")
    init_db()
    
    # 2. Collect Data
    logging.info(f"Poller running for last {lookback_hours} hours...")
    
    youtube_items = []
    try:
        youtube_items = collect_youtube_news(lookback_hours=lookback_hours, test_mode=test_mode)
        logging.info(f"YouTube Collector: Found {len(youtube_items)} video items.")
    except Exception as e:
        logging.error(f"YouTube Collector failed: {e}")
        
    reddit_items = []
    try:
        reddit_items = collect_reddit_news(lookback_hours=lookback_hours, test_mode=test_mode)
        logging.info(f"Reddit Collector: Found {len(reddit_items)} post items.")
    except Exception as e:
        logging.error(f"Reddit Collector failed: {e}")

    hn_items = []
    try:
        hn_items = collect_hn_news(lookback_hours=lookback_hours, test_mode=test_mode)
        logging.info(f"Hacker News Collector: Found {len(hn_items)} stories.")
    except Exception as e:
        logging.error(f"Hacker News Collector failed: {e}")
        
    all_collected = youtube_items + reddit_items + hn_items
    if not all_collected:
        logging.warning("No items collected from any sources. Checking for pending items in database...")
    
    # 3. Store new items in SQLite (deduplication)
    new_inserts_count = 0
    for item in all_collected:
        is_new = save_raw_item(item)
        if is_new:
            new_inserts_count += 1
            logging.info(f"Stored new item: [{item['source'].upper()}] {item['title'][:50]}")
            
    logging.info(f"Database sync: {new_inserts_count} new unique items added.")
    
    # 4. Fetch all items that need summarization
    pending_items = get_unsummarized_items()
    logging.info(f"Summarizer: {len(pending_items)} items waiting for AI processing.")
    
    # 5. Summarize and Categorize each item
    for i, item in enumerate(pending_items, start=1):
        title = item['title']
        content = item['content']
        ext_id = item['external_id']
        
        logging.info(f"[{i}/{len(pending_items)}] Summarizing ({item['source'].upper()}): '{title[:45]}...'")
        
        result = summarize_and_categorize(title, content, test_mode=test_mode)
        
        update_item_summary(
            external_id=ext_id,
            summary=result['summary'],
            category=result['category']
        )
        
    # 6. Retrieve all summarized items that haven't been emailed yet
    unsent_items = get_summarized_unsent_items()
    logging.info(f"Composer: Found {len(unsent_items)} summarized stories to package in digest.")
    
    if not unsent_items:
        logging.info("No summarized stories are available to send. Digest skipped.")
        return
        
    # 7. Build Digest
    logging.info("Building HTML and plain-text digests...")
    html_digest = build_html_digest(unsent_items)
    text_digest = build_plain_text_digest(unsent_items)
    
    # 8. Send Email
    today_str = datetime.date.today().strftime("%b %d, %Y")
    subject = f"Daily AI News Digest - {today_str}"
    
    logging.info("Initiating email delivery...")
    delivery_success = send_email_digest(
        html_content=html_digest,
        text_content=text_digest,
        subject=subject,
        dry_run=dry_run
    )
    
    # 9. If successfully sent, mark them as sent in DB
    if delivery_success:
        unsent_ids = [item['external_id'] for item in unsent_items]
        if not dry_run:
            mark_items_as_sent(unsent_ids)
            logging.info(f"State updated: Marked {len(unsent_ids)} items as sent.")
        else:
            logging.info("[Dry Run] Items were not marked as sent in DB to allow re-testing.")
            
    logging.info("Pipeline execution completed successfully.")
    logging.info("=" * 50)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI News Digest Pipeline")
    parser.add_argument("--dry-run", action="store_true", help="Generate digest HTML locally but do not send email")
    parser.add_argument("--test", action="store_true", help="Run with mock API keys and heuristic LLM (useful for first-time runs)")
    parser.add_argument("--lookback", type=int, default=24, help="Number of hours to look back for new items (default 24)")
    args = parser.parse_args()
    
    run_pipeline(lookback_hours=args.lookback, dry_run=args.dry_run, test_mode=args.test)
