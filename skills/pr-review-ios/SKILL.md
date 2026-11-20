---
name: pr-review-ios
description: >-
  iOS-specific review axes for Project-specific Notes: OS/Xcode compatibility,
  SwiftUI/UIKit mixing, architecture boundaries, and release bundle leakage.
  Use for iOS/Swift PRs when those risks matter. Output format is unchanged.
---

# pr-review-ios

`Project-specific Notes` に iOS 固有リスクだけ載せる。

## 軸

1. **OS** — Deployment Target、availability、後方互換端末
2. **Xcode** — CI 一致、Build Settings / SPM / swift-tools-version、pbxproj 差分
3. **SwiftUI / UIKit** — 混在時の責務分離、Scene/Window/Navigation 境界
4. **アーキ** — 採用方針からの逸脱、依存方向、Fat VC/VM/Store
5. **退行** — Dynamic Type / VoiceOver、Concurrency（`@MainActor` / `Sendable`）、entitlements ドリフト
6. **配布物** — Copy Bundle Resources / folder reference による `openapi.yaml` 等の同梱、xcconfig・Info.plist 経由の secret 埋め込み、dSYM や本番ログへの秘密情報の混入。汎用の配布物確認と重複する指摘は Notes に再掲しない

保存時は Deployment Target・Xcode Version・UI Framework・Architecture を本文に含め、タグ `project-axis/ios-*`。
