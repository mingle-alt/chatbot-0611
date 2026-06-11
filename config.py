AVAILABLE_MODELS = [
    "gpt-4o-mini",
    "gpt-4o",
    "gpt-4.1-mini",
    "gpt-5-mini",
    "gpt-5.4-mini",
    "gpt-5.4",
]

DEFAULT_MODEL = "gpt-4o-mini"
DEFAULT_TEMPERATURE = 0.7
DEFAULT_MAX_HISTORY = 20

TRAVEL_STYLES = ["혼자", "커플", "가족여행", "친구"]

VISION_MODELS = {"gpt-4o-mini", "gpt-4o", "gpt-4.1-mini", "gpt-5-mini", "gpt-5.4-mini", "gpt-5.4"}

_SYSTEM_PROMPT_TEMPLATE = """당신은 10년 경력의 전문 여행 플래너이자 현지 가이드입니다.

## 역할과 전문성
- 여행지 추천, 일정 계획, 맛집·숙소·교통 정보를 전문적으로 안내합니다.
- 사용자의 예산, 기간, 여행 스타일에 맞춘 맞춤형 조언을 제공합니다.
- 응답 시 구체적인 장소명, 주소, 운영시간, 실용적인 팁을 항상 포함합니다.
- 한국어로 응답하되, 외국 지명은 현지어+한국어를 병기합니다. (예: 시부야(渋谷, Shibuya))

## 현재 여행 컨텍스트
{context}

## 응답 형식
- 장소명은 **굵게** 표시하세요.
- 일정 제안 시 Day 1, Day 2 형식으로 구체적으로 작성하세요.
- 예산 정보는 한국 원화(₩) 기준으로 환산해 주세요.
- 💡 팁은 💡로, ⚠️ 주의사항은 ⚠️로 표시하세요.
"""


def build_system_prompt(destination="", date_range=None, budget=None, travel_style=""):
    parts = []
    if destination:
        parts.append(f"- 여행지: {destination}")
    if date_range and len(date_range) == 2:
        start, end = date_range
        days = (end - start).days + 1
        parts.append(f"- 여행 기간: {start} ~ {end} ({days}일)")
    elif date_range and len(date_range) == 1:
        parts.append(f"- 여행 출발일: {date_range[0]}")
    if budget:
        parts.append(f"- 예산: {budget[0]}만원 ~ {budget[1]}만원")
    if travel_style:
        parts.append(f"- 여행 스타일: {travel_style}")

    context = (
        "\n".join(parts)
        if parts
        else "설정된 여행 정보가 없습니다. 사용자에게 여행 관련 정보를 물어보며 맞춤 안내를 제공하세요."
    )
    return _SYSTEM_PROMPT_TEMPLATE.format(context=context)
