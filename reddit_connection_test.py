# reddit_test.py
# Standalone script to verify Reddit connection and fetch top posts.

import os
import time
import yaml
from dotenv import load_dotenv
import praw


def load_config():
    """
    Load subreddit list and thresholds from config.yml, secrets from .env
    """
    load_dotenv()  # loads REDDIT_* vars
    config = yaml.safe_load(open("config.yml"))
    secrets = {
        'reddit_client_id': os.getenv('REDDIT_CLIENT_ID'),
        'reddit_client_secret': os.getenv('REDDIT_CLIENT_SECRET'),
        'reddit_username': os.getenv('REDDIT_USERNAME'),
        'reddit_password': os.getenv('REDDIT_PASSWORD'),
    }
    return config, secrets


def init_reddit(secrets):
    """
    Initialize PRAW Reddit client
    """
    return praw.Reddit(
        client_id=secrets['reddit_client_id'],
        client_secret=secrets['reddit_client_secret'],
        username=secrets['reddit_username'],
        password=secrets['reddit_password'],
        user_agent="reddit_test/1.0"
    )


def fetch_top_posts(reddit, config):
    """
    Fetch recent hot posts from configured subreddits, filtered by upvotes, age, and collect metadata.
    """
    posts = []
    now = time.time()
    one_week_ago = now - 7 * 24 * 3600
    threshold = config.get('min_upvotes', 1000)
    max_posts = config.get('max_posts_per_run', 3)

    for subreddit in config['subreddits']:
        for submission in reddit.subreddit(subreddit).hot(limit=20):
            if submission.score >= threshold and submission.created_utc >= one_week_ago:
                posts.append({
                    'title': submission.title,
                    'author': str(submission.author),
                    'subreddit': subreddit,
                    'score': submission.score,
                    'awards': submission.total_awards_received,
                    'url': f"https://reddit.com{submission.permalink}"
                })
            if len(posts) >= max_posts:
                break
        if len(posts) >= max_posts:
            break
    return posts


if __name__ == '__main__':
    config, secrets = load_config()
    reddit = init_reddit(secrets)
    posts = fetch_top_posts(reddit, config)

    if not posts:
        print("No posts found with the specified filters.")
    else:
        print("Top Reddit posts fetched:\n")
        for p in posts:
            print(f"- {p['title']} by u/{p['author']} in r/{p['subreddit']}")
            print(f"    👍 {p['score']}  🎖️ {p['awards']}  🔗 {p['url']}\n")
