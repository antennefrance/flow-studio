# 【決定版】Project Pyrite & FLOW 統合マスターロードマップ

**推進責任者:** Masahiro NAKATSUGAWA (中津川 昌弘) / [ORCID: 0009-0000-3224-0103](https://orcid.org/0009-0000-3224-0103)  
**組織:** n.p.minerva & Co. (`tip.co.jp`) / AntenneFrance  
**改定日:** 2026年10月31日

---

## 1. 概念と役割の完全整理（定義）

開発者自身やコミュニティの混乱を根絶するため、**Pyrite** と **FLOW** の役割を以下のように厳密に二分・定義します。

```
┌────────────────────────────────────────────────────────────────────────┐
│                        【Project Pyrite】                              │
│              モデルの互換性を持った量子化・圧縮技術                    │
│   (Sensitivity-Aware Low-Bit Quantization Algorithm / Δ = 0 B)          │
├────────────────────────────────────────────────────────────────────────┤
│ ・出力形式: 標準 .safetensors / 標準 .gguf (フォーマット変更ゼロ)      │
│ ・目的: 知能を保ったまま極限まで重みを小さくし、既存の公的クラスタや   │
│         llama.cpp, MLX, vLLM でそのまま無改造で評価・動作させる。       │
│ ・主要モデル:                                                          │
│   1. masahiroid/llm-jp-4.1-8b-thinking-4bit-mlx                       │
│   2. masahiroid/llm-jp-4-32b-a3b-base-Pyrite-2bit-MLX                 │
│   3. masahiroid/DeepSeek-Coder-V2-Lite-Instruct-Pyrite-2bit-GGUF       │
│ ・公的ベンチマーク: Open Japanese LLM Leaderboard v2 / Nejumi 4        │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ このPyriteモデルも
                                    │ そのまま無変換で流せる！
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                          【FLOW システム】                             │
│               大きなモデルをRAMに全部入れずに行える技術                │
│             (Out-of-Core Ring-Buffered Streaming Runtime)             │
├────────────────────────────────────────────────────────────────────────┤
│ ・システム名 / アプリ名: FLOW Studio (※Pyrite Studioという呼称は廃止)  │
│ ・目的: 16GB Mac等のコンシューマPCで、141Bや32Bなどの巨大モデルを       │
│         RAM 2.5GB〜3.5GB の固定枠だけでOOMゼロ・高速に動かす。         │
│                                                                        │
│ ■ 2つの実行形態:                                                       │
│   1. 【FLOW-Direct】(非圧縮・ゼロコピー・ストリーミング)               │
│      ・対象: Pyriteモデルを含むすべての標準 .gguf / .safetensors       │
│      ・特徴: 変換不要、待ち時間ゼロ、CPU解凍オーバーヘッド完全ゼロ。   │
│   2. 【FLOW-Boost】(可逆圧縮ストリーミング)                            │
│      ・対象: .gguf.flow / .safetensors.flow                            │
│      ・特徴: バイトシャッフル＋ZstdでNVMe実効転送帯域を2.4倍にブースト。│
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. 実行ステップ（明確化された4段階）

```mermaid
flowchart TD
    Step1["【Step 1】アプリの統一: FLOW Studio の完成\n・アプリ名称を『FLOW Studio』に完全統一\n・標準モデル（Pyrite等）を無変換で即実行できる『FLOW-Direct』機能\n・帯域ブースト用『FLOW-Boost (.flow)』の選択対応\n・OpenAI互換API (/v1/chat/completions) & メモリ可視化稼働中"]

    Step2["【Step 2】公的リーダーボードへの申請（Pyriteモデル）\n・対象: 標準形式の Pyrite 2-bit / Thinking 4-bit モデル\n・提出先: Open Japanese LLM Leaderboard v2 (NII / mdx)\n・ChatGPT 指示書 (chatgpt_codex_benchmark_instructions.md) で申請代行"]

    Step3["【Step 3】llama.cpp への2段階公式RFC提出（FLOW技術）\n・第1弾: RFC Part 1『標準GGUFで動く非圧縮ストリーミング (FLOW-Direct)』\n  → 反対理由ゼロ、低RAMユーザーのOOM救済として熱烈歓迎を狙う\n・第2弾: RFC Part 2『帯域倍増の可逆圧縮拡張 (FLOW-Boost: .gguf.flow)』\n  → 第1弾のパイプラインをベースにSSD帯域限界を突破する提案"]

    Step4["【Step 4】LLM-jp / コミュニティ発信 & 学会論文\n・LLM-jp Slack (#open-ja-llm-leaderboard / #モデル構築_モデル公開) 投稿\n・Hugging Face 既存リポジトリへの .flow 併記（任意）\n・mdx公的JGLUEスコアを取得し、ACL ARR / NeurIPS へ提出"]

    Step1 --> Step2 --> Step3 --> Step4

    classDef s1 fill:#1e3a8a,stroke:#3b82f6,stroke-width:2px,color:#fff;
    classDef s2 fill:#065f46,stroke:#10b981,stroke-width:2px,color:#fff;
    classDef s3 fill:#7c2d12,stroke:#f97316,stroke-width:2px,color:#fff;
    classDef s4 fill:#581c87,stroke:#a855f7,stroke-width:2px,color:#fff;
    class Step1 s1;
    class Step2 s2;
    class Step3 s3;
    class Step4 s4;
```

---

## 3. アクション進捗表

| No | 項目 | 区分 | 状態 | 詳細 |
| :---: | :--- | :---: | :---: | :--- |
| **1** | **FLOW Studio アプリ完成** | FLOW | **完了** | クリーンアーキテクチャ化完了。`http://127.0.0.1:8080` にて FLOW-Direct / FLOW-Boost 選択可能。 |
| **2** | **公的リーダーボード申請** | Pyrite | **完了** | **Open Japanese LLM Leaderboard v2（NII/mdx）への申請完了！**（※Nejumi 4は後回し） |
| **3** | **llama.cpp 向け RFC 起票** | FLOW | **着手 (実行中)** | GitHub CLI (`gh`) 経由で Part 1（非圧縮 Direct ストリーミング）を起票可能。 |
| **4** | **LLM-jp / コミュニティ共有** | Pyrite | **完了** | **LLM-jp Slack での発信・成果共有完了！** |
| **5** | **Hugging Face への .flow 追加** | FLOW | **任意・待機** | 必要に応じていつでも既存リポジトリへアップロード可能。 |
