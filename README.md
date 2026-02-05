# search-ad-keyword-monitor

네이버 모바일 검색 결과 기반 **광고·UGC 노출 모니터링 자동화 도구**

---

## 개요

`search-ad-keyword-monitor`는  
**네이버 모바일 검색 결과**에서 특정 키워드에 대해

- 광고(파워링크 / 브랜드콘텐츠)
- 플레이스(광고 / 일반)
- UGC(블로그·카페)

영역에서 **특정 브랜드(예: YK)가 노출되는지 여부와 상대적 위치를 자동으로 수집·분석**하는 프로그램입니다.

운영 환경에서는 수집 결과를 **Elasticsearch에 적재**하고,  
테스트 환경에서는 **콘솔 로그 형태로 결과를 확인**할 수 있도록 설계되어 있습니다.

---

## 현재 지원 범위 (2026.01 기준)

### 광고 영역

- ✅ **모바일 파워링크**
  - 노출 여부
  - 파워링크 영역 내 순위
- ✅ **브랜드콘텐츠**
  - 노출 여부
  - 브랜드콘텐츠 영역 내 순위
- ⛔ 브랜드콘텐츠 내부 광고/일반 구분
  - 네이버 정책상 시각적 구분 불가로 동일 영역 처리

---

### 플레이스 영역

- ✅ **플레이스 광고**
  - 노출 여부
  - 광고 슬롯 내 순위 (일반적으로 최대 3개)
- ✅ **플레이스 일반**
  - 노출 여부
  - 일반 플레이스 결과 내 순위
- ⚠️ 플레이스 영역이 존재하지 않는 키워드도 있음
  - 자동 감지 후 스킵 처리

---

### UGC 영역 (통합 처리)

> 블로그 + 카페 통합 순위

- ✅ **인기글 / 검색결과 UGC 통합 분석**
- 지식인(KIN) 콘텐츠 제외
- 브랜드콘텐츠로 판단되는 UGC 제외
- 매칭 방식
  - 텍스트 기반 (제목/본문 키워드)
  - 이미지 기반 (썸네일 로고 pHash 비교)

#### 결과 타입 분류

| type | 설명                           |
| ---- | ------------------------------ |
| blog | 네이버 블로그                  |
| cafe | 네이버 카페                    |
| site | 기타 웹문서 (텍스트 기반 매칭) |

---

## 프로젝트 구조

```bash
search-ad-keyword-monitor/
├── config/
│ ├── keywords.json # 모니터링 대상 키워드 목록
│ └── constants.py # 브랜드 키워드, CSS 셀렉터 설정
├── crawler/
│ ├── base.py # Chrome WebDriver 래퍼
│ └── naver_mobile.py # 네이버 모바일 크롤링 로직
├── assets/
│ └── naver_thumbnails/ # 로고 템플릿 이미지 (pHash 비교용)
├── logo_detector.py # 이미지 기반 로고 탐지
├── util.py # 공통 유틸리티 함수
├── main.py # 메인 실행 스크립트
├── requirements.txt
└── YKOS/ # 네이버웍스 알림 연동용 (별도 프로젝트)
```

---

## 동작 흐름

1. 키워드별 네이버 모바일 검색 페이지 접속
2. 영역별 분석 수행
   - 파워링크
   - 브랜드콘텐츠
   - 플레이스(광고 / 일반)
   - UGC(블로그·카페 통합)
3. 브랜드 노출 판단
   - 텍스트 키워드 매칭
   - 썸네일 로고 이미지 매칭
4. 결과 수집
5. 실행 모드에 따라
   - Elasticsearch 인덱싱 (기본)
   - 콘솔 출력 (`--test`)

---

## 시스템 요구사항

### OS

Ubuntu / Debian 기준

```bash
sudo apt update
sudo apt install -y chromium-browser chromium-chromedriver xvfb
```

> `infinite-loop.sh`에서 `xvfb-run`을 사용하므로 `xvfb`가 필요합니다.  
> `crawler/base.py`는 `/snap/bin/chromium`을 사용합니다.

### Python 환경

# Python 3.12 이상 권장

```bash
python3 -m venv venv
source venv/bin/activate
```

### 의존성 설치

```bash
pip install -r requirements.txt
```

### 키워드 설정

키워드는 Google Sheets에서 읽어옵니다.

- 스프레드시트 ID 및 시트 목록은 [config/constants.py](config/constants.py)에서 설정
- 각 시트의 `A2:A` 범위를 키워드 목록으로 사용
- 결과는 `GOOGLE_OUTPUT_SHEET_MAP`에 지정된 시트로 append

### 실행 방법

백그라운드 실행 (무한 루프)

```bash
./start.sh
```

중지

```bash
./stop.sh
```

단발 실행 (운영 모드)

```bash
python3 main.py
```

테스트 모드 (로그 출력)

```bash
python3 main.py --test > main.log
```

### 출력 예시 (--test)

```bash
[2] keyword='강남형사전문변호사'
[ES MOCK] index=search*ad_keyword_monitoring-2026-01-30
[
  {
    "section": "파워링크",
    "rank": 2,
    "source": "naver",
    "query": "강남형사전문변호사"
  },
  {
    "section": "플레이스_광고",
    "rank": 1
  },
  {
    "section": "인기글",
    "content_type": "blog",
    "rank": 1,
    "detect_reason": "text"
  }
]
```
