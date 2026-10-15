---
name: slot-worktree
description: >-
  Fixed-slot isolated Git worktrees under
  ${AGENT_WORKTREE_ROOT:-~/worktrees}/<key>/slot-<N>. Use when isolating
  parallel branch or PR head work without touching the control checkout.
  Commands: spin, status, free.
---

# slot-worktree

制御 checkout を切り替えず `slot-1`..`slot-6` に隔離する。出典は [NOTICE](NOTICE)。

既定ルート `${AGENT_WORKTREE_ROOT:-~/worktrees}`（`--worktree-root` 可）。配置キーは origin の `owner/repo` をサニタイズ（basename 衝突回避）。

## 実行

1. この skill のディレクトリを解決する
2. 実行（成功時 stdout は JSON のみ）:

```bash
python3 <slot-worktree-skill-dir>/scripts/slot-worktree.py <subcommand> ...
```

| サブコマンド | 用途 |
|-------------|------|
| `spin --branch <name>` | 作成、または既存 checkout 再利用 |
| `spin --pr <n>` | head 解決して同上（fork は失敗） |
| `status` | `in-use` / `missing` / `orphan-dir` |
| `free --slot N` / `free --branch NAME` | 解放。dirty は失敗。`--force` は明示時のみ |

共通: `--repo` / `--worktree-root` / `--remote` / `--dry-run`。

`worktree` を作業ルートにする。`cursor <slot>` は起動しない。CLI は push しない。

| `kind` | `slot` | |
|--------|--------|--|
| `slot` | 1..6 | Approve 相当で `free` 可 |
| `control` / `other` | `null` | 既存 path で続行。**`free` しない** |

解放判定は `slot != null` のみ。

## エージェント

1. `spin --branch <head>`（または `--pr`）
2. `worktree` で `move_agent_to_root`
3. ルート移動せず絶対パス編集しない
4. `free` は `slot` が数のときだけ

移動失敗時: `move_agent_to_cloned_root` → 必要なら手動 `push -u` → `move_agent_to_root` 再試行。不能なら編集しない。

## 解放

呼び出し元の責任。dirty / ignored 残りで失敗したら保持して報告。満杯時は `status`。`orphan-dir` は `free --force`。

fetch はするが既存ローカル tip は書き換えない（レビュー用の意図しないリセットを避ける）。

## 制約

- 上限 6。空きなし・fork PR・lock 失敗は非 0
- Cursor 公式 `/worktree` とは別系統
