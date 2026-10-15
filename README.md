# agents

自作の Agent Skills と slash commands。正本は [`skills/`](skills/) と [`commands/`](commands/)。ルートを `~/.agents` に置く。

## License

[MIT](LICENSE)。`slot-worktree` の一部は ConnorGriffin `spin-worktree` 由来（[skills/slot-worktree/NOTICE](skills/slot-worktree/NOTICE)）。

## 前提（スキル横断）

- [GitHub CLI](https://cli.github.com/) (`gh`) と公式 skill `gh`
- `pr-review-memory`: [Exocortex](https://github.com/fuwasegu/exocortex) MCP（任意）
- `slot-worktree`: Python 3

各 skill / command の手順・オプションはそれぞれのファイルを見る。
