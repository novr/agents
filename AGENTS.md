# AGENTS

## 責務

- 自作 Agent Skills（`skills/`）と slash commands（`commands/`）の**正本**
- 自作 Cursor project rules（`.cursor/rules/`）の**正本**
- `./sync.sh` で skills / commands を `~/.agents`（および Claude 用 `~/.claude/skills`）へ **symlink** する（`.cursor/rules/` は対象外。ワークスペースが読む）

## 境界

- このリポは `~/.agents` **ではない**。`~/.agents` はランタイム専用の実ディレクトリ
- サードパーティ skill / install の正本管理はしない（`~/.agents` に実体のまま置く。`sync.sh` は実ディレクトリを上書きしない）
- クライアントの読み込み仕様・二重配置・Cloud 同期の運用は扱わない（配備先は `sync.sh` が知る範囲のみ。user 規則 `~/.cursor/rules` も対象外）
- 各 skill / command / rule の手順・オプションはそれぞれのファイル。横断前提だけ README
