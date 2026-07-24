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
 - [신규] 학생과 애덤 스미스의 대화는 교사가 확인할 수 있도록
   구글 스프레드시트에 실시간으로(질문-답변 한 쌍이 생길 때마다) 기록됩니다.
=====================================================================
"""

import os
import base64
from datetime import datetime
import streamlit as st
from openai import OpenAI
from pathlib import Path

# requests: 구글 앱스크립트(Apps Script) 웹앱으로 대화 기록을 전송하기 위한 라이브러리입니다.
import requests

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

if missing_files:
    st.warning(
        "⚠️ 다음 참고 자료 파일을 찾을 수 없어요: "
        + ", ".join(missing_files)
        + "\n\n(data 폴더 위치와 파일명을 확인해주세요. 자료가 없어도 "
        "일반적인 지식을 바탕으로 대화는 계속할 수 있습니다.)"
    )

# ---------------------------------------------------------------
# 5. 시스템 프롬프트 만들기
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
- ...더군.
- ...라고 보았네.
- ...라고 생각하였지.
- ...라고 주장하였네.
- 흥미로운 질문이군.
- 좋은 생각일세.
- 그 점은 조금 달리 생각해 볼 수도 있겠네.
- ...가 가장 궁금한가?
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

## 현대 사회에 대한 질문을 받을 경우
내가 살던 시대에는 존재하지 않았던 제도나 기술이라도
현대 사회를 이해하려는 태도로 대답한다.
현대 경제 현상을 내 이론에 비추어 해석하되,
내가 직접 경험한 사실인 것처럼 말하지 않는다.

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


def check_mission(user_question):

    judge_prompt = f"""
학생 질문:

{user_question}

다음 세 가지 가운데 어떤 주제에 해당하는지만 판단하라.

1 division
- 분업이 생산성을 높이는 이유

2 invisible
- 보이지 않는 손
- 시장가격
- 시장 가격
- 경쟁

3 government
- 정부 역할
- 중상주의 정부와의 차이
- 국방
- 사법
- 공공사업

답은 반드시

division
invisible
government
none

중 하나만 출력.
"""

    try:

        result = client.chat.completions.create(
            model="solar-open2",
            messages=[
                {"role": "system", "content": "너는 분류기이다."},
                {"role": "user", "content": judge_prompt},
            ],
            stream=False,
            reasoning_effort="minimal",
        )

        return result.choices[0].message.content.strip().lower()

    except Exception:
        return "none"


# API 키가 없다면, 화면에 친절한 한국어 안내 메시지를 보여줍니다.
if client is None:
    st.error(
        "🔑 Solar API 키가 설정되어 있지 않아요.\n\n"
        "Streamlit Cloud의 [Settings] → [Secrets] 메뉴에서 아래와 같이 "
        "SOLAR_API_KEY 값을 등록한 뒤 다시 실행해주세요.\n\n"
        "```\nSOLAR_API_KEY = \"여기에_발급받은_키를_입력\"\n```"
    )
    st.stop()

# =================================================================
# 6-1. [신규] 구글 스프레드시트 로깅 기능 (앱스크립트 웹앱 방식)
#    - 학생과 애덤 스미스의 대화를 교사가 확인할 수 있도록
#      구글 스프레드시트에 실시간으로 한 줄씩 기록합니다.
#    - 구글 시트에 배포해 둔 "앱스크립트 웹앱(Apps Script Web App)" URL로
#      매 질문-답변마다 POST 요청을 보내면, 앱스크립트가 시트에 한 줄을 추가합니다.
#    - 서비스 계정이나 gspread 없이, Streamlit Secrets에 웹앱 URL 하나만
#      등록하면 됩니다. (GAS_WEBHOOK_URL)
#    - 요청이 실패하더라도(URL 미설정, 네트워크 오류 등) 학생이 챗봇을
#      사용하는 데는 지장이 없도록, 모든 예외를 조용히 처리합니다.
# =================================================================
GAS_WEBHOOK_URL = st.secrets.get("GAS_WEBHOOK_URL", None)


def log_conversation_to_sheet(student_name, question, answer, mission_label=""):
    """
    질문-답변 한 쌍을 구글 앱스크립트 웹앱으로 전송하여
    스프레드시트에 즉시 한 줄로 기록합니다.
    전송에 실패해도(URL 미설정, 일시적 네트워크 오류 등) 학생 화면에는
    아무 영향을 주지 않습니다.
    """
    if not GAS_WEBHOOK_URL:
        return
    try:
        payload = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "student_name": student_name,
            "question": question,
            "answer": answer,
            "mission_label": mission_label,
        }
        requests.post(GAS_WEBHOOK_URL, json=payload, timeout=10)
    except Exception:
        pass


# ---------------------------------------------------------------
# 7. 대화 기록(세션 상태) 관리
# ---------------------------------------------------------------
MISSION_TOPICS = {
    "division": {
        "title": "분업과 생산성",
        "description": "분업은 어떻게 노동 생산성을 높이나요?",
    },
    "invisible": {
        "title": "보이지 않는 손",
        "description": "보이지 않는 손은 어떻게 시장을 조정하나요?",
    },
    "government": {
        "title": "정부의 역할",
        "description": "정부의 역할은 중상주의 시대의 정부 역할과 어떻게 다른가요?",
    },
}

if "gold_coins" not in st.session_state:
    st.session_state.gold_coins = 0

if "completed_missions" not in st.session_state:
    st.session_state.completed_missions = set()

if "badge_animation_shown" not in st.session_state:
    st.session_state.badge_animation_shown = False

if "student_name" not in st.session_state:
    st.session_state.student_name = ""

# -----------------------------------------------------------------
# 7-1. [신규] 학생 이름(또는 번호) 입력받기
#    - 대화를 시작하기 전에 이름을 먼저 입력하도록 하여,
#      구글 스프레드시트에 "누가" 대화했는지 구분할 수 있게 합니다.
#    - 이름을 입력하지 않으면 아래 st.stop()에서 앱 실행을 멈추므로,
#      채팅창 자체가 아직 나타나지 않습니다.
# -----------------------------------------------------------------
if not st.session_state.student_name:
    st.markdown("### 👋 대화를 시작하기 전에, 이름(또는 학번)을 알려주세요")
    st.caption("선생님이 나중에 학습 기록을 확인할 때 사용됩니다.")
    with st.form("student_name_form"):
        name_input = st.text_input(
            "이름 또는 학번",
            placeholder="예: 2학년 3반 김철수 / 20315",
        )
        submitted = st.form_submit_button("대화 시작하기 →")
        if submitted:
            if name_input.strip():
                st.session_state.student_name = name_input.strip()
                st.rerun()
            else:
                st.warning("이름 또는 학번을 입력해주세요.")
    st.stop()

if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": (
                f"안녕하신가, {st.session_state.student_name}. 나는 애덤 스미스라 하네. "
                "『국부론』과 『도덕감정론』을 쓴 사람이지. "
                "먼 길을 왔군. 준비가 되면 무엇이든 물어보게."
            ),
        }
    )

if len(st.session_state.messages) <= 1:

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

# 사이드바
with st.sidebar:
    st.subheader("⚙️ 설정")
    st.markdown(
        "이 앱은 **통합사회2** 교과서 보조 학습 자료입니다.\n\n"
        "애덤 스미스 역할의 AI와 대화하며 시대적 배경과 그의 사상에 대해 학습하고, "
        "애덤 스미스의 사상을 현대인의 시각에서 탐구해 봅시다."
    )

    st.info(f"👤 현재 학생: **{st.session_state.student_name}**")

    if st.button("🔄 대화 새로 시작하기"):
        st.session_state.messages = []
        st.rerun()

    st.divider()

    st.subheader("🧭 경제 탐험 현황")

    st.markdown(
        """
        시간을 달리는 경제 탐험가가 되어
        애덤 스미스와 대화하며 핵심 사상을 탐구해 보세요.
        """
    )

    st.metric("🪙 Gold Coins", f"{st.session_state.gold_coins} / 3")

    progress = st.session_state.gold_coins / 3
    st.progress(progress)

    st.markdown("### 🎯 핵심 탐험")

    for key, mission in MISSION_TOPICS.items():

        if key in st.session_state.completed_missions:
            st.success(f"✅ {mission['title']}")
        else:
            st.write(f"⬜ {mission['title']}")

    if st.session_state.gold_coins == 3:
        st.success("🏆 경제 탐험 완료!")
    if (
        st.session_state.gold_coins == 3
        and not st.session_state.badge_animation_shown
    ):
        st.balloons()
        st.success("🏆 경제 탐험 완료!")
        st.session_state.badge_animation_shown = True

    st.divider()

    use_deep_reasoning = st.toggle(
        "🧠 심화 추론 모드 (답변이 느려질 수 있어요)",
        value=False,
        help=(
            "이 모드를 켜면 애덤 스미스가 답변 전에 더 깊이 생각한 뒤 답합니다. "
            "복잡한 질문에는 도움이 되지만 응답 속도가 느려집니다. "
            "평소에는 꺼두는 것을 추천해요."
        ),
    )
    REASONING_EFFORT = "high" if use_deep_reasoning else "minimal"

    with st.expander("📚 참고 자료 목록 보기"):
        for f in DATA_FILES:
            status = "✅ 로드됨" if f not in missing_files else "❌ 없음"
            st.write(f"- {f} ({status})")

    # [신규] 구글 시트(앱스크립트 웹훅) 연결 상태를 교사/개발자가 바로 확인할 수 있게 표시합니다.
    st.divider()
    st.subheader("📊 학습 기록 저장 상태")
    if GAS_WEBHOOK_URL:
        st.success("✅ 구글 시트 웹훅이 연결되어, 대화가 자동으로 기록되고 있어요.")
    else:
        st.warning(
            "⚠️ 구글 시트 웹훅이 설정되지 않았어요. (학생 사용에는 문제없지만, "
            "대화 기록은 저장되지 않습니다.)\n\n"
            "Secrets에 `GAS_WEBHOOK_URL` 값이 올바르게 등록되어 있는지 확인해주세요."
        )

# ---------------------------------------------------------------
# 8. 지금까지의 대화 내용을 화면에 그려주기
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
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user", avatar="🕵️"):
        st.markdown(user_input)

    api_messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    api_messages += [
        {"role": m["role"], "content": m["content"]}
        for m in st.session_state.messages
    ]

    with st.chat_message("assistant", avatar=ADAM_SMITH_CHAT_AVATAR):
        placeholder = st.empty()
        full_response = ""
        mission_label = ""  # [신규] 이번 턴에 새로 달성한 미션 이름 (시트 기록용)

        try:
            stream = client.chat.completions.create(
                model="solar-open2",
                messages=api_messages,
                stream=True,
                reasoning_effort=REASONING_EFFORT,
            )

            for chunk in stream:
                delta = chunk.choices[0].delta.content
                if delta:
                    full_response += delta
                    placeholder.markdown(full_response + "▌")

            placeholder.markdown(full_response)

            mission = check_mission(user_input)

            if (
                mission in MISSION_TOPICS
                and mission not in st.session_state.completed_missions
            ):

                st.session_state.completed_missions.add(mission)
                st.session_state.gold_coins += 1
                mission_label = MISSION_TOPICS[mission]["title"]

                st.toast(
                    f"🪙 Gold Coin 획득!\n\n{mission_label}",
                    icon="✨",
                )

                if st.session_state.gold_coins == 3:
                    st.success("🏆 경제 탐험 완료!")

        except Exception as e:
            full_response = (
                "미안하네. 지금은 내 생각을 전달하는 데 문제가 생긴 것 같군. "
                "잠시 후 다시 질문해주겠나? "
                "(만약 문제가 계속된다면, 선생님께 API 키 설정이나 인터넷 연결 상태를 "
                "확인해달라고 요청해주세요.)"
            )
            placeholder.markdown(full_response)
            with st.expander("🔧 (선생님/개발자용) 오류 상세 정보"):
                st.code(str(e))

    st.session_state.messages.append(
        {"role": "assistant", "content": full_response}
    )

    # [신규] 이번 질문-답변 한 쌍을 구글 스프레드시트에 즉시 기록합니다.
    log_conversation_to_sheet(
        student_name=st.session_state.student_name,
        question=user_input,
        answer=full_response,
        mission_label=mission_label,
    )
