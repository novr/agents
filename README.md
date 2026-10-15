# agents

自作の Agent Skills と slash commands。正本は [`skills/`](skills/) と [`commands/`](commands/)。

`~/.agents` はランタイム用の別ディレクトリ。自作だけ symlink する:

```bash
./sync.sh
```

サードパーティ（`sim-use init` 等）は `~/.agents` に直接入り、このリポには触れない。

## License

[MIT](LICENSE)。`slot-worktree` の一部は ConnorGriffin `spin-worktree` 由来（[skills/slot-worktree/NOTICE](skills/slot-worktree/NOTICE)）。

## 前提（スキル横断）

- [GitHub CLI](https://cli.github.com/) (`gh`) と公式 skill `gh`
- `pr-review-memory`: [Exocortex](https://github.com/fuwasegu/exocortex) MCP（任意）
- `slot-worktree`: Python 3

各 skill / command の手順・オプションはそれぞれのファイルを見る。
