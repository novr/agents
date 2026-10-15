# pr_review-history

マージ済み PR のレビュー履歴を Exocortex に記録する。判断はしない。

| スキル | 役割 |
|--------|------|
| `pr-review-fetch` | 一覧・詳細・コメント |
| `pr-review-memory`（`history`） | 失敗時・タグ・reference.md |

## 入力

| 引数 | 意味 |
|------|------|
| `owner/repo` | 省略時 cwd remote |
| 件数 `N` | 直近 N 件 |
| `since:YYYY-MM-DD` | `merged:>` |

## 手順

1. `exo_ping` — 失敗で中止
2. `exo_list_memories` 全ページ — 失敗で中止
3. `gh pr list` + reference の窓走査 — 失敗で中止
4. 一件ずつ: 詳細 → `memory_type` → store → `extends` link。一件失敗は記録して次へ

## 出力

```
## PR Review History Collection Summary

repository: {owner/repo}
走査ページ: {pages}
確認した PR: {checked}
保存済みスキップ: {skipped}
処理対象: {n}
保存成功: {m}
保存失敗: {f}
リンク作成: {l}

### 処理した PR
| PR | Author | Merged | memory_type | Memory ID |

### 失敗した PR
| PR | 段階 | 理由 |

### スキップ（保存済み）
| PR | Author | Merged |

### 特筆
- failure 型 PR、打ち切り理由、再試行、すべて保存済み 等
```

失敗表が空なら「なし」。`f > 0` でもサマリ必須。
