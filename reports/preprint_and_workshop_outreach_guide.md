# Project Pyrite: 学術プレプリント・ワークショップ投稿＆コミュニティ連携ガイド

本ドキュメントは、**Project Pyrite**（Sensitivity-aware 2-bit quantization on Apple Silicon）を国際学会ワークショップやプレプリントサーバー（TechRxiv, arXiv）へ展開し、Hugging Faceフォロワーや研究者コミュニティと連携するための完全ガイドです。

---

## 1. 投稿先プラットフォームの比較と戦略

| プラットフォーム | 審査 / Endorsement | DOI発行 | インデックス | 特徴・メリット |
| :--- | :--- | :--- | :--- | :--- |
| **Zenodo** (公開済) | なし（即時公開） | あり (`10.5281/zenodo.23786705`) | Google Scholar, OpenAIRE | CERN運営。Version 2として即座にDeepSeek-Coder-V2の追記版を更新可能。 |
| **TechRxiv (IEEE)** | 編集委員会による簡易チェック（1〜3営業日） | あり（TechRxiv固有DOI） | IEEE Xplore, Google Scholar | **Endorsement不要**。IEEE傘下で電気工学・計算機科学分野で高い権威。 |
| **arXiv (`cs.LG`, `cs.AR`)** | **既存著者からのEndorsementが必要** | あり (arXiv ID) | Google Scholar, Semantic Scholar | AI分野の世界標準。フォロワーへの推薦依頼が必要。 |
| **OpenReview 国際ワークショップ** | 査読（ピアレビュー） | 会議 Proceedings または arXiv/OpenReview DOI | DBLP, Google Scholar | NeurIPS / ICLR / ICML 等の併設ワークショップ。採択されれば正式な学会業績となる。 |

---

## 2. TechRxiv (IEEE) 投稿手順

TechRxivは IEEE が運営する工学・計算機科学専門のオープンアクセスプレプリントサーバーです。arXivのような「推薦人（Endorsement）」が不要で、質の高い論文であれば数日で掲載されます。

- **URL**: [https://www.techrxiv.org](https://www.techrxiv.org)
- **アカウント**: IEEE アカウントまたは Cambridge Open Engage アカウントで無料登録（ORCID連携推奨）。

### 入力メタデータ推奨値
- **Title**:
  `Project Pyrite: Sensitivity-Aware 2-Bit Quantization on Apple Silicon MLX with Zero-Byte Budget Overhead`
- **Abstract**:
  （`paper/pyrite_en.tex` の Abstract をそのままコピー＆ペースト）
- **Primary Subject**:
  `Computing and Processing` > `Hardware and Architecture` または `Computer Systems Organization`
- **Secondary Subject**:
  `Computing and Processing` > `Artificial Intelligence`
- **Keywords**:
  `Model Quantization, Apple Silicon, MLX, Mixture of Experts, Large Language Models, Low-Bit Inference`
- **License**:
  `Creative Commons Attribution 4.0 International (CC BY 4.0)`
- **Related DOI**:
  `10.5281/zenodo.23786705` (Zenodo preprint)
- **Related Link**:
  `https://huggingface.co/masahiroid/llm-jp-4-32b-a3b-base-Pyrite-2bit-MLX`
- **アップロードファイル**:
  `pyrite-mlx/paper/pyrite_en.pdf`

---

## 3. arXiv Endorsement 依頼（Hugging Faceフォロワー・協力者向け）

arXiv に `cs.LG` (Machine Learning) または `cs.AR` (Hardware Architecture) で初めて投稿する場合、過去数年間にその分野で論文を発表している研究者からの「Endorsement（推薦）」が必要です。

### 推薦用URLの発行方法
1. [arXiv Endorsement Request Page](https://arxiv.org/auth/endorse.php) にログイン。
2. 投稿予定カテゴリ（`cs.LG` または `cs.AR`）を選択。
3. あなた専用の **Endorsement Code**（例: `ABCDEF`）および **推薦用リンク**（`https://arxiv.org/auth/endorse.php?x=...`）が発行されます。

---

### メッセージテンプレート A: Hugging Face コミュニティ・個別DM用（英語）

> **Subject**: Invitation to review / arXiv endorsement request for Project Pyrite (Zero-overhead 2-bit quantization on Apple Silicon)
>
> Dear [Name / Colleague],
>
> I hope this message finds you well. I noticed your interest and contributions in the open-source LLM community on Hugging Face.
>
> I recently published a technical report on **Project Pyrite**, which introduces an exact zero-byte-overhead sensitivity-guided 2-bit quantization scheme for Apple Silicon MLX. By expanding inactive routing projections from $g64$ to $g128$ and reinvesting the freed bits into critical layers (e.g. `down_proj` in MoE architectures like DeepSeek-Coder-V2-Lite and llm-jp-4-32B), Pyrite significantly mitigates perplexity degradation and retains coding capability within the same byte footprint (~4.88 GiB for 16B MoE).
>
> - **Preprint (Zenodo DOI)**: https://zenodo.org/records/23786705
> - **Model Weights & Code**: https://huggingface.co/masahiroid
>
> We are currently preparing to submit this preprint to **arXiv (`cs.LG` / `cs.AR`)** and an upcoming **international workshop on efficient ML / on-device AI (NeurIPS / ICLR)**.
>
> If you find our work interesting and have endorsement privileges on arXiv for `cs.LG` or `cs.AR`, I would be deeply grateful if you could endorse my submission:
> 🔗 Endorsement Link: [YOUR_ARXIV_ENDORSEMENT_LINK]
> (Code: [YOUR_CODE])
>
> We would also love to hear your feedback, discuss potential collaborations, or explore joint extensions on other open MoE architectures.
>
> Best regards,  
> **Masahiro Nakatsugawa** (ORCID: 0009-0000-3224-0103)

---

### メッセージテンプレート B: 日本語フォロワー・知人・SNS連絡用

> **件名**: 【論文プレプリントご案内】Apple Silicon向け超低ビット量子化 Project Pyrite のarXiv推薦・フィードバックのお願い
>
> [お名前] 様
>
> いつも大変お世話になっております。中津川 昌弘（Masahiro NAKATSUGAWA）です。
>
> この度、Apple Silicon (MLX) 上で動作するLLMの2ビット量子化手法「**Project Pyrite**」のテクニカルレポートを執筆し、Zenodoにて先行公開いたしました。
>
> - **プレプリント (Zenodo DOI)**: https://zenodo.org/records/23786705
> - **Hugging Face公開モデル**: https://huggingface.co/masahiroid
>
> 本研究では、モデル総バイト数を「1バイトたりとも増やさない（$\Delta = 0$ B）」厳密な同一予算制約下で、MoEモデル（DeepSeek-Coder-V2-Lite や llm-jp-4-32B）の感度勾配に基づき、不要な重みのグループサイズを拡大して浮かせた予算を高感度な `down_proj` へ再投資する手法を提案しています。これにより、4.88 GiB（16GB Macで余裕で動作）で高精度な推論を達成しました。
>
> 現在、本レポートを **arXiv（`cs.LG` / `cs.AR`）** および国際ワークショップ（ICLR/NeurIPS等のOn-Device/Efficient ML系）へ投稿準備中です。
>
> もし arXiv の `cs.LG` または `cs.AR` カテゴリで Endorsement（推薦人）資格をお持ちでしたら、推薦をいただけますと大変心強いです。
> 🔗 推薦URL: [YOUR_ARXIV_ENDORSEMENT_LINK]（コード: [YOUR_CODE]）
>
> また、論文へのフィードバックや、今後のエッジAI・量子化に関する共同研究・議論も大歓迎です。ぜひお気軽にご意見をいただけますと幸いです。
>
> 中津川 昌弘  
> ORCID: 0009-0000-3224-0103

---

## 4. OpenReview 国際ワークショップの候補とロードマップ

現在、主要国際学会（MLSys, ICLR, ICML, NeurIPS）では、オンデバイス・低ビット量子化に特化したワークショップが定期開催されています。

### 狙い目の主要国際ワークショップ
1. **MLSys (Conference on Machine Learning and Systems)**
   - トピック: Hardware-software co-design, on-device model compression, unified memory systems.
   - 特徴: システム寄りの実用的な実装（Apple Silicon / MLX / GGUF）が最も高く評価される場。
2. **ICLR / ICML Workshop on Resource-Constrained / Edge Machine Learning**
   - 例: *TinyML Research Symposium*, *Workshop on Efficient Systems for Foundation Models (ES-FoMo)*.
   - フォーマット: 通常 4〜6 ページのショートペーパー（Pyriteのペーパースタイルと完全に合致）。
3. **NeurIPS Workshop on Efficient Natural Language and Speech Processing (ENLSP)**
   - トピック: Extreme quantization (2-bit/3-bit), speculative decoding, MoE serving.
   - OpenReview経由で査読が行われ、コミュニティへの露出度が非常に高い。

### OpenReview 投稿準備ステップ
1. [OpenReview.net](https://openreview.net) でアカウント作成（所属機関または独立研究者プロファイル）。
2. プロファイルに ORCID (`0009-0000-3224-0103`) と Zenodo DOI を紐付け。
3. ワークショップの CFP（Call for Papers）が告知され次第、LaTeX原稿のスタイルファイルをワークショップ形式（NeurIPS/ICLR形式）に合わせてコンパイル・提出。

