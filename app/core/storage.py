"""数据层：JSON 存储、任务查询与排序、自动清理。"""
from __future__ import annotations

import json
import os
import time
import uuid
from datetime import date, timedelta
from pathlib import Path

# 用户数据目录：app/data（与源码同级，不纳入版本管理）
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DATA_FILE = DATA_DIR / "plan.json"

DEFAULT_SETTINGS = {"cleanup_days": 15}


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
) -> dict:
    """创建一个新任务字典。"""
    return {
        "id": new_task_id(),
        "text": text.strip(),
        "date": date_str,
        "time_start": time_start or None,
        "time_end": time_end or None,
        "is_daily": bool(is_daily),
        "pinned": False,
        "pinned_at": None,
        "created_at": time.time(),
    }


def empty_data() -> dict:
    return {"settings": dict(DEFAULT_SETTINGS), "tasks": [], "done": {}}


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


def run_cleanup(data: dict) -> int:
    """自动清理：删除超过 N 天的非每天任务及过期完成记录，返回删除数量。"""
    try:
        cleanup_days = max(1, int(data.get("settings", {}).get("cleanup_days", 15)))
    except (TypeError, ValueError):
        cleanup_days = 15
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
    return removed
