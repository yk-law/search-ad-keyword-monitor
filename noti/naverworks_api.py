import requests
import asyncio
import jwt
import time

import logging

logger = logging.getLogger("noti")


class NaverWorksAPI:
    def __init__(
        self, client_id, client_secret, service_account, private_key_path, bot_id
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.service_account = service_account
        self.private_key_path = private_key_path
        self.bot_id = bot_id
        self.access_token = None
        self.token_refresh_task = None  # ✅ 백그라운드 태스크 추가

    def refresh_access_token(self):
        """네이버웍스 API용 액세스 토큰 갱신"""
        url = "https://auth.worksmobile.com/oauth2/v2.0/token"
        headers = {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}
        data = {
            "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
            "assertion": self.generate_jwt(),
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "scope": "bot user.read",
        }

        response = requests.post(url, headers=headers, data=data)
        if response.status_code == 200:
            self.access_token = response.json().get("access_token")
        else:
            raise Exception(f"Failed to refresh access token: {response.text}")

    def generate_jwt(self):
        """JWT 생성 로직 (private key 사용)"""
        iat = int(time.time())  # 현재 시간
        exp = iat + 3600  # 만료 시간 (1시간 뒤)
        payload = {
            "iss": self.client_id,
            "sub": self.service_account,
            "iat": iat,
            "exp": exp,
        }

        with open(self.private_key_path, "r") as key_file:
            private_key = key_file.read()

        token = jwt.encode(
            payload,
            private_key,
            algorithm="RS256",
            headers={"alg": "RS256", "typ": "JWT"},
        )
        return token

    def send_message_to_channel(self, channel_id, message, url_link):
        if not self.access_token:
            self.refresh_access_token()  # 액세스 토큰이 없으면 갱신

        url = f"https://www.worksapis.com/v1.0/bots/{self.bot_id}/channels/{channel_id}/messages"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.access_token}",
        }

        NWORKS_MSG_LIMIT = 1000
        SUFFIX = "\n\n...(생략)"

        if len(message) > NWORKS_MSG_LIMIT:
            cut = max(0, NWORKS_MSG_LIMIT - len(SUFFIX))
            message = message[:cut] + SUFFIX

        if url_link:
            payload = {
                "content": {
                    "type": "link",
                    "contentText": message,
                    "linkText": "🔗 바로가기",
                    "link": url_link,
                }
            }
        else:
            payload = {"content": {"type": "text", "text": message}}

        response = requests.post(url, json=payload, headers=headers)

        if response.status_code == 201:
            return {"result": "success"}
        else:
            logger.error(
                f"⚠️ 메시지 전송 실패: {payload} => {response.status_code} {response.text}"
            )
            return {
                "result": "fail",
                "status_code": response.status_code,
                "error": response.text,
            }

    def send_image_to_channel(self, channel_id, image_url):
        if not self.access_token:
            self.refresh_access_token()  # 액세스 토큰이 없으면 갱신

        url = f"https://www.worksapis.com/v1.0/bots/{self.bot_id}/channels/{channel_id}/messages"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.access_token}",
        }
        payload = {
            "content": {
                "type": "image",
                "previewImageUrl": image_url,
                "originalContentUrl": image_url,
            }
        }

        response = requests.post(url, json=payload, headers=headers)

        if response.status_code == 201:
            return {"result": "success"}
        else:
            logger.error(
                f"⚠️ 메시지 전송 실패: {payload} => {response.status_code} {response.text}"
            )
            return {
                "result": "fail",
                "status_code": response.status_code,
                "error": response.text,
            }

    async def refresh_access_token_task(self):
        """주기적으로 액세스 토큰 갱신 (12시간마다)"""
        while True:
            try:
                self.refresh_access_token()
                print("✅ 네이버웍스 액세스 토큰 갱신 완료")
            except Exception as e:
                print(f"⚠️ 네이버웍스 액세스 토큰 갱신 실패: {e}")
            await asyncio.sleep(12 * 60 * 60)  # 12시간마다 실행
