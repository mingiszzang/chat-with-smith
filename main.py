# -*- coding: utf-8 -*-
"""
=====================================================================
 애덤 스미스와 대화하기 (통합사회2 보조 학습 챗봇)
=====================================================================
 - 이 앱은 파이썬 웹앱 프레임워크인 "Streamlit"으로 만들어졌습니다.
 - AI 답변은 업스테이지(Upstage)의 Solar API를 사용합니다.
 - Solar API는 OpenAI 라이브러리와 호환되는 방식으로 호출할 수 있어서,
   openai 라이브러리를 그대로 사용하되 접속 주소(base_url)만 Solar 주소로
   바꿔서 사용합니다.
 - 학생이 채팅창에 질문을 입력하면, 애덤 스미스 역할을 맡은 AI가
   미리 정해진 "역할/교육 원칙"에 따라 답변을 스트리밍(실시간 타이핑 효과)
   으로 보여줍니다.
=====================================================================
"""

import os
import base64
import streamlit as st
from openai import OpenAI
from pathlib import Path

# ---------------------------------------------------------------
# 1. 페이지 기본 설정
#    - Streamlit 앱의 제목, 아이콘, 레이아웃 등을 설정합니다.
# ---------------------------------------------------------------
st.set_page_config(
    page_title="애덤 스미스와의 대화",
    page_icon="📜",
    layout="centered",
)

# ---------------------------------------------------------------
# 1-1. 애덤 스미스 초상화 이미지 불러오기
#    - data/adam_smith.png 라는 로컬 이미지 파일을 사용합니다.
#      (외부 URL 대신 저장소에 포함된 이미지를 사용하므로,
#       인터넷 상황과 상관없이 항상 얼굴이 안정적으로 보입니다.)
#    - st.chat_message의 avatar 옵션은 "로컬 파일 경로"를 그대로 받을 수 있어서
#      ADAM_SMITH_AVATAR_PATH 변수를 채팅 아바타에 바로 사용합니다.
#    - 반면 위쪽 헤더는 순수 HTML(<img src="...">)로 그리기 때문에,
#      로컬 경로를 못 읽으므로 이미지를 base64 문자열로 바꿔서 넣어줍니다.
# ---------------------------------------------------------------
BASE_DIR = Path(__file__).parent
ADAM_SMITH_AVATAR_PATH = BASE_DIR / "data" / "adam_smith.png"
BACKGROUND_PATH = BASE_DIR / "data" / "parchment_background.png"


@st.cache_data(show_spinner=False)
def load_image_as_base64(path):
    if not os.path.exists(path):
        return None

    ext = os.path.splitext(path)[1].lower()
    mime = "image/png" if ext == ".png" else "image/jpeg"

    with open(path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("utf-8")

    return f"data:{mime};base64,{encoded}"


ADAM_SMITH_IMAGE_B64 = load_image_as_base64(str(ADAM_SMITH_AVATAR_PATH))
BACKGROUND_IMAGE_B64 = load_image_as_base64(str(BACKGROUND_PATH))

HEADER_IMAGE_SRC = ADAM_SMITH_IMAGE_B64 or ""

ADAM_SMITH_CHAT_AVATAR = (
    str(ADAM_SMITH_AVATAR_PATH)
    if ADAM_SMITH_AVATAR_PATH.exists()
    else "🧑‍🏫"
)

# ---------------------------------------------------------------
# 2. 화면 디자인을 위한 CSS
#    - 채팅창이 너무 밋밋해 보이지 않도록 배경/말풍선 스타일을 꾸며줍니다.
#    - 18세기 느낌이 나도록 세피아 톤(갈색 계열)의 색을 사용했습니다.
# ---------------------------------------------------------------
st.markdown(
    f"""
<style>

/* ==========================
   전체 배경
========================== */

.stApp {{
    background-image: url("{BACKGROUND_IMAGE_B64}");
    background-size: cover;
    background-position: center;
    background-attachment: fixed;
}}

/* 메인 컨테이너 */

.main .block-container {{
    background: rgba(255,250,238,0.78);
    padding: 2rem 2.3rem;
    border-radius: 18px;
    border: 2px solid rgba(120,85,40,0.25);
    box-shadow: 0 6px 18px rgba(0,0,0,0.15);
}}

/* 헤더 */

.smith-header {{
    display:flex;
    align-items:center;
    gap:18px;

    background:rgba(255,248,235,0.90);

    border:2px solid #8b5e34;

    border-radius:18px;

    padding:18px;

    margin-bottom:20px;
}}

.smith-header img{{
    width:78px;
    height:78px;
    border-radius:50%;
    border:3px solid #8b5e34;
}}

.smith-header h1{{
    color:#4a2f14;
}}

.smith-header p{{
    color:#6b4a26;
}}

/* 채팅 */

[data-testid="stChatMessage"] {{

    background:rgba(255,252,245,0.72);

    border-radius:18px;

    border:1px solid rgba(120,85,40,.25);

    margin-bottom:10px;

    padding:8px;
}}

/* 입력창 */

[data-testid="stChatInput"] {{

    background:rgba(255,251,240,.9);

    border-radius:18px;
}}

</style>
""",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------
# 3. 상단 헤더 (애덤 스미스 이미지 + 소개 문구)
# ---------------------------------------------------------------
if ADAM_SMITH_IMAGE_B64:
    header_image_html = f'<img src="{HEADER_IMAGE_SRC}" alt="Adam Smith">'
else:
    # 이미지 파일을 찾지 못했을 때는 이모지로 대체해서 앱이 깨지지 않게 합니다.
    header_image_html = (
        '<div style="font-size:48px; width:78px; height:78px; '
        'display:flex; align-items:center; justify-content:center;">🧑‍🏫</div>'
    )

st.markdown(
    f"""
    <div class="smith-header">
        {header_image_html}
        <div class="smith-header-text">
            <h1>애덤 스미스와의 대화</h1>
            <p>『국부론』및『도덕감정론』저자와 딥토킹하기</p>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# 👇 여기로 이동
if "intro_shown" not in st.session_state:

    st.markdown(
        """
        <div style="
        background:rgba(255,248,235,.92);
        border:2px solid #8b5e34;
        border-radius:18px;
        padding:22px;
        margin-bottom:24px;
        text-align:center;
        ">

        <h2>⌛ 시간을 달리는 경제 탐험가 ⌛</h2>

        <h3>시간여행이 완료되었습니다.</h3>

        <hr>

        <p style="font-size:18px;">
        📍 <b>현재 위치</b><br>
        Edinburgh, Scotland
        </p>

        <p style="font-size:18px;">
        📅 <b>현재 연도</b><br>
        1776년
        </p>

        <hr>

        <p style="font-size:20px;">
        애덤 스미스가 당신을 기다리고 있습니다.
        </p>
       
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.session_state.intro_shown = True

if not ADAM_SMITH_IMAGE_B64:
    st.info(
        f"ℹ️ '{ADAM_SMITH_AVATAR_PATH}' 위치에서 초상화 이미지를 찾지 못했어요. "
        "data 폴더에 adam_smith.png 파일이 있는지 확인해주세요."
    )

st.caption(
    "💡 이 챗봇은 고등학교 통합사회2 학습을 돕는 보조자료입니다. "
    "애덤 스미스가 살던 시대적 배경과 그의 주장을 읽기자료에 근거해 답하고, "
    "여러분의 생각을 넓혀주는 질문을 함께 던집니다."
)

# ---------------------------------------------------------------
# 4. data 폴더의 참고 자료(.md 파일) 불러오기
#    - 같은 저장소(repository) 안의 data 폴더에 있는
#      01_profile.md, 02_background.md, 03_wealth_of_nations.md
#      세 파일을 읽어서, AI가 우선적으로 참고할 자료로 활용합니다.
#    - st.cache_data를 사용하면 앱이 다시 실행될 때마다 파일을
#      새로 읽지 않고 한 번 읽은 내용을 재사용해서 속도가 빨라집니다.
# ---------------------------------------------------------------
DATA_FILES = [
    "data/01_profile.md",
    "data/02_background.md",
    "data/03_wealth_of_nations.md",
]


@st.cache_data(show_spinner=False)
def load_reference_materials():
    """data 폴더 안의 마크다운 자료들을 하나의 텍스트로 합쳐서 반환합니다."""
    combined_text = ""
    missing_files = []

    for file_path in DATA_FILES:
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            combined_text += f"\n\n### 참고자료: {file_path}\n{content}\n"
        else:
            missing_files.append(file_path)

    return combined_text.strip(), missing_files


reference_text, missing_files = load_reference_materials()

# 자료 파일이 없다면 화면에 살짝 알려줍니다 (앱이 멈추지는 않습니다).
if missing_files:
    st.warning(
        "⚠️ 다음 참고 자료 파일을 찾을 수 없어요: "
        + ", ".join(missing_files)
        + "\n\n(data 폴더 위치와 파일명을 확인해주세요. 자료가 없어도 "
        "일반적인 지식을 바탕으로 대화는 계속할 수 있습니다.)"
    )

# ---------------------------------------------------------------
# 5. 시스템 프롬프트 만들기
#    - AI에게 "너는 이런 역할과 규칙을 지켜야 해"라고 알려주는 지침입니다.
#    - 사용자가 요청한 [역할 원칙], [교육 원칙], [출력 규칙]을 그대로 반영합니다.
# ---------------------------------------------------------------
SYSTEM_PROMPT = f"""
당신은 18세기 스코틀랜드(영국)의 경제학자이자 철학자인 "애덤 스미스(Adam Smith)"입니다.
당신은 대한민국 고등학생이 배우는 "통합사회2" 교과서의 보조 학습 챗봇으로서,
학생과 대화하며 애덤 스미스의 사상과 시대적 배경을 이해시키고,
그의 주장을 현대적 시각에서 다시 생각해보도록 돕는 역할을 맡고 있습니다.

아래는 당신(애덤 스미스)에 대한 참고 자료입니다. 이 자료를 최우선으로 근거로 삼아 답변하세요.
자료 범위를 벗어나는 일반적인 내용에 대해서는, 당신이 이미 알고 있는 사실(학습된 지식)을
바탕으로 답하되, 확실하지 않은 것은 확실하지 않다고 말하세요.

----- 참고 자료 시작 -----
{reference_text if reference_text else "(현재 불러올 수 있는 참고 자료가 없습니다.)"}
----- 참고 자료 끝 -----

[역할 원칙]
1. 애덤 스미스의 저술과 위에 제공된 자료에 근거하여 답한다.
2. 현대 사회에 관한 내용은 학생에게 전달받은 정보라고 전제한다. (당신은 18세기 사람이므로
   현대 사회를 직접 알지 못합니다. 학생이 알려준 정보를 바탕으로 반응하세요.)
3. 역사적으로 알 수 없는 사실(자신의 사후에 일어난 일 등)을 직접 경험한 것처럼 말하지 않는다.
4. 자신의 사상을 지나치게 단순화하지 않는다. (『국부론』, 『도덕감정론』 등에 담긴
   복잡함과 맥락을 존중하여 설명한다.)

[교육 원칙]
1. 학생의 질문에 먼저 명확하게 답한다.
2. 매 답변의 마지막에는 사고를 확장하는 질문을 하나 제시한다.
3. 학생이 어떤 주장을 하면 그 근거를 묻는다.
4. 학생이 한 가지 관점만 고려하면, 다른 이해관계자의 관점을 제시해준다.
5. 답을 바로 알려주기보다, 필요한 경우 단서를 단계적으로 제공한다.
6. 학생의 답변을 구체적으로 짚어가며 피드백한다.
7. 근거가 있다면 다양한 형태의 답을 인정한다.

[출력 규칙]
1. 학생의 질문에 3~5문장으로 답한다. (너무 길게 답하지 않는다.)
2. 제공된 자료에 근거한 내용과, 당신의 추론(추정)을 구분해서 말한다.
   예: "제가 남긴 글에 따르면 ~합니다" vs "이건 제 추측입니다만 ~"
3. 어려운 경제·철학 용어는 고등학생이 이해할 수 있도록 쉽게 풀어 설명한다.
4. 학생의 생각을 확장하는 질문을 반드시 하나 제시한다.
5. 학생이 충분한 근거를 제시했다면 이를 구체적으로 칭찬하고 인정한다.
6. 학생의 답이 불충분하면 정답을 바로 알려주지 말고, 단계적인 단서(힌트)를 제공한다.
7. 자료에 없는 사실은 절대로 지어내지 않는다. 모르면 모른다고 솔직히 말한다.


# 애덤 스미스의 화법(반드시 준수)

매우 중요: 당신은 '애덤 스미스에 대해 설명하는 AI'가 아니라, 실제 애덤 스미스 본인이다.
항상 자신의 생각과 저술을 직접 이야기하듯 답변한다.
말투는 18세기 지식인다운 정중하고 사려 깊은 어투를 사용한다.

## 말투
모든 답변은 처음부터 끝까지 18세기 스코틀랜드 신사가 학생에게 이야기하는 듯한 어조를 유지한다.
다음과 같은 표현을 자연스럽게 사용한다.
- 자네
- 말일세
- ...하였네.
- ...이라네.
- ...이지.
- ...일세.
- ...라고 보았네.
- ...라고 생각하였지.
- ...라고 주장하였네.
- 흥미로운 질문이군.
- 좋은 생각일세.
- 그 점은 조금 달리 생각해 볼 수도 있겠네.
- 자네는 어떻게 생각하는가?
- 왜 그렇게 보았는가?
- 말해 보게.

답변은 지나치게 연극적이거나 고어체가 되어서는 안 되지만,
전체 문체는 현대인이 아니라 애덤 스미스가 직접 말하는 듯한 느낌을 유지한다.

## 절대로 사용하지 말 것
다음과 같은 현대적인 표현은 절대로 사용하지 않는다.
- 제가 남긴 글에 따르면
- 저는 ~라고 생각합니다.
- 설명드리겠습니다.
- 말씀드리겠습니다.
- 이해했습니다.
- 알겠습니다.
- 맞습니다.
- 좋은 질문입니다.
- 정리하면
- 쉽게 말해서
- 다음과 같습니다.
- 제가 보기에는
- 현대 경제학에서는
- AI로서
- ChatGPT로서
- Solar로서
이러한 표현이 답변에 들어가면 안 된다.

## 답변 방식
답변은 항상 자신의 견해를 먼저 이야기한 뒤,
학생이 스스로 생각해 볼 수 있도록 질문으로 마무리하는 것을 원칙으로 한다.

예를 들어,
"나는 ……라고 보았네."
"그 까닭은 ……이라 생각하였지."
"그러나 오늘날에는 자네가 다른 의견을 가질 수도 있겠네."
"자네는 어떻게 생각하는가?"
와 같은 흐름을 유지한다.

## 현대 사회에 대한 질문을 받을 경우
내가 살던 시대에는 존재하지 않았던 제도나 기술이라도
현대 사회를 이해하려는 태도로 대답한다.
현대 경제 현상을 내 이론에 비추어 해석하되,
내가 직접 경험한 사실인 것처럼 말하지 않는다.

예를 들어
"내가 살던 시대에는 이러한 기술은 없었지만,
내 생각을 적용해 본다면 ……이라 말할 수 있겠네."
처럼 표현한다.

## 학생 수준
대화 상대는 대한민국의 중·고등학생이다.
지나치게 어려운 경제학 용어나 학술적인 표현은 피한다.
필요한 경우에는 빵집, 시장, 농부, 직공 등
내 시대에 어울리는 사례를 먼저 설명하고,
오늘날의 예시는 이어서 덧붙인다.

## 답변 길이
한 번에 300~400자 정도를 기본으로 한다.
너무 짧게 끝내지 않는다.
너무 긴 설명도 하지 않는다.

## 반드시 마지막에는
학생이 생각할 수 있는 질문을 하나 던진다.
예)
"자네는 어떻게 생각하는가?"
"그 까닭은 무엇이라 보는가?"
"오늘날에도 그러한 원리가 그대로 적용될 수 있을까?"

## 마지막 자기 점검 (반드시 수행)
답변을 보내기 전에 스스로 확인한다.
① 현대적인 존댓말이 들어갔는가?
② "제가", "설명드리겠습니다", "좋은 질문입니다" 같은 표현이 있는가?
③ 답변 전체가 애덤 스미스가 직접 말하는 것처럼 들리는가?
④ 첫 문장부터 마지막 문장까지 동일한 화자가 말하는가?
⑤ 마지막을 학생에게 던지는 질문으로 끝냈는가?
하나라도 만족하지 못하면 답변을 다시 작성한다.

## 예시 대화
학생: 국부란 무엇인가요?

애덤 스미스:
흥미로운 물음이로군. 나는 한 나라의 부란 금과 은을 얼마나 많이 쌓아 두었는가가 아니라, 백성이 얼마나 많은 재화를 생산하고 소비할 수 있는가에 달려 있다고 보았네.
그러므로 국민의 생활이 넉넉해질수록 나라 또한 부유해진다고 생각하였지. 그렇다면 자네는 오늘날 한 나라의 부를 무엇으로 판단하겠는가?

""".strip()

# ---------------------------------------------------------------
# 6. Solar API 클라이언트 만들기
#    - openai 라이브러리를 그대로 쓰되, base_url만 Solar 주소로 바꿉니다.
#    - API 키는 코드에 직접 적지 않고, Streamlit의 "비밀 금고(secrets)"에서
#      SOLAR_API_KEY 라는 이름으로 불러옵니다.
#      (Streamlit Cloud 배포 시 [Settings] > [Secrets] 메뉴에서
#       SOLAR_API_KEY = "발급받은키" 형태로 등록해야 합니다.)
# ---------------------------------------------------------------
def get_client():
    """Solar API용 OpenAI 호환 클라이언트를 생성합니다."""
    api_key = st.secrets.get("SOLAR_API_KEY", None)
    if not api_key:
        return None
    client = OpenAI(
        api_key=api_key,
        base_url="https://api.upstage.ai/v1",
    )
    return client


client = get_client()

# API 키가 없다면, 화면에 친절한 한국어 안내 메시지를 보여줍니다.
if client is None:
    st.error(
        "🔑 Solar API 키가 설정되어 있지 않아요.\n\n"
        "Streamlit Cloud의 [Settings] → [Secrets] 메뉴에서 아래와 같이 "
        "SOLAR_API_KEY 값을 등록한 뒤 다시 실행해주세요.\n\n"
        "```\nSOLAR_API_KEY = \"여기에_발급받은_키를_입력\"\n```"
    )
    st.stop()

# ---------------------------------------------------------------
# 7. 대화 기록(세션 상태) 관리
#    - st.session_state는 사용자가 새로고침하지 않는 한
#      대화 내용을 계속 기억해주는 저장 공간입니다.
#    - messages 리스트 안에 {"role": ..., "content": ...} 형태로 쌓입니다.
# ---------------------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []
    # 처음 접속했을 때 애덤 스미스가 먼저 인사를 건네도록 설정합니다.
    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": (
                "안녕하신가. 나는 애덤 스미스라 하네. "
                "『국부론』과 『도덕감정론』을 쓴 사람이지. "
                "먼 길을 왔군. 무엇이든 물어보게."                
            ),
        }
    )

# 사이드바에 '대화 초기화' 버튼을 두어, 새로 시작하고 싶을 때 사용할 수 있게 합니다.
with st.sidebar:
    st.subheader("⚙️ 설정")
    st.markdown(
        "이 앱은 **통합사회2** 교과서 보조 학습 자료입니다.\n\n"
        "애덤 스미스 역할의 AI와 대화하며 시대 배경, 사상, "
        "현대적 재해석을 함께 탐구해보세요."
    )
    if st.button("🔄 대화 새로 시작하기"):
        st.session_state.messages = []
        st.rerun()

    st.divider()
    # -----------------------------------------------------------
    # 추론(reasoning) 모드 켜고 끄기
    #   - Solar 모델은 답변 전에 내부적으로 여러 단계를 더 생각하는
    #     "추론 모드"를 지원합니다. 이 모드를 켜면 답변 품질이 조금
    #     더 좋아질 수 있지만, 그만큼 응답 속도가 느려집니다.
    #   - 이 챗봇은 답변을 3~5문장으로 짧게 하도록 설계되어 있어서
    #     기본값은 "꺼짐"(minimal)으로 두어 빠른 응답을 우선합니다.
    # -----------------------------------------------------------
    use_deep_reasoning = st.toggle(
        "🧠 심화 추론 모드 (답변이 느려질 수 있어요)",
        value=False,
        help=(
            "켜면 애덤 스미스가 답변 전에 더 깊이 생각한 뒤 답합니다. "
            "복잡한 질문에는 도움이 되지만 응답 속도가 느려집니다. "
            "평소에는 꺼두는 것을 추천해요."
        ),
    )
    REASONING_EFFORT = "high" if use_deep_reasoning else "minimal"

    with st.expander("📚 참고 자료 목록 보기"):
        for f in DATA_FILES:
            status = "✅ 로드됨" if f not in missing_files else "❌ 없음"
            st.write(f"- {f} ({status})")

# ---------------------------------------------------------------
# 8. 지금까지의 대화 내용을 화면에 그려주기
#    - assistant(애덤 스미스)의 말풍선에는 초상화 아바타를 사용합니다.
#    - user(학생)의 말풍선에는 기본 아바타를 사용합니다.
# ---------------------------------------------------------------
for msg in st.session_state.messages:
    avatar = ADAM_SMITH_CHAT_AVATAR if msg["role"] == "assistant" else "🕵️"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])

# ---------------------------------------------------------------
# 9. 학생의 새 질문 입력받기
# ---------------------------------------------------------------
user_input = st.chat_input("애덤 스미스에게 궁금한 것을 물어보세요...")

if user_input:
    # 9-1. 학생의 메시지를 먼저 화면과 대화 기록에 추가합니다.
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user", avatar="🕵️"):
        st.markdown(user_input)

    # 9-2. Solar API에 보낼 메시지 목록을 구성합니다.
    #      맨 앞에 시스템 프롬프트를 넣고, 그 뒤에 지금까지의 대화를 이어붙입니다.
    api_messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    api_messages += [
        {"role": m["role"], "content": m["content"]}
        for m in st.session_state.messages
    ]

    # 9-3. 애덤 스미스(assistant)의 답변을 스트리밍으로 받아 보여줍니다.
    with st.chat_message("assistant", avatar=ADAM_SMITH_CHAT_AVATAR):
        placeholder = st.empty()  # 실시간으로 글자를 채워나갈 빈 공간
        full_response = ""

        try:
            # stream=True 옵션을 주면, 답변이 완성되기 전부터
            # 조금씩(chunk) 잘라서 실시간으로 전달받을 수 있습니다.
            stream = client.chat.completions.create(
                model="solar-open2",  # 모델 이름은 그대로 사용해야 합니다.
                messages=api_messages,
                stream=True,
                # reasoning_effort: 추론 강도를 조절하는 옵션입니다.
                # "minimal"이면 깊은 추론 없이 바로 답해서 응답 속도가 빨라지고,
                # "high"면 더 깊이 생각한 뒤 답해서 속도는 느리지만 품질이 좋아질 수 있습니다.
                reasoning_effort=REASONING_EFFORT,
            )

            for chunk in stream:
                # 각 chunk 안에 새로 생성된 글자 조각이 들어있습니다.
                delta = chunk.choices[0].delta.content
                if delta:
                    full_response += delta
                    # 타이핑 효과: 커서 모양(▌)을 끝에 붙여서 보여줍니다.
                    placeholder.markdown(full_response + "▌")

            # 스트리밍이 끝나면 커서를 떼고 최종 답변을 보여줍니다.
            placeholder.markdown(full_response)

        except Exception as e:
            # API 호출이 실패했을 때(네트워크 오류, 키 오류 등),
            # 에러 화면을 그대로 보여주지 않고 친절한 한국어 메시지를 보여줍니다.
            full_response = (
                "죄송합니다, 학생. 지금은 제 생각을 전달하는 데 문제가 생긴 것 같군요. "
                "잠시 후 다시 질문해주시겠습니까? "
                "(만약 문제가 계속된다면, 선생님께 API 키 설정이나 인터넷 연결 상태를 "
                "확인해달라고 요청해주세요.)"
            )
            placeholder.markdown(full_response)
            # 개발/디버깅용으로 실제 오류 내용을 화면 아래쪽에 작게 남겨둡니다.
            with st.expander("🔧 (선생님/개발자용) 오류 상세 정보"):
                st.code(str(e))

    # 9-4. 완성된 답변을 대화 기록에 저장해서, 다음 질문에도 이어서 기억하게 합니다.
    st.session_state.messages.append(
        {"role": "assistant", "content": full_response}
    )
