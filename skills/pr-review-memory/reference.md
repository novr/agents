# reference

ツール引数は `GetMcpTools`。失敗時は `SKILL.md`。

## タグ・context

| 用途 | `context_name` | tags |
|------|----------------|------|
| review | `owner/repo` | `pr-review`、必要に応じて `review-axis/*`、`finding-type/*`、`risk/*`、`project-axis/*` / `project/*` |
| history | `owner/repo` | `pr-review-history`、`{author}`、`owner/repo`、`PR-{number}` |

`context_filter` は `owner/repo`。

## review テンプレート

```
Engineer: <author.login> / Repository: <owner/repo> / PR: #<number> / Date: <YYYY-MM-DD>
Summary:
- <変更の要点>

Critical:
- <重大指摘と根拠>

Axes:
- spec-fit: <評価と根拠>
- regression-risk: <評価と根拠>
- error-behavior: <評価と根拠>
- security-impact: <評価と根拠>
- observability: <評価と根拠>
- test-validity: <評価と根拠>
- maintainability: <評価と根拠>

Project-specific:
- <固有観点のみ>

Next Focus:
- <次回の重点観点>
```

## history 手順

### 入力

- リポジトリ: `owner/repo` または `gh repo view --json nameWithOwner`
- 件数 `N`: 直近 N 件の未取得をすべて処理
- `since:YYYY-MM-DD`: `--search "merged:>YYYY-MM-DD"`
- 省略: 同期フロンティアまで

### 保存済み

`exo_list_memories` を全ページ（`context_filter` = `owner/repo`、`tag_filter` = `["pr-review-history"]`、`limit` 100、`offset` 0,100,…）。`tags` から `PR-{number}` を集める。

### 探索

`gh pr list -R owner/repo`。窓 10 件、`--limit` を 10,20,30… とし末尾窓だけ評価。

1. `cumulative_limit = 10`、`pages_scanned = 0`、`found_unfetched = false`
2. list → `pages_scanned += 1`
3. 末尾窓で未取得をキュー。あれば `found_unfetched = true`
4. 打ち切り（以外は `cumulative_limit += 10`）:
   - 返却 < `cumulative_limit`
   - 件数／期間上限
   - デフォルト: `found_unfetched` かつ直近窓がすべて保存済み
   - `pages_scanned >= 10`
5. 未取得 0 の窓だけで終了しない
6. 件数指定: 範囲取り切ってから処理
7. 範囲がすべて保存済みなら 0 件
8. キューの未取得のみ処理

### 一件

1. 詳細取得（view + 行 / レビュー / 会話）。失敗 → 失敗一覧
2. **memory_type**（部分一致）:

| type | キーワード例 |
|------|----------------|
| `failure` | バグ, bug, セキュリティ, security, 脆弱性, critical, blocker, 修正必須 |
| `success` | 良い, good, excellent, お手本, best practice, 綺麗, clean |
| `decision` | 設計, design, アーキテクチャ, 方針, トレードオフ, trade-off |
| `insight` | 上記以外 |

3. **store**: Repository / PR# / Author / Merged At / Changes、Review Summary、Key Review Comments、Conversations、Extracted Topics、Lessons Learned
4. **link**: `exo_recall_memories`（`PR-{number}`）→ あれば `exo_link_memories`（`extends`）
5. store / link 失敗 → 失敗一覧、次へ
