import streamlit as st
from openai import OpenAI, AuthenticationError, RateLimitError, APIConnectionError

MAX_HISTORY = 20  # 최대 유지할 대화 턴 수 (user+assistant 쌍)

SYSTEM_PROMPT = """당신은 친절하고 유능한 AI 어시스턴트입니다.
- 항상 정확하고 도움이 되는 답변을 제공합니다.
- 모르는 것은 모른다고 솔직하게 말합니다.
- 답변은 간결하되 필요한 경우 충분히 설명합니다.
- 한국어로 질문받으면 한국어로, 영어로 질문받으면 영어로 답변합니다."""

st.title("💬 Chatbot")
st.write(
    "GPT-4o-mini 기반 챗봇입니다. "
    "사용하려면 [OpenAI API 키](https://platform.openai.com/account/api-keys)가 필요합니다."
)

if "messages" not in st.session_state:
    st.session_state.messages = []

# 사이드바: API 키 입력 여부와 무관하게 항상 표시
with st.sidebar:
    st.header("설정")
    turn_count = len(st.session_state.messages) // 2
    st.caption(f"현재 대화: {turn_count}턴 / 최대 {MAX_HISTORY}턴")
    if st.button("🗑️ 대화 초기화", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

openai_api_key = st.text_input("OpenAI API Key", type="password")
if not openai_api_key:
    st.info("OpenAI API 키를 입력해 주세요.", icon="🗝️")
    st.stop()

client = OpenAI(api_key=openai_api_key)

# 오래된 대화 자동 정리 (MAX_HISTORY 턴 초과 시 앞부분 제거)
if len(st.session_state.messages) > MAX_HISTORY * 2:
    st.session_state.messages = st.session_state.messages[-(MAX_HISTORY * 2):]

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("메시지를 입력하세요..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        placeholder.markdown("⏳ 답변 생성 중...")

        try:
            stream = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    *[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
                ],
                stream=True,
            )
            placeholder.empty()
            response = st.write_stream(stream)
            st.session_state.messages.append({"role": "assistant", "content": response})

        except AuthenticationError:
            placeholder.error("API 키가 올바르지 않습니다. 키를 확인해 주세요.", icon="🔑")
            st.session_state.messages.pop()
        except RateLimitError:
            placeholder.error("요청 한도를 초과했습니다. 잠시 후 다시 시도해 주세요.", icon="⏱️")
            st.session_state.messages.pop()
        except APIConnectionError:
            placeholder.error("네트워크 연결에 실패했습니다. 인터넷 연결을 확인해 주세요.", icon="🌐")
            st.session_state.messages.pop()
        except Exception as e:
            placeholder.error(f"오류가 발생했습니다: {e}", icon="⚠️")
            st.session_state.messages.pop()
