---
name: pr-review-fetch
description: >-
  Fetch-only GitHub PR/Issue data (view, diff, list, comment APIs). Apply the
  official `gh` skill first for CLI patterns.
---

# pr-review-fetch

取得のみ。create / merge / review submit / comment 投稿は範囲外。

構文・pagination・`gh api` fallback は公式 skill **`gh`** を先に適用。

## JSON

`gh pr view --json` に `repository` はない。owner/repo は `headRepository`（`name` / `owner.login`）。head は `headRefName`。

## コメント

`gh pr view --comments` は issue 会話欄のみ。行・レビューは `gh api`:

- 行: `repos/{owner}/{repo}/pulls/{n}/comments`
- レビュー: `repos/{owner}/{repo}/pulls/{n}/reviews`
- 会話: `repos/{owner}/{repo}/issues/{n}/comments`

## 一件

```bash
gh pr view <PR> -R owner/repo --json number,author,headRepository,headRefName,title,body,mergedAt
gh pr diff <PR> -R owner/repo
```

## 一覧

```bash
gh pr list -R owner/repo [--search "merged:>YYYY-MM-DD"] [--limit N]
```

窓走査・打ち切りは呼び出し元の責務。
