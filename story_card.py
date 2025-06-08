from PIL import Image, ImageDraw, ImageFont, ImageOps
import textwrap, os, sys

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

    # Draw title text with adaptive scaling to fill space
    title_x = x0 + padding
    title_y = y0 + padding + avatar_size + padding//2
    max_text_w = CW - 2*padding
    max_text_h = CH - avatar_size - 3*padding - stat_icon_size

    # Initial wrap by approx char count
    char_w = draw.textbbox((0,0), "A", font=title_fnt)[2]
    chars_per_line = max(10, max_text_w // char_w)
    lines = textwrap.wrap(title, width=chars_per_line)

    # Calculate current text block size
    lh = draw.textbbox((0,0), "Ay", font=title_fnt)[3] - draw.textbbox((0,0), "Ay", font=title_fnt)[1] + 8
    total_h = lh * len(lines)
    line_widths = [draw.textbbox((0,0), line, font=title_fnt)[2] for line in lines] if lines else [0]
    total_w = max(line_widths)

    # Determine scaling factors
    scale_w = (max_text_w * 0.9) / total_w if total_w>0 else 1.0
    scale_h = (max_text_h * 0.9) / total_h if total_h>0 else 1.0
    scale = min(scale_w, scale_h, 1.0)

    # Scale font if needed
    if scale < 1.0 or total_w < max_text_w * 0.8:
        new_size = max(12, min(int(title_font_size * scale * 1.2), title_font_size*2))
        title_fnt = ImageFont.truetype(font_path, new_size)
        # recompute lines and metrics
        char_w = draw.textbbox((0,0), "A", font=title_fnt)[2]
        chars_per_line = max(10, max_text_w // char_w)
        lines = textwrap.wrap(title, width=chars_per_line)
        lh = draw.textbbox((0,0), "Ay", font=title_fnt)[3] - draw.textbbox((0,0), "Ay", font=title_fnt)[1] + 8

    # Draw lines centered vertically in available area
    cur_h = lh * len(lines)
    start_y = title_y + (max_text_h - cur_h)//2
    for i, line in enumerate(lines):
        draw.text((title_x, start_y + i*lh), line, font=title_fnt, fill=(0,0,0,255))

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