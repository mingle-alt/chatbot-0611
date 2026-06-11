import streamlit as st
from chat import get_client, trim_history, stream_response
from config import AVAILABLE_MODELS, DEFAULT_MODEL, DEFAULT_TEMPERATURE, DEFAULT_MAX_HISTORY

st.title("💬 Chatbot")
st.write(
    "GPT 기반 챗봇입니다. "
    "사용하려면 [OpenAI API 키](https://platform.openai.com/account/api-keys)가 필요합니다."
)

if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar:
    st.header("설정")

    # 모델 선택 (#10)
    model = st.selectbox("모델", AVAILABLE_MODELS, index=AVAILABLE_MODELS.index(DEFAULT_MODEL))

    # temperature 조절 (#12)
    temperature = st.slider("Temperature", min_value=0.0, max_value=2.0, value=DEFAULT_TEMPERATURE, step=0.1,
                            help="낮을수록 일관된 답변, 높을수록 창의적인 답변")

    # 히스토리 길이 조절 (#10)
    max_history = st.slider("최대 대화 턴", min_value=5, max_value=50, value=DEFAULT_MAX_HISTORY, step=5,
                            help="이전 대화를 몇 턴까지 기억할지 설정합니다")

    st.divider()
    turn_count = len(st.session_state.messages) // 2
    st.caption(f"현재 대화: {turn_count}턴 / 최대 {max_history}턴")
    if st.button("🗑️ 대화 초기화", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# API 키: secrets.toml 우선, 없으면 UI 입력 (#1)
try:
    api_key = st.secrets.get("OPENAI_API_KEY", "")
except Exception:
    api_key = ""
if not api_key:
    api_key = st.text_input("OpenAI API Key", type="password")
if not api_key:
    st.info("OpenAI API 키를 입력해 주세요.", icon="🗝️")
    st.stop()

# 클라이언트 캐싱 (#2)
client = get_client(api_key)

st.session_state.messages = trim_history(st.session_state.messages, max_history)

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("메시지를 입력하세요..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        response, error = stream_response(client, st.session_state.messages, model, temperature)

    if error:
        st.error(error[0], icon=error[1])
        st.session_state.messages.pop()
    else:
        st.session_state.messages.append({"role": "assistant", "content": response})
