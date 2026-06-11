import io
import time
import json
import streamlit as st
from openai import OpenAI, AuthenticationError, RateLimitError, APIConnectionError
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError


@st.cache_resource
def get_client(api_key: str) -> OpenAI:
    return OpenAI(api_key=api_key)


@st.cache_resource
def get_geocoder():
    return Nominatim(user_agent="travel-buddy-chatbot/1.0")


def transcribe_audio(client, audio_bytes: bytes) -> str:
    try:
        audio_file = io.BytesIO(audio_bytes)
        audio_file.name = "audio.wav"
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
        )
        return transcript.text.strip()
    except Exception as e:
        st.error(f"음성 인식에 실패했습니다: {e}", icon="🎤")
        return ""


def trim_history(messages: list, max_history: int) -> list:
    if len(messages) > max_history * 2:
        return messages[-(max_history * 2):]
    return messages


def stream_response(client, messages: list, model: str, temperature: float, system_prompt: str):
    placeholder = st.empty()
    placeholder.markdown("✈️ 여행 정보를 찾는 중...")
    try:
        stream = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                *[{"role": m["role"], "content": m["content"]} for m in messages],
            ],
            temperature=temperature,
            stream=True,
        )
        placeholder.empty()
        return st.write_stream(stream), None
    except AuthenticationError:
        placeholder.empty()
        return None, ("API 키가 올바르지 않습니다. 키를 확인해 주세요.", "🔑")
    except RateLimitError:
        placeholder.empty()
        return None, ("요청 한도를 초과했습니다. 잠시 후 다시 시도해 주세요.", "⏱️")
    except APIConnectionError:
        placeholder.empty()
        return None, ("네트워크 연결에 실패했습니다. 인터넷 연결을 확인해 주세요.", "🌐")
    except Exception as e:
        placeholder.empty()
        return None, (f"오류가 발생했습니다: {e}", "⚠️")


def extract_places(client, text: str) -> list[dict]:
    try:
        result = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Extract specific place names (tourist spots, restaurants, cafes, hotels, "
                        "stations, streets, parks, etc.) from the text and return as JSON. "
                        "Format: {\"places\": [{\"name\": \"place name in English or local language\", "
                        "\"description\": \"one-line description in Korean\"}]} "
                        "Return {\"places\": []} if no places found. Maximum 5 places."
                    ),
                },
                {"role": "user", "content": text[:3000]},
            ],
            response_format={"type": "json_object"},
            temperature=0,
        )
        data = json.loads(result.choices[0].message.content)
        return data.get("places", [])
    except Exception:
        return []


def geocode_places(places: list[dict], destination: str = "") -> list[dict]:
    if not places:
        return []
    geocoder = get_geocoder()
    result = []
    for place in places[:5]:
        try:
            query = f"{place['name']}, {destination}" if destination else place["name"]
            location = geocoder.geocode(query, timeout=8)
            if not location and destination:
                location = geocoder.geocode(place["name"], timeout=8)
            if location:
                result.append({
                    "name": place["name"],
                    "description": place.get("description", ""),
                    "lat": location.latitude,
                    "lon": location.longitude,
                })
            time.sleep(1.1)  # Nominatim: 초당 1건 제한
        except (GeocoderTimedOut, GeocoderServiceError, Exception):
            continue
    return result
