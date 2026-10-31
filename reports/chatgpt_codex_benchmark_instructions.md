# 【ChatGPT 向け完全指示書】Pyrite 公的リーダーボード申請・コミュニティ発信プロンプト（最新版）

**更新情報（最新のベンチマーク動向を反映）:**
* ⚠️ **グローバルの旧「Hugging Face Open LLM Leaderboard」は、2025年3月に公式に終了（Retired / アーカイブ化）されました。** （静的ベンチマークの陳腐化やベンチマックス問題による閉鎖）
* ⭕ 現在アクティブかつ最も権威があるのは、**「Open Japanese LLM Leaderboard v2（NII / LLM-jp / 理研）」** および **「Nejumi LLM リーダーボード 4（Weights & Biases Japan）」** です。
* ⭕ 開発組織 **AntenneFrance** は LLM-jp コンソーシアムの正式メンバーです。

---

## 📋 ChatGPT への指示プロンプト（ここから下をコピー）

```markdown
# 依頼: 自作AI技術「Project Pyrite」の最新公的リーダーボード申請およびコミュニティ発信代行

あなたはブラウザ操作と外部フォーム入力が可能な優秀なAIエージェントです。
以下の前提条件と最新の手順に従って、Webサービスにアクセスし、私の代わりに【公的リーダーボード申請】【国内産業界ベンチマーク申請】【コミュニティ発信】を順次代行してください。

---

### 【開発者・研究基本情報】
* **氏名:** Masahiro NAKATSUGAWA (中津川 昌弘)
* **所属組織:** AntenneFrance / n.p.minerva & Co. (URL: tip.co.jp)
  ※AntenneFrance は国立情報学研究所 (NII) 主宰「LLM-jp コンソーシアム」の正式参加メンバーです。
* **ORCID:** 0009-0000-3224-0103
* **Hugging Face アカウント:** `masahiroid`
* **対象モデル:**
  1. `masahiroid/llm-jp-4.1-8b-thinking-4bit-mlx` (日本語思考モデル)
  2. `masahiroid/llm-jp-4-32b-a3b-base-Pyrite-2bit-MLX` (32B 2-bit極小量子化)
  3. `masahiroid/DeepSeek-Coder-V2-Lite-Instruct-Pyrite-2bit-GGUF` (64 MoE コーディング)
* **論文DOI:**
  * Phase 1: 10.5281/zenodo.23786705
  * Phase 2: 10.5281/zenodo.23811995
  * Phase 3: 10.5281/zenodo.23814635

---

### 【ミッション 1】日本の公的最高峰「Open Japanese LLM Leaderboard v2」への申請（現在稼働中）
* **URL:** https://huggingface.co/spaces/llm-jp/open-japanese-llm-leaderboard-v2
* **運営機関:** 国立情報学研究所 (NII) / 理化学研究所 / LLM-jp
* **手順:**
  1. 上記スペースにアクセスし、「Submit here!」または「Submission」タブを開いてください。
  2. モデル名に `masahiroid/llm-jp-4.1-8b-thinking-4bit-mlx` を入力してください。
  3. 精度（Precision: 4-bit / quantized）等を選択し、「Submit」をクリックしてキュー登録してください。
  4. 続けて可能であれば `masahiroid/llm-jp-4-32b-a3b-base-Pyrite-2bit-MLX` も申請してください。

---

### 【ミッション 2】国内産業界デファクト「Nejumi LLM リーダーボード 4」への掲載申請
* **URL:** https://nejumi.ai （または Weights & Biases Japan 問い合わせ窓口）
* **運営機関:** Weights & Biases Japan 株式会社
* **手順:**
  1. `https://nejumi.ai` を開き、新規モデル掲載申請フォーム（または問い合わせリンク）を確認してください。
  2. 以下の内容で申請情報を入力・送信してください：
     * モデル名: `masahiroid/llm-jp-4.1-8b-thinking-4bit-mlx` および `masahiroid/llm-jp-4-32b-a3b-base-Pyrite-2bit-MLX`
     * 開発組織: AntenneFrance / n.p.minerva & Co. (中津川 昌弘)
     * 特徴: 「感度適応型2-bit量子化（Project Pyrite）により、知能を保ったまま16GB Mac等のコンシューマ環境で完全動作するLLM-jp派生モデル。Nejumi 4での評価・掲載を希望。」

---

### 【ミッション 3】LLM-jp 公式Slack（コンソーシアム会員用）への投稿準備
* **背景:** AntenneFrance はすでにLLM-jpの正式メンバーです。Slackの `#model` または `#general` チャンネルに成果共有の投稿を行います。
* **Slack 投稿文案（日本語）:**
  ```text
  【成果共有】llm-jp-4 (8B/32B) の感度適応型2-bit量子化モデル（Project Pyrite）およびNVMeストリーミング推論について

  LLM-jpコンソーシアム参加メンバーの AntenneFrance（中津川）です。
  一般コンシューマ端末（16GB MacBook等のローカル環境）における、llm-jpモデル群の極小量子化・オンデマンド実行技術を研究開発いたしましたので共有させていただきます。

  ■ 公開モデル（Hugging Face）:
  ・llm-jp-4.1-8b-thinking (4-bit MLX): masahiroid/llm-jp-4.1-8b-thinking-4bit-mlx
  ・llm-jp-4-32b-a3b-base (2-bit Pyrite MLX): masahiroid/llm-jp-4-32b-a3b-base-Pyrite-2bit-MLX

  ■ コア技術（Project Pyrite）:
  1. 感度適応型ゼロバイト量子化（Δ = 0 B）:
     層ごとの感度勾配に基づき、重要層に高ビットを配分しつつ、頑丈な中間層から借用することでファイルサイズ増加ゼロを厳密に維持。
  2. NVMeオンデマンド・ストリーミング:
     RAMとNVMeを階層分離し、16GB Mac上で物理RAM消費 2.5GB〜3.5GB 枠内で安定動作を確認（OOMゼロ）。

  ■ 技術レポート（Open Access DOI）:
  ・Phase 1: https://doi.org/10.5281/zenodo.23786705
  ・Phase 2: https://doi.org/10.5281/zenodo.23811995
  ・Phase 3: https://doi.org/10.5281/zenodo.23814635

  Open Japanese LLM Leaderboard v2 にも提出しております。LLM-jpモデルのローカルエッジ展開にご活用いただけますと幸いです。
  ```

---

### 【ミッション 4】Hugging Face Community Article（解説ブログ）の公開
* **URL:** https://huggingface.co/posts （または masahiroid アカウントのコミュニティ投稿）
* **投稿タイトル:**
  `Project Pyrite: Sensitivity-Aware 2-Bit Quantization on Apple Silicon with Exact Zero-Byte Budget Overhead`
* **本文:**
  以下の内容をそのまま投稿してください：
  ```markdown
  *By Masahiro NAKATSUGAWA (ORCID: 0009-0000-3224-0103) / AntenneFrance / n.p.minerva & Co.*
  Technical Report DOI: https://doi.org/10.5281/zenodo.23786705

  We are excited to share Project Pyrite — an open-source low-bit quantization framework that enforces an exact Zero-Byte Budget Overhead (Δ = 0 B) constraint while running 32B and MoE models on 16GB Apple Silicon Macs.

  Key Innovations:
  1. Layer Sensitivity Ranking: Calculates sensitivity gradients across hidden states to identify critical bottleneck layers.
  2. Compensatory Allocation: Boosts bottleneck layers to 3-bit/4-bit while borrowing exact byte equivalents from robust layers.
  3. Zero Disk Overhead: Total model size matches baseline 2-bit byte-for-byte.

  Available Models on Hugging Face:
  - masahiroid/llm-jp-4.1-8b-thinking-4bit-mlx
  - masahiroid/llm-jp-4-32b-a3b-base-Pyrite-2bit-MLX
  - masahiroid/DeepSeek-Coder-V2-Lite-Instruct-Pyrite-2bit-GGUF
  ```

---

### 【ミッション 5】Reddit r/LocalLLaMA への第一報投稿
* **URL:** https://www.reddit.com/r/LocalLLaMA/submit
* **Post Title:**
  `[Project Pyrite] Running 141B MoE and 32B LLMs on 16GB Apple Silicon Mac with Zero OOM: In-Flight Streaming & Zero-Byte Quantization`
* **Post Body:**
  ```markdown
  Hi r/LocalLLaMA,

  We've developed Project Pyrite — a framework that allows running 141B MoE (Mixtral-8x22B) and 32B models on consumer 16GB Macs under 3.5GB RAM:

  - Exact Zero-Byte Budget Overhead (Δ = 0 B): Preserves reasoning by ranking layer sensitivity without increasing total size.
  - Streaming I/O Engine: Offloads routed experts to NVMe SSD with in-flight lossless decompression, completely eliminating OOM.

  Open Access DOIs:
  - Phase 1: https://doi.org/10.5281/zenodo.23786705
  - Phase 2: https://doi.org/10.5281/zenodo.23811995
  - Phase 3: https://doi.org/10.5281/zenodo.23814635

  Models are available on Hugging Face (masahiroid). We'd love your feedback!
  ```

---

### 【報告】
各ミッションの完了状況（申請URL、登録番号、投稿リンク、エラー等の有無）を箇条書きで報告してください。
```
