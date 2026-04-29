# 云端部署说明：GitHub Actions 版

这个方案可以在电脑关机、睡眠、休眠时继续发送邮件，因为定时任务运行在 GitHub 云端。

## 已配置的时间

- 早间学习邮件：每天北京时间 07:30
- 晚间复盘邮件：每天北京时间 23:00

GitHub Actions 的 cron 使用 UTC，所以工作流中写的是：

- `30 23 * * *`：对应北京时间第二天 07:30
- `0 15 * * *`：对应北京时间当天 23:00

## 明天从第 6 天开始

工作流环境中已设置：

- `START_DATE=2026-04-30`
- `START_DAY=6`

因此 2026-04-30 会发送第 6 天，之后每天自动递增。

## 需要在 GitHub 仓库设置的 Secrets

进入仓库：

`Settings -> Secrets and variables -> Actions -> New repository secret`

添加三个 Secret：

- `QQ_SMTP_USER`：QQ 邮箱地址
- `QQ_SMTP_AUTH_CODE`：QQ 邮箱 SMTP 授权码
- `DAILY_EMAIL_TO`：收件邮箱地址

## 重要限制

当前云端脚本只会发送已经预生成好的 Markdown 内容。现在仓库里已有第 1-5 天早间内容和第 1 天晚间复盘内容。

为了让第 6 天以后也能稳定发送，需要继续把第 6-40 天早间内容、以及对应晚间复盘内容生成出来并提交到仓库。

## 手动测试

在 GitHub 仓库页面：

`Actions -> Daily physiology study email -> Run workflow`

可以选择：

- `mode=morning`
- `day=1`

手动触发测试邮件。

