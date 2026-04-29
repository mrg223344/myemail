import datetime as dt
import os
import re
import subprocess
import sys
from pathlib import Path
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[1]


MORNING_FILES = {
    1: "第01天-生理学绪论.md",
    2: "第02天-跨细胞膜的物质转运.md",
    3: "第03天-细胞的电活动-静息电位.md",
    4: "第04天-细胞的电活动-动作电位.md",
    5: "第05天-横纹肌收缩.md",
    6: "第06天-血液-组成血浆蛋白.md",
}


EVENING_FILES = {
    1: "第01天-晚间复盘.md",
    6: "第06天-晚间复盘-血液-组成血浆蛋白.md",
}


SCHEDULE_TOPICS = {
    1: "生理学绪论",
    2: "跨细胞膜的物质转运",
    3: "细胞的电活动（一）静息电位",
    4: "细胞的电活动（二）动作电位",
    5: "横纹肌收缩",
    6: "血液：组成、血浆蛋白",
    7: "血细胞生理",
    8: "红细胞生理",
    9: "白细胞与血小板",
    10: "生理性止血 I",
    11: "生理性止血 II",
    12: "血型和输血原则",
    13: "血液循环：心脏泵血过程",
    14: "血液循环：心脏泵血功能",
    15: "血液循环：心脏电生理",
    16: "血液循环：血管生理 I",
    17: "血液循环：血管生理 II",
    18: "心血管调节：神经调节",
    19: "心血管调节：体液调节",
    20: "冠脉循环",
    21: "呼吸：肺通气",
    22: "呼吸：肺换气与气体运输",
    23: "消化和吸收：概述",
    24: "消化和吸收：口腔、胃、大肠",
    25: "消化和吸收：小肠消化吸收",
    26: "能量代谢",
    27: "体温及其调节",
    28: "尿生成和排出 I",
    29: "尿生成和排出 II",
    30: "感觉 I：感受器总论",
    31: "感觉 II：视觉",
    32: "感觉 III：听觉和平衡觉",
    33: "神经 I：突触传递",
    34: "神经 II：外周递质和受体",
    35: "神经 III：脑电和睡眠",
    36: "神经 IV：躯体运动调控",
    37: "内分泌 I：激素分类与作用机制",
    38: "内分泌 II：生长激素等",
    39: "内分泌 III：糖皮质激素等",
    40: "生殖",
}


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


def subject_for(mode: str, day: int) -> str:
    topic = SCHEDULE_TOPICS.get(day, f"第 {day} 天")
    if mode == "evening":
        return f"生理第 {day:02d} 天晚间复盘：{topic}"
    return f"生理第 {day:02d} 天：{topic}"


def file_for(mode: str, day: int) -> Path:
    mapping = EVENING_FILES if mode == "evening" else MORNING_FILES
    filename = mapping.get(day)
    if not filename:
        topic = SCHEDULE_TOPICS.get(day, f"第 {day} 天")
        raise SystemExit(
            f"Missing pre-generated {mode} content for day {day}: {topic}. "
            "Generate this markdown file and add it to scripts/cloud_daily_email.py."
        )
    path = ROOT / filename
    if not path.exists():
        raise SystemExit(f"Content file not found: {path}")
    return path


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
    body_file = file_for(mode, day)
    subject = subject_for(mode, day)
    send_email(subject, body_file)
    print(f"Sent {mode} day {day}: {subject}")


if __name__ == "__main__":
    main()
