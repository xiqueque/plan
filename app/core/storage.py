"""数据层：JSON 存储、任务查询与排序、自动清理。"""
from __future__ import annotations

import json
import os
import shutil
import sys
import time
import uuid
from datetime import date, timedelta
from pathlib import Path

# 用户数据目录：开发时 app/data；打包后为 exe 同目录下的 data
if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys.executable).resolve().parent
else:
    BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_FILE = DATA_DIR / "plan.json"
IMAGES_DIR = DATA_DIR / "images"

DEFAULT_SETTINGS = {"cleanup_days": 0, "sound_volume": 12, "image_viewer": ""}
WEEKDAY_NAMES = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
ALL_WEEKDAYS = list(range(7))


def today_str() -> str:
    return date.today().isoformat()


def new_task_id() -> str:
    return uuid.uuid4().hex[:12]


def new_task(
    text: str,
    date_str: str,
    time_start: str | None = None,
    time_end: str | None = None,
    is_daily: bool = False,
    color: str = "#1F3A4D",
    reminder_mode: str = "none",
    reminder_time: str | None = None,
    reminder_weekdays: list[int] | None = None,
    images: list | None = None,
) -> dict:
    """创建一个新任务字典。"""
    if reminder_mode == "daily" or is_daily:
        reminder_mode = "daily"
        is_daily = True
    return {
        "id": new_task_id(),
        "text": text.strip(),
        "date": date_str,
        "time_start": time_start or None,
        "time_end": time_end or None,
        "is_daily": is_daily or reminder_mode == "daily",
        "color": color or "#1F3A4D",
        "reminder_mode": reminder_mode or ("daily" if is_daily else "none"),
        "reminder_time": reminder_time or None,
        "reminder_weekdays": (
            list(reminder_weekdays) if reminder_weekdays else list(ALL_WEEKDAYS)
        ),
        "images": list(images) if images else [],
        "pinned": False,
        "pinned_at": None,
        "created_at": time.time(),
    }


def empty_data() -> dict:
    return {
        "settings": dict(DEFAULT_SETTINGS),
        "tasks": [],
        "done": {},
        "reminded": {},
        "day_images": {},
        "image_names": {},
        "image_daily": {},
    }


def load_data() -> dict:
    """读取数据文件；文件不存在或损坏时返回空数据。"""
    if not DATA_FILE.exists():
        return empty_data()
    try:
        with DATA_FILE.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        _backup_broken_file()
        return empty_data()
    if not isinstance(data, dict):
        _backup_broken_file()
        return empty_data()
    data.setdefault("settings", dict(DEFAULT_SETTINGS))
    data.setdefault("tasks", [])
    data.setdefault("done", {})
    data.setdefault("reminded", {})
    data.setdefault("day_images", {})
    data.setdefault("image_names", {})
    data.setdefault("image_daily", {})
    settings = data["settings"]
    # 兼容旧版本：check_sound -> sound_file
    if "check_sound" in settings and "sound_file" not in settings:
        settings["sound_file"] = settings.pop("check_sound")
    settings.setdefault("sound_file", "")
    settings.setdefault("sound_volume", 12)
    settings.setdefault("image_viewer", "")
    # 旧数据迁移：is_daily -> reminder_mode；补全提醒字段
    for task in data["tasks"]:
        if "reminder_mode" not in task:
            task["reminder_mode"] = "daily" if task.get("is_daily") else "none"
        if "reminder_time" not in task:
            task["reminder_time"] = None
        if "reminder_weekdays" not in task:
            task["reminder_weekdays"] = list(ALL_WEEKDAYS)
        if "images" not in task:
            task["images"] = []
        task["is_daily"] = task.get("reminder_mode") == "daily"
    return data


def _backup_broken_file() -> None:
    """数据文件损坏时，先把原文件改名备份，避免覆盖丢失。"""
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        broken = DATA_FILE.with_suffix(".broken.json")
        os.replace(DATA_FILE, broken)
    except OSError:
        pass


def save_data(data: dict) -> None:
    """先写临时文件再替换，防止写入中途损坏数据。"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    tmp = DATA_FILE.with_suffix(".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, DATA_FILE)


def task_sort_key(task: dict):
    """排序：置顶优先（按置顶时间），其余按时段、创建时间。"""
    if task.get("pinned"):
        return (0, task.get("pinned_at") or 0, "", 0)
    return (1, 0, task.get("time_start") or "", task.get("created_at") or 0)


def tasks_for_date(data: dict, date_str: str) -> list:
    """返回某天要显示的任务列表（每天重复任务 + 当天创建的任务），已排序。"""
    tasks = [
        t for t in data.get("tasks", [])
        if t.get("is_daily") or t.get("date") == date_str
    ]
    tasks.sort(key=task_sort_key)
    return tasks


def is_done(data: dict, task_id: str, date_str: str) -> bool:
    return bool(data.get("done", {}).get(date_str, {}).get(task_id))


def set_done(data: dict, task_id: str, date_str: str, done: bool) -> None:
    """记录某天某任务的完成状态（每天重复任务按天分别记录）。"""
    day = data.setdefault("done", {}).setdefault(date_str, {})
    if done:
        day[task_id] = True
    else:
        day.pop(task_id, None)


def is_reminded(data: dict, task_id: str, date_str: str) -> bool:
    """当天该任务是否已提醒过。"""
    return bool(data.get("reminded", {}).get(date_str, {}).get(task_id))


def mark_reminded(data: dict, task_id: str, date_str: str, time_str: str) -> None:
    """记录当天该任务已在某时间提醒过（防止重复提醒）。"""
    day = data.setdefault("reminded", {}).setdefault(date_str, {})
    day[task_id] = time_str


def format_weekdays(weekdays) -> str:
    """把周几列表格式化为简短中文说明；全选返回空字符串。"""
    days = sorted(set(weekdays or []))
    if not days or len(days) == 7:
        return ""
    if days == [0, 1, 2, 3, 4]:
        return "（周一~周五）"
    names = [WEEKDAY_NAMES[d] for d in days if 0 <= d <= 6]
    return "（" + "、".join(names) + "）"


def format_time_period(time_start: str | None, time_end: str | None) -> str:
    """时间段显示：结束早于开始时视为跨午夜，标为「次日」。"""
    if not time_start:
        return ""
    if not time_end:
        return time_start
    if time_end < time_start:
        return f"{time_start} – 次日{time_end}"
    return f"{time_start} – {time_end}"


def cleanup_orphan_images(data: dict) -> int:
    """删除未被任何任务/图片区引用的图片文件，返回删除数量。"""
    referenced = referenced_image_names(data)
    removed = 0
    if IMAGES_DIR.exists():
        for f in IMAGES_DIR.iterdir():
            if f.is_file() and f.name not in referenced:
                try:
                    f.unlink()
                    removed += 1
                except OSError:
                    pass
    data["image_names"] = {
        k: v for k, v in data.get("image_names", {}).items() if k in referenced
    }
    data["image_daily"] = {
        k: v for k, v in data.get("image_daily", {}).items() if k in referenced
    }
    return removed


# ---------- 图片 ----------
def import_image(src_path) -> str | None:
    """把图片复制到数据目录，返回存储文件名；失败返回 None。"""
    try:
        IMAGES_DIR.mkdir(parents=True, exist_ok=True)
        ext = Path(src_path).suffix.lower()
        if ext not in {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp"}:
            ext = ".png"
        name = f"{uuid.uuid4().hex[:12]}{ext}"
        shutil.copy2(src_path, IMAGES_DIR / name)
        return name
    except OSError:
        return None


def image_path(name: str) -> Path:
    return IMAGES_DIR / name


def delete_image_file(name: str) -> None:
    try:
        (IMAGES_DIR / name).unlink()
    except OSError:
        pass


def referenced_image_names(data: dict) -> set:
    """所有仍被引用（任务附图 + 每日图片区）的图片文件名。"""
    names = set()
    for task in data.get("tasks", []):
        names.update(task.get("images") or [])
    for day_list in data.get("day_images", {}).values():
        names.update(day_list)
    return names


def get_image_display_names() -> dict:
    """读取图片显示名映射（文件名 -> 自定义名称）。"""
    data = load_data()
    return dict(data.get("image_names", {}))


def set_image_display_name(name: str, display: str) -> None:
    """保存图片自定义显示名。"""
    data = load_data()
    data.setdefault("image_names", {})[name] = display
    save_data(data)


def forget_image_display(name: str) -> None:
    """删除图片时同步移除显示名记录。"""
    data = load_data()
    data.get("image_names", {}).pop(name, None)
    save_data(data)


def run_cleanup(data: dict) -> int:
    """自动清理：删除超过 N 天的非每天任务及过期完成记录，返回删除数量。"""
    try:
        cleanup_days = int(data.get("settings", {}).get("cleanup_days", 0))
    except (TypeError, ValueError):
        cleanup_days = 0
    if cleanup_days <= 0:
        return 0  # 默认不清除：0 天表示不自动清理
    cutoff = (date.today() - timedelta(days=cleanup_days)).isoformat()
    kept = []
    removed = 0
    for task in data.get("tasks", []):
        if not task.get("is_daily") and task.get("date", "") < cutoff:
            removed += 1
        else:
            kept.append(task)
    data["tasks"] = kept
    data["done"] = {d: v for d, v in data.get("done", {}).items() if d >= cutoff}
    data["reminded"] = {
        d: v for d, v in data.get("reminded", {}).items() if d >= cutoff
    }
    data["day_images"] = {
        d: v for d, v in data.get("day_images", {}).items() if d >= cutoff
    }
    referenced = referenced_image_names(data)
    data["image_names"] = {
        k: v for k, v in data.get("image_names", {}).items() if k in referenced
    }
    data["image_daily"] = {
        k: v for k, v in data.get("image_daily", {}).items() if k in referenced
    }
    # 删除未被任何任务/图片区引用的图片文件
    if IMAGES_DIR.exists():
        for f in IMAGES_DIR.iterdir():
            if f.is_file() and f.name not in referenced:
                try:
                    f.unlink()
                except OSError:
                    pass
    return removed
