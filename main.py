"""
TikTok 바이럴 영상 분석 및 원고 생성기
사용법:
  python main.py --keyword 탈모 --count 10
  python main.py --keyword 탈모 --urls-file urls.txt   # URL 파일로 한 번에 입력
"""

import os
import sys
import argparse
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()


def check_dependencies():
    """필수 패키지 설치 여부 확인"""
    missing = []
    for pkg in ["yt_dlp", "faster_whisper", "anthropic"]:
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg.replace("_", "-"))

    if missing:
        print(f"\n[오류] 다음 패키지가 설치되어 있지 않습니다: {', '.join(missing)}")
        print("아래 명령어로 설치해주세요:\n")
        print("  pip install -r requirements.txt\n")
        sys.exit(1)


def get_product_info(product_arg: str | None) -> str:
    """제품 정보 입력 받기"""
    if product_arg:
        return product_arg

    print("\n" + "="*50)
    print("제품 정보 입력")
    print("="*50)
    print("원고 생성에 사용될 제품 정보를 입력해주세요.\n")

    name = input("제품명: ").strip()
    features = input("주요 특징/효능 (쉼표로 구분): ").strip()
    target = input("타겟 고객 (예: 다이어트 중인 20-30대 여성): ").strip()
    differentiation = input("경쟁 제품 대비 차별점: ").strip()

    return f"""제품명: {name}
주요 특징/효능: {features}
타겟 고객: {target}
차별점: {differentiation}"""


def save_results(results: dict, videos: list[dict], output_dir: str, keyword: str):
    """결과를 텍스트 파일로 저장"""
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(output_dir, f"scripts_{keyword}_{timestamp}.txt")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(f"TikTok 바이럴 분석 결과\n")
        f.write(f"키워드: #{keyword}\n")
        f.write(f"생성일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("="*60 + "\n\n")

        # 수집된 원고들
        f.write("[ 수집된 바이럴 영상 원고 ]\n")
        f.write("-"*40 + "\n")
        for i, video in enumerate(videos, 1):
            if video.get("transcript"):
                f.write(f"\n영상 {i}: {video['title'][:50]}\n")
                if video.get("views"):
                    f.write(f"조회수: {video['views']:,} | 좋아요: {video.get('likes', 0):,}\n")
                f.write(f"{video['transcript']}\n")
        f.write("\n")

        # 패턴 분석
        f.write("[ 바이럴 패턴 분석 ]\n")
        f.write("-"*40 + "\n")
        f.write(results["analysis"] + "\n\n")

        # 생성된 원고
        f.write("[ 내 제품용 TikTok 원고 ]\n")
        f.write("-"*40 + "\n")
        for i, script in enumerate(results["scripts"], 1):
            f.write(f"\n[ 원고 {i} ]\n")
            f.write(script + "\n")

    return output_path


def main():
    parser = argparse.ArgumentParser(
        description="TikTok 바이럴 영상 분석 및 원고 생성기",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  python main.py --keyword 단백질쉐이크 --count 5
  python main.py --keyword 다이어트음료 --count 3 --model small
  python main.py --keyword 건강음료 --product "제품명: 그린밀 / 특징: 저칼로리 식사대용"
        """
    )
    parser.add_argument("--keyword", required=True,
                        help="TikTok 검색 키워드 또는 해시태그 (예: 단백질쉐이크)")
    parser.add_argument("--count", type=int, default=10,
                        help="수집할 영상 수 (기본: 10)")
    parser.add_argument("--urls-file", type=str, default=None,
                        help="URL 목록 텍스트 파일 경로 (한 줄에 URL 하나, 예: urls.txt)")
    parser.add_argument("--target-age", type=str, default="5060",
                        help="타겟 연령대 (기본: 5060, 예: 2030, 4050)")
    parser.add_argument("--product", type=str, default=None,
                        help="제품 정보 문자열 (없으면 실행 중 입력)")
    parser.add_argument("--model", type=str, default="small",
                        choices=["tiny", "base", "small", "medium"],
                        help="Whisper 모델 크기 (기본: small)")
    parser.add_argument("--output", type=str, default="output",
                        help="결과 저장 폴더 (기본: output)")
    args = parser.parse_args()

    # 의존성 확인
    check_dependencies()

    # API 키 확인
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("\n[오류] ANTHROPIC_API_KEY가 설정되어 있지 않습니다.")
        print(".env 파일에 API 키를 추가해주세요:")
        print("  ANTHROPIC_API_KEY=sk-ant-...\n")
        sys.exit(1)

    print("\n" + "="*50)
    print("TikTok 바이럴 영상 분석기")
    print("="*50)
    print(f"키워드: #{args.keyword}")
    print(f"타겟 연령대: {args.target_age}대")
    print(f"수집 목표: {args.count}개")
    print(f"Whisper 모델: {args.model}")
    print("="*50)

    # 제품 정보 수집
    product_info = get_product_info(args.product)

    # 1단계: 영상 수집
    from crawler import collect_videos, collect_from_urls_file
    if args.urls_file:
        videos = collect_from_urls_file(args.urls_file, args.output)
    else:
        videos = collect_videos(args.keyword, args.count, args.output)

    if not videos:
        print("\n[종료] 수집된 영상이 없습니다.")
        sys.exit(1)

    # 2단계: 음성 → 텍스트 변환
    from transcriber import transcribe_videos
    videos = transcribe_videos(videos, model_size=args.model)

    valid_count = sum(1 for v in videos if v.get("transcript", "").strip())
    if valid_count == 0:
        print("\n[종료] 변환된 원고가 없습니다. ffmpeg가 설치되어 있는지 확인해주세요.")
        sys.exit(1)

    # 3단계: 분석 및 원고 생성
    from analyzer import analyze_and_generate
    results = analyze_and_generate(videos, product_info, api_key, target_age=args.target_age)

    # 결과 출력
    print("="*50)
    print("[ 바이럴 패턴 분석 결과 ]")
    print("="*50)
    print(results["analysis"])

    print("\n" + "="*50)
    print("[ 생성된 TikTok 원고 ]")
    print("="*50)
    for i, script in enumerate(results["scripts"], 1):
        print(f"\n--- 원고 {i} ---")
        print(script)

    # 파일 저장
    output_path = save_results(results, videos, args.output, args.keyword)
    print(f"\n\n결과 파일 저장 완료: {output_path}")


if __name__ == "__main__":
    main()
