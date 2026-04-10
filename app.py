"""
TikTok 바이럴 분석기 - 웹 앱
실행: streamlit run app.py
"""

import os
import streamlit as st
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()


# ── 함수 정의 (호출보다 먼저) ────────────────────────────────

def _transcribe_single(model, audio_path: str) -> str:
    try:
        segments, _ = model.transcribe(
            audio_path,
            language="ko",
            beam_size=5,
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=500),
        )
        return " ".join(seg.text.strip() for seg in segments)
    except Exception:
        return ""


def save_results_to_file(results, videos, target_age):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    os.makedirs("output", exist_ok=True)
    path = f"output/scripts_{target_age}대_{timestamp}.txt"

    with open(path, "w", encoding="utf-8") as f:
        f.write(f"TikTok 바이럴 분석 결과\n생성일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("="*60 + "\n\n")
        f.write("[ 바이럴 패턴 분석 ]\n" + results["analysis"] + "\n\n")
        f.write("[ 생성된 원고 ]\n")
        for i, script in enumerate(results["scripts"], 1):
            f.write(f"\n--- 원고 {i} ---\n{script}\n")

    st.success(f"✅ 로컬 파일 저장 완료: `{path}`")


def export_to_notion(notion_token, notion_page_id, keyword, target_age,
                     product_info, urls, videos, results):
    from notion_exporter import save_to_notion
    try:
        with st.spinner("노션에 저장 중..."):
            page_url = save_to_notion(
                notion_token=notion_token,
                database_id=notion_page_id,
                keyword=keyword,
                target_age=target_age,
                product_info=product_info,
                urls=urls,
                videos=videos,
                results=results,
            )
        st.success(f"✅ 노션 저장 완료!")
        st.markdown(f"[📎 노션에서 보기]({page_url})", unsafe_allow_html=False)
    except Exception as e:
        st.error(f"노션 저장 실패: {e}")
        st.caption("Integration이 페이지에 연결되어 있는지 확인해주세요.")


def run_analysis(urls, product_info, api_key, target_age, whisper_model,
                 keyword="탈모", notion_token=None, notion_page_id=None):
    from crawler import _download_audio
    from analyzer import analyze_and_generate
    from faster_whisper import WhisperModel

    output_dir = "output"
    audio_dir = os.path.join(output_dir, "audio")
    os.makedirs(audio_dir, exist_ok=True)

    st.divider()
    st.subheader("📥 영상 다운로드 및 음성 변환")

    # ── 1단계: 다운로드 ──
    videos = []
    download_progress = st.progress(0, text="다운로드 준비 중...")

    for i, url in enumerate(urls):
        download_progress.progress(i / len(urls), text=f"다운로드 중 ({i+1}/{len(urls)}): {url[:50]}...")
        audio_path = _download_audio(url, audio_dir, f"video_{i+1}_{int(datetime.now().timestamp())}")
        if audio_path:
            videos.append({"url": url, "title": f"영상 {i+1}", "audio_path": audio_path, "views": 0, "likes": 0})
        else:
            st.warning(f"⚠️ 다운로드 실패: {url[:60]}")

    download_progress.progress(1.0, text=f"✅ 다운로드 완료 ({len(videos)}/{len(urls)}개)")

    if not videos:
        st.error("다운로드된 영상이 없습니다. URL을 확인해주세요.")
        return

    # ── 2단계: 음성 변환 ──
    st.info(f"🎙️ Whisper({whisper_model}) 모델로 음성 변환 중... (첫 실행 시 모델 다운로드로 수 분 소요)")
    whisper_progress = st.progress(0, text="Whisper 모델 로딩 중...")

    model = WhisperModel(whisper_model, device="cpu", compute_type="int8")

    valid_videos = []
    for i, video in enumerate(videos):
        whisper_progress.progress(i / len(videos), text=f"음성 변환 중 ({i+1}/{len(videos)}): {video['title']}")
        transcript = _transcribe_single(model, video["audio_path"])
        if len(transcript) >= 30:
            video["transcript"] = transcript
            valid_videos.append(video)
        else:
            st.warning(f"⚠️ {video['title']}: 음성 내용 부족 (배경음악만 있는 영상으로 추정)")

    whisper_progress.progress(1.0, text=f"✅ 음성 변환 완료 ({len(valid_videos)}개)")

    if not valid_videos:
        st.error("변환된 음성 원고가 없습니다.")
        return

    # ── 3단계: 영상별 분석 + 원고 생성 + 노션 저장 ──
    from analyzer import analyze_single_video
    from notion_exporter import save_video_to_notion

    st.divider()
    st.subheader("🔍 영상별 분석 및 원고 생성")

    all_results = []
    for i, video in enumerate(valid_videos):
        with st.expander(f"영상 {i+1} 처리 중...", expanded=True):
            st.caption(f"🔗 {video['url'][:60]}...")

            with st.spinner(f"Claude 분석 중 ({i+1}/{len(valid_videos)})..."):
                result = analyze_single_video(
                    transcript=video["transcript"],
                    product_info=product_info,
                    api_key=api_key,
                    target_age=target_age,
                )

            if result.get("title"):
                st.markdown(f"**🎯 썸네일 제목:** `{result['title']}`")

            st.markdown("**📊 대본 분석**")
            st.info(result["analysis"])

            st.markdown("**✍️ 생성된 원고**")
            st.text_area("", value=result["script"], height=250,
                         key=f"script_{i}", label_visibility="collapsed")

            # 노션 저장
            if notion_token and notion_page_id:
                try:
                    page_url = save_video_to_notion(
                        notion_token=notion_token,
                        database_id=notion_page_id,
                        keyword=keyword,
                        product_info=product_info,
                        url=video["url"],
                        transcript=video["transcript"],
                        analysis=result["analysis"],
                        script=result["script"],
                        thumbnail_title=result.get("title", ""),
                    )
                    st.success(f"✅ 노션 저장 완료")
                    st.markdown(f"[📎 노션에서 보기]({page_url})")
                except Exception as e:
                    st.error(f"노션 저장 실패: {e}")

            # 이력 저장
            from history import save_history
            product_name_extracted = ""
            for line in product_info.split("\n"):
                if "제품명" in line:
                    product_name_extracted = line.split(":")[-1].strip()
                    break
            save_history(
                keyword=keyword,
                product_name=product_name_extracted,
                url=video["url"],
                transcript=video["transcript"],
                analysis=result["analysis"],
                script=result["script"],
                title=result.get("title", ""),
            )

            all_results.append({**video, **result})

    # ── 로컬 파일 저장 ──
    save_results_to_file({"analysis": "", "scripts": [r["script"] for r in all_results]},
                         valid_videos, target_age)


# ── 페이지 설정 ──────────────────────────────────────────────

st.set_page_config(
    page_title="TikTok 바이럴 분석기",
    page_icon="🎵",
    layout="wide"
)

st.title("🎵 TikTok 바이럴 분석기")
st.caption("탈모 영상 URL을 붙여넣으면 패턴 분석 후 내 제품 원고를 자동 생성합니다.")

tab_main, tab_history = st.tabs(["🚀 분석 시작", "📋 분석 이력"])

# ── 사이드바 ─────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ 설정")

    api_key = st.text_input(
        "Anthropic API 키",
        value=os.getenv("ANTHROPIC_API_KEY", ""),
        type="password",
        help="console.anthropic.com 에서 발급"
    )

    st.divider()
    st.header("📦 내 제품 정보")

    from profiles import load_profiles, save_profile, delete_profile, get_profile_names

    profile_names = get_profile_names()
    options = ["✏️ 직접 입력 (새 제품)"] + profile_names
    selected = st.selectbox("저장된 프로필 선택", options, index=0)

    # 선택된 프로필 데이터 불러오기
    if selected != "✏️ 직접 입력 (새 제품)":
        profiles = load_profiles()
        p = profiles.get(selected, {})
    else:
        p = {}

    product_name     = st.text_input("제품명", value=p.get("name", ""), placeholder="예: 헤어케어 앰플")
    product_features = st.text_area("주요 효능/특징", value=p.get("features", ""),
                                    placeholder="예: 탈모 완화, 두피 영양 공급, 천연 성분", height=80)
    product_target   = st.text_input("타겟 고객", value=p.get("target", "50-60대"),
                                     placeholder="예: 탈모 고민 있는 50-60대 남녀")
    product_diff     = st.text_area("경쟁 제품 대비 차별점", value=p.get("diff", ""),
                                    placeholder="예: 병원 처방 성분 동일, 부작용 없음", height=80)
    product_extra    = st.text_area("➕ 오늘만 추가할 내용 (선택)",
                                    placeholder="예: 이번 주 할인 이벤트 중, 신규 성분 추가됨",
                                    height=60)

    # 프로필 저장/삭제 버튼
    col_save, col_del = st.columns(2)
    with col_save:
        save_name = st.text_input("저장할 프로필 이름", value=product_name, label_visibility="collapsed",
                                  placeholder="프로필 이름 입력 후 저장")
        if st.button("💾 프로필 저장", use_container_width=True):
            if save_name and product_name:
                save_profile(save_name, {
                    "name": product_name,
                    "features": product_features,
                    "target": product_target,
                    "diff": product_diff,
                })
                st.success(f"저장됨: {save_name}")
                st.rerun()
            else:
                st.warning("제품명을 먼저 입력해주세요.")
    with col_del:
        if selected != "✏️ 직접 입력 (새 제품)":
            if st.button("🗑️ 프로필 삭제", use_container_width=True):
                delete_profile(selected)
                st.success(f"삭제됨: {selected}")
                st.rerun()

    target_age = st.selectbox("타겟 연령대", ["5060", "4050", "2030", "6070"], index=0)
    whisper_model = st.selectbox(
        "Whisper 모델",
        ["small", "base", "tiny", "medium"],
        index=0,
        help="small 권장 / medium: 더 정확하지만 느림"
    )

    st.divider()
    st.header("📒 노션 연동")
    notion_token = st.text_input(
        "Notion Integration Token",
        value=os.getenv("NOTION_TOKEN", ""),
        type="password",
        placeholder="ntn_...",
        help="notion.so/my-integrations 에서 발급"
    )
    notion_database_id = st.text_input(
        "노션 데이터베이스 ID",
        value=os.getenv("NOTION_DATABASE_ID", ""),
        placeholder="데이터베이스 URL 32자리",
        help="노션 데이터베이스 URL에서 복사"
    )
    use_notion = st.toggle("분석 완료 시 노션 자동 저장", value=bool(notion_token and notion_database_id))

# ── 탭1: 분석 시작 ───────────────────────────────────────────
with tab_main:
    st.subheader("📎 영상 URL 입력")
    keyword = st.text_input("키워드 (노션 저장 시 태그로 사용)", placeholder="예: 탈모, 중년탈모", value="탈모")
    st.caption("TikTok 또는 YouTube Shorts 링크를 한 줄에 하나씩 붙여넣기 (혼합 가능)")

    urls_input = st.text_area(
        "URL 목록",
        placeholder="https://www.tiktok.com/@user1/video/...\nhttps://youtube.com/shorts/...\nhttps://www.youtube.com/watch?v=...",
        height=200,
        label_visibility="collapsed"
    )

    col1, col2 = st.columns([1, 4])
    with col1:
        run_btn = st.button("🚀 분석 시작", type="primary", use_container_width=True)

    if run_btn:
        errors = []
        if not api_key:
            errors.append("사이드바에서 Anthropic API 키를 입력해주세요.")
        if not product_name:
            errors.append("사이드바에서 제품명을 입력해주세요.")
        if not urls_input.strip():
            errors.append("분석할 TikTok URL을 입력해주세요.")

        urls = [u.strip() for u in urls_input.strip().split("\n") if u.strip().startswith("http")]
        if not urls:
            errors.append("유효한 TikTok URL이 없습니다. (http로 시작하는 URL을 입력해주세요)")

        if errors:
            for e in errors:
                st.error(e)
        else:
            product_info = f"""제품명: {product_name}
주요 특징/효능: {product_features}
타겟 고객: {product_target}
차별점: {product_diff}"""
            if product_extra.strip():
                product_info += f"\n오늘 추가 강조사항: {product_extra}"

            run_analysis(urls, product_info, api_key, target_age, whisper_model,
                         keyword=keyword,
                         notion_token=notion_token if use_notion else None,
                         notion_page_id=notion_database_id if use_notion else None)

# ── 탭2: 분석 이력 ───────────────────────────────────────────
with tab_history:
    from history import load_history, delete_history

    st.subheader("📋 분석 이력")

    records = load_history()

    if not records:
        st.info("아직 분석 이력이 없습니다. 영상을 분석하면 여기에 자동으로 저장됩니다.")
    else:
        # 검색/필터
        col_search, col_filter = st.columns([2, 1])
        with col_search:
            search = st.text_input("🔍 검색", placeholder="키워드, 제품명, 제목으로 검색", label_visibility="collapsed")
        with col_filter:
            keywords = ["전체"] + list(set(r.get("keyword", "") for r in records if r.get("keyword")))
            filter_keyword = st.selectbox("키워드 필터", keywords, label_visibility="collapsed")

        # 필터링
        filtered = records
        if filter_keyword != "전체":
            filtered = [r for r in filtered if r.get("keyword") == filter_keyword]
        if search:
            filtered = [r for r in filtered if
                        search.lower() in r.get("keyword", "").lower() or
                        search.lower() in r.get("product_name", "").lower() or
                        search.lower() in r.get("title", "").lower() or
                        search.lower() in r.get("script", "").lower()]

        st.caption(f"총 {len(filtered)}건")

        for record in filtered:
            title = record.get("title") or f"[{record.get('keyword')}] {record.get('product_name')}"
            with st.expander(f"**{title}** — {record.get('date')} · {record.get('keyword')} · {record.get('product_name')}"):

                col_url, col_del = st.columns([4, 1])
                with col_url:
                    st.caption(f"🔗 {record.get('url', '')[:80]}")
                with col_del:
                    if st.button("🗑️ 삭제", key=f"del_{record['id']}"):
                        delete_history(record["id"])
                        st.rerun()

                st.markdown("**📊 대본 분석**")
                st.info(record.get("analysis", ""))

                st.markdown("**✍️ 생성된 원고**")
                st.text_area("", value=record.get("script", ""), height=250,
                             key=f"hist_script_{record['id']}", label_visibility="collapsed")
