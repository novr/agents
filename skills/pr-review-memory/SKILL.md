---
name: pr-review-memory
description: >-
  PR review memory via Exocortex (user-exocortex): tag taxonomy, context_name,
  store templates, next_actions policy, and failure handling. Tool schemas come
  from GetMcpTools — not this skill.
---

# pr-review-memory

Exocortex（`server: user-exocortex`、`exo_*`）。引数は `GetMcpTools` → `CallMcpTool`。`tags` / `tag_filter` は配列。`next_actions` は回さない。

詳細・history 窓走査: [reference.md](reference.md)。

## 失敗時

モード: **review** / **history** / **explicit**（未指定は explicit）。

| モード | 利用不可時 |
|--------|------------|
| `review` | スキップ。report に未使用／未保存と理由 |
| `history` | 開始・探索失敗で中止。一件失敗は記録して次へ |
| `explicit` | 中止 |

| 種類 | 対応 |
|------|------|
| 引数・スキーマ | ping しない。スキーマ修正後最大1回 |
| 一時障害 | 最大1回再試行。再試行前に `exo_ping`、不通なら打ち切り |
| 利用不可 | 上表。`mcp_auth` は要求時のみ |
| 空ヒット | 失敗ではない |

`review`: recall 失敗は続行、store 失敗は出力必須・未保存明記。store 前に同 `PR-{number}` の二重確認。

`history`: サマリに成功／失敗件数と失敗 PR を必ず出す。

compact / consolidate / sleep / stale 一括はユーザー明示時のみ。

## タグ（要約）

| 用途 | `context_name` | tags |
|------|----------------|------|
| review | `owner/repo` | `pr-review`、`review-axis/*`、`finding-type/*`、`risk/*`、`project-axis/*` / `project/*` |
| history | `owner/repo` | `pr-review-history`、`{author}`、`owner/repo`、`PR-{number}` |

recall は作者・PR 番号に閉じず同観点を優先。
