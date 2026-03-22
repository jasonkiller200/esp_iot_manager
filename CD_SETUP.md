# CD（持續部署）設定指南

本專案已加入基本 CD workflow：`.github/workflows/deploy.yml`

## 流程設計

- `push master`：自動部署到 `staging`（若 staging secrets 已設定）
- `workflow_dispatch`：可手動選擇 `staging` 或 `production`
- `production` 只允許手動觸發，建議搭配 GitHub Environment 審核

## 需要設定的 GitHub Secrets

### Staging

- `STAGING_HOST`
- `STAGING_USER`
- `STAGING_SSH_KEY`
- `STAGING_APP_PATH`

### Production

- `PROD_HOST`
- `PROD_USER`
- `PROD_SSH_KEY`
- `PROD_APP_PATH`

## 伺服器前置條件

1. 已安裝 Docker + Docker Compose
2. 專案目錄存在且可 `git pull`
3. `.env` 已配置

## 部署命令（workflow 內執行）

```bash
git pull origin master
docker compose pull || true
docker compose up -d --build
```

## 建議安全設定

1. 啟用 GitHub Environment：`staging`, `production`
2. `production` 啟用 required reviewers
3. branch protection：master 必須通過 CI 才可合併
