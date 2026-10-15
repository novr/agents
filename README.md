# agents

User-level の Agent Skills と、Cursor / Claude Code 用の slash commands。

## License

[MIT](LICENSE)。`slot-worktree` の一部は ConnorGriffin `spin-worktree` 由来（[skills/slot-worktree/NOTICE](skills/slot-worktree/NOTICE)）。

## 配置

このリポジトリのルートを **`~/.agents`** にする（`skills/` → `~/.agents/skills`）。

別パスに clone した場合、project skill にはならない（クライアントが探すのはリポ内の `.agents/skills/` であり、このリポの `skills/` ではない）。user-level に載せる:

```bash
mkdir -p ~/.agents/skills
for s in /path/to/novr/agents/skills/*/; do
  ln -sfn "$s" ~/.agents/skills/"$(basename "$s")"
done
```

中身の正本は [`skills/`](skills/) と [`commands/`](commands/)。

## Skills の読み込み

| クライアント | `~/.agents/skills` | 追加作業 |
|--------------|--------------------|----------|
| Cursor（ローカル） | 読む | なし。`~/.cursor/skills` へ同じ skill を重ねない（二重登録になる） |
| Codex | 読む | なし |
| Claude Code | **読まない** | 下の Claude 節 |
| Cursor Cloud Agents | 同期されない | Sync Skills は `~/.cursor/skills` の**実体**のみ。symlink は同期対象外 |

### Claude Code

`~/.claude/skills/<name>` が必要。既存が `~/.cursor/skills` へのディレクトリ symlink なら外してから:

```bash
# 既存の ~/.claude/skills が symlink なら: rm ~/.claude/skills
mkdir -p ~/.claude/skills
for s in ~/.agents/skills/*/; do
  ln -sfn "$s" ~/.claude/skills/"$(basename "$s")"
done
# Cursor 側だけにある skill（例: gh）があれば:
# ln -sfn ~/.cursor/skills/gh ~/.claude/skills/gh
```

## Commands

`commands/` は `~/.agents` の標準ロード対象外。`/pr-review` 等を使うときだけクライアント側へ:

```bash
mkdir -p ~/.cursor/commands
for c in ~/.agents/commands/*.md; do
  ln -sfn "$c" ~/.cursor/commands/"$(basename "$c")"
done
```

Claude Code は `~/.claude/commands` へ同様（新規は skill 化も可）。

## 前提

- [GitHub CLI](https://cli.github.com/) (`gh`)
- 公式 skill `gh`（`gh skill install` 等。置き場所はクライアントの user skills）
- `pr-review-memory`: [Exocortex](https://github.com/fuwasegu/exocortex) MCP（任意。無い場合は review モードでスキップ可）
- `slot-worktree`: Python 3、任意で `AGENT_WORKTREE_ROOT`（既定 `~/worktrees`）

## slot-worktree

```bash
python3 ~/.agents/skills/slot-worktree/scripts/slot-worktree.py status --repo .
python3 ~/.agents/skills/slot-worktree/scripts/slot-worktree.py spin --branch <name>
python3 ~/.agents/skills/slot-worktree/scripts/slot-worktree.py free --slot N
```
