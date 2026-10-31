# Project Pyrite: 国際ワークショップ（OpenReview系）投稿詳細ガイド

本ドキュメントは、**Project Pyrite**（Sensitivity-aware 2-bit quantization on Apple Silicon & GGUF）を、NeurIPS / ICLR / ICML 等の併設国際ワークショップ（OpenReviewプラットフォーム）へ投稿するための**ターゲット選定・フォーマット要件・投稿戦略**をまとめた実戦ガイドです。

---

## 1. ターゲット国際ワークショップ一覧（最有力候補）

Project Pyrite の研究テーマ（**「厳密な 0 バイト予算制約下での超低ビット量子化」「Apple Silicon Metal / GGUF での高速オンデバイス MoE / Dense 推論」「メモリ帯域制約の克服」**）に最も合致するトップカンファレンス併設ワークショップは以下の通りです。

| ワークショップ名 | 主催学会 / 会場 | 主なテーマ・合致点 | OpenReview Hub |
| :--- | :--- | :--- | :--- |
| **ODI (On-Device Intelligence: Foundation Models under Real-World Constraints)** | **NeurIPS 2026** (Sydney) | 実環境のメモリ・帯域制約、オンデバイス実行、低ビット量子化、エッジ MoE ルーティング | `openreview.net/group?id=NeurIPS.cc/2026/Workshop/ODI` |
| **MLForSys (Machine Learning for Systems)** | **NeurIPS 2025/2026** | MLアルゴリズムとハードウェア・システム協調設計、アクセラレータ最適化 (Apple Metal / GGUF) | `openreview.net/group?id=NeurIPS.cc/2025/Workshop/MLForSys` |
| **OS-FMs / FM-Wild (Open Science & Efficient Foundation Models)** | **ICLR 2025/2026** | オープンソース基盤モデルの効率的実装、コンシューマPCでの民主化、圧縮・量子化 | `openreview.net/group?id=ICLR.cc/2026/Workshop` |
| **FM4LS (Foundation Models for Low-Resource Systems)** | **ICML 2025/2026** (Seoul) | 低リソース環境・限定メモリでの推論、適応的メモリ管理、低ビット表現 | `openreview.net/group?id=ICML.cc/2026/Workshop` |

> **推奨第一候補**: **NeurIPS 2026 ODI (On-Device Intelligence)**
> 16GB Mac 上での 80.5 tokens/sec（DeepSeek MoE）および 0 バイト制約による高精度化は、ODI の Call for Papers (CFP) のど真ん中に位置します。

---

## 2. 投稿フォーマット要件（一般的な基準）

国際ワークショップは、本会議（Main Conference）と異なり**「Non-archival（非アーカイブ）」**のトラックが多く、arXiv や将来のジャーナル・本会議との二重投稿制限が緩やかであることが特徴です。

### A. ページ数制限 (Page Limit)
* **Short Paper / Extended Abstract**: **4 ページ**（本文＋図表。引用文献・付録はページ数無制限）。
* **Full Paper**: **6〜8 ページ**（引用文献・付録はページ数無制限）。
* **現状の Pyrite 論文 (`pyrite_en.tex`) の状況**:
  - 本文: 約 5 ページ
  - 参考文献: 約 1 ページ
  - 表・結果一覧: 約 1 ページ
  - **計 7 ページ**: そのまま 8 ページ枠（Full Paper）に収まります。4 ページ枠（Short Paper）を狙う場合は、イントロと関連研究を少し凝縮し、詳細な実験結果表を Appendix（付録）へ回すことで即座に対応可能です。

### B. 査読方式 (Review Policy)
* **Double-Blind（二重盲検）**:
  - 査読者に著者情報が伝わらないよう、論文中の著者名・所属を匿名化（`Anonymous Authors`）にする必要があります。
  - Hugging Face や GitHub のリポジトリリンクも、匿名化サービス（例: [Anonymous GitHub](https://anonymous.4open.science/)）を利用するか、一次審査時は URL を伏せて「released upon acceptance」と記載します。
* **査読プラットフォーム**:
  - **OpenReview.net** でアカウントを作成（ORCID または機関メールアドレスを推奨）。

---

## 3. 採択率を高めるための論文構成・強調ポイント

ワークショップの査読者（On-Device / Systems 系の研究者）が最も評価するポイントと、Pyrite が強みとしてアピールすべき要素：

1. **「Fair Comparison（公平な比較）」の徹底**:
   - 既存の Mixed-Precision は「精度を上げたがモデルサイズも 500MB〜1GB 増えた」ものが多く、公平な比較が難しかった。
   - Pyrite は **$\Delta = 0\text{ Bytes}$（厳密な同一バイト数）** で PPL・Top-1 一致率が向上している点を数学的・実測的に証明している。
2. **Dense（Qwen 27B）と MoE（DeepSeek 15.7B / llm-jp 32B）の双方での汎用性実証**:
   - 単一のモデルだけでなく、アーキテクチャが全く異なる複数モデルで普遍的に効果を発揮することを提示。
3. **実機（Apple M2 Pro Metal 4）での測定速度（80.5 tok/s）**:
   - 理論だけでなく、実際に手元で動く GGUF / MLX の推論スループットが大幅に向上した（Prompt 処理 2.6 倍）実測データ。

---

## 4. 今後の具体的ステップ

1. **OpenReview アカウントの確認・作成**:
   - [OpenReview.net](https://openreview.net) にてアカウントを作成（審査に 24〜48 時間程度かかる場合があるため、事前登録が推奨されます）。
2. **二重盲検（Double-Blind）版 TeX ソースの切り替えスイッチ整備**:
   - `\ifanonymous` スイッチを `pyrite_en.tex` に追加し、学術ワークショップ投稿用（著者秘匿）と公開版（著者表示）を 1 コマンドで切り替えられるように設定。
3. **4 ページ凝縮版（Short Paper 版）の構成案作成**:
   - 4 ページ制限のワークショップに備え、本文 4 ページ＋付録（Appendix）のレイアウトをあらかじめ設計。

