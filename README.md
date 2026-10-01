# Daily English Push 📚

每天 07:00 (CST) 自动推送 10 句英语日常对话 + 1 部经典电影到微信。

## 流程

```
GitHub Actions (cron 0 23 * * * UTC)
    ↓
Python 脚本调 Claude Haiku 生成结构化 JSON
    ↓
渲染为 Markdown
    ↓
PushPlus HTTP POST → 微信通知卡片
```

## 配置 Secrets

GitHub repo → Settings → Secrets and variables → Actions,加 2 个:

| Secret 名 | 说明 |
|-----------|------|
| `ANTHROPIC_API_KEY` | Claude API key (`sk-ant-...`) |
| `PUSHPLUS_TOKEN` | PushPlus 个人中心 token (pushplus.plus) |

## 本地测试

```bash
export ANTHROPIC_API_KEY=sk-ant-...
export PUSHPLUS_TOKEN=...
python scripts/generate_and_send.py
```

## 手动触发测试

GitHub repo → Actions → "Daily English Push" → Run workflow

## 调整推送时间

修改 `.github/workflows/daily.yml` 的 cron 表达式,GitHub Actions 用 UTC。
`0 23 * * *` UTC = 07:00 CST。

## 自定义内容风格

修改 `scripts/generate_and_send.py` 的 `SYSTEM_PROMPT`(句式难度、电影偏好、轮换规则)。

## 成本预估

- Claude Haiku 4.5:每天 ~2K tokens input + ~2K output ≈ $0.005/天 ≈ $1.8/年
- PushPlus:免费 200 条/天,只发 1 条,完全够用
- GitHub Actions:免费 2000 分钟/月,每天跑 1 分钟 ≈ 30 分钟/月
