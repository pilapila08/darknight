# -*- coding: utf-8 -*-
"""FX 贴图后处理流水线（fx_texture_pipeline，PIL 版）。

针对特效贴图（爆炸/新星冲击波/闪电/枪口火光）的后处理，区别于 ai_sprite_pipeline.py：
- 输入：AI 生成的 1024×1024 候选，**纯黑背景 + 亮主体**（与 sprite 的浅底暗主体相反）
- 流程：水印裁剪（右下角 strip）→ 黑色背景亮度抠图（luminance < 阈值 → 透明）→
       bbox 裁剪居中 → 降采样到目标尺寸（NEAREST 保像素感）→ 保存 RGBA PNG
- 不做调色板量化（FX 需保留渐变发光；sprite 才有 ≤11 色约束 art-bible §9.2）

用法：python tools/fx_texture_pipeline.py
输出：design/art/ai-samples/fx-<effect>/fx_<effect>_<variant>.png（RGBA）
不替换 assets/ 下任何文件（入游戏运行时是第二批 engineering-lead 的事）。

调阈值：若主体被误抠，调大 KEY_THRESHOLD；若黑色 bg 残留，调小。
"""
import glob
import os

from PIL import Image

BASE = os.path.join("design", "art", "ai-samples")


def luminance(r, g, b):
    return 0.299 * r + 0.587 * g + 0.114 * b


# 每特效: raw 子目录、目标尺寸、key 阈值、水印裁剪比例、(raw 文件名前缀, 定稿名)
# crop_right/crop_bottom: 从右/下裁掉的比例（0.17 = 裁掉右 17%）
KEY_THRESHOLD_DEFAULT = 22  # luminance < 此值 → 透明
EFFECTS = {
    "explosion": {
        "raw_dir": "fx-explosion/raw",
        "target": (256, 256),
        "key_threshold": 22,
        "crop_right": 0.17,
        "crop_bottom": 0.10,
        "candidates": [
            ("pixel_art_explosion_effect__bi", "fire_01"),
            ("pixel_art_explosion_effect__la", "fire_02"),
            ("pixel_art_magic_energy_explosi", "purple_01"),
            ("pixel_art_dark_magic_blast__de", "purple_02"),
        ],
    },
    "nova": {
        "raw_dir": "fx-nova/raw",
        "target": (256, 256),
        "key_threshold": 22,
        "crop_right": 0.17,
        "crop_bottom": 0.10,
        "candidates": [
            ("pixel_art_magic_shockwave_ring", "runic_01"),
            ("pixel_art_arcane_shockwave__pu", "spike_02"),
            ("pixel_art_expanding_energy_rin", "double_03"),
        ],
    },
    "lightning": {
        "raw_dir": "fx-lightning/raw",
        "target": (96, 256),  # 高瘦画布：竖直 bolt，engineering 可旋转
        "key_threshold": 22,
        "crop_right": 0.15,
        "crop_bottom": 0.07,  # bolt 末端会被裁一点，可接受
        "candidates": [
            ("pixel_art_lightning_bolt__jagg", "bolt_01"),
            ("pixel_art_lightning_strike__ja", "bolt_02"),
        ],
    },
    "muzzle": {
        "raw_dir": "fx-muzzle/raw",
        "target": (128, 128),
        "key_threshold": 22,
        "crop_right": 0.17,
        "crop_bottom": 0.10,
        "candidates": [
            ("pixel_art_muzzle_flash__star_s", "star_01"),
        ],
    },
}


def crop_watermark_strip(img, crop_right, crop_bottom):
    """从右下角裁掉水印 strip，返回新 RGBA Image。"""
    w, h = img.size
    new_w = int(w * (1.0 - crop_right))
    new_h = int(h * (1.0 - crop_bottom))
    return img.crop((0, 0, new_w, new_h))


def key_black_to_transparent(img, threshold):
    """黑色背景亮度抠图：luminance < threshold → alpha=0。返回新 RGBA Image。"""
    img = img.convert("RGBA")
    pixels = img.load()
    w, h = img.size
    new_data = []
    for y in range(h):
        for x in range(w):
            r, g, b, a = pixels[x, y]
            if luminance(r, g, b) < threshold:
                new_data.append((0, 0, 0, 0))
            else:
                new_data.append((r, g, b, 255))
    out = Image.new("RGBA", (w, h))
    out.putdata(new_data)
    return out


def bbox_crop_fit(img, target_w, target_h):
    """bbox 裁主体 → 等比缩放填入 target（保留纵横比 + 8px 边距，居中）。返回 RGBA Image。"""
    # bbox via getbbox (基于 alpha)
    bbox = img.getbbox()
    if not bbox:
        return Image.new("RGBA", (target_w, target_h), (0, 0, 0, 0))
    crop = img.crop(bbox)
    cw, ch = crop.size
    pad = 8
    scale = min((target_w - 2 * pad) / cw, (target_h - 2 * pad) / ch)
    new_w = max(1, int(cw * scale))
    new_h = max(1, int(ch * scale))
    scaled = crop.resize((new_w, new_h), Image.NEAREST)
    canvas = Image.new("RGBA", (target_w, target_h), (0, 0, 0, 0))
    canvas.paste(scaled, ((target_w - new_w) // 2, (target_h - new_h) // 2), scaled)
    return canvas


def metrics(img):
    """统计不透明像素占比（基于 alpha > 0）。"""
    if img.mode != "RGBA":
        img = img.convert("RGBA")
    alpha = img.split()[-1]
    hist = alpha.histogram()
    opaque = sum(hist[1:])
    total = img.size[0] * img.size[1]
    return opaque / total if total else 0.0


def find_raw(raw_dir, prefix):
    matches = sorted(glob.glob(os.path.join(raw_dir, f"{prefix}*.png")))
    return matches[-1] if matches else None


def main():
    results = []
    for effect, cfg in EFFECTS.items():
        raw_dir = os.path.join(BASE, cfg["raw_dir"])
        out_dir = os.path.dirname(raw_dir)  # fx-<effect>/
        os.makedirs(out_dir, exist_ok=True)
        target_w, target_h = cfg["target"]
        thr = cfg["key_threshold"]

        for prefix, variant_name in cfg["candidates"]:
            src_path = find_raw(raw_dir, prefix)
            if not src_path:
                results.append(f"[MISS] {effect}/{variant_name}: no raw matching {prefix}*")
                continue
            src = Image.open(src_path)
            cropped = crop_watermark_strip(src, cfg["crop_right"], cfg["crop_bottom"])
            keyed = key_black_to_transparent(cropped, thr)
            final = bbox_crop_fit(keyed, target_w, target_h)

            out_name = f"fx_{effect}_{variant_name}.png"
            out_path = os.path.join(out_dir, out_name)
            final.save(out_path, "PNG")
            op = metrics(final)
            results.append(
                f"[OK]  {effect}/{out_name}  {target_w}x{target_h}  "
                f"opaque={op*100:.0f}%  raw={os.path.basename(src_path)}"
            )
    print("\n".join(results))


if __name__ == "__main__":
    main()