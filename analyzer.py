"""
영상 분석 및 원고 생성 모듈 (Claude API 기반)
바이럴 영상 패턴을 분석하고 내 제품에 맞는 원고를 생성합니다.
"""

import anthropic


def analyze_and_generate(
    videos: list[dict],
    product_info: str,
    api_key: str,
    target_age: str = "5060",
) -> dict:
    """
    수집된 영상 원고를 분석하고 내 제품용 TikTok 원고를 생성합니다.

    Args:
        videos: transcript가 포함된 영상 목록
        product_info: 제품명과 주요 특징 (사용자 입력)
        api_key: Anthropic API 키

    Returns:
        {
            "analysis": "바이럴 패턴 분석 결과",
            "scripts": ["원고1", "원고2", "원고3"]
        }
    """
    client = anthropic.Anthropic(api_key=api_key)

    # 유효한 스크립트만 필터링
    valid_videos = [v for v in videos if v.get("transcript", "").strip()]

    if not valid_videos:
        return {
            "analysis": "분석할 영상 원고가 없습니다.",
            "scripts": []
        }

    # 영상 원고 목록 정리
    transcripts_text = ""
    for i, video in enumerate(valid_videos, 1):
        views = video.get("views", 0)
        likes = video.get("likes", 0)
        views_str = f"{views:,}회" if views else "정보없음"
        likes_str = f"{likes:,}개" if likes else "정보없음"
        transcripts_text += f"""
---영상 {i} (조회수: {views_str}, 좋아요: {likes_str})---
{video['transcript']}
"""

    # Step 1: 패턴 분석
    print("[분석] 바이럴 패턴 분석 중...")
    analysis = _analyze_patterns(client, transcripts_text, target_age)
    print(f"[분석 완료]\n")

    # Step 2: 원고 생성
    print("[생성] 내 제품용 TikTok 원고 생성 중...")
    scripts = _generate_scripts(client, analysis, transcripts_text, product_info, target_age)
    print(f"[생성 완료] {len(scripts)}개 원고 작성됨\n")

    return {
        "analysis": analysis,
        "scripts": scripts
    }


def _analyze_patterns(client: anthropic.Anthropic, transcripts_text: str, target_age: str) -> str:
    """바이럴 영상들의 공통 패턴을 분석합니다."""

    age_context = _get_age_context(target_age)

    response = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=1500,
        messages=[{
            "role": "user",
            "content": f"""다음은 TikTok에서 바이럴된 영상들의 원고입니다.
타겟 시청자: {target_age}대 ({age_context})

{transcripts_text}

위 영상들을 분석해서 다음 항목을 정리해주세요:

1. **후킹 패턴** - 영상 첫 3초에 어떤 방식으로 {target_age}대 시청자를 잡는지
2. **스토리 구조** - 문제제기 → 해결책 → CTA 흐름. {target_age}대가 공감하는 문제를 어떻게 표현하는지
3. **언어/어조** - {target_age}대에게 어필하는 단어, 말투, 감성적 요소
4. **신뢰 구축 방식** - {target_age}대가 믿음을 갖게 하는 표현 (경험담, 수치, 전문성 등)
5. **CTA 방식** - {target_age}대가 행동하게 만드는 마무리 방식

마크다운 없이 항목별로 간결하게 작성해주세요."""
        }]
    )
    return response.content[0].text


def _generate_scripts(
    client: anthropic.Anthropic,
    analysis: str,
    transcripts_text: str,
    product_info: str,
    target_age: str = "5060",
) -> list[str]:
    """분석 결과를 바탕으로 내 제품용 TikTok 원고 3개를 생성합니다."""

    age_context = _get_age_context(target_age)

    response = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=3000,
        messages=[{
            "role": "user",
            "content": f"""다음은 TikTok 바이럴 영상 패턴 분석 결과입니다:

=== 바이럴 패턴 분석 ===
{analysis}

=== 참고 영상 원고 ===
{transcripts_text}

=== 내 제품 정보 ===
{product_info}

=== 타겟 시청자 ===
{target_age}대 ({age_context})

위 바이럴 패턴을 활용해서 내 제품을 홍보하는 TikTok 영상 원고를 3개 작성해주세요.

조건:
- 타겟은 {target_age}대 — {age_context}에 맞는 언어, 공감대, 신뢰 요소 사용
- 각 원고는 30~60초 분량 (말하기 기준 약 100~180단어)
- 바이럴 영상의 후킹 방식과 스토리 구조를 그대로 적용
- 한국어로 자연스럽고 구어체로 작성 (너무 젊은 말투 금지)
- 각 원고는 다른 각도로 접근: 원고1(공감/경험담), 원고2(놀라운 사실/정보), 원고3(비교/결과)
- 원고 사이에 "---원고1---", "---원고2---", "---원고3---" 구분자 사용

원고만 작성하고 설명은 생략해주세요."""
        }]
    )

    raw = response.content[0].text

    # 원고 분리
    scripts = []
    for marker in ["---원고1---", "---원고2---", "---원고3---"]:
        if marker in raw:
            parts = raw.split(marker)
            if len(parts) > 1:
                next_markers = ["---원고1---", "---원고2---", "---원고3---"]
                content = parts[1]
                for nm in next_markers:
                    if nm != marker and nm in content:
                        content = content.split(nm)[0]
                scripts.append(content.strip())

    if not scripts:
        scripts = [raw.strip()]

    return scripts


def analyze_single_video(
    transcript: str,
    product_info: str,
    api_key: str,
    target_age: str = "5060",
) -> dict:
    """
    영상 1개를 분석하고 내 제품용 원고 1개를 생성합니다.

    Returns:
        {"analysis": "분석결과", "script": "생성된 원고"}
    """
    client = anthropic.Anthropic(api_key=api_key)
    age_context = _get_age_context(target_age)

    # 분석 + 원고 생성을 한 번에 요청
    response = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=2000,
        messages=[{
            "role": "user",
            "content": f"""다음은 TikTok 바이럴 영상의 원고입니다.
타겟: {target_age}대 ({age_context})

=== 영상 원고 ===
{transcript}

=== 내 제품 정보 ===
{product_info}

아래 두 가지를 작성해주세요:

[대본 분석]
이 영상이 {target_age}대에게 반응을 얻은 이유를 분석해주세요:
- 후킹 방식 (첫 3초)
- 스토리 구조
- 공감 포인트
- CTA 방식
(5줄 이내로 간결하게)

[생성된 원고]
위 영상의 패턴을 활용해서 내 제품을 홍보하는 TikTok 원고를 1개 작성해주세요.
- {target_age}대 타겟에 맞는 어조
- 30~60초 분량 (100~180단어)
- 구어체, 자연스럽게

반드시 아래 3개 구분자를 사용해주세요:
"[썸네일 제목]" — 15자 이내, 숫자(50대/60대) 포함, 직관적이고 강렬하게, 예: "50대 탈모 이거 하나로 끝냄"
"[대본 분석]" — 분석 내용
"[생성된 원고]" — 원고 내용"""
        }]
    )

    raw = response.content[0].text

    title = ""
    analysis = ""
    script = ""

    if "[썸네일 제목]" in raw:
        after_title = raw.split("[썸네일 제목]")[1]
        title = after_title.split("[대본 분석]")[0].strip() if "[대본 분석]" in after_title else after_title[:30].strip()

    if "[대본 분석]" in raw and "[생성된 원고]" in raw:
        parts = raw.split("[생성된 원고]")
        analysis = parts[0].replace("[대본 분석]", "").replace("[썸네일 제목]", "").replace(title, "").strip()
        script = parts[1].strip()
    else:
        analysis = raw[:500]
        script = raw[500:].strip()

    return {"title": title, "analysis": analysis, "script": script}


def _get_age_context(target_age: str) -> str:
    """연령대별 특성 설명 반환"""
    contexts = {
        "2030": "트렌드에 민감하고 짧고 임팩트 있는 콘텐츠 선호, 유머/챌린지에 반응",
        "4050": "실용적 정보와 검증된 효과를 중시, 가족/건강/경제적 가치에 공감",
        "5060": "신뢰와 전문성을 중시, 직접적인 효능과 경험담에 반응, 과장보다 진정성 선호, 건강과 젊음 유지에 관심",
        "6070": "쉽고 친근한 설명 선호, 또래의 경험담에 강하게 공감, 건강 회복과 일상 불편 해소에 집중",
    }
    return contexts.get(target_age, f"{target_age}대 타겟, 해당 연령대의 관심사와 언어에 맞게 작성")
