"""
노션 데이터베이스 저장 모듈
영상 1개당 1행씩 저장합니다.
"""

from notion_client import Client
from datetime import datetime


def save_video_to_notion(
    notion_token: str,
    database_id: str,
    keyword: str,
    product_info: str,
    url: str,
    transcript: str,
    analysis: str,
    script: str,
    thumbnail_title: str = "",
) -> str:
    """
    영상 1개 분석 결과를 노션 데이터베이스 1행에 저장합니다.

    Returns:
        생성된 노션 페이지 URL
    """
    notion = Client(auth=notion_token)

    # 제품명 추출
    product_name = ""
    for line in product_info.split("\n"):
        if "제품명" in line:
            product_name = line.split(":")[-1].strip()
            break

    title = thumbnail_title if thumbnail_title else f"[{keyword}] {datetime.now().strftime('%Y.%m.%d %H:%M')}"

    page = notion.pages.create(
        parent={"database_id": database_id},
        properties={
            "제목": {
                "title": [{"text": {"content": title}}]
            },
            "키워드": {
                "rich_text": [{"text": {"content": keyword}}]
            },
            "제품명": {
                "rich_text": [{"text": {"content": product_name}}]
            },
            "URL": {
                "rich_text": [{"text": {"content": url[:2000]}}]
            },
            "작업날짜": {
                "date": {"start": datetime.now().strftime("%Y-%m-%d")}
            },
            "대본 분석": {
                "rich_text": [{"text": {"content": analysis[:2000]}}]
            },
            "원고": {
                "rich_text": [{"text": {"content": script[:2000]}}]
            },
        },
        children=_build_page_content(url, transcript, analysis, script)
    )

    return page.get("url", "")


def _build_page_content(url: str, transcript: str, analysis: str, script: str) -> list:
    """노션 페이지 본문 블록 구성 (전체 내용 저장)"""
    blocks = []

    blocks.append(_heading("🔗 영상 URL", level=2))
    blocks.append(_paragraph(url))
    blocks.append(_divider())

    blocks.append(_heading("🎙️ 영상 원고 (음성 추출)", level=2))
    for chunk in _split_text(transcript, 1900):
        blocks.append(_paragraph(chunk))
    blocks.append(_divider())

    blocks.append(_heading("📊 대본 분석", level=2))
    for chunk in _split_text(analysis, 1900):
        blocks.append(_paragraph(chunk))
    blocks.append(_divider())

    blocks.append(_heading("✍️ 생성된 원고", level=2))
    for chunk in _split_text(script, 1900):
        blocks.append(_paragraph(chunk))

    return blocks


# ── 블록 헬퍼 ─────────────────────────────────────────────────

def _heading(text: str, level: int = 2) -> dict:
    tag = f"heading_{level}"
    return {
        "object": "block",
        "type": tag,
        tag: {"rich_text": [{"type": "text", "text": {"content": text[:2000]}}]}
    }


def _paragraph(text: str) -> dict:
    return {
        "object": "block",
        "type": "paragraph",
        "paragraph": {"rich_text": [{"type": "text", "text": {"content": text[:2000]}}]}
    }


def _divider() -> dict:
    return {"object": "block", "type": "divider", "divider": {}}


def _split_text(text: str, max_len: int = 1900) -> list[str]:
    if not text:
        return ["(내용 없음)"]
    if len(text) <= max_len:
        return [text]
    chunks = []
    while text:
        chunks.append(text[:max_len])
        text = text[max_len:]
    return chunks
