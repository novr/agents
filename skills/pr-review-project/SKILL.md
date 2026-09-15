---
name: pr-review-project
description: >-
  Repository- or domain-specific review axes for Project-specific Notes. Use
  when a PR has architecture rules, operational constraints, or domain
  requirements beyond generic review axes. Output format is unchanged.
---

# pr-review-project

`Project-specific Notes` にドメイン／運用／アーキの固有軸だけ足す。

## 条件

1. diff / code / docs / test で検証できる
2. 汎用 7 軸と被らない
3. OK/NG を短く言える
4. 具体的な修正案を示せる

外部資料（Figma / Confluence / Jira 等）は使える MCP で突合し、差分も Notes へ。
