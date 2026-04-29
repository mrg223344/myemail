import argparse
import html
import os
import re
import smtplib
import ssl
from email.message import EmailMessage
from pathlib import Path


def required_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise SystemExit(f"Missing required environment variable: {name}")
    return value


def markdown_to_html(markdown: str) -> str:
    lines = markdown.splitlines()
    body: list[str] = []

    def close_lists() -> None:
        return

    def inline(text: str) -> str:
        escaped = html.escape(text)
        escaped = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", escaped)
        escaped = re.sub(r"`(.+?)`", r"<code>\1</code>", escaped)
        return escaped

    def list_line(text: str, marker: str, depth: int) -> str:
        depth = max(0, min(depth, 4))
        return (
            f'<div class="md-line depth-{depth}">'
            f'<span class="md-marker">{html.escape(marker)}</span>'
            f'<span class="md-text">{inline(text)}</span>'
            "</div>"
        )

    for raw in lines:
        line = raw.rstrip()
        if not line.strip():
            body.append("")
            continue
        if line.startswith("# "):
            body.append(f"<h1>{inline(line[2:].strip())}</h1>")
        elif line.startswith("## "):
            body.append(f"<h2>{inline(line[3:].strip())}</h2>")
        elif line.startswith("### "):
            body.append(f"<h3>{inline(line[4:].strip())}</h3>")
        elif match := re.match(r"^(\s*)(\d+)\.\s+(.*)$", line):
            depth = len(match.group(1).replace("\t", "    ")) // 2
            body.append(list_line(match.group(3), f"{match.group(2)}.", depth))
        elif match := re.match(r"^(\s*)-\s+(.*)$", line):
            depth = len(match.group(1).replace("\t", "    ")) // 2
            body.append(list_line(match.group(2), "•", depth))
        else:
            body.append(f"<p>{inline(line.strip())}</p>")

    content = "\n".join(body)
    return f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body {{
      margin: 0;
      padding: 0;
      background: #f5f7fb;
      color: #243044;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Microsoft YaHei", Arial, sans-serif;
      font-size: 16px;
      line-height: 1.68;
    }}
    .wrap {{
      max-width: 800px;
      margin: 0 auto;
      padding: 22px 12px;
    }}
    .card {{
      background: #ffffff;
      border: 1px solid #e7edf5;
      border-radius: 8px;
      padding: 28px 34px;
      box-shadow: 0 6px 18px rgba(23, 37, 84, 0.05);
    }}
    h1 {{
      margin: 0 0 22px;
      padding: 0 0 14px;
      border-bottom: 1px solid #d8e2f0;
      color: #172554;
      font-size: 24px;
      font-weight: 700;
      line-height: 1.4;
      letter-spacing: 0;
    }}
    h2 {{
      margin: 28px 0 14px;
      padding: 8px 0 8px 12px;
      border-left: 4px solid #2563eb;
      background: transparent;
      color: #1e3a8a;
      font-size: 19px;
      font-weight: 700;
      line-height: 1.45;
    }}
    h3 {{
      margin: 20px 0 9px;
      color: #334155;
      font-size: 16px;
      font-weight: 700;
      line-height: 1.5;
    }}
    p {{
      margin: 8px 0 10px;
      font-size: 16px;
    }}
    .md-line {{
      display: table;
      width: 100%;
      box-sizing: border-box;
      margin: 4px 0;
      padding: 2px 0;
      background: transparent;
      font-size: 16px;
    }}
    .md-marker {{
      display: table-cell;
      width: 30px;
      color: #64748b;
      font-weight: 600;
      white-space: nowrap;
    }}
    .md-text {{
      display: table-cell;
      vertical-align: top;
    }}
    .depth-0 {{
      margin-top: 8px;
      color: #243044;
      font-weight: 500;
    }}
    .depth-0 .md-marker {{
      color: #2563eb;
    }}
    .depth-1 {{
      margin-left: 22px;
      width: calc(100% - 22px);
      color: #334155;
    }}
    .depth-2 {{
      margin-left: 44px;
      width: calc(100% - 44px);
      color: #475569;
      font-size: 15px;
    }}
    .depth-3 {{
      margin-left: 60px;
      width: calc(100% - 60px);
      color: #64748b;
      font-size: 15px;
    }}
    .depth-4 {{
      margin-left: 72px;
      width: calc(100% - 72px);
      color: #64748b;
      font-size: 15px;
    }}
    strong {{
      color: #1d4ed8;
      font-weight: 700;
    }}
    code {{
      background: #eef2f7;
      padding: 2px 5px;
      border-radius: 4px;
      font-family: "Cascadia Mono", Consolas, monospace;
    }}
    @media (max-width: 640px) {{
      body {{ font-size: 15px; }}
      .wrap {{ padding: 12px 8px; }}
      .card {{ padding: 20px 16px; }}
      h1 {{ font-size: 22px; }}
      h2 {{ font-size: 18px; }}
      h3 {{ font-size: 16px; }}
      p, .md-line {{ font-size: 15px; }}
      .depth-1, .depth-2, .depth-3, .depth-4 {{
        margin-left: 14px;
        width: calc(100% - 14px);
      }}
    }}
  </style>
</head>
<body>
  <div class="wrap">
    <div class="card">
{content}
    </div>
  </div>
</body>
</html>
"""


def strip_html(value: str) -> str:
    value = re.sub(r"<br\s*/?>", "\n", value, flags=re.I)
    value = re.sub(r"</(p|h1|h2|h3|li)>", "\n", value, flags=re.I)
    value = re.sub(r"<[^>]+>", "", value)
    return html.unescape(value)


def main() -> None:
    parser = argparse.ArgumentParser(description="Send a markdown/plain-text study email via QQ SMTP.")
    parser.add_argument("--subject", required=True, help="Email subject")
    parser.add_argument("--body-file", required=True, help="UTF-8 text or markdown body file")
    parser.add_argument("--to", default=os.environ.get("DAILY_EMAIL_TO"), help="Recipient email address")
    parser.add_argument("--smtp-host", default=os.environ.get("QQ_SMTP_HOST", "smtp.qq.com"))
    parser.add_argument("--smtp-port", type=int, default=int(os.environ.get("QQ_SMTP_PORT", "465")))
    args = parser.parse_args()

    sender = required_env("QQ_SMTP_USER")
    auth_code = required_env("QQ_SMTP_AUTH_CODE")
    recipient = args.to
    if not recipient:
        raise SystemExit("Missing recipient. Pass --to or set DAILY_EMAIL_TO.")

    body_path = Path(args.body_file)
    body = body_path.read_text(encoding="utf-8")

    message = EmailMessage()
    message["From"] = sender
    message["To"] = recipient
    message["Subject"] = args.subject
    if body_path.suffix.lower() in {".html", ".htm"}:
        message.set_content(strip_html(body), subtype="plain", charset="utf-8")
        message.add_alternative(body, subtype="html", charset="utf-8")
    else:
        message.set_content(body, subtype="plain", charset="utf-8")
        message.add_alternative(markdown_to_html(body), subtype="html", charset="utf-8")

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(args.smtp_host, args.smtp_port, context=context) as smtp:
        smtp.login(sender, auth_code)
        smtp.send_message(message)

    print(f"Sent email to {recipient}: {args.subject}")


if __name__ == "__main__":
    main()
