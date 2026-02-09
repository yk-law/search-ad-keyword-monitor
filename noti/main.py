from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from contextlib import asynccontextmanager
import asyncio
import argparse
import os, sys
import uvicorn
import version
import config
from config import NWORKS, find_chat_uids, load_config
from naverworks_api import NaverWorksAPI
from typing import List, Optional
from logger import setup_logger
import logging

# 로깅 설정
logging_config = setup_logger()
logger = logging.getLogger("noti")

# 전역 변수
nworks = None


# Pydantic 모델 정의
class NotificationRequest(BaseModel):
    event_type: str
    args: list
    message: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    global nworks  # 전역 변수 사용

    logger.warning("🚀 Starting Noti Server")

    # 네이버웍스 API 초기화
    nworks = NaverWorksAPI(
        client_id=NWORKS.get("NWORKS_CLIENT_ID"),
        client_secret=NWORKS.get("NWORKS_CLIENT_SECRET"),
        service_account=NWORKS.get("NWORKS_SERVICE_ACCOUNT"),
        private_key_path=NWORKS.get("NWORKS_PRIVATE_KEY_PATH"),
        bot_id=NWORKS.get("NWORKS_BOT_ID"),
    )

    # 네이버웍스 엑세스 토큰 초기 갱신
    try:
        nworks.refresh_access_token()
        logger.info("✅ 네이버웍스 엑세스 토큰 갱신 완료.")
    except Exception as e:
        logger.error(f"⚠️ 네이버웍스 엑세스 토큰 갱신 실패: {e}")

    # 🔹 백그라운드 태스크 실행 (토큰 자동 갱신)
    nworks.token_refresh_task = asyncio.create_task(nworks.refresh_access_token_task())

    yield  # 앱 실행

    # 서버 종료 시 백그라운드 태스크 정리
    if nworks.token_refresh_task:
        nworks.token_refresh_task.cancel()
        logger.info("🛑 서버 종료: 토큰 갱신 태스크 중지됨.")


# FastAPI 앱 생성 및 lifespan 적용
app = FastAPI(lifespan=lifespan)


@app.get("/status")
def get_status():
    return JSONResponse(status_code=200, content={"pid": os.getpid()})


@app.post("/reload-config")
def reload_config():
    """설정 파일 다시 로드"""
    try:
        load_config()
        logger.info("🔄 config.yaml 파일이 다시 로드되었습니다.")
        return {"status": "success", "message": "Configuration reloaded."}
    except Exception as e:
        logger.error(f"⚠️ config.yaml 파일 로드 실패: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to reload config: {str(e)}"
        )


class EventNotiRequest(BaseModel):
    event_type: str
    args: Optional[List[str]] = []
    message: str
    url_link: str = None


@app.post("/send-event-noti")
def send_event_notification(request: EventNotiRequest):
    expanded_args = []
    for arg in request.args:
        if "=" in arg and "," in arg:  # ✅ 여러 값이 포함된 경우
            key, values = arg.split("=")
            for value in values.split(","):
                expanded_args.append(
                    f"{key}={value.strip()}"
                )  # ✅ 각 값을 개별 항목으로 변환
        else:
            expanded_args.append(arg)

    chat_uids = find_chat_uids(request.event_type, expanded_args)

    if not chat_uids:
        logger.error(
            f"⚠️ 해당 이벤트에 대한 Chat UID를 찾을 수 없습니다: {request.event_type}, {request.args}"
        )
        return JSONResponse(
            status_code=404,
            content={"status": "fail", "reason": "No matching Chat UID found"},
        )

    success_responses = []
    failed_responses = []

    for chat_uid in chat_uids:
        try:
            response_data = nworks.send_message_to_channel(
                chat_uid, request.message, request.url_link
            )

            if response_data.get("result") == "success":
                success_responses.append(
                    {"chat_uid": chat_uid, "response": response_data}
                )
                logger.debug(
                    f"✅ 알림 전송 성공: {request.event_type}, {request.args}, {chat_uid} -> {response_data}"
                )
            else:
                failed_responses.append({"chat_uid": chat_uid, "error": response_data})
                logger.error(
                    f"⚠️ 알림 전송 실패: {request.event_type}, {request.args}, {chat_uid} -> {response_data}"
                )

        except Exception as e:
            error_message = str(e)
            failed_responses.append({"chat_uid": chat_uid, "error": error_message})
            logger.error(f"⚠️ noti API 호출 중 오류 발생: {error_message}")

    # ✅ 하나라도 실패한 경우, 전체 실패 응답 반환
    if failed_responses:
        return JSONResponse(
            status_code=(
                500 if not success_responses else 207
            ),  # ✅ 모두 실패하면 500, 일부 성공하면 207 Multi-Status
            content={
                "status": "partial_success" if success_responses else "fail",
                "success_count": len(success_responses),
                "failure_count": len(failed_responses),
                "failures": failed_responses,
            },
        )

    # ✅ 모든 메시지 전송 성공 시 200 OK 반환
    return JSONResponse(
        status_code=200, content={"status": "success", "sent_to": success_responses}
    )


class MessageNotiRequest(BaseModel):
    chat_uid: str
    message: str


@app.post("/send-message-noti")
def send_message_notification(request: MessageNotiRequest):
    chat_uid = request.chat_uid

    error_message = None

    try:
        response_data = nworks.send_message_to_channel(chat_uid, request.message)

        if response_data.get("result") == "success":
            logger.debug(f"✅ 알림 전송 성공: {chat_uid} -> {response_data}")
        else:
            logger.error(f"⚠️ 알림 전송 실패: {chat_uid} -> {response_data}")
            error_message = response_data

    except Exception as e:
        error_message = str(e)
        logger.error(f"⚠️ noti API 호출 중 오류 발생: {error_message}")

    if error_message:
        return JSONResponse(
            status_code=500, content={"status": "fail", "error": error_message}
        )

    return JSONResponse(status_code=200, content={"status": "success"})


class ImageNotiRequest(BaseModel):
    chat_uid: str
    image_url: str


@app.post("/send-image-noti")
def send_image_notification(request: ImageNotiRequest):
    chat_uid = request.chat_uid

    error_message = None

    try:
        response_data = nworks.send_image_to_channel(chat_uid, request.image_url)

        if response_data.get("result") == "success":
            logger.debug(f"✅ 알림 전송 성공: {chat_uid} -> {response_data}")
        else:
            logger.error(f"⚠️ 알림 전송 실패: {chat_uid} -> {response_data}")
            error_message = response_data

    except Exception as e:
        error_message = str(e)
        logger.error(f"⚠️ noti API 호출 중 오류 발생: {error_message}")

    if error_message:
        return JSONResponse(
            status_code=500, content={"status": "fail", "error": error_message}
        )

    return JSONResponse(status_code=200, content={"status": "success"})


DEFAULT_PORT = int(os.getenv("YKOS_NOTI_PORT", "10002"))

parser = argparse.ArgumentParser(description="Run the Noti server")
parser.add_argument(
    "-c", "--config", type=str, help="Path to the config.yaml file", default=None
)
parser.add_argument("--host", type=str, default="0.0.0.0", help="Host address")
parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Port number")
parser.add_argument("--reload", action="store_true", help="Enable reload")
parser.add_argument(
    "--no-reload", action="store_false", dest="reload", help="Disable reload"
)
parser.set_defaults(reload=True)

args = parser.parse_args()

if __name__ == "__main__":
    logger.info("Starting Noti")

    uvicorn.run(
        "main:app",
        host=args.host,
        port=args.port,
        log_config=logging_config,
        reload=args.reload,
    )
