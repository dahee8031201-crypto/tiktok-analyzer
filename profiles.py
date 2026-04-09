"""
제품 프로필 저장/불러오기 모듈
profiles.json 파일에 제품 정보를 저장합니다.
"""

import json
import os

PROFILES_PATH = os.path.join(os.path.dirname(__file__), "profiles.json")


def load_profiles() -> dict:
    """저장된 프로필 전체 불러오기"""
    if not os.path.exists(PROFILES_PATH):
        return {}
    with open(PROFILES_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_profile(name: str, data: dict):
    """프로필 저장 (덮어쓰기)"""
    profiles = load_profiles()
    profiles[name] = data
    with open(PROFILES_PATH, "w", encoding="utf-8") as f:
        json.dump(profiles, f, ensure_ascii=False, indent=2)


def delete_profile(name: str):
    """프로필 삭제"""
    profiles = load_profiles()
    if name in profiles:
        del profiles[name]
        with open(PROFILES_PATH, "w", encoding="utf-8") as f:
            json.dump(profiles, f, ensure_ascii=False, indent=2)


def get_profile_names() -> list[str]:
    """저장된 프로필 이름 목록"""
    return list(load_profiles().keys())
