import os
import sys
import argparse
import yaml
from typing import List
from collections import defaultdict


def get_basedir():
    """PyInstaller 실행 여부에 따라 기반 디렉토리를 반환"""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.abspath(__file__))

def get_config_path():
    """config.yaml 파일 경로 반환 (Argument Parser 포함)"""
    parser = argparse.ArgumentParser(description="Configuration for the application", add_help=False)
    parser.add_argument("-c", "--config", type=str, help="Path to the config.yaml file", default=None)
    args, _ = parser.parse_known_args()

    if args.config:
        return args.config
    else:
        basedir = get_basedir()
        return os.path.join(basedir, "config/config.yaml")

# 설정 파일 경로
CONFIG_PATH = get_config_path()

# 초기화된 설정 변수
CONFIG = {}
NWORKS = {}
LOGGING_FILE_PATH = "/tmp"
LOGGING_FILE_MAX_BACKUP_COUNT = 3
NOTIFICATIONS = []

def load_config():
    """config.yaml 파일을 다시 로드"""
    global CONFIG, NWORKS, LOGGING_FILE_PATH, LOGGING_FILE_MAX_BACKUP_COUNT, NOTIFICATIONS

    with open(CONFIG_PATH, "r") as file:
        CONFIG = yaml.safe_load(file)

    # 주요 설정 변수 업데이트
    NWORKS = CONFIG.get("NWORKS", {})
    LOGGING_FILE_PATH = CONFIG["LOGGING"].get("FILE_PATH", "/tmp")
    LOGGING_FILE_MAX_BACKUP_COUNT = CONFIG["LOGGING"].get("MAX_BACKUP_COUNT", 3)

    # 알림 설정 로드
    NOTIFICATIONS = CONFIG.get("NOTIFICATIONS", [])

# 초기 설정 로드
load_config()

def find_chat_uids(event_type: str, args: List[str]) -> List[str]:
    """이벤트 타입 및 인자에 따른 모든 Chat UID 찾기"""
    matched_chat_uids = []

    # ✅ 입력 `args`를 `dict` 형태로 변환 (같은 키에 여러 값이 있을 경우 리스트로 저장)
    parsed_input_args = defaultdict(list)
    for arg in args:
        key, value = arg.split("=")
        parsed_input_args[key].append(value)

    for notification in NOTIFICATIONS:
        notification_event_type = notification["EVENT_TYPE"]

        # ✅ EVENT_TYPE이 리스트인 경우 OR 조건으로 비교
        if isinstance(notification_event_type, list):
            if event_type not in notification_event_type:
                continue  # OR 조건에 포함되지 않으면 스킵
        else:
            if event_type != notification_event_type:
                continue  # 기존 단일 매칭

        notification_args_list = notification.get("ARGS", [])

        # ✅ 입력 `args`가 없고, 설정에도 `ARGS`가 없으면 매칭
        if not args and not notification_args_list:
            matched_chat_uids.append(notification.get("CHAT_UID"))
            continue  # ✅ 다음 설정 확인

        # ✅ 입력 `args`가 없는데, 설정에 `ARGS`가 있는 경우 매칭 X
        if not args and notification_args_list:
            continue

        # ✅ 설정된 `ARGS`의 각 조건을 `&`로 나누고, 모든 조건을 만족해야 매칭
        for notification_args in notification_args_list:
            conditions = notification_args.split("&")
            parsed_conditions = {cond.split("=")[0]: cond.split("=")[1] for cond in conditions}

            # ✅ 모든 조건이 입력 args에서 매칭되어야 함 (`*`인 경우 존재 여부만 체크)
            is_match = True
            for key, value in parsed_conditions.items():
                if value == "*":
                    if key not in parsed_input_args:
                        is_match = False
                        break
                elif value not in parsed_input_args.get(key, []):
                    is_match = False
                    break

            if is_match:
                matched_chat_uids.append(notification.get("CHAT_UID"))
                break

    return matched_chat_uids