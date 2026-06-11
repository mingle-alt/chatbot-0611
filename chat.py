import streamlit as st
from openai import OpenAI, AuthenticationError, RateLimitError, APIConnectionError
from config import SYSTEM_PROMPT


@st.cache_resource
def get_client(api_key: str) -> OpenAI:
    return OpenAI(api_key=api_key)


def trim_history(messages: list, max_history: int) -> list:
    if len(messages) > max_history * 2:
        return messages[-(max_history * 2):]
    return messages


def stream_response(client: OpenAI, messages: list, model: str, temperature: float):
    placeholder = st.empty()
    placeholder.markdown("⏳ 답변 생성 중...")

    try:
        stream = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                *[{"role": m["role"], "content": m["content"]} for m in messages],
            ],
            temperature=temperature,
            stream=True,
        )
        placeholder.empty()
        return st.write_stream(stream), None

    except AuthenticationError:
        return None, ("API 키가 올바르지 않습니다. 키를 확인해 주세요.", "🔑")
    except RateLimitError:
        return None, ("요청 한도를 초과했습니다. 잠시 후 다시 시도해 주세요.", "⏱️")
    except APIConnectionError:
        return None, ("네트워크 연결에 실패했습니다. 인터넷 연결을 확인해 주세요.", "🌐")
    except Exception as e:
        return None, (f"오류가 발생했습니다: {e}", "⚠️")
