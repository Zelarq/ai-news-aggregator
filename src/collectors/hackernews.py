import sys
import re
import time
import datetime
import argparse
import json
import urllib.request

# ---------------------------------------------------------------------------
# AI relevance filter — titles containing any of these keywords are collected
# ---------------------------------------------------------------------------
AI_KEYWORDS = [
    "llm", "gpt", "claude", "gemini", "llama", "mistral", "ollama",
    "openai", "anthropic", "deepmind", "hugging face", "huggingface",
    "transformer", "neural", "diffusion", "stable diffusion",
    "reinforcement learning", "fine-tun", "embedding", "vector",
    "artificial intelligence", " ai ", "machine learning", "deep learning",
    "language model", "multimodal", "rag", "agent", "copilot",
    "midjourney", "sora", "runway", "flux", "imagen",
    "benchmark", "inference", "quantiz", "lora", "qlora",
    "pytorch", "tensorflow", "jax", "cuda", "tpu",
]

HN_BASE_URL = "https://hacker-news.firebaseio.com/v0"


def _safe_print(msg: str, file=None):
    """Prints a string, replacing unencodable characters to avoid Windows console crashes."""
    target = file if file is not None else sys.stdout
    try:
        print(msg, file=target)
    except UnicodeEncodeError:
        encoding = getattr(target, 'encoding', None) or 'ascii'
        safe = msg.encode(encoding, errors='replace').decode(encoding)
        print(safe, file=target)


def _hn_get(path: str, timeout: int = 8):
    """Makes a GET request to the HN Firebase API and returns parsed JSON."""
    url = f"{HN_BASE_URL}{path}"
    with urllib.request.urlopen(url, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _is_ai_related(title: str) -> bool:
    """Returns True if the story title contains any AI-related keyword."""
    lower = title.lower()
    return any(kw in lower for kw in AI_KEYWORDS)


def _fetch_top_comment_text(comment_ids: list, max_comments: int = 3) -> str:
    """
    Fetches the text of the top N comments for a story.
    Skips deleted/dead comments gracefully.
    """
    texts = []
    for cid in comment_ids[:max_comments * 2]:  # Fetch extras in case some are dead
        if len(texts) >= max_comments:
            break
        try:
            comment = _hn_get(f"/item/{cid}.json")
            if not comment or comment.get("deleted") or comment.get("dead"):
                continue
            raw = comment.get("text", "").strip()
            if not raw:
                continue
            # Strip HTML tags (HN returns basic HTML)
            clean = re.sub(r"<[^>]+>", " ", raw).strip()
            clean = re.sub(r"\s+", " ", clean)
            if len(clean) > 300:
                clean = clean[:297] + "..."
            texts.append(f"- {clean}")
        except Exception:
            continue
    return "\n".join(texts) if texts else "[No comments available]"


def collect_hn_news(lookback_hours: int = 24, max_stories: int = 30, test_mode: bool = False):
    """
    Fetches AI-relevant top stories from Hacker News using the public Firebase API.
    No API key required.

    Args:
        lookback_hours: Only return stories published within this many hours.
        max_stories: Maximum number of story IDs to scan from the top stories list.
        test_mode: If True, returns mock data without hitting the real API.

    Returns:
        List of item dicts compatible with the pipeline schema.
    """
    if test_mode:
        print("Warning: HN collector running in test mode. Returning mock HN data.")
        return [
            {
                "external_id": "hn_test_story_001",
                "source": "hackernews",
                "title": "Show HN: I built a local AI news aggregator using Ollama and SQLite",
                "content": (
                    "Points: 342 | Comments: 87 | Author: hn_user_42\n\n"
                    "Post URL: https://github.com/example/ai-news-agent\n\n"
                    "Top Comments:\n"
                    "- Great project! I've been looking for something like this for ages. "
                    "The Ollama integration is clever.\n"
                    "- Does it support custom RSS feeds? Would love to add ML papers.\n"
                    "- How does it handle deduplication across sources?"
                ),
                "url": "https://news.ycombinator.com/item?id=40000001",
                "published_at": (
                    datetime.datetime.utcnow() - datetime.timedelta(hours=3)
                ).isoformat(),
            },
            {
                "external_id": "hn_test_story_002",
                "source": "hackernews",
                "title": "Anthropic releases Claude 3.7 with extended thinking mode",
                "content": (
                    "Points: 1204 | Comments: 231 | Author: hn_user_99\n\n"
                    "Post URL: https://www.anthropic.com/news/claude-3-7\n\n"
                    "Top Comments:\n"
                    "- The extended thinking traces are genuinely impressive on math.\n"
                    "- Benchmarks look great but real-world coding is still hit-or-miss.\n"
                    "- I wonder how this compares to o3 mini on AIME."
                ),
                "url": "https://news.ycombinator.com/item?id=40000002",
                "published_at": (
                    datetime.datetime.utcnow() - datetime.timedelta(hours=5)
                ).isoformat(),
            },
        ]

    print(f"Fetching top {max_stories} HN story IDs...")
    try:
        top_ids = _hn_get("/topstories.json")[:max_stories]
    except Exception as e:
        _safe_print(f"HN Collector: Failed to fetch top stories list: {e}", file=sys.stderr)
        return []

    threshold_ts = time.time() - (lookback_hours * 3600)
    collected = []

    for story_id in top_ids:
        try:
            item = _hn_get(f"/item/{story_id}.json")
            if not item or item.get("type") != "story":
                continue
            if item.get("dead") or item.get("deleted"):
                continue

            title = item.get("title", "").strip()
            if not title or not _is_ai_related(title):
                continue

            created_ts = item.get("time", 0)
            if created_ts < threshold_ts:
                continue

            published_at = datetime.datetime.utcfromtimestamp(created_ts).isoformat()
            score = item.get("score", 0)
            author = item.get("by", "unknown")
            num_comments = item.get("descendants", 0)
            story_url = item.get("url", f"https://news.ycombinator.com/item?id={story_id}")
            hn_url = f"https://news.ycombinator.com/item?id={story_id}"
            comment_ids = item.get("kids", [])

            _safe_print(f"  Found: '{title}' ({score} pts, {num_comments} comments)")
            comment_text = _fetch_top_comment_text(comment_ids)

            content = (
                f"Points: {score} | Comments: {num_comments} | Author: {author}\n\n"
                f"Post URL: {story_url}\n\n"
                f"Top Comments:\n{comment_text}"
            )

            collected.append({
                "external_id": f"hn_{story_id}",
                "source": "hackernews",
                "title": title,
                "content": content,
                "url": hn_url,
                "published_at": published_at,
            })

        except Exception as e:
            _safe_print(f"  Skipping story {story_id}: {e}", file=sys.stderr)
            continue

    print(f"HN Collector: Found {len(collected)} AI-relevant stories.")
    return collected


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test Hacker News Collector")
    parser.add_argument("--test", action="store_true", help="Run in test mode with mock data")
    parser.add_argument("--lookback", type=int, default=24, help="Hours to look back (default: 24)")
    parser.add_argument("--max", type=int, default=50, help="Max stories to scan (default: 50)")
    args = parser.parse_args()

    print("Starting Hacker News Collector test...")
    stories = collect_hn_news(lookback_hours=args.lookback, max_stories=args.max, test_mode=args.test)
    print(f"\nCollected {len(stories)} stories:")
    for s in stories:
        print(f"  [{s['source'].upper()}] {s['title']}")
        print(f"    URL: {s['url']}")
        print(f"    Published: {s['published_at']}")
        print(f"    Content length: {len(s['content'])} chars")
        print("-" * 50)
