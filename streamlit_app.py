import base64
import hashlib
import streamlit as st
import folium
from streamlit_folium import st_folium
from datetime import date, timedelta
from audio_recorder_streamlit import audio_recorder
from chat import get_client, trim_history, stream_response, transcribe_audio, extract_places, geocode_places
from config import (
    AVAILABLE_MODELS, DEFAULT_MODEL, DEFAULT_TEMPERATURE,
    DEFAULT_MAX_HISTORY, TRAVEL_STYLES, VISION_MODELS, build_system_prompt,
)

st.set_page_config(
    page_title="Travel Buddy",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
/* 앱 배경 */
.stApp {
    background: linear-gradient(160deg, #e8f6fd 0%, #f0faf4 55%, #fdf8ec 100%);
}

/* 사이드바 배경 */
section[data-testid="stSidebar"] > div:first-child {
    background: linear-gradient(180deg, #023e8a 0%, #0077b6 50%, #0096c7 100%);
}

/* 사이드바 텍스트 */
section[data-testid="stSidebar"] .stMarkdown p,
section[data-testid="stSidebar"] h1, section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] small,
section[data-testid="stSidebar"] .stCaption p {
    color: rgba(255, 255, 255, 0.92) !important;
}
section[data-testid="stSidebar"] hr {
    border-color: rgba(255, 255, 255, 0.25) !important;
}

/* 사이드바 버튼 */
section[data-testid="stSidebar"] .stButton > button {
    background: rgba(255, 255, 255, 0.15) !important;
    color: white !important;
    border: 1px solid rgba(255, 255, 255, 0.4) !important;
    border-radius: 8px;
}
section[data-testid="stSidebar"] .stButton > button:hover {
    background: rgba(255, 255, 255, 0.28) !important;
}

/* 채팅 메시지 */
[data-testid="stChatMessage"] {
    border-radius: 14px;
    padding: 6px 10px;
    margin-bottom: 6px;
}

/* 채팅 입력창 */
[data-testid="stChatInput"] {
    border-color: #90e0ef;
}
</style>
""", unsafe_allow_html=True)


def render_map(places: list[dict]):
    if not places:
        return
    lats = [p["lat"] for p in places]
    lons = [p["lon"] for p in places]
    center = [sum(lats) / len(lats), sum(lons) / len(lons)]

    m = folium.Map(location=center, zoom_start=13, tiles="CartoDB positron")

    for idx, place in enumerate(places, 1):
        folium.Marker(
            location=[place["lat"], place["lon"]],
            popup=folium.Popup(
                f"<b>{place['name']}</b><br><small>{place['description']}</small>",
                max_width=220,
            ),
            tooltip=f"{idx}. {place['name']}",
            icon=folium.DivIcon(
                html=(
                    f'<div style="background:#0096c7;color:white;border-radius:50%;'
                    f'width:28px;height:28px;display:flex;align-items:center;'
                    f'justify-content:center;font-weight:bold;font-size:13px;'
                    f'border:2px solid white;box-shadow:0 2px 6px rgba(0,0,0,0.3);">'
                    f'{idx}</div>'
                ),
                icon_size=(28, 28),
                icon_anchor=(14, 14),
            ),
        ).add_to(m)

    if len(places) > 1:
        m.fit_bounds(
            [[min(lats), min(lons)], [max(lats), max(lons)]],
            padding=[40, 40],
        )

    with st.expander("🗺️ 장소 지도", expanded=True):
        st_folium(m, height=400, use_container_width=True, returned_objects=[])


# 세션 상태 초기화
if "messages" not in st.session_state:
    st.session_state.messages = []
if "place_maps" not in st.session_state:
    st.session_state.place_maps = {}
if "last_audio_hash" not in st.session_state:
    st.session_state.last_audio_hash = None
if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0

# ── 사이드바 ──────────────────────────────────────────
with st.sidebar:
    st.markdown("## ✈️ Travel Buddy")
    st.markdown("*AI 여행 플래너*")
    st.divider()

    st.markdown("### 🗺️ 여행 정보")
    destination = st.text_input("여행지", placeholder="예: 도쿄, 파리, 발리...")

    today = date.today()
    date_range = st.date_input(
        "여행 기간",
        value=(today + timedelta(days=30), today + timedelta(days=37)),
        min_value=today,
        format="YYYY/MM/DD",
    )

    budget = st.slider("예산 범위 (만원)", min_value=10, max_value=500, value=(50, 150), step=10)
    travel_style = st.selectbox("여행 스타일", TRAVEL_STYLES)

    st.divider()

    st.markdown("### ⚙️ AI 설정")
    model = st.selectbox("모델", AVAILABLE_MODELS, index=AVAILABLE_MODELS.index(DEFAULT_MODEL))
    temperature = st.slider(
        "Temperature", 0.0, 2.0, DEFAULT_TEMPERATURE, 0.1,
        help="낮을수록 일관된 답변, 높을수록 창의적인 답변",
    )
    max_history = st.slider("최대 대화 턴", 5, 50, DEFAULT_MAX_HISTORY, 5)
    show_map = st.toggle("🗺️ 지도 자동 표시", value=True)

    st.divider()

    turn_count = len(st.session_state.messages) // 2
    st.caption(f"대화: {turn_count}턴 / 최대 {max_history}턴")
    if st.button("🗑️ 대화 초기화", use_container_width=True):
        st.session_state.messages = []
        st.session_state.place_maps = {}
        st.rerun()

# ── API 키 ────────────────────────────────────────────
try:
    api_key = st.secrets.get("OPENAI_API_KEY", "")
except Exception:
    api_key = ""
if not api_key:
    api_key = st.text_input("OpenAI API Key", type="password")
if not api_key:
    st.info("OpenAI API 키를 입력해 주세요.", icon="🗝️")
    st.stop()

client = get_client(api_key)
st.session_state.messages = trim_history(st.session_state.messages, max_history)

# ── 헤더 ─────────────────────────────────────────────
dest_label = f" — {destination}" if destination else ""
st.markdown(
    f'<h1 style="color:#023e8a;margin-bottom:2px;">✈️ Travel Buddy</h1>'
    f'<p style="color:#0096c7;margin-top:0;margin-bottom:16px;border-bottom:2px solid #90e0ef;'
    f'padding-bottom:10px;">AI 여행 플래너{dest_label}</p>',
    unsafe_allow_html=True,
)

# 환영 메시지
if not st.session_state.messages:
    st.info(
        "안녕하세요! 여행 플래너 Travel Buddy입니다. ✈️\n\n"
        "사이드바에서 여행 정보를 입력하거나 바로 질문해 보세요!\n\n"
        "**예시:** 도쿄 3박 4일 일정 짜줘 · 파리 맛집 추천 · 발리 숙소 어디가 좋아?",
        icon="🌍",
    )

# ── 채팅 히스토리 ─────────────────────────────────────
for i, message in enumerate(st.session_state.messages):
    avatar = "🧳" if message["role"] == "user" else "✈️"
    with st.chat_message(message["role"], avatar=avatar):
        if message.get("image_b64"):
            st.image(base64.b64decode(message["image_b64"]), width=320)
        st.markdown(message["content"])
    if show_map and message["role"] == "assistant" and i in st.session_state.place_maps:
        render_map(st.session_state.place_maps[i])

# ── 음성 입력 ─────────────────────────────────────────
voice_prompt = None
mic_col, hint_col = st.columns([1, 11])
with mic_col:
    audio_bytes = audio_recorder(
        text="",
        recording_color="#e63946",
        neutral_color="#0096c7",
        icon_size="2x",
        pause_threshold=2.0,
    )
with hint_col:
    st.markdown(
        '<p style="color:#888;font-size:0.82rem;margin-top:16px;">'
        "🎤 마이크를 눌러 음성으로 질문하세요 (Whisper AI)</p>",
        unsafe_allow_html=True,
    )

if audio_bytes:
    audio_hash = hashlib.md5(audio_bytes).hexdigest()
    if audio_hash != st.session_state.last_audio_hash:
        st.session_state.last_audio_hash = audio_hash
        with st.spinner("🎤 음성 인식 중..."):
            transcribed = transcribe_audio(client, audio_bytes)
        if transcribed and transcribed != "[BLANK_AUDIO]":
            voice_prompt = transcribed
        elif not transcribed or transcribed == "[BLANK_AUDIO]":
            st.warning("음성을 인식하지 못했습니다. 다시 시도해 주세요.", icon="🎤")

# ── 이미지 첨부 ───────────────────────────────────────
with st.expander("🖼️ 이미지 첨부", expanded=False):
    uploaded_file = st.file_uploader(
        "이미지를 첨부하면 다음 메시지와 함께 전송됩니다.",
        type=["jpg", "jpeg", "png", "webp", "gif"],
        key=f"img_uploader_{st.session_state.uploader_key}",
        label_visibility="collapsed",
    )
    if uploaded_file:
        st.image(uploaded_file, width=320)
        st.caption(f"📎 {uploaded_file.name} — 다음 전송 시 함께 첨부됩니다.")
        if model not in VISION_MODELS:
            st.warning("현재 선택된 모델은 이미지를 지원하지 않습니다. gpt-4o-mini 이상을 선택해 주세요.", icon="⚠️")

# ── 채팅 입력 ─────────────────────────────────────────
text_prompt = st.chat_input("여행에 대해 무엇이든 물어보세요! 🌍")
prompt = voice_prompt or text_prompt
if prompt:
    # 이미지 인코딩
    image_b64, image_type = None, None
    if uploaded_file and model in VISION_MODELS:
        image_b64 = base64.b64encode(uploaded_file.read()).decode("utf-8")
        image_type = uploaded_file.type
        st.session_state.uploader_key += 1  # 업로더 초기화

    user_msg = {"role": "user", "content": prompt}
    if image_b64:
        user_msg["image_b64"] = image_b64
        user_msg["image_type"] = image_type

    st.session_state.messages.append(user_msg)
    with st.chat_message("user", avatar="🧳"):
        if image_b64:
            st.image(base64.b64decode(image_b64), width=320)
        st.markdown(prompt)

    system_prompt = build_system_prompt(
        destination=destination,
        date_range=date_range if isinstance(date_range, (list, tuple)) and len(date_range) >= 1 else None,
        budget=budget,
        travel_style=travel_style,
    )

    with st.chat_message("assistant", avatar="✈️"):
        response, error = stream_response(
            client, st.session_state.messages, model, temperature, system_prompt
        )

    if error:
        st.error(error[0], icon=error[1])
        st.session_state.messages.pop()
    else:
        new_msg_index = len(st.session_state.messages)
        st.session_state.messages.append({"role": "assistant", "content": response})

        if show_map:
            with st.spinner("🗺️ 장소를 지도에서 찾는 중..."):
                places_raw = extract_places(client, response)
                geocoded = geocode_places(places_raw, destination)
            if geocoded:
                st.session_state.place_maps[new_msg_index] = geocoded
                st.rerun()
