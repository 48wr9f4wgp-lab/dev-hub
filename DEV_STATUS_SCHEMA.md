# DEV_STATUS.json

DEV HUBが各リポジトリの開発状態を表示するための正本ファイルです。

## ルール

- ルート直下に `DEV_STATUS.json` を置く。
- DEV HUBはファイル構成から開発フェーズを推測しない。
- フェーズや確認状況を変えた開発作業では、このファイルも同じ変更単位で更新する。
- 未確認を `ok` にしない。
- 対象外の項目は `na` を使う。

## フェーズ

次のいずれかを使います。

- `企画確認中`
- `企画確定`
- `中核部分の試作`
- `主要機能実装`
- `見た目・操作感の改善`
- `品質確認`
- `公開前最終版`
- `公開可能`

## checks

値は `ok` / `warn` / `none` / `na` のいずれかです。

- `boot`: 起動確認
- `test`: 自動テスト
- `device`: 実機確認
- `save`: 保存
- `analytics`: 分析計測
- `performance`: 性能確認
- `release`: 公開準備

意味:

- `ok`: 実際に確認済み
- `warn`: 確認中、または一部のみ確認済み
- `none`: 未確認
- `na`: このプロダクトでは対象外

## 例

```json
{
  "schema": 1,
  "phase": "主要機能実装",
  "checks": {
    "boot": "ok",
    "test": "warn",
    "device": "ok",
    "save": "none",
    "analytics": "none",
    "performance": "none",
    "release": "warn"
  },
  "next": "初回プレイ導線を実機で確認する",
  "note": "未確認項目は推測で完了扱いにしない。",
  "updated_at": "2026-09-15"
}
```
