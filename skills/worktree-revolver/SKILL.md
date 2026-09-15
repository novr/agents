---
name: worktree-revolver
description: >-
  Run parallel git branches via wt-spin into ~/.cursor/worktrees/<repo-name>/slot-<N>.
  Use when working on another branch without touching the main working tree.
---

# worktree-revolver

`wt-spin` 経由で `~/.cursor/worktrees/<repo-name>/slot-<N>` に隔離。External-File Protection 外なのでルート外編集が承認待ちにならない。

直接 `git checkout` / `git worktree add` はしない。挙動は `~/.local/bin/wt-spin` を参照。

## コマンド

```bash
wt-spin spin <branch> [slot]   # WT_SPIN_SLOT_PATH=<path>
wt-spin status                 # 同義: ls
wt-spin free [slot|branch]     # 同義: release
wt-spin trim                   # 空きスロット・旧 slot-*-base 掃除
wt-spin clean                  # poi → 空きスロット削除
wt-spin purge --force          # 全削除（未コミットも消える）
```

同義: `spin` = `run` = `open`。`WT_SPIN_OPEN` / `WT_SPIN_PUSH` 既定 `auto`（エージェント時 open 抑止・push 実行）。上限 6。スロット番号は省略（名指し時のみ指定）。

## エージェント

1. `wt-spin spin <branch>`
2. `WT_SPIN_SLOT_PATH` で `move_agent_to_root` → 移動後に編集
3. `cursor <slot>` は実行しない

ルート移動せず絶対パス編集しない。

### 移動失敗時

`move_agent_to_root` は `git fetch origin <branch>` する。upstream 未設定時は `wt-spin` が `push -u` するが失敗したら:

1. `move_agent_to_cloned_root`
2. `git -C <slot> push -u origin <branch>` → `move_agent_to_root` 再試行
3. 不能なら編集せずユーザーへ

## 挙動

- 既存ブランチは checkout のみ（古い可能性 → 移動後 `git status -sb`）
- `origin/<branch>` あれば `--track`、それ以外は `--no-track` + 必要時 `push -u`
- 分岐元: `origin/HEAD`（なければ `main`）
- 同一ブランチは 1 スロットのみ
- 空き = detached HEAD。到達不能な detached は使用中（`slot-<N>-base` は作らない）
- 枠 6 固定。上限時は `gh poi --dry-run` → detach → lock 全 worktree → `gh poi`（メインで実行）→ 確認済みスロット削除。枠は増やさない
- 解放: `wt-spin free`。タイミングは呼び出し元が指定
- `clean` は poi + 空き削除。壊れたスロットは自動削除しない。`purge` 前に `status`
- `slot-*` 以外（Cursor 自動 worktree）は消さない
- `cursor.worktreeMaxCount` = 500、`cursor.worktreesGlobalMaxSizeGb` = 0 を維持
