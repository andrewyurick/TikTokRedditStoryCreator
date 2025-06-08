#!/usr/bin/env python3
"""
main.py

Generate TikTok videos by overlaying top Reddit submissions over gameplay footage
with lofi music and AI narration (cached). Displays a story card overlay for the first 5 seconds.
"""
import os
import random
import yaml
from dotenv import load_dotenv
import praw
import boto3
from PIL import Image
# Patch PIL.Image.ANTIALIAS for compatibility
if not hasattr(Image, 'ANTIALIAS'):
    try:
        Image.ANTIALIAS = Image.Resampling.LANCZOS
    except Exception:
        Image.ANTIALIAS = getattr(Image, 'LANCZOS', 1)

from moviepy.editor import (
    VideoFileClip,
    AudioFileClip,
    CompositeAudioClip,
    concatenate_videoclips,
    ImageClip,
    CompositeVideoClip
)
from story_card import create_story_card

# Configuration
VIDEOS_FOLDER = 'videos'
MUSIC_FOLDER = 'music'
AUDIO_CACHE = 'audio_cache'
OUTPUT_FOLDER = 'output'
MAX_TOTAL_DURATION = 180  # seconds
CARD_DURATION = 5         # seconds overlay duration
CARD_SCALE = 0.75         # scale relative to video resolution

# Load YAML config
def load_config(path='config.yml') -> dict:
    load_dotenv()
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

# Fetch top submissions only (no comments)
def get_reddit_posts(reddit, subs, max_posts, min_upvotes):
    posts = []
    for sub in subs:
        for submission in reddit.subreddit(sub).top('week', limit=max_posts * 3):
            if submission.score >= min_upvotes and not submission.stickied:
                posts.append(submission)
                if len(posts) >= max_posts:
                    return posts
    return posts

# Synthesize speech with caching and manage Polly limits
def synthesize_speech(text: str, out_path: str):
    if os.path.exists(out_path):
        return
    polly = boto3.client(
        'polly',
        region_name=os.getenv('AWS_REGION'),
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
    )
    max_chars = 3000
    def _synth(chunk, fname):
        resp = polly.synthesize_speech(Text=chunk, OutputFormat='mp3', VoiceId=os.getenv('AWS_POLLY_VOICE'))
        with open(fname, 'wb') as f:
            f.write(resp['AudioStream'].read())
    if len(text) <= max_chars:
        _synth(text, out_path)
    else:
        words = text.split()
        chunks, cur = [], ''
        for w in words:
            if len(cur) + len(w) + 1 <= max_chars:
                cur = (cur + ' ' + w).strip()
            else:
                chunks.append(cur)
                cur = w
        if cur:
            chunks.append(cur)
        temp_paths = []
        for i, c in enumerate(chunks):
            part = out_path.replace('.mp3', f'_part{i}.mp3')
            _synth(c, part)
            temp_paths.append(part)
        audio_clips = [AudioFileClip(p) for p in temp_paths]
        combined = CompositeAudioClip(audio_clips)
        combined.write_audiofile(out_path)
        for p in temp_paths:
            os.remove(p)

# Select and trim gameplay clip for narration duration
def pick_gameplay_clip(duration: float) -> VideoFileClip:
    candidates = [os.path.join(VIDEOS_FOLDER, f) for f in os.listdir(VIDEOS_FOLDER) if f.lower().endswith('.mp4')]
    random.shuffle(candidates)
    for path in candidates:
        clip = VideoFileClip(path).without_audio()
        if clip.duration >= duration:
            start = random.uniform(0, clip.duration - duration)
            return clip.subclip(start, start + duration)
        clip.close()
    raise RuntimeError(f'No gameplay video >= {duration}s found')

# Split and write video parts <= MAX_TOTAL_DURATION
def split_and_write_clips(clips, max_duration: float, out_dir: str, fps: int):
    groups, current, total = [], [], 0
    for clip in clips:
        if total + clip.duration <= max_duration:
            current.append(clip)
            total += clip.duration
        else:
            groups.append(current)
            current, total = [clip], clip.duration
    if current:
        groups.append(current)
    os.makedirs(out_dir, exist_ok=True)
    for idx, grp in enumerate(groups, 1):
        final = concatenate_videoclips(grp)
        out_path = os.path.join(out_dir, f'part{idx}.mp4')
        final.write_videofile(out_path, fps=fps, codec='libx264', audio_codec='aac')

# Main execution
def main():
    cfg = load_config()
    reddit = praw.Reddit(
        client_id=os.getenv('REDDIT_CLIENT_ID'),
        client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
        username=os.getenv('REDDIT_USERNAME'),
        password=os.getenv('REDDIT_PASSWORD'),
        user_agent='TikTokVideoGen/1.0'
    )
    posts = get_reddit_posts(reddit, cfg['subreddits'], cfg['max_posts_per_run'], cfg['min_upvotes'])
    os.makedirs(AUDIO_CACHE, exist_ok=True)
    final_clips = []
    for post in posts:
        # Generate story card overlay
        card_path = os.path.join(AUDIO_CACHE, f"{post.id}_card.png")
        create_story_card(
             username="redditstories_doggo",
            title=post.title,
           avatar_path="images/reddit_avatr.png",
            is_verified=True,
            verified_icon_path="icon_verified_blue.png",
            reward_paths=["images/reddit_gold.png", "images/reddit_platinum.png"],
            heart_icon_path="images/heart-icon.png",
            comment_icon_path="images/comment-icon.png",
            like_count="99+",
            comment_count="99+",
            font_path="images/Roboto-Regular.ttf",
            output_path=card_path
        )
        # Synthesize narration
        text = post.title + ("\n\n" + post.selftext if post.selftext else "")
        mp3_path = os.path.join(AUDIO_CACHE, f"{post.subreddit.display_name}_{post.id}.mp3")
        synthesize_speech(text, mp3_path)
        # bump the AI narration up by ~20%
        narration = AudioFileClip(mp3_path).volumex(1.2)

        # Prepare gameplay and audio
        gameplay = pick_gameplay_clip(narration.duration)
        gameplay = gameplay.resize(tuple(cfg['tiktok']['resolution']))
        music_list = [os.path.join(MUSIC_FOLDER, f) for f in os.listdir(MUSIC_FOLDER) if f.lower().endswith(('.mp4','.mp3'))]
        bg_audio = AudioFileClip(random.choice(music_list)).audio_loop(duration=narration.duration).volumex(0.15)
        combined_audio = CompositeAudioClip([bg_audio, narration])
        # Create overlay clip
        card_clip = ImageClip(card_path)
        vid_w, vid_h = cfg['tiktok']['resolution']
        card_clip = card_clip.set_duration(CARD_DURATION)
        # scale to 75% of video size
        card_clip = card_clip.resize(height=int(vid_h * CARD_SCALE))
        card_clip = card_clip.set_position(('center','center'))
        # Composite gameplay under card overlay
        comp = CompositeVideoClip([gameplay.set_audio(combined_audio), card_clip], size=(vid_w, vid_h))
        final_clips.append(comp)
    # Split and write
    split_and_write_clips(final_clips, MAX_TOTAL_DURATION, OUTPUT_FOLDER, cfg['tiktok']['frame_rate'])

if __name__ == '__main__':
    main()
