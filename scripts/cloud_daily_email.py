import datetime as dt
import json
import os
import subprocess
import sys
from pathlib import Path
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[1]


def local_today() -> dt.date:
    return dt.datetime.now(ZoneInfo("Asia/Shanghai")).date()


def scheduled_day() -> int:
    manual_day = os.environ.get("MANUAL_DAY", "").strip()
    if manual_day:
        return int(manual_day)
    start_date = dt.date.fromisoformat(os.environ.get("START_DATE", "2026-04-30"))
    start_day = int(os.environ.get("START_DAY", "6"))
    return start_day + (local_today() - start_date).days


def scheduled_mode() -> str:
    if os.environ.get("GITHUB_EVENT_NAME") == "workflow_dispatch":
        return os.environ.get("MANUAL_MODE", "morning")
    schedule = os.environ.get("GITHUB_SCHEDULE", "")
    if schedule == "0 15 * * *":
        return "evening"
    return "morning"


def load_manifest() -> dict:
    path = ROOT / "content_manifest.json"
    return json.loads(path.read_text(encoding="utf-8"))


def subject_for(mode: str, day: int, topic: str) -> str:
    if mode == "evening":
        return f"生理第 {day:02d} 天晚间复盘：{topic}"
    return f"生理第 {day:02d} 天：{topic}"


def file_for(mode: str, day: int, manifest: dict) -> tuple[Path, str]:
    entry = manifest.get(str(day))
    if not entry:
        raise SystemExit(f"Missing manifest entry for day {day}.")
    filename = entry.get(mode)
    topic = entry.get("topic", f"第 {day} 天")
    if not filename:
        raise SystemExit(f"Missing {mode} content for day {day}: {topic}.")
    path = ROOT / filename
    if not path.exists():
        raise SystemExit(f"Content file not found: {path}")
    return path, topic


def send_email(subject: str, body_file: Path) -> None:
    script = ROOT / "scripts" / "send_markdown_email.py"
    cmd = [
        sys.executable,
        str(script),
        "--subject",
        subject,
        "--body-file",
        str(body_file),
        "--to",
        os.environ["DAILY_EMAIL_TO"],
    ]
    subprocess.run(cmd, check=True)


def main() -> None:
    for name in ("QQ_SMTP_USER", "QQ_SMTP_AUTH_CODE", "DAILY_EMAIL_TO"):
        if not os.environ.get(name):
            raise SystemExit(f"Missing required secret/environment variable: {name}")

    day = scheduled_day()
    if day < 1 or day > 40:
        raise SystemExit(f"Day {day} is outside the 1-40 plan.")

    mode = scheduled_mode()
    manifest = load_manifest()
    body_file, topic = file_for(mode, day, manifest)
    subject = subject_for(mode, day, topic)
    send_email(subject, body_file)
    print(f"Sent {mode} day {day}: {subject}")


if __name__ == "__main__":
    main()
