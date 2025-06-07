# reddit_test.py
from dotenv import load_dotenv
import os, yaml
import praw

# 1. Load your .env
load_dotenv()

# 2. Load config (to get at least one subreddit)
cfg = yaml.safe_load(open("config.yml"))
subreddits = cfg.get("subreddits", [])

# 3. Initialize PRAW
reddit = praw.Reddit(
    client_id=os.getenv("REDDIT_CLIENT_ID"),
    client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
    username=os.getenv("REDDIT_USERNAME"),
    password=os.getenv("REDDIT_PASSWORD"),
    user_agent="reddit_test/1.0"
)

# 4. Fetch & print a few hot posts
if not subreddits:
    print("No subreddits defined in config.yml")
else:
    sr = subreddits[0]
    print(f"Fetching top 3 hot posts from r/{sr}…\n")
    for post in reddit.subreddit(sr).hot(limit=3):
        print(f"• {post.title!r}")
        print(f"    by u/{post.author} — {post.score} upvotes, {post.total_awards_received} awards")
        print()
