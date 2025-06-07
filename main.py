#!/usr/bin/env python3
"""
main.py

Overlay Reddit submission titles and selftext over gameplay footage with lofi music,
on-screen captions synced word-by-word to narration audio, using cached Polly.
"""
import sys
import os
import random
import textwrap
import yaml
from dotenv import load_dotenv
import praw
import boto3
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import (
    VideoFileClip,
    AudioFileClip,
    CompositeVideoClip,
    ImageClip,
    concatenate_videoclips,
    CompositeAudioClip,
    concatenate_audioclips
)

# Patch PIL.Image.ANTIALIAS for Pillow >=10
from PIL import Image as PILImage
try:
    filter = PILImage.Resampling.LANCZOS
except AttributeError:
    filter = getattr(PILImage, 'LANCZOS', 1)
setattr(PILImage, 'ANTIALIAS', filter)
if 'PIL.Image' in sys.modules:
    setattr(sys.modules['PIL.Image'], 'ANTIALIAS', filter)

# Configuration constants
VIDEOS_FOLDER = 'videos'
MUSIC_FOLDER = 'music'
AUDIO_CACHE = 'audio_cache'
OUTPUT_FOLDER = 'output'
MAX_TOTAL_DURATION = 180  # seconds

# Utility to read text files with LF normalization
def read_text_file(path, encoding='utf-8') -> str:
    data = open(path, 'rb').read()
    try:
        txt = data.decode('utf-8-sig')
    except UnicodeDecodeError:
        txt = data.decode(encoding, errors='ignore')
    return txt.replace('\r\n', '\n').replace('\r', '\n')

# Load YAML config
def load_config(path: str = 'config.yml') -> dict:
    content = read_text_file(path)
    return yaml.safe_load(content)

# Fetch top submissions (no comments)
def get_reddit_posts(reddit, subreddits, max_posts, min_upvotes):
    posts = []
    for sub in subreddits:
        for submission in reddit.subreddit(sub).top('week', limit=max_posts * 3):
            if submission.score >= min_upvotes and not submission.stickied:
                posts.append(submission)
                if len(posts) >= max_posts:
                    return posts
    return posts

# Synthesize or reuse cached speech, with chunking for long texts
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
    def _synth_chunk(chunk, fname):
        res = polly.synthesize_speech(Text=chunk, OutputFormat='mp3', VoiceId=os.getenv('AWS_POLLY_VOICE'))
        with open(fname, 'wb') as f:
            f.write(res['AudioStream'].read())
    # split by words preserving boundaries
    if len(text) <= max_chars:
        _synth_chunk(text, out_path)
    else:
        words = text.split()
        chunks = []
        cur = ''
        for word in words:
            if len(cur) + len(word) + 1 <= max_chars:
                cur += ' ' + word if cur else word
            else:
                chunks.append(cur)
                cur = word
        if cur:
            chunks.append(cur)
        temp_files = []
        for i, chunk in enumerate(chunks):
            tmp = out_path.replace('.mp3', f'_part{i}.mp3')
            _synth_chunk(chunk, tmp)
            temp_files.append(tmp)
        clips = [AudioFileClip(t) for t in temp_files]
        final = concatenate_audioclips(clips)
        final.write_audiofile(out_path)
        for t in temp_files:
            os.remove(t)

# Select and trim a gameplay clip of at least 'duration' seconds
def pick_gameplay_clip(duration: float) -> VideoFileClip:
    files = [os.path.join(VIDEOS_FOLDER, f) for f in os.listdir(VIDEOS_FOLDER) if f.endswith('.mp4')]
    random.shuffle(files)
    for path in files:
        clip = VideoFileClip(path).without_audio()
        if clip.duration >= duration:
            start = random.uniform(0, clip.duration - duration)
            return clip.subclip(start, start + duration)
        clip.close()
    raise RuntimeError(f'No gameplay video >= {duration}s found')

# Render centered text block using PIL onto transparent image
def render_text_image(text: str, size: tuple, font_name: str, font_size: int, color: str) -> np.ndarray:
    img = Image.new('RGBA', size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype(f'{font_name}.ttf', font_size)
    except IOError:
        font = ImageFont.load_default()
    # measure text bbox
    bbox = draw.textbbox((0, 0), text, font=font)
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = (size[0] - w) // 2
    y = (size[1] - h) // 2
    draw.text((x, y), text, font=font, fill=color)
    return np.array(img)

# Split clips into parts <= max_total and write files
def split_and_write_clips(clips, max_total: float, out_dir: str, fps: int):
    groups, cur, dur = [], [], 0
    for clip in clips:
        if dur + clip.duration <= max_total:
            cur.append(clip)
            dur += clip.duration
        else:
            groups.append(cur)
            cur, dur = [clip], clip.duration
    if cur:
        groups.append(cur)
    os.makedirs(out_dir, exist_ok=True)
    for idx, grp in enumerate(groups, 1):
        final = concatenate_videoclips(grp)
        final.write_videofile(
            os.path.join(out_dir, f'part{idx}.mp4'),
            fps=fps,
            codec='libx264',
            audio_codec='aac'
        )

# Main execution
def main():
    load_dotenv()
    cfg = load_config()
    reddit = praw.Reddit(
        client_id=os.getenv('REDDIT_CLIENT_ID'),
        client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
        username=os.getenv('REDDIT_USERNAME'),
        password=os.getenv('REDDIT_PASSWORD'),
        user_agent='TikTokVideoGen/1.0'
    )
    posts = get_reddit_posts(
        reddit,
        cfg['subreddits'],
        cfg['max_posts_per_run'],
        cfg['min_upvotes']
    )
    os.makedirs(AUDIO_CACHE, exist_ok=True)
    clips = []
    for post in posts:
        text = post.title
        if post.selftext:
            text += '\n\n' + post.selftext

        mp3_path = os.path.join(AUDIO_CACHE, f'{post.subreddit.display_name}_{post.id}.mp3')
        synthesize_speech(text, mp3_path)
        narration = AudioFileClip(mp3_path)

        gameplay = pick_gameplay_clip(narration.duration)
        gameplay = gameplay.resize(cfg['tiktok']['resolution'])

        # background music
        music_files = [os.path.join(MUSIC_FOLDER, f) for f in os.listdir(MUSIC_FOLDER) if f.lower().endswith(('.mp4', '.mp3'))]
        bg_audio = AudioFileClip(random.choice(music_files)).audio_loop(duration=narration.duration).volumex(0.3)
        final_audio = CompositeAudioClip([bg_audio, narration])

        # word-synced captions
        words = text.split()
        per = narration.duration / len(words)
        res = tuple(cfg['tiktok']['resolution'])
        style = cfg['style']
        caption_clips = []
        for i, word in enumerate(words):
            img_arr = render_text_image(word, res, style['font'], style['title_size'], style['text_color'])
            c = ImageClip(img_arr).set_start(i * per).set_duration(per)
            caption_clips.append(c)

        composite = CompositeVideoClip([gameplay] + caption_clips).set_audio(final_audio)
        clips.append(composite)

    split_and_write_clips(clips, MAX_TOTAL_DURATION, OUTPUT_FOLDER, cfg['tiktok']['frame_rate'])

if __name__ == '__main__':
    main()
