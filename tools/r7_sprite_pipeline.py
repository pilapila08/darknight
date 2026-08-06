# -*- coding: utf-8 -*-
"""R7 sprite 后处理流水线（r7_sprite_pipeline，PIL 版）。

针对 R7 P1 四套 sprite 重绘（boss_corpse_king / boss_shadow_mage / shadow / voidling）。
世界实体（非 FX），必须保留浓黑描边 anchor ① → 用浅底亮度抠图（保留暗主体+黑描边）。

与 ai_sprite_pipeline.py 的差异：
- 输入：两张候选（frame1 基础 + frame2 动作极点），不是单张 wobble
- 输出：[frame1, frame2, frame1] 横向 sprite sheet（loader 切帧正常）
- Boss body 占比 ≥90%（目标像素更高），召唤怪 80%

用法：python tools/r7_sprite_pipeline.py
输出：design/art/ai-samples/r7-<entity>/r7_<entity>.png（288×96 / 48×16，RGBA）
"""
import glob
import os

from PIL import Image

BASE = os.path.join("design", "art", "ai-samples")
BG_THRESHOLD = 45  # 与 ai_sprite_pipeline.py 同款：与背景色距离 < 此值 → 透明


def luminance(r, g, b):
    return 0.299 * r + 0.587 * g + 0.114 * b


def estimate_bg(img):
    """四角均值估计背景色（RGB）。"""
    px = img.load()
    w, h = img.size
    pts = [(5, 5), (w - 6, 5), (5, h - 6), (w - 6, h - 6)]
    vals = [(r, g, b) for (r, g, b, _) in (px[x, y] for (x, y) in pts)]
    return tuple(sum(c[i] for c in vals) / len(vals) for i in range(3))


def crop_watermark_strip(img, crop_right=0.17, crop_bottom=0.10):
    """从右下角裁掉水印 strip。"""
    w, h = img.size
    new_w = int(w * (1.0 - crop_right))
    new_h = int(h * (1.0 - crop_bottom))
    return img.crop((0, 0, new_w, new_h))


def matte_light_bg(img, threshold=BG_THRESHOLD):
    """浅底亮度抠图：与背景色距离 < threshold → alpha=0（保留暗主体+黑描边）。
    输入应为浅灰底；输出 RGBA。"""
    img = img.convert("RGBA")
    bg = estimate_bg(img)
    bg_r, bg_g, bg_b = int(bg[0]), int(bg[1]), int(bg[2])
    px = img.load()
    w, h = img.size
    out_data = []
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            dist = max(abs(r - bg_r), abs(g - bg_g), abs(b - bg_b))
            if dist < threshold:
                out_data.append((0, 0, 0, 0))
            else:
                out_data.append((r, g, b, 255))
    out = Image.new("RGBA", (w, h))
    out.putdata(out_data)
    return out


def bbox_crop_to_frame(img, frame_size, body_fill=0.80):
    """bbox 裁主体 → 等比缩放到 frame_size，居中（保留 body_fill 比例留 1-2px 透明外缘）。"""
    bbox = img.getbbox()
    if not bbox:
        return Image.new("RGBA", (frame_size, frame_size), (0, 0, 0, 0))
    crop = img.crop(bbox)
    cw, ch = crop.size
    scale = min((frame_size * body_fill) / cw, (frame_size * body_fill) / ch)
    new_w = max(1, int(cw * scale))
    new_h = max(1, int(ch * scale))
    scaled = crop.resize((new_w, new_h), Image.NEAREST)
    canvas = Image.new("RGBA", (frame_size, frame_size), (0, 0, 0, 0))
    canvas.paste(scaled, ((frame_size - new_w) // 2, (frame_size - new_h) // 2), scaled)
    return canvas


def compose_3frames(frames, frame_size):
    """横向合成 3 帧 sprite sheet。"""
    sheet = Image.new("RGBA", (frame_size * 3, frame_size), (0, 0, 0, 0))
    for i, f in enumerate(frames):
        sheet.paste(f, (i * frame_size, 0), f)
    return sheet


def process_frame(raw_path, frame_size, body_fill):
    """单帧处理：crop → matte → bbox+scale → 返回。"""
    img = Image.open(raw_path)
    cropped = crop_watermark_strip(img)
    matted = matte_light_bg(cropped)
    return bbox_crop_to_frame(matted, frame_size, body_fill)


def find_raw(raw_dir, prefix):
    matches = sorted(glob.glob(os.path.join(raw_dir, f"{prefix}*.png")))
    return matches[-1] if matches else None


# 实体配置：(目录名, frame_size, body_fill, raw1_dir, raw2_dir)
ENTITIES = {
    "corpse_king":  {"frame_size": 96, "body_fill": 0.90, "raw1": "r7-corpse-king/raw",  "raw2": "r7-corpse-king/raw2"},
    "shadow_mage":  {"frame_size": 96, "body_fill": 0.90, "raw1": "r7-shadow-mage/raw",  "raw2": "r7-shadow-mage/raw2"},
    "shadow":       {"frame_size": 16, "body_fill": 0.85, "raw1": "r7-shadow/raw",       "raw2": "r7-shadow/raw2"},
    "voidling":     {"frame_size": 16, "body_fill": 0.85, "raw1": "r7-voidling/raw",     "raw2": "r7-voidling/raw2"},
}


def main():
    results = []
    for entity, cfg in ENTITIES.items():
        fs = cfg["frame_size"]
        raw1_dir = os.path.join(BASE, cfg["raw1"])
        raw2_dir = os.path.join(BASE, cfg["raw2"])
        out_dir = os.path.dirname(raw1_dir)  # r7-<entity>/
        os.makedirs(out_dir, exist_ok=True)

        f1_path = find_raw(raw1_dir, "pixel_art")
        f2_path = find_raw(raw2_dir, "pixel_art")
        if not f1_path or not f2_path:
            results.append(f"[MISS] {entity}: f1={f1_path} f2={f2_path}")
            continue

        f1 = process_frame(f1_path, fs, cfg["body_fill"])
        f2 = process_frame(f2_path, fs, cfg["body_fill"])
        # frame1=frame3 乒乓式：第三帧复用 frame1（spec §4.2 通用约束）
        sheet = compose_3frames([f1, f2, f1], fs)
        out_name = f"r7_{entity}.png"
        out_path = os.path.join(out_dir, out_name)
        sheet.save(out_path, "PNG")

        # 量化: 不透明占比
        alpha = sheet.split()[-1]
        hist = alpha.histogram()
        op = sum(hist[1:]) / (sheet.size[0] * sheet.size[1])
        results.append(
            f"[OK]  {out_path}  {fs*3}x{fs}  opaque={op*100:.0f}%  "
            f"f1={os.path.basename(f1_path)}  f2={os.path.basename(f2_path)}"
        )

    out_log = "r7_pipeline_log.txt"
    with open(out_log, "w") as fh:
        fh.write("\n".join(results) + "\n")
    print("\n".join(results))


if __name__ == "__main__":
    main()