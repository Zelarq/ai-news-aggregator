import sys
import time
import datetime
import argparse
import logging
import praw
from src.config import Config

# Subreddits to poll
SUBREDDITS = ["MachineLearning", "LocalLLaMA", "singularity", "artificial"]

def collect_reddit_news(lookback_hours=24, limit=10, test_mode=False):
    """
    Fetches hot/top posts from subreddits published in the last `lookback_hours` hours.
    Extracts post body and top 3 comments for community context.
    """
    if not (Config.REDDIT_CLIENT_ID and Config.REDDIT_CLIENT_SECRET and Config.REDDIT_USERNAME and Config.REDDIT_PASSWORD):
        if test_mode:
            print("Warning: Reddit API credentials are not set. Returning mock Reddit data for testing.")
            return [
                {
                    "external_id": "test_reddit_post_456",
                    "source": "reddit",
                    "title": "Llama 4 Release Discussion and Benchmarks",
                    "content": "Subreddit: r/LocalLLaMA\nScore: 1250 | Comments: 184\n\nPost Body:\nMeta has just dropped Llama 4 details. It claims to match GPT-4o on reasoning and is open weights.\n\nTop Comments:\n- Comment 1: This is absolutely huge! Let's see the context window details.\n- Comment 2: Running 405B locally is going to be tough, but quantized versions will fit on consumer GPUs.\n- Comment 3: Is it commercial friendly license?",
                    "url": "https://reddit.com/r/LocalLLaMA/comments/test_reddit_post_456",
                    "published_at": (datetime.datetime.utcnow() - datetime.timedelta(hours=4)).isoformat()
                }
            ]
        else:
            logging.warning("Reddit API credentials are not set. Skipping Reddit collector.")
            return []

    # Initialize Reddit client
    reddit = praw.Reddit(
        client_id=Config.REDDIT_CLIENT_ID,
        client_secret=Config.REDDIT_CLIENT_SECRET,
        user_agent=Config.REDDIT_USER_AGENT,
        username=Config.REDDIT_USERNAME,
        password=Config.REDDIT_PASSWORD
    )
    
    threshold_time = time.time() - (lookback_hours * 3600)
    collected_posts = []
    
    for sub_name in SUBREDDITS:
        try:
            print(f"Collecting posts from r/{sub_name}...")
            subreddit = reddit.subreddit(sub_name)
            
            # Fetch hot posts to capture active discussions
            for submission in subreddit.hot(limit=limit):
                # Filter by age
                if submission.created_utc < threshold_time:
                    continue
                
                # Check for pinned posts (sometimes stickied announcements are older)
                if submission.stickied:
                    continue
                    
                post_id = submission.id
                title = submission.title
                score = submission.score
                num_comments = submission.num_comments
                selftext = submission.selftext
                url = f"https://reddit.com{submission.permalink}"
                published_at = datetime.datetime.utcfromtimestamp(submission.created_utc).isoformat()
                
                # Get top comments
                submission.comment_sort = "top"
                submission.comments.replace_more(limit=0)  # Flatten comment tree, ignore 'load more'
                top_comments = []
                
                for comment in submission.comments[:3]:
                    # Ignore deleted/removed comments
                    if comment.body in ["[deleted]", "[removed]"]:
                        continue
                    # Truncate comment body if too long
                    body = comment.body[:300] + "..." if len(comment.body) > 300 else comment.body
                    top_comments.append(f"- {body}")
                
                comments_text = "\n".join(top_comments) if top_comments else "[No comments]"
                
                content = (
                    f"Subreddit: r/{sub_name}\n"
                    f"Score: {score} | Comments: {num_comments}\n\n"
                    f"Post Body:\n{selftext if selftext else '[Link Post / No Body Text]'}\n\n"
                    f"Top Comments:\n{comments_text}"
                )
                
                collected_posts.append({
                    "external_id": post_id,
                    "source": "reddit",
                    "title": title,
                    "content": content,
                    "url": url,
                    "published_at": published_at
                })
                
        except Exception as e:
            print(f"Error collecting from r/{sub_name}: {e}", file=sys.stderr)
            
    return collected_posts

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test Reddit Collector")
    parser.add_argument("--test", action="store_true", help="Run in test mode with fallback mock data")
    args = parser.parse_args()
    
    print("Starting Reddit Collector test...")
    posts = collect_reddit_news(lookback_hours=48, limit=10, test_mode=args.test)
    print(f"Collected {len(posts)} posts:")
    for p in posts:
        print(f"- [{p['source'].upper()}] r/{p['url'].split('/r/')[1].split('/')[0]} | {p['title']}")
        print(f"  URL: {p['url']}")
        print(f"  Content length: {len(p['content'])} characters")
        print("-" * 40)
