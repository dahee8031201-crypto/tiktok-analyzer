"""
TikTok 영상 수집 모듈 (yt-dlp 기반)
해시태그 페이지에서 영상을 다운로드하고 오디오를 추출합니다.
"""

import os
import json
import subprocess
import sys


def collect_videos(keyword: str, count: int, output_dir: str) -> list[dict]:
    """
    TikTok에서 키워드/해시태그 관련 영상을 수집합니다.

    Args:
        keyword: 검색 키워드 (예: "다이어트식품", "단백질쉐이크")
        count: 수집할 영상 수
        output_dir: 저장 폴더

    Returns:
        [{"url": ..., "title": ..., "audio_path": ..., "views": ..., "likes": ...}, ...]
    """
    os.makedirs(output_dir, exist_ok=True)
    audio_dir = os.path.join(output_dir, "audio")
    os.makedirs(audio_dir, exist_ok=True)

    hashtag_url = f"https://www.tiktok.com/tag/{keyword.lstrip('#')}"
    print(f"\n[수집] 해시태그 페이지: {hashtag_url}")
    print(f"[수집] 목표 영상 수: {count}개\n")

    # yt-dlp로 해시태그 페이지에서 영상 정보 추출
    info_cmd = [
        sys.executable, "-m", "yt_dlp",
        "--dump-json",
        "--flat-playlist",
        "--playlist-end", str(count),
        "--no-warnings",
        hashtag_url
    ]

    print("[수집] 영상 목록 가져오는 중...")
    result = subprocess.run(info_cmd, capture_output=True, text=True, encoding="utf-8")

    if result.returncode != 0 and not result.stdout.strip():
        print(f"[오류] 영상 목록 수집 실패: {result.stderr[:300]}")
        print("[안내] URL을 직접 입력하는 방법으로 전환합니다.")
        return _collect_from_manual_urls(output_dir, count)

    videos = []
    for i, line in enumerate(result.stdout.strip().split("\n")):
        if not line.strip():
            continue
        try:
            info = json.loads(line)
            video_url = info.get("url") or info.get("webpage_url") or info.get("id")
            if not video_url:
                continue

            title = info.get("title", f"video_{i+1}")
            views = info.get("view_count", 0)
            likes = info.get("like_count", 0)

            print(f"[{i+1}/{count}] 다운로드 중: {title[:40]}...")
            audio_path = _download_audio(video_url, audio_dir, f"video_{i+1}")

            if audio_path:
                videos.append({
                    "url": video_url,
                    "title": title,
                    "audio_path": audio_path,
                    "views": views,
                    "likes": likes,
                })
                print(f"       완료: {os.path.basename(audio_path)}")

        except json.JSONDecodeError:
            continue

    if not videos:
        print("[안내] 자동 수집에 실패했습니다. URL을 직접 입력하는 방법으로 전환합니다.")
        return _collect_from_manual_urls(output_dir, count)

    print(f"\n[수집 완료] 총 {len(videos)}개 영상 오디오 추출됨\n")
    return videos


def _download_audio(url: str, output_dir: str, filename: str) -> str | None:
    """단일 영상에서 오디오만 추출합니다."""
    output_template = os.path.join(output_dir, f"{filename}.%(ext)s")

    cmd = [
        sys.executable, "-m", "yt_dlp",
        "--extract-audio",
        "--audio-format", "mp3",
        "--audio-quality", "5",
        "--output", output_template,
        "--no-warnings",
        "--quiet",
        url
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    # 생성된 mp3 파일 찾기
    for f in os.listdir(output_dir):
        if f.startswith(filename) and f.endswith(".mp3"):
            return os.path.join(output_dir, f)

    return None


def collect_from_urls_file(urls_file: str, output_dir: str) -> list[dict]:
    """
    텍스트 파일에서 URL 목록을 읽어 영상을 다운로드합니다.
    파일 형식: 한 줄에 TikTok URL 하나

    Args:
        urls_file: URL 목록 파일 경로 (예: urls.txt)
        output_dir: 저장 폴더
    """
    if not os.path.exists(urls_file):
        print(f"[오류] URL 파일을 찾을 수 없습니다: {urls_file}")
        return []

    with open(urls_file, "r", encoding="utf-8") as f:
        urls = [line.strip() for line in f if line.strip() and line.strip().startswith("http")]

    if not urls:
        print(f"[오류] URL 파일에 유효한 URL이 없습니다.")
        return []

    print(f"\n[수집] URL 파일에서 {len(urls)}개 URL 로드됨: {urls_file}\n")

    audio_dir = os.path.join(output_dir, "audio")
    os.makedirs(audio_dir, exist_ok=True)

    videos = []
    for i, url in enumerate(urls):
        print(f"[{i+1}/{len(urls)}] 다운로드 중: {url[:60]}...")
        audio_path = _download_audio(url, audio_dir, f"video_{i+1}")
        if audio_path:
            videos.append({
                "url": url,
                "title": f"영상 {i+1}",
                "audio_path": audio_path,
                "views": 0,
                "likes": 0,
            })
            print(f"       완료")
        else:
            print(f"       실패: 다운로드 불가")

    print(f"\n[수집 완료] 총 {len(videos)}개 영상 오디오 추출됨\n")
    return videos


def _collect_from_manual_urls(output_dir: str, count: int) -> list[dict]:
    """사용자가 TikTok URL을 직접 붙여넣는 방식으로 수집합니다."""
    audio_dir = os.path.join(output_dir, "audio")
    os.makedirs(audio_dir, exist_ok=True)

    print(f"\n[수동 입력 모드]")
    print(f"분석할 TikTok 영상 URL을 {count}개 입력해주세요.")
    print("(각 URL 입력 후 Enter, 완료 시 빈 줄 입력)\n")

    urls = []
    for i in range(count):
        url = input(f"  URL {i+1}: ").strip()
        if not url:
            break
        if url.startswith("http"):
            urls.append(url)

    videos = []
    for i, url in enumerate(urls):
        print(f"[{i+1}/{len(urls)}] 다운로드 중: {url[:60]}...")
        audio_path = _download_audio(url, audio_dir, f"video_{i+1}")
        if audio_path:
            videos.append({
                "url": url,
                "title": f"영상 {i+1}",
                "audio_path": audio_path,
                "views": 0,
                "likes": 0,
            })
            print(f"       완료")

    return videos
