import sys
import argparse
import datetime
import logging
from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi
from src.config import Config

# Curated list of AI YouTube Channels (Name: Channel ID)
AI_CHANNELS = {
    "Google DeepMind": "UC0rquc1614sgfspwPudfT8w",
    "OpenAI": "UC1P2zW21QeA_C673wS2sR-w",
    "Anthropic": "UCrVv_a9v00oB95t8S-7K4gw",
    "Andrej Karpathy": "UCOi5701YJUXYiSdXOq84N4g",
    "AI Explained": "UC295-Dw_tDNt3KtiZ56E24Q",
    "Yannic Kilcher": "UCZHmUTtLge5y0nR8j--C54A",
    "Two Minute Papers": "UCbfYPyITQ-7qOwJHjsPM5sg",
    "Sentdex": "UCfzlCWGWYyIQ0aLC5w7Us1A",
    "Wes Roth": "UC8wGs6n16g7VAMz8_x_e4wA",
    "Matt Wolfe": "UCtS6G47_S7SpwP1s1u1x9dw"
}

def get_uploads_playlist_id(channel_id):
    """
    Deterministically replaces the second character of the channel ID with a 'U'
    to get the uploads playlist ID. This saves API quota.
    Example: UC0rquc1614sgfspwPudfT8w -> UU0rquc1614sgfspwPudfT8w
    """
    if len(channel_id) >= 2 and channel_id.startswith("UC"):
        return "UU" + channel_id[2:]
    return channel_id

def fetch_transcript(video_id):
    """
    Fetches the transcript text for a video using youtube-transcript-api.
    Returns transcript text if successful, or an explanation string if failed.
    """
    try:
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        transcript_text = " ".join([entry['text'] for entry in transcript_list])
        return transcript_text
    except Exception as e:
        return f"[Transcript unavailable: {str(e)}]"

def collect_youtube_news(lookback_hours=24, test_mode=False):
    """
    Fetches videos from selected AI channels published in the last `lookback_hours` hours.
    If test_mode is True, it will run using mock logic or print API warnings if key is missing.
    """
    if not Config.YOUTUBE_API_KEY:
        if test_mode:
            print("Warning: YOUTUBE_API_KEY is not set. Returning mock YouTube data for testing.")
            return [
                {
                    "external_id": "test_video_123",
                    "source": "youtube",
                    "title": "GPT-5 Announcement and Architecture Discussion",
                    "content": "Today we are looking at the new announcement of the model details. It features 20 trillion parameters and runs natively on local devices.",
                    "url": "https://www.youtube.com/watch?v=test_video_123",
                    "published_at": (datetime.datetime.utcnow() - datetime.timedelta(hours=2)).isoformat()
                }
            ]
        else:
            logging.warning("YOUTUBE_API_KEY is not set. Skipping YouTube collector.")
            return []

    # Initialize YouTube client
    youtube = build("youtube", "v3", developerKey=Config.YOUTUBE_API_KEY)
    
    now = datetime.datetime.utcnow()
    time_threshold = now - datetime.timedelta(hours=lookback_hours)
    
    collected_videos = []
    
    for channel_name, channel_id in AI_CHANNELS.items():
        uploads_playlist_id = get_uploads_playlist_id(channel_id)
        
        try:
            # Get latest items from uploads playlist
            request = youtube.playlistItems().list(
                playlistId=uploads_playlist_id,
                part="snippet",
                maxResults=5
            )
            response = request.execute()
            
            for item in response.get("items", []):
                snippet = item.get("snippet", {})
                published_at_str = snippet.get("publishedAt")
                if not published_at_str:
                    continue
                
                # Parse YouTube datetime (e.g. 2023-10-27T16:00:00Z)
                published_at = datetime.datetime.strptime(published_at_str, "%Y-%m-%dT%H:%M:%SZ")
                
                if published_at >= time_threshold:
                    video_id = snippet.get("resourceId", {}).get("videoId")
                    if not video_id:
                        continue
                    
                    title = snippet.get("title")
                    video_url = f"https://www.youtube.com/watch?v={video_id}"
                    
                    print(f"Fetching transcript for YouTube video: '{title}' from {channel_name}...")
                    transcript = fetch_transcript(video_id)
                    
                    collected_videos.append({
                        "external_id": video_id,
                        "source": "youtube",
                        "title": title,
                        "content": f"Channel: {channel_name}\n\nTranscript:\n{transcript}",
                        "url": video_url,
                        "published_at": published_at_str
                    })
                    
        except Exception as e:
            print(f"Error collecting from channel {channel_name} ({channel_id}): {e}", file=sys.stderr)
            
    return collected_videos

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test YouTube Collector")
    parser.add_argument("--test", action="store_true", help="Run in test mode with fallback mock data")
    args = parser.parse_args()
    
    print("Starting YouTube Collector test...")
    videos = collect_youtube_news(lookback_hours=48, test_mode=args.test)
    print(f"Collected {len(videos)} videos:")
    for v in videos:
        print(f"- [{v['source'].upper()}] {v['title']} (Published: {v['published_at']})")
        print(f"  URL: {v['url']}")
        print(f"  Content length: {len(v['content'])} characters")
        print("-" * 40)
