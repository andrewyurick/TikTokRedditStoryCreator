from PIL import Image, ImageDraw, ImageFont, ImageOps
import textwrap, os
import sys

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
        try:
            av = Image.open(avatar_path).convert("RGBA").resize((avatar_size,avatar_size), Image.LANCZOS)
            mask = Image.new("L", av.size, 0)
            ImageDraw.Draw(mask).ellipse([(0,0), av.size], fill=255)
            base.paste(av, (text_x, y0+padding), mask)
            text_x += avatar_size + padding//2
        except Exception as e:
            print(f"Warning: could not load avatar '{avatar_path}': {e}", file=sys.stderr)

    # Draw username
    uname_y = y0 + padding + (avatar_size - username_font_size)//2
    draw.text((text_x, uname_y), username, font=uname_fnt, fill=(0,0,0,255))

    # Measure username width
    uname_bbox = draw.textbbox((0,0), username, font=uname_fnt)
    uname_w = uname_bbox[2] - uname_bbox[0]

    # Draw verified badge
    offset_x = text_x + uname_w
    if is_verified and verified_icon_path and os.path.exists(verified_icon_path):
        try:
            offset_x += stat_spacing
            vy = y0 + padding + (avatar_size - verified_icon_size)//2
            vc = Image.open(verified_icon_path).convert("RGBA").resize((verified_icon_size,verified_icon_size), Image.LANCZOS)
            base.paste(vc, (offset_x, vy), vc)
            offset_x += verified_icon_size
        except Exception as e:
            print(f"Warning: could not load verified icon '{verified_icon_path}': {e}", file=sys.stderr)

    # Start rewards after verified badge/username
    offset_x += reward_spacing
    if reward_paths:
        ry = y0 + padding + (avatar_size - reward_size)//2
        for p in reward_paths:
            if os.path.exists(p):
                try:
                    ico = Image.open(p).convert("RGBA").resize((reward_size,reward_size), Image.LANCZOS)
                    base.paste(ico, (offset_x, ry), ico)
                    offset_x += reward_size + reward_spacing
                except Exception as e:
                    print(f"Warning: could not load reward icon '{p}': {e}", file=sys.stderr)

    # Draw title text (wrapped)
    title_x = x0 + padding
    title_y = y0 + padding + avatar_size + padding//2
    max_w = CW - 2*padding
    # wrap by char count approximation
    char_width = draw.textbbox((0,0), "A", font=title_fnt)[2]
    wrap_chars = max(10, max_w // char_width)
    lines = textwrap.wrap(title, width=wrap_chars)
    # scale title font if too short
    if lines:
        widths = [draw.textbbox((0,0), ln, font=title_fnt)[2] for ln in lines]
        max_line = max(widths)
        if max_line < max_w * 0.8:
            scale = (max_w*0.8) / max_line
            new_size = min(int(title_font_size * scale), title_font_size*2)
            title_fnt = ImageFont.truetype(font_path, new_size)
    lh = (draw.textbbox((0,0), "Ay", font=title_fnt)[3] - draw.textbbox((0,0), "Ay", font=title_fnt)[1]) + 8
    for i, line in enumerate(lines):
        draw.text((title_x, title_y + i*lh), line, font=title_fnt, fill=(0,0,0,255))

    # Draw bottom stats
    stats_y = y0 + CH - padding - stat_icon_size
    sx = x0 + padding
    if heart_icon_path and os.path.exists(heart_icon_path):
        try:
            heart = Image.open(heart_icon_path).convert("RGBA").resize((stat_icon_size,stat_icon_size), Image.LANCZOS)
            base.paste(heart, (sx, stats_y), heart)
        except Exception as e:
            print(f"Warning: could not load heart icon '{heart_icon_path}': {e}", file=sys.stderr)
    sx += stat_icon_size + stat_text_padding
    stat_h = draw.textbbox((0,0), "Ay", font=stat_fnt)[3] - draw.textbbox((0,0), "Ay", font=stat_fnt)[1]
    text_offset = (stat_h - stat_font_size)//2
    draw.text((sx, stats_y + text_offset), like_count, font=stat_fnt, fill=(0,0,0,255))
    like_w = draw.textbbox((0,0), like_count, font=stat_fnt)[2]
    sx += like_w + stat_spacing*2
    if comment_icon_path and os.path.exists(comment_icon_path):
        try:
            com = Image.open(comment_icon_path).convert("RGBA").resize((stat_icon_size,stat_icon_size), Image.LANCZOS)
            base.paste(com, (sx, stats_y), com)
        except Exception as e:
            print(f"Warning: could not load comment icon '{comment_icon_path}': {e}", file=sys.stderr)
    sx += stat_icon_size + stat_text_padding
    draw.text((sx, stats_y + text_offset), comment_count, font=stat_fnt, fill=(0,0,0,255))

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
        reward_paths=["images/reddit_gold.png", "images/reddit_platinum.png"],
        heart_icon_path="images/heart-icon.png",
        comment_icon_path="images/comment-icon.png",
        like_count="99+",
        comment_count="99+",
        font_path="images/Roboto-Regular.ttf",
        output_path="story_card_full.png"
    )
    # Display the generated image
    card.show()