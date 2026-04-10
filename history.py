"""
분석 이력 저장/불러오기 모듈
history.json 파일에 분석 결과를 누적 저장합니다.
"""

import json
import os
from datetime import datetime

HISTORY_PATH = os.path.join(os.path.dirname(__file__), "history.json")


def save_history(keyword: str, product_name: str, url: str,
                 transcript: str, analysis: str, script: str, title: str = ""):
    """분석 결과 1건을 이력에 추가합니다."""
    records = load_history()

    records.append({
        "id": len(records) + 1,
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "keyword": keyword,
        "product_name": product_name,
        "url": url,
        "transcript": transcript,
        "analysis": analysis,
        "script": script,
        "title": title,
    })

    with open(HISTORY_PATH, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)


def load_history() -> list[dict]:
    """저장된 이력 전체 불러오기 (최신순)"""
    if not os.path.exists(HISTORY_PATH):
        return []
    with open(HISTORY_PATH, "r", encoding="utf-8") as f:
        records = json.load(f)
    return list(reversed(records))


def delete_history(record_id: int):
    """특정 이력 삭제"""
    if not os.path.exists(HISTORY_PATH):
        return
    with open(HISTORY_PATH, "r", encoding="utf-8") as f:
        records = json.load(f)
    records = [r for r in records if r.get("id") != record_id]
    with open(HISTORY_PATH, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)
