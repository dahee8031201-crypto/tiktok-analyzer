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

반드시 아래 스토리 구조를 따르세요:

① 첫 후킹 (1~2줄) — 권위자 발언으로 시작
  - 아래 중 랜덤으로 1개 선택:
    · "탈모병원 원장님이 그러시더라고요."
    · "영양사 선생님한테 들은 얘긴데요."
    · "피부과 선생님이 딱 한 마디 하셨어요."
    · "연예인들이 챙겨먹는다는 거 따라해봤어요."
    · "헤어 디자이너가 알려준 방법인데요."
  - 이어서 핵심 한 마디: "바르는 건 한계 있어요. 안에서부터 채워야 해요." 같은 반전 발언

② 공감 (1~2줄) — "{target_age}대 타겟이 고개 끄덕일 불편함"
  예: "저도 한 달에 한 번 염색하면서 두피 따갑고, 돈만 나가고."

③ 제품 소개 (2~3줄) — 자연스럽게
  - 제품명 + 핵심 성분/효능을 쉽게 설명

④ 변화/결과 (1~2줄) — 구체적이고 놀라운 변화
  예: "어느 날 보니까 뿌리에서 검은 머리가 올라오고 있는 거예요. 신기하더라고요."

⑤ 자연스러운 CTA (1줄) — 강요 아닌 제안
  예: "궁금하신 분 댓글에 [키워드] 남겨주세요."

추가 조건:
- {target_age}대 타겟 어조 (진정성, 또래 경험담 느낌)
- 40~50초 분량 (80~120단어), 1.3배속 기준 30~40초
- 구어체, 자연스럽게
- 과장/허위 표현 금지

반드시 아래 3개 구분자를 사용해주세요:

"[썸네일 제목]"
— 10자 이내로 짧고 굵게
— 아래 공식 중 하나를 골라서 작성:
  · "~있으면 꼭 보세요" (예: 흰머리 있으면 꼭 보세요)
  · "~후회합니다/후회해요" (예: 이거 놓치면 후회해요)
  · "~달라졌어요/사라졌어요/까매졌어요" (예: 뿌리부터 까매졌어요)
  · "N세/50대/60대 + 결과" (예: 54세 새치 없애는 법)
  · "바르지 말고/먹어야/이걸" 반전 공식 (예: 바르지 말고 이걸 드세요)
— 절대 문장형 금지, 과장 표현 금지

"[대본 분석]" — 분석 내용
"[생성된 원고]" — 원고 내용"""
        }]
    )

    raw = response.content[0].text

    title = ""
    analysis = ""
    script = ""

    # 썸네일 제목 추출
    if "[썸네일 제목]" in raw:
        after_title = raw.split("[썸네일 제목]")[1]
        # 다음 구분자 전까지만 추출
        for delimiter in ["[대본 분석]", "[생성된 원고]"]:
            if delimiter in after_title:
                after_title = after_title.split(delimiter)[0]
        # 마크다운 ** 제거, 앞뒤 공백 제거
        title = after_title.strip().replace("**", "").replace("*", "").strip()
        # 첫 줄만 사용 (여러 줄이면 첫 줄이 제목)
        title = title.split("\n")[0].strip()

    # 대본 분석 추출
    if "[대본 분석]" in raw and "[생성된 원고]" in raw:
        analysis_part = raw.split("[대본 분석]")[1].split("[생성된 원고]")[0]
        analysis = analysis_part.strip()
        script = raw.split("[생성된 원고]")[1].strip()
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
