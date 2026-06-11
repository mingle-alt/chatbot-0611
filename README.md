# 💬 Chatbot

OpenAI GPT 모델을 사용하는 Streamlit 기반 챗봇입니다.

## 기능

- **다양한 모델 선택** — gpt-4o-mini, gpt-4o, gpt-4.1-mini, gpt-5-mini 등 사이드바에서 즉시 전환
- **Temperature 조절** — 슬라이더로 응답의 일관성/창의성 조절 (0.0~2.0)
- **대화 히스토리 제한** — 최대 대화 턴 수 설정으로 토큰 비용 자동 관리
- **대화 초기화** — 사이드바 버튼으로 새 대화 시작
- **에러 처리** — 인증 실패·요청 한도 초과·네트워크 오류 개별 안내
- **API 키 관리** — `secrets.toml` 등록 시 UI 입력 불필요

## 파일 구조

```
├── streamlit_app.py   # UI 및 메인 진입점
├── chat.py            # OpenAI API 호출 로직
├── config.py          # 모델 목록, 기본값, 시스템 프롬프트
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
