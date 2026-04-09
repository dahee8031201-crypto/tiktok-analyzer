"""
음성 → 텍스트 변환 모듈 (faster-whisper 기반, 로컬 처리)
"""

from faster_whisper import WhisperModel


def transcribe_videos(videos: list[dict], model_size: str = "small") -> list[dict]:
    """
    영상 오디오 파일들을 텍스트로 변환합니다.

    Args:
        videos: crawler.py에서 반환된 영상 목록
        model_size: Whisper 모델 크기 ("tiny", "base", "small", "medium")
                    - tiny: 가장 빠름, 정확도 낮음
                    - small: 속도/정확도 균형 (기본값, 권장)
                    - medium: 정확도 높음, 느림

    Returns:
        각 영상에 "transcript" 필드가 추가된 목록
    """
    print(f"[변환] Whisper 모델 로딩 중 ({model_size})...")
    print("       첫 실행 시 모델 다운로드가 필요합니다 (최대 수 분 소요)\n")

    # CPU 사용 (GPU 없는 환경 대응)
    model = WhisperModel(model_size, device="cpu", compute_type="int8")

    results = []
    for i, video in enumerate(videos):
        audio_path = video.get("audio_path")
        title = video.get("title", f"영상 {i+1}")

        print(f"[{i+1}/{len(videos)}] 음성 변환 중: {title[:40]}...")

        if not audio_path or not __import__("os").path.exists(audio_path):
            print(f"       건너뜀: 오디오 파일 없음")
            video["transcript"] = ""
            results.append(video)
            continue

        transcript = _transcribe_file(model, audio_path)

        # 음성이 너무 짧으면 (30자 미만) 음성 없는 영상으로 판단하고 건너뜀
        if len(transcript) < 30:
            print(f"       건너뜀: 음성 내용 부족 (배경음악만 있는 영상으로 추정)")
            video["transcript"] = ""
            results.append(video)
            continue

        video["transcript"] = transcript
        preview = transcript[:100].replace("\n", " ")
        print(f"       완료: \"{preview}...\"" if len(transcript) > 100 else f"       완료: \"{transcript}\"")
        results.append(video)

    print(f"\n[변환 완료] {sum(1 for v in results if v.get('transcript'))}개 영상 변환됨\n")
    return results


def _transcribe_file(model: WhisperModel, audio_path: str) -> str:
    """단일 오디오 파일을 텍스트로 변환합니다."""
    try:
        segments, info = model.transcribe(
            audio_path,
            language="ko",          # 한국어 우선 (None으로 바꾸면 자동 감지)
            beam_size=5,
            vad_filter=True,        # 무음 구간 자동 제거
            vad_parameters=dict(min_silence_duration_ms=500),
        )

        text_parts = [segment.text.strip() for segment in segments]
        return " ".join(text_parts)

    except Exception as e:
        print(f"       변환 오류: {e}")
        return ""
