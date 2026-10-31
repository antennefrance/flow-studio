import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

W, H = 1200, 648

def load_font(size, bold=False, mono=False):
    if mono:
        candidates = ["/System/Library/Fonts/Menlo.ttc"]
    elif bold:
        candidates = [
            "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
            "/System/Library/Fonts/SFNS.ttf",
        ]
    else:
        candidates = [
            "/System/Library/Fonts/Supplemental/Arial.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
            "/System/Library/Fonts/SFNS.ttf",
        ]
    for p in candidates:
        if Path(p).exists():
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()

def draw_grid_background(draw, W, H):
    for x in range(0, W, 40):
        draw.line([(x, 0), (x, H)], fill=(20, 28, 48), width=1)
    for y in range(0, H, 40):
        draw.line([(0, y), (W, y)], fill=(20, 28, 48), width=1)

def generate_deepseek_thumbnail(output_path):
    img = Image.new("RGB", (W, H), (10, 14, 26))
    draw = ImageDraw.Draw(img)
    draw_grid_background(draw, W, H)

    f_tag = load_font(13, bold=True)
    f_title = load_font(42, bold=True)
    f_sub = load_font(20, bold=True)
    f_card_header = load_font(20, bold=True)
    f_metric_val = load_font(32, bold=True)
    f_metric_lbl = load_font(13, bold=False)
    f_body = load_font(15, bold=False)
    f_body_bold = load_font(15, bold=True)
    f_footer = load_font(15, bold=True)

    # 1. Top Badges (width: 360, 350, 310)
    # Pyrite Badge (Purple / Indigo)
    draw.rounded_rectangle([60, 36, 420, 72], radius=8, fill=(30, 27, 75), outline=(99, 102, 241), width=2)
    draw.text((80, 46), "PROJECT PYRITE  •  ZERO-BYTE 2-BIT", fill=(199, 210, 254), font=f_tag)

    # GGUF + MLX Badge (Cyan / Teal)
    draw.rounded_rectangle([440, 36, 800, 72], radius=8, fill=(8, 47, 73), outline=(14, 165, 233), width=2)
    draw.text((465, 46), "GGUF (METAL 4) & MLX NATIVE", fill=(186, 230, 253), font=f_tag)

    # DOI Badge (Emerald)
    draw.rounded_rectangle([820, 36, 1140, 72], radius=8, fill=(6, 78, 59), outline=(16, 185, 129), width=2)
    draw.text((842, 46), "DOI: 10.5281/zenodo.23786705", fill=(167, 243, 208), font=f_tag)

    # 2. Main Title & Subtitle
    draw.text((60, 90), "DeepSeek-Coder-V2 at 2-Bit", fill=(255, 255, 255), font=f_title)
    draw.text((60, 146), "15.7B MoE (2.36B Active) in 6.0 GiB  |  80.5 tok/s Generation Speed on M2 Pro", fill=(56, 189, 248), font=f_sub)

    # 3. Left Card: Metal 4 GGUF Benchmark
    draw.rounded_rectangle([60, 192, 585, 565], radius=14, fill=(15, 23, 42), outline=(14, 165, 233), width=2)
    
    # Left Header
    draw.rounded_rectangle([75, 206, 570, 246], radius=6, fill=(12, 74, 110))
    draw.text((90, 215), "GGUF Benchmark (llama.cpp / Ollama)", fill=(224, 242, 254), font=f_card_header)

    # Metric Row 1: Generation Speed & Prompt Speed
    draw.rounded_rectangle([80, 260, 315, 345], radius=10, fill=(15, 35, 60), outline=(14, 165, 233), width=2)
    draw.text((95, 270), "80.5 tok/s", fill=(56, 189, 248), font=f_metric_val)
    draw.text((95, 312), "Token Generation (Metal 4)", fill=(186, 230, 253), font=f_metric_lbl)

    draw.rounded_rectangle([330, 260, 565, 345], radius=10, fill=(6, 45, 35), outline=(16, 185, 129), width=2)
    draw.text((345, 270), "135.1 tok/s", fill=(52, 211, 153), font=f_metric_val)
    draw.text((345, 312), "Prompt Processing (2.6x Boost)", fill=(167, 243, 208), font=f_metric_lbl)

    # Bullet points Left
    bullets_left = [
        ("• Memory footprint:", " 6.0 GiB RAM (Fits easily in 16GB Macs)"),
        ("• MoE Architecture:", " 64 Routed Experts + 2 Shared Experts"),
        ("• Attention Engine:", " Multi-Head Latent Attention (MLA)"),
        ("• Runtime:", " Universal Ollama, LM Studio, llama.cpp"),
        ("• Zero Crash:", " Complete elimination of repetition collapse"),
    ]
    cur_y = 365
    for b_title, b_desc in bullets_left:
        draw.text((85, cur_y), b_title, fill=(241, 245, 249), font=f_body_bold)
        w_title = draw.textlength(b_title, font=f_body_bold)
        draw.text((85 + w_title, cur_y), b_desc, fill=(148, 163, 184), font=f_body)
        cur_y += 36

    # 4. Right Card: Mathematical Exact Zero-Byte-Overhead & MLX Results
    draw.rounded_rectangle([615, 192, 1140, 565], radius=14, fill=(15, 23, 42), outline=(139, 92, 246), width=2)

    # Right Header
    draw.rounded_rectangle([630, 206, 1125, 246], radius=6, fill=(76, 29, 149))
    draw.text((645, 215), "Sensitivity-Aware Math & MLX Native", fill=(237, 233, 254), font=f_card_header)

    # Metric Row 2: Exact Zero Byte & Top-1 Gain
    draw.rounded_rectangle([635, 260, 870, 345], radius=10, fill=(45, 20, 65), outline=(168, 85, 247), width=2)
    draw.text((650, 270), "Delta = 0 Byte", fill=(216, 180, 254), font=f_metric_val)
    draw.text((650, 312), "Exact 5,241,265,152 Bytes Budget", fill=(233, 213, 255), font=f_metric_lbl)

    draw.rounded_rectangle([885, 260, 1120, 345], radius=10, fill=(55, 35, 15), outline=(245, 158, 11), width=2)
    draw.text((900, 270), "+1.18%", fill=(251, 191, 36), font=f_metric_val)
    draw.text((900, 312), "Top-1 Token Agreement Gain", fill=(254, 243, 199), font=f_metric_lbl)

    bullets_right = [
        ("• Perplexity (PPL):", " 11.1105 -> 10.9707 (-0.1398 gain)"),
        ("• Router Logits:", " FP32 unquantized gate prevents routing error"),
        ("• Shielded Experts:", " High-sensitivity down_proj (L14-26) 3-bit/4-bit"),
        ("• Native MLX:", " 4.88 GiB size, leaves >10 GiB for 32k KV cache"),
        ("• No Custom Kernels:", " Stock MLX & llama.cpp native compatible"),
    ]
    cur_y = 365
    for b_title, b_desc in bullets_right:
        draw.text((640, cur_y), b_title, fill=(241, 245, 249), font=f_body_bold)
        w_title = draw.textlength(b_title, font=f_body_bold)
        draw.text((640 + w_title, cur_y), b_desc, fill=(148, 163, 184), font=f_body)
        cur_y += 36

    # 5. Bottom Footer Bar
    draw.rounded_rectangle([60, 580, 1140, 620], radius=8, fill=(17, 24, 39), outline=(51, 65, 85), width=1)
    draw.text((80, 592), "Hugging Face: masahiroid/DeepSeek-Coder-V2-Lite-Instruct-Pyrite-2bit-GGUF", fill=(148, 163, 184), font=f_footer)
    draw.text((875, 592), "Author: Masahiro NAKATSUGAWA", fill=(56, 189, 248), font=f_footer)

    img.save(output_path, quality=95)
    print("Saved:", output_path)

def generate_consolidated_thumbnail(output_path):
    img = Image.new("RGB", (W, H), (10, 14, 26))
    draw = ImageDraw.Draw(img)
    draw_grid_background(draw, W, H)

    f_tag = load_font(13, bold=True)
    f_title = load_font(42, bold=True)
    f_sub = load_font(20, bold=True)
    f_card_header = load_font(19, bold=True)
    f_metric_val = load_font(30, bold=True)
    f_metric_lbl = load_font(13, bold=False)
    f_body = load_font(15, bold=False)
    f_body_bold = load_font(15, bold=True)
    f_footer = load_font(15, bold=True)

    # 1. Top Badges
    draw.rounded_rectangle([60, 36, 420, 72], radius=8, fill=(30, 27, 75), outline=(99, 102, 241), width=2)
    draw.text((80, 46), "PROJECT PYRITE  •  ZERO-BYTE 2-BIT", fill=(199, 210, 254), font=f_tag)

    draw.rounded_rectangle([440, 36, 800, 72], radius=8, fill=(8, 47, 73), outline=(14, 165, 233), width=2)
    draw.text((465, 46), "APPLE SILICON & GGUF PLATFORM", fill=(186, 230, 253), font=f_tag)

    draw.rounded_rectangle([820, 36, 1140, 72], radius=8, fill=(6, 78, 59), outline=(16, 185, 129), width=2)
    draw.text((842, 46), "DOI: 10.5281/zenodo.23786705", fill=(167, 243, 208), font=f_tag)

    # 2. Main Title & Subtitle
    draw.text((60, 90), "27B Dense & 16B MoE in 6–10 GiB", fill=(255, 255, 255), font=f_title)
    draw.text((60, 146), "Exact Zero-Byte-Overhead (Delta = 0 B) Sensitivity-Aware Quantization on 16GB Macs", fill=(56, 189, 248), font=f_sub)

    # 3. Left Card: DeepSeek-Coder-V2 MoE
    draw.rounded_rectangle([60, 192, 585, 565], radius=14, fill=(15, 23, 42), outline=(14, 165, 233), width=2)
    draw.rounded_rectangle([75, 206, 570, 246], radius=6, fill=(12, 74, 110))
    draw.text((90, 215), "DeepSeek-Coder-V2-Lite (MoE 15.7B / 2.36B)", fill=(224, 242, 254), font=f_card_header)

    draw.rounded_rectangle([80, 260, 315, 345], radius=10, fill=(15, 35, 60), outline=(14, 165, 233), width=2)
    draw.text((95, 270), "80.5 tok/s", fill=(56, 189, 248), font=f_metric_val)
    draw.text((95, 312), "GGUF Metal 4 Generation", fill=(186, 230, 253), font=f_metric_lbl)

    draw.rounded_rectangle([330, 260, 565, 345], radius=10, fill=(6, 45, 35), outline=(16, 185, 129), width=2)
    draw.text((345, 270), "6.0 GiB RAM", fill=(52, 211, 153), font=f_metric_val)
    draw.text((345, 312), "Delta = 0 B Budget (4.88 GiB MLX)", fill=(167, 243, 208), font=f_metric_lbl)

    bullets_moe = [
        ("• Architecture:", " 64 Experts + Multi-Head Latent Attention"),
        ("• Speedup:", " 135.1 t/s Prompt Processing (2.6x over Q2_K)"),
        ("• Quality:", " Top-1 Token Agreement 68.8% -> 70.0%"),
        ("• FP32 Gate Logits:", " Eliminates expert routing collapse"),
        ("• Deployment:", " Ollama, LM Studio, MLX-LM, llama.cpp"),
    ]
    cur_y = 365
    for b_title, b_desc in bullets_moe:
        draw.text((85, cur_y), b_title, fill=(241, 245, 249), font=f_body_bold)
        w_title = draw.textlength(b_title, font=f_body_bold)
        draw.text((85 + w_title, cur_y), b_desc, fill=(148, 163, 184), font=f_body)
        cur_y += 36

    # 4. Right Card: Qwen3.8-27B & LLM-jp 32B Dense
    draw.rounded_rectangle([615, 192, 1140, 565], radius=14, fill=(15, 23, 42), outline=(139, 92, 246), width=2)
    draw.rounded_rectangle([630, 206, 1125, 246], radius=6, fill=(76, 29, 149))
    draw.text((645, 215), "Qwen3.8-27B & LLM-jp-4-32B (Dense / Hybrid)", fill=(237, 233, 254), font=f_card_header)

    draw.rounded_rectangle([635, 260, 870, 345], radius=10, fill=(45, 20, 65), outline=(168, 85, 247), width=2)
    draw.text((650, 270), "-22.3% KL", fill=(216, 180, 254), font=f_metric_val)
    draw.text((650, 312), "Validation KL Divergence Drop", fill=(233, 213, 255), font=f_metric_lbl)

    draw.rounded_rectangle([885, 260, 1120, 345], radius=10, fill=(55, 35, 15), outline=(245, 158, 11), width=2)
    draw.text((900, 270), "10.11 GiB", fill=(251, 191, 36), font=f_metric_val)
    draw.text((900, 312), "Full 27B Footprint on 16GB Mac", fill=(254, 243, 199), font=f_metric_lbl)

    bullets_dense = [
        ("• Architecture:", " Hybrid Gated DeltaNet + Full Attention"),
        ("• Trading Principle:", " Group size g64->g128 funds 3-bit upgrades"),
        ("• Multilingual:", " English, Japanese, and Code benchmarks"),
        ("• Unified Memory:", " Runs locally with zero custom Metal kernels"),
        ("• Open Models:", " Available on Hugging Face / Zenodo v2"),
    ]
    cur_y = 365
    for b_title, b_desc in bullets_dense:
        draw.text((640, cur_y), b_title, fill=(241, 245, 249), font=f_body_bold)
        w_title = draw.textlength(b_title, font=f_body_bold)
        draw.text((640 + w_title, cur_y), b_desc, fill=(148, 163, 184), font=f_body)
        cur_y += 36

    # 5. Bottom Footer Bar
    draw.rounded_rectangle([60, 580, 1140, 620], radius=8, fill=(17, 24, 39), outline=(51, 65, 85), width=1)
    draw.text((80, 592), "Hugging Face Models: masahiroid/*-Pyrite-2bit-MLX / GGUF", fill=(148, 163, 184), font=f_footer)
    draw.text((875, 592), "Author: Masahiro NAKATSUGAWA", fill=(56, 189, 248), font=f_footer)

    img.save(output_path, quality=95)
    print("Saved:", output_path)

if __name__ == "__main__":
    os.makedirs("/Volumes/NVMe2TB/AI-LLM/LLMjp/Pyrite/reports", exist_ok=True)
    p1 = "/Volumes/NVMe2TB/AI-LLM/LLMjp/Pyrite/reports/thumbnail_deepseek_1200x648.png"
    p2 = "/Volumes/NVMe2TB/AI-LLM/LLMjp/Pyrite/reports/thumbnail_pyrite_v2_1200x648.png"
    generate_deepseek_thumbnail(p1)
    generate_consolidated_thumbnail(p2)
