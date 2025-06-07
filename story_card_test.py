from PIL import Image, ImageDraw, ImageFont, ImageOps
import textwrap, os

def create_story_card(
    username: str,
    title: str,
    video_size=(1080, 1920),
    card_size=(800, 600),
    padding=30,
    # Avatar / verified
    avatar_path: str = None,
    avatar_size=80,
    is_verified: bool = False,
    verified_icon_path: str = None,
    verified_icon_size=40,
    # Awards (gold/silver/etc)
    reward_paths: list = None,
    reward_size=40,
    reward_spacing=10,
    # Bottom stats
    like_count: str = "0",
    comment_count: str = "0",
    heart_icon_path: str = None,
    comment_icon_path: str = None,
    stat_icon_size=30,
    stat_spacing=10,
    stat_text_padding=5,
    # Fonts
    font_path="arial.ttf",
    username_font_size=50,
    title_font_size=36,
    stat_font_size=28,
    # Output
    output_path="story_card_full.png"
):
    W, H = video_size
    CW, CH = card_size
    x0 = (W - CW) // 2
    y0 = (H - CH) // 4

    # Create canvas + rounded white card
    base = Image.new("RGBA", (W, H), (0,0,0,0))
    draw = ImageDraw.Draw(base)
    draw.rounded_rectangle([(x0, y0), (x0+CW, y0+CH)], radius=20, fill=(255,255,255,230))

    # Load fonts
    uname_fnt = ImageFont.truetype(font_path, username_font_size)
    title_fnt = ImageFont.truetype(font_path, title_font_size)
    stat_fnt  = ImageFont.truetype(font_path, stat_font_size)

    # Draw avatar
    text_x = x0 + padding
    if avatar_path and os.path.exists(avatar_path):
        av = Image.open(avatar_path).convert("RGBA").resize((avatar_size,avatar_size), Image.LANCZOS)
        mask = Image.new("L", av.size, 0)
        ImageDraw.Draw(mask).ellipse([(0,0), av.size], fill=255)
        base.paste(av, (x0+padding, y0+padding), mask)
        text_x += avatar_size + padding//2

    # Draw username
    uname_y = y0 + padding + (avatar_size - username_font_size)//2
    draw.text((text_x, uname_y), username, font=uname_fnt, fill=(0,0,0,255))

    # Verified badge (if any)
    if is_verified and verified_icon_path and os.path.exists(verified_icon_path):
        bbox = draw.textbbox((0,0), username, font=uname_fnt)
        uname_width = bbox[2] - bbox[0]
        vx = text_x + uname_width + stat_spacing
        vy = y0 + padding + (avatar_size - verified_icon_size)//2
        vc = Image.open(verified_icon_path).convert("RGBA").resize((verified_icon_size,verified_icon_size), Image.LANCZOS)
        base.paste(vc, (vx,vy), vc)
        reward_start_x = vx + verified_icon_size + reward_spacing
    else:
        bbox = draw.textbbox((0,0), username, font=uname_fnt)
        uname_width = bbox[2] - bbox[0]
        reward_start_x = text_x + uname_width + reward_spacing

    # Draw reward icons
    if reward_paths:
        rx = reward_start_x
        ry = y0 + padding + (avatar_size - reward_size)//2
        for p in reward_paths:
            if os.path.exists(p):
                ico = Image.open(p).convert("RGBA").resize((reward_size,reward_size), Image.LANCZOS)
                base.paste(ico, (rx,ry), ico)
                rx += reward_size + reward_spacing

    # Draw title text (wrapped)
    title_x = x0 + padding
    title_y = y0 + padding + avatar_size + padding//2
    max_w = CW - 2*padding
    char_bbox = draw.textbbox((0,0), "A", font=title_fnt)
    avg_char_w = char_bbox[2] - char_bbox[0]
    chars_per_line = max_w // avg_char_w
    lines = textwrap.wrap(title, width=chars_per_line)
    line_bbox = draw.textbbox((0,0), "Ay", font=title_fnt)
    lh = (line_bbox[3] - line_bbox[1]) + 8
    for i, line in enumerate(lines):
        draw.text((title_x, title_y + i*lh), line, font=title_fnt, fill=(0,0,0,255))

    # Draw bottom stats (heart + likes, comment + count)
    stats_y = y0 + CH - padding - stat_icon_size
    sx = x0 + padding
    if heart_icon_path and os.path.exists(heart_icon_path):
        heart = Image.open(heart_icon_path).convert("RGBA").resize((stat_icon_size,stat_icon_size), Image.LANCZOS)
        base.paste(heart, (sx, stats_y), heart)
    sx += stat_icon_size + stat_text_padding
    draw.text((sx, stats_y + ((draw.textbbox((0,0), "Ay", font=stat_fnt)[3] - draw.textbbox((0,0), "Ay", font=stat_fnt)[1] - stat_font_size)//2)), like_count, font=stat_fnt, fill=(0,0,0,255))
    like_bbox = draw.textbbox((0,0), like_count, font=stat_fnt)
    like_width = like_bbox[2] - like_bbox[0]
    sx += like_width + stat_spacing*2
    if comment_icon_path and os.path.exists(comment_icon_path):
        com = Image.open(comment_icon_path).convert("RGBA").resize((stat_icon_size,stat_icon_size), Image.LANCZOS)
        base.paste(com, (sx, stats_y), com)
    sx += stat_icon_size + stat_text_padding
    draw.text((sx, stats_y + ((draw.textbbox((0,0), "Ay", font=stat_fnt)[3] - draw.textbbox((0,0), "Ay", font=stat_fnt)[1] - stat_font_size)//2)), comment_count, font=stat_fnt, fill=(0,0,0,255))

    # Save PNG
    base.save(output_path)
    return base

if __name__ == "__main__":
    # Example call: adjust paths and parameters as needed
    card = create_story_card(
        username="redditstories_doggo",
        title="I am refusing to go to my brother's wedding because he won't tell me the reason his fiancé didn't invite me…",
        avatar_path="images/reddit_avatr.png",
        is_verified=True,
        verified_icon_path="icon_verified_blue.png",
        reward_paths=["images/gold.png", "images/platinum.png"],
        heart_icon_path="images/heart-icon.png",
        comment_icon_path="images/comment-icon.png",
        like_count="99+",
        comment_count="99+",
        font_path="images/Roboto-Regular.ttf",
        output_path="story_card_full.png"
    )
    # Display the generated image
    card.show()