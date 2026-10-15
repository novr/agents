# pr_review

| スキル | 役割 |
|--------|------|
| `pr-review-fetch` | 取得 |
| `slot-worktree` | head 隔離 |
| `pr-review-memory`（`review`） | 記憶 |
| `pr-review-project` / `pr-review-ios` | 固有軸（任意） |

## 入力

PR 番号 / URL、または head ブランチ名。リポジトリは cwd remote または `owner/repo`。

## 投稿

チャットへのレビュー出力と Exocortex 保存までは行う。**GitHub 上への comment / review submit / approve / request-changes は、ユーザーが明示確認するまでしない。**

## 手順

1. **PR 解決** — `pr-review-fetch` で `number`, `title`, `body`, `author`, `headRefName`, `headRepository`, `base`。ブランチ名のみのときは head PR を特定。不能なら中止。
2. **worktree** — `slot-worktree` の `spin --branch <headRefName>`（または `spin --pr <n>`）。JSON の `worktree` で `move_agent_to_root`。`kind` が `control` / `other`（`slot: null`）ならその path で続行。失敗時は skill のフォールバック。不能なら中止。
3. **差分** — `gh pr diff`（merge-base）。stale なローカル two-dot を正にしない。
4. **既存コメント取得** — 行 / レビュー / 会話を読む。重複指摘しない。投稿しない。
5. **過去知見** — `pr-review-memory` recall。失敗はスキップ。
6. **外部資料** — Figma / Confluence / Jira 等。未取得は report に記載。
7. **レビュー → チャット出力 → 保存** — 下記方針・形式。`pr-review-memory` store。失敗でも出力必須。GitHub へは出さない。
8. **スロット解放** — Approve 相当かつ JSON の `slot` が数のときだけ `free --slot N`（または `free --branch`）。`slot: null` では free しない。dirty なら未解放を report に書いて保持。Request changes / 保留は free しない。「Approve 相当」はチャット上の判定であり、GitHub への approve 投稿ではない。

## 失敗時

| 対象 | 方針 |
|------|------|
| PR 解決不能 | 中止 |
| worktree / ルート移動不能 | 中止 |
| Exocortex | スキップ可 |
| 外部資料 | 明記して続行 |
| free が dirty で失敗 | 保持して report に明記 |

## 方針

1. **要約** — 1〜3 文。追跡済み論点は「追跡済み」。
2. **過去知見** — 同リポジトリ・同観点を優先。
3. **汎用軸**:

   | キー | 見るもの |
   |------|----------|
   | `spec-fit` | 目的・受け入れ。外部資料があれば突合 |
   | `regression-risk` | 既存利用者への破壊 |
   | `error-behavior` | 失敗時の沈黙・追跡 |
   | `security-impact` | 入力・権限・機密 |
   | `observability` | 運用での観測 |
   | `test-validity` | 重要経路・境界・失敗系 |
   | `maintainability` | 責務・命名・複雑度 |

4. **固有軸** — iOS/Swift リスク時 `pr-review-ios`、それ以外 `pr-review-project`（併用可）。
5. **ドキュメント中心 PR** — 読者・構成・前提・論理。UI 変更は余白・階層。
6. **アクション** — 未追跡のみ。「今すぐ / 余裕があれば / 将来」。
7. **メタ** — 事実と過去知見に根拠があるときだけ。

## 出力

1. Summary
2. Critical Issues
3. Important Issues
4. Suggestions
5. Review Axes Summary（7 キー各: 判定と根拠）
6. Project-specific Notes
7. Action Plan（該当時）
8. Author Feedback（該当時）
9. Exocortex（保存 / スキップ＋理由）

空セクションは「なし」で可。
