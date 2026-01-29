# search-ad-keyword-monitor

네이버 모바일 검색 광고 키워드 모니터링 자동화 도구

## 개요

네이버 모바일 검색 결과에서 특정 키워드에 대한 광고 노출 순위를 자동으로 추적하는 프로그램입니다.

### 주요 기능

- 네이버 모바일 파워링크 순위 추적
- 브랜드콘텐츠 영역 순위 추적 (개발 중)
- 2,700개 이상의 키워드 자동 모니터링
- JSON 기반 키워드 관리

## 프로젝트 구조

```
search-ad-keyword-monitor/
├── config/
│   ├── keywords.json          # 모니터링 대상 키워드 목록
│   └── constants.py            # 설정 상수 (TARGET_KEYWORDS, 셀렉터 등)
├── crawler/
│   ├── base.py                 # Chrome WebDriver 기본 래퍼
│   └── naver_mobile.py         # 네이버 모바일 검색 크롤러
├── runner.py                   # 메인 실행 스크립트
└── requirements.txt            # Python 패키지 의존성
```

## Prerequisites (OS level)

Chromium 기반 브라우저가 시스템에 설치되어 있어야 합니다.

### Ubuntu / Debian

```bash
sudo apt update
sudo apt install -y chromium-browser
```

## 설치 및 실행

### 1. Python 환경 설정

```bash
# Python 3.12 이상 권장
python3 --version

# 가상환경 생성 (선택사항)
python3 -m venv venv
source venv/bin/activate
```

### 2. 의존성 설치

```bash
pip install -r requirements.txt
```

### 3. 설정 파일 수정

#### config/constants.py

```python
# 광고주/브랜드 식별 키워드
TARGET_KEYWORDS = [
    "yk",
    "법무법인 yk",
]
```

#### config/keywords.json

모니터링할 키워드 목록을 JSON 형식으로 관리합니다.

```json
{
  "keywords": [
    "강제추행변호사",
    "마약변호사",
    ...
  ]
}
```

### 4. 실행

```bash
# 전체 키워드 실행
python3 runner.py

# 테스트 실행 (제한된 개수만)
# runner.py의 main(limit=10) 수정
python3 runner.py
```

## 출력 예시

```
[1] keyword='강제추행변호사', run_key=abc123de
  ✅ 모바일 파워링크 5번째 노출

[2] keyword='마약변호사', run_key=xyz789fg
  ❌ 모바일 파워링크 노출 없음

[3] keyword='교통사고전문변호사', run_key=hij456kl
  ✅ 모바일 파워링크 3번째 노출
```

## 주요 설정

### config/constants.py

- `TARGET_KEYWORDS`: 광고 내용에서 찾을 키워드 리스트
- `NAVER_MOBILE_POWERLINK_SELECTOR`: 파워링크 영역 CSS 셀렉터
- `NAVER_MOBILE_BRAND_CONTENT_SELECTOR`: 브랜드콘텐츠 영역 CSS 셀렉터

### crawler/base.py

Chrome 옵션 설정:

- `--headless=new`: Headless 모드 실행
- `--no-sandbox`: 샌드박스 비활성화
- `--disable-gpu`: GPU 가속 비활성화

## 주의사항

- Headless 모드로 실행되므로 브라우저 창이 보이지 않습니다
- 네이버 검색 결과 페이지 구조 변경 시 셀렉터 업데이트 필요
- 과도한 요청 시 IP 차단 위험이 있으므로 적절한 딜레이 유지 (현재 3~5초)
- 키워드 개수가 많을 경우 실행 시간이 오래 걸릴 수 있습니다

## 라이센스

MIT

[검색결과로 뜨는 키워드] - 부동산변호사

      - xxx 관련광고 (파워링크) : 노출 여부, 순위o
      - 브랜드 콘텐츠 : 노출 여부, 순위o

      - 플레이스 (광고) : 거의 세개있는데 그중에 몇위인지 (없는경우도 있음) / 플레이스가 있을수도 없을수도 있음
      - 플레이스 : 노출 여부, 순위o

- 검색결과영역 : 카페+블로그, seo(web) - seo 따로 된다면 좋을듯
- 블로그 : 이름에 yk 포함, 순위x
- 카페글 : 썸네일에 yk 포함, 순위x

[인기글로 뜨는 키워드] - 강남형사전문변호사

      - xxx 관련광고 (파워링크) : 노출 여부, 순위o

      - 플레이스 (광고) : 거의 세개있는데 그중에 몇위인지 (없는경우도 있음)
      - 플레이스 : 노출 여부, 순위o

      - 인기글 광고 : 거의 세개있는데 그중에 몇위인지 (없는경우도 있음)
      - 인기글 (일반글) 블로그 : yk 포함, 순위x
      - 인기글 (일반글) 카페글 : 썸네일에 yk 포함, 순위x
