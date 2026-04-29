param(
    [string]$To = "mengruogang@163.com"
)

$ErrorActionPreference = "Stop"

if (-not $env:QQ_SMTP_USER) {
    throw "请先设置环境变量 QQ_SMTP_USER，例如你的 QQ 邮箱地址。"
}

if (-not $env:QQ_SMTP_AUTH_CODE) {
    throw "请先设置环境变量 QQ_SMTP_AUTH_CODE，即 QQ 邮箱 SMTP/IMAP 授权码。"
}

$python = "C:\Users\孟若刚\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
$body = Join-Path (Get-Location) "第01天-生理学绪论.md"

& $python ".\scripts\send_markdown_email.py" `
    --subject "生理第 01 天：生理学绪论" `
    --body-file $body `
    --to $To

