# ✈️ Travel Buddy

OpenAI GPT 모델을 사용하는 Streamlit 기반 AI 여행 플래너입니다.

## 기능

### 여행 챗봇
- **여행 전문가 응답** — 여행지 추천, 일정 계획, 맛집·숙소·교통 정보 안내
- **맞춤형 컨텍스트** — 여행지·기간·예산·스타일을 사이드바에서 설정하면 시스템 프롬프트에 자동 반영
- **한/영 병기** — 외국 지명은 현지어+한국어 병기 (예: 시부야(渋谷, Shibuya))

### 지도 연동
- **장소 자동 감지** — 응답에서 장소명을 자동 추출 (GPT function calling)
- **지도 렌더링** — Folium + Nominatim 지오코딩으로 응답 바로 아래 지도 표시
- **번호 마커** — 장소별 파란 원형 번호 마커 + 팝업 설명
- **토글 on/off** — 사이드바에서 지도 표시 여부 선택 가능

### 음성 입력
- **마이크 버튼** — 브라우저에서 바로 녹음, 2초 침묵 시 자동 종료
- **Whisper AI 전사** — OpenAI whisper-1 모델로 높은 정확도의 음성 인식 (한국어 포함 100개 언어 지원)
- **자동 전송** — 전사 완료 즉시 채팅 메시지로 자동 전송
- **중복 방지** — MD5 해시로 동일 녹음 재처리 차단

### 이미지 첨부
- **파일 업로드** — JPG, PNG, WEBP, GIF 지원
- **Vision AI 분석** — GPT-4o Vision으로 이미지 내용 인식 및 답변
- **여행 활용 예시** — 간판 번역, 음식 정보, 장소 식별 등
- **자동 초기화** — 전송 후 업로더 자동 리셋

### AI 설정
- **모델 선택** — gpt-4o-mini, gpt-4o, gpt-4.1-mini, gpt-5-mini 등 즉시 전환
- **Temperature 조절** — 슬라이더로 응답 일관성/창의성 조절 (0.0~2.0)
- **히스토리 제한** — 최대 대화 턴 수 설정으로 토큰 비용 자동 관리
- **에러 처리** — 인증 실패·한도 초과·네트워크 오류 개별 안내
- **API 키 관리** — `secrets.toml` 등록 시 UI 입력 불필요

## 파일 구조

```
├── streamlit_app.py   # UI, 음성 입력, 지도 렌더링, 메인 진입점
├── chat.py            # OpenAI 스트리밍, Whisper 전사, 장소 추출, 지오코딩
├── config.py          # 모델 목록, 여행 시스템 프롬프트 템플릿
└── requirements.txt
```

## 실행 방법

### 1. 패키지 설치

```bash
pip install -r requirements.txt
```

### 2. API 키 설정

**방법 A — secrets.toml (권장)**

`.streamlit/secrets.toml` 파일을 생성하고 아래 내용을 입력합니다.

```toml
OPENAI_API_KEY = "sk-..."
```

**방법 B — UI 직접 입력**

앱 실행 후 화면에서 API 키를 입력합니다.

### 3. 앱 실행

```bash
streamlit run streamlit_app.py
```
