# AGENTS

## 責務

- Agent Skills（`skills/`）と slash commands（`commands/`）の正本を管理する。
- Cursor project rules（`.cursor/rules/`）の正本を管理する。
- `./sync.sh` で skills と commands を所定の実行環境へ symlink する。

## 境界

- `~/.agents` はランタイム用のディレクトリとして扱う。
- サードパーティ製の skill や install は正本として管理しない。
- クライアントの読み込み仕様や同期の運用は、明示的に依頼された場合を除き扱わない。
- 各 skill、command、rule の手順やオプションは、それぞれのファイルに記載する。
- 個別案件の背景、顧客情報、担当者、期限、機密情報は記載しない。
- 一時的な判断や作業メモは記載しない。
