# 人南片区取送日报 · 云端自动运行（GitHub Actions）

把「人南片区取送情况分析」日报流水线搬到 GitHub Actions 云端运行，
**不依赖本地电脑开机**。每日 20:30（北京时间）自动：
取数（国色星洗 SaaS）→ 计算门店/伙伴/基线/日环比 → 生成交互式 HTML → 发布 GitHub Pages。

## 链接
- 云端看板（每日自动更新，固定链接）：
  `https://<你的GitHub用户名>.github.io/<仓库名>/`
- 本地兜底看板（CloudStudio，电脑开机时由本地自动化更新）：
  `https://f97b62bfc2d84f11b770fef194d6d346.sh2.agentos-app.net`

## 代码结构
```
cloud_daily/
├── run_daily.py          # 一键流水线入口（pull → analysis → build → dist）
├── pull_qusong.py        # 从 SaaS 拉取取送明细（Playwright 登录）
├── analysis.py           # 指标计算 → analysis_data.json
├── build_html.py         # 生成交互式 HTML → dist/index.html
├── etl/
│   ├── gsx_client.py     # SaaS 登录/取数客户端（可移植）
│   └── config.json       # 配置模板（凭据为空，由环境变量注入）
└── .github/workflows/daily.yml  # 每日 20:30 定时任务
```

## 首次配置（一次性）
1. 在 GitHub 创建**私有仓库**，推送本目录全部内容。
2. 仓库 Settings → Secrets and variables → Actions → New repository secret，添加：
   | Secret | 值 |
   |---|---|
   | `GSX_BASE` | `https://server.guosexiran.com` |
   | `GSX_USER` | SaaS 登录账号（手机号） |
   | `GSX_PASS` | SaaS 登录密码 |
3. 仓库 Settings → Pages → Source 选 **GitHub Actions**。
4. 手动触发一次 `workflow_dispatch` 验证全链路。

## 手动运行
仓库 Actions 页 → 选中「人南片区取送日报（每日20:30）」→ Run workflow。

## 注意事项
- 凭据只存 GitHub Secrets，仓库内 config.json 为空占位，**不要提交明文密码**。
- SaaS 后端不校验 MAC（已实测），`GSX_MAC` 固定为 `00-11-22-33-44-55` 即可。
- 本地电脑上保留原 WorkBuddy 每日 20:30 自动化作为兜底，继续维护 CloudStudio 旧链接。
