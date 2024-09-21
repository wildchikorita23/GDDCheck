import streamlit as st
from openai import OpenAI
import PyPDF2
import pandas as pd
import matplotlib.pyplot as plt
import json
import re
import os
import uuid

#관리자
adminpassword = st.secrets.security.password

# OpenAI API 키 설정
try:
   api_key = st.secrets.openai.openai_api_key
except KeyError:
    st.error("API 키가 설정되지 않았습니다. secrets.toml 파일을 확인하세요.")
client = OpenAI(api_key=api_key)

# 이미지 추가 (로고나 배너 이미지)
st.image("https://yt3.googleusercontent.com/K-3bx-q3srYXlCBGGqEMdSeHv2LfWTO_cxhfKhG1X0VcFfb_JoxxWJ3M1KdB7Ug9qVmnUcvuRw=w1707-fcrop64=1,00005a57ffffa5a8-k-c0xffffffff-no-nd-rj", use_column_width=True)

# HTML과 CSS를 이용해 제목을 꾸밈
st.markdown(
    """
   <style>
         /* 전체 배경색 설정 */
        .main {
            background-color: #f4faff; /* 밝은 파스텔 블루 */
            padding: 20px;
        }        
        
        .title {
            text-align: center;
            font-family: Arial, sans-serif;
            color: #4A90E2;
            font-size: 36px;
            margin-bottom: 0;
        }
        .subtitle {
            text-align: center;
            color: #333;
            font-size: 16px;
            margin-top: 0;
        }
        .evaluation-card {
            background-color: #f9f9f9;
            border: 1px solid #ddd;
            padding: 5px;
            border-radius: 8px;
            margin-top: 10px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
            font-size: 14px; /* 텍스트 크기 조절 */
            line-height: 1.6; /* 줄 간격 조절 */
        }
        .evaluation-card h3 {
            color: #4A90E2;      
            margin-top: 10px;
            font-size: 18px;
        }
        
        .total-score {
            background-color: #4A90E2;
            color: white;
            padding: 10px;
            text-align: center;
            border-radius: 8px;
            margin-top: 20px;
            font-size: 20px;
            font-weight: bold;
        }
        .score-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
        }
        .score-table th, .score-table td {
            padding: 10px;
            border: 1px solid #ddd;
            text-align: center;
        }
        .score-table th {
            background-color: #4A90E2;
            color: white;
        }
        .score-table tr:nth-child(even) {
            background-color: #f3f3f3;
        }
    </style>
    <h1 style="text-align:center; font-family:Arial, sans-serif;">
        게임 기획서 평가 AI (BETA)
    </h1>
    <p style="text-align:center; font-family:Arial, sans-serif;"> AI의 성능 한계로 평가가 부정확한 경우가 많습니다. 참고 용도로만 활용해 주세요.
    <br>평가 결과는 AI에게 수집이 됩니다. 보안이 중요한 문서는 넣지 않는 것이 좋습니다.</p>
    """,
    unsafe_allow_html=True
)

# 유튜브 링크 추가
youtube_link = "https://www.youtube.com/@gamedesigneryuriring"  
st.markdown(
    f"""
    <div style="text-align:center; margin-top:10px;">
        <a href="{youtube_link}" target="_blank" font-size:18px; text-decoration:none;">
            📺 유리링 유튜브
        </a>
    </div>
    """,
    unsafe_allow_html=True
)


# PDF 파일 업로드 받기
uploaded_file = st.file_uploader("기획서 PDF 파일을 업로드하세요.", type="pdf")

# 평가 데이터를 저장할 경로 설정
feedback_data_path = "feedback_data.json"
pdf_save_directory = "uploaded_pdfs"
os.makedirs(pdf_save_directory, exist_ok=True)

try:
    if os.path.exists(feedback_data_path):
        with open(feedback_data_path, 'r', encoding='utf-8') as file:
            feedback_data = json.load(file)
    else:
        feedback_data = []
except Exception as e:
    st.error(f"평가 데이터를 불러오는 중 오류가 발생했습니다: {e}")
    feedback_data = []


# 비밀번호 입력을 통한 접근 제어
st.sidebar.write("관리자 전용 기능")
password = st.sidebar.text_input("비밀번호를 입력하세요:", type="password")

# 비밀번호 확인 
if password == adminpassword:
    st.sidebar.success("접근이 허용되었습니다.")      
    if st.sidebar.button("내 로그 보기"):
        if feedback_data:
            st.write("로그:")
            for idx, feedback in enumerate(feedback_data, 1):
                st.write(f"**평가 {idx}:**")
                st.write(f"**텍스트:** {feedback['text'][:200]}...") 
                st.write(f"**평가 내용:** {feedback['evaluation']}")
              
                pdf_path = feedback.get('pdf_path', None)
                if pdf_path and os.path.exists(pdf_path):
                    with open(pdf_path, "rb") as pdf_file:
                        st.download_button(
                            label=f"로그({os.path.basename(pdf_path)})",
                            data=pdf_file,
                            file_name=os.path.basename(pdf_path),
                            mime='application/pdf',
                            key=f"download_{idx}"  # 고유한 key 지정
                        )
                st.write("---")
        else:
            st.write("저장된 평가 데이터가 없습니다.")

   # 평가 데이터 초기화 버튼 추가
    if st.sidebar.button("평가 데이터 초기화"):
        if os.path.exists(feedback_data_path):
            os.remove(feedback_data_path)  # JSON 파일 삭제로 초기화
            feedback_data = []  # 메모리상의 데이터도 초기화
            st.success("평가 데이터가 초기화되었습니다.")
        else:
            st.warning("초기화할 평가 데이터가 없습니다.")

else:
    st.sidebar.warning("올바른 비밀번호를 입력하세요.")



# 각 평가 항목 초기화
categories = [
    "주제 선정", "창의력", "구성과 흐름", "가독성", "문장력과 맞춤법",
    "분석력", "논리력", "통찰력", "실무력", "시각적 구성 및 디자인"
]

evaluation_criteria = { 
   "evaluation_criteria": [
    {
      "name": "주제 선정",
      "evaluation_factors": [
        "주제가 흔하지 않고 독창적인가",
        "주제와 실제 다루는 내용이 일치하는가",
        "창작 기획서의 경우, 가상의 게임을 대상으로 한 시스템, 콘텐츠 창작이 아닌, 기존에 존재하는 게임의 신규 시스템, 콘텐츠를 창작한 기획서인가"
      ],
      "deduction_factors": [
        "신규 시스템, 신규 콘텐츠 창작 기획서인데 대상으로 삼은 게임이 없고, 존재하지 않는 가상의 게임을 주제로 삼아, 독자의 공감을 얻기 어려움",
        "다양한 역량을 보여주기 어려운 주제",
        "분량이 충분히 나오기 어려운 지엽적인 주제",
        "다루는 범위가 지나치게 넓은 주제 (예: 길드 시스템 전체)",
        "시스템 기획서이지만 시스템의 성공과 실패가 콘텐츠 기획자의 역량에 더 많이 달려있는 주제 (예: 스토리 모드, 블루 아카이브의 모모톡과 같은 서비스처럼 캐릭터와 대화하는 콘텐츠)"
      ]
    },
    {
      "name": "창의력",
      "evaluation_factors": [
        "기존 기획서에서 보기 어려운 창의적인 아이디어가 있는가?",
        "독창적인 접근 방식이 돋보이는지"
      ],
      "deduction_factors": [
        "너무 뻔한 논리 전개 흐름",
        "너무 당연한 기획 의도 (예: 매출 증대, 리텐션 증가, 캐릭터 애착 형성과 같은 문구가 문서 내에 있는 경우)",
        "너무 흔한 아이디어"
      ],
      "additional_evaluation": [
        "제안된 아이디어가 게임의 핵심 재미 요소를 강화하고, 새로운 유저 경험을 창출할 수 있는지"
      ]
    },
    {
      "name": "구성과 흐름",
      "evaluation_factors": [
        "문서가 논리적 순서에 따라 잘 구성되어 있는지",
        "각 섹션이 유기적으로 연결되어 있는지"
        "문서가 온전히 완결되어 있는지"
      ],
      "deduction_factors": [
        "필요한 내용을 찾기 어렵거나, 내용이 뒤죽박죽인 구성",
        "불필요하거나 중복된 내용으로 페이지를 낭비하는 것",
        "문서의 맥락 상 반드시 필요하지 않은 정보 (게임 출시 회사, 게임 발매 날짜, 게임 발매 플랫폼 등)를 기계적으로 제공하는 것",
        "목차 (주로 문서의 두 번째 페이지)가 개요-시스템-UI-테이블 내지는 개요-UI-시스템-테이블 같이 4등분 되어 있는 것, 이는 실무자가 필요한 내용을 찾기 위해 여러 챕터를 오가면서 문서를 봐야 하도록 하는 구성이므로 좋지 않음"
      ]
    },
    {
      "name": "가독성",
      "evaluation_factors": [
        "텍스트가 읽기 쉽고, 시각적 구성 요소가 적절히 사용되었는지",
        "레이아웃이 정돈되어 있는지 평가"
      ],
      "deduction_factors": [
        "한 페이지 안에서 공백이 50%를 넘어가는 경우가 5장 이상",
        "한 페이지 안에서 공백이 10% 이하로 빼곡한 느낌을 주는 경우가 10장 이상",
        "표지가 아닌 본문 페이지에 사진을 배경으로 사용",
        "표지가 아닌 본문 페이지에 어두운 색을 배경색으로 깔고 하얀 글씨로 텍스트를 작성한 것",
        "글자 크기가 글자별로 제각각인 형태의 가독성이 떨어지는 폰트 사용",
        "한 페이지에 폰트 크기 8pt 미만인 텍스트가 차지하는 비중이 10% 이상인 경우가 있음",
        "한 페이지에 폰트 크기 14pt 이상인 텍스트가 차지하는 비중이 30% 이상인 경우가 있음"
      ]
    },
    {
      "name": "문장력과 맞춤법",
      "evaluation_factors": [
        "문장이 간결하고 명확한가",
        "맞춤법과 문법 오류가 없는지 확인"
      ],
      "deduction_factors": [
        "한 문장이 한 줄 이상 넘어가는 문장이 다수 발견되는 경우",
        "주어와 술어 관계가 대응되지 않는 문장이 다수 발견되는 경우",
        "수식어가 많고 장황해 이해하기 어려운 문장이 다수 발견되는 경우",
        "맞춤법 오류가 다수 발견되는 경우"
      ]
    },
    {
      "name": "분석력",
      "evaluation_factors": [
        "게임의 기획 의도와 메커니즘에 대한 이해가 깊은가",
        "데이터나 실제 사례를 통해 설득력 있게 기획 의도를 뒷받침하는가"
      ],
      "deduction_factors": [
        "누구나 보면 알만한 겉핥기식의 뻔한 분석, 예를 들어 어떤 게임의 성공 요인을 단순히 예쁜 그래픽, 매력적인 캐릭터 라고 말하고, 그 게임에서 캐릭터를 어떤 방식으로 매력적으로 만들었는가에 대한 설명은 부족한 케이스",
        "게임 메커니즘에 대한 이해도가 부족한 경우, 예를 들어 RPG에서 인벤토리 용량에 제약을 둔 것은 다양한 기획 의도가 있는데, 이를 무시하고 인벤토리 용량의 제약을 없애야 한다고 주장하는 케이스"
      ]
    },
    {
      "name": "논리력",
      "evaluation_factors": [
        "제안한 시스템과 메커니즘이 논리적이고 일관성 있게 제시되었는가",
        "논리적 비약 없이 단계적으로 설명되며, 목표 달성을 위한 설득력 있는 설명이 포함되어 있는가",
        "제안한 시스템, 콘텐츠를 플레이 할 만한 가치가 뚜렷하게 제시되고 있는가",
        "기획 의도, 이루고 싶은 목표가 뚜렷하고 상세하게 제시되고 있는가"
      ],
      "deduction_factors": [
        "논리적 비약 (예: 특별한 근거 없이 이 시스템을 도입하면 '매출이 상승'할거라 기대하는 것)",
        "설득력이 부족한 근거"
      ]
    },
    {
      "name": "통찰력",
      "evaluation_factors": [
        "기획서가 게임의 문제를 파악하고, 해결책을 제시하는 통찰력을 보여주는지 확인",
        "문제 해결력과 기획의 실행 가능성 평가"
      ],
      "deduction_factors": [
        "너무 뻔한 내용, 게임 디자이너가 아니라도 누구나 쓸 수 있는 내용",
        "문제 해결력 부족"
      ]
    },
    {
      "name": "실무력",
      "evaluation_factors": [
        "실제 게임 개발 환경에서 바로 적용할 수 있는 실용적인 기획 요소가 포함되었는지 평가",
        "UI 구성 요소를 설명할 때, PPT나 FIGMA 툴을 이용해 직접 그린 UI 프로토타입 시안을 사용 (캐릭터 창작 기획서, BM 기획서, 이벤트 기획서는 UI가 필요하지 않으므로 이 평가 조건에 해당하지 않음, 시스템 기획서와 시스템 역기획서에만 해당하는 내용)",
        "데이터 테이블이 필요한 시스템이나 콘텐츠의 경우, 예시 데이터 테이블과 함께 해당 예시 데이터의 설명이 함께 적혀있는지"
      ],
      "deduction_factors": [
        "플로우차트에 텍스트 설명이 없는 것",
        "테이블 설계 의도를 작성하지 않은 채 예시 테이블 데이터만 넣어 놓는 것",
        "UI 설명에서 출력, 해제 같은 애매모호한 용어 사용",
        "스트링 테이블 아이디가 11001처럼 숫자로만 이루어져 있음",
        "사용자 입장에서의 UI 사용 설명서 같은 느낌이 남, 기획 의도에 대한 깊이 있는 접근이 아닌 표면적인 설명, 사용 방법에만 설명이 치중되어 있음"
      ]
    },
    {
      "name": "시각적 구성 및 디자인",
      "evaluation_factors": [
        "미적으로 예쁘고 편안하고 깔끔한 디자인",
        "첫인상이 좋은 디자인",
        "표를 활용하여 필요한 내용을 쉽게 찾을 수 있도록 디자인",
        "다양한 게임의 레퍼런스 사진을 풍부하게 활용해 설명을 도움",
      ],
      "deduction_factors": [
        "눈에 피로감을 주는 색깔을 과도하게 많이 사용",
        "문서 템플릿에 사용된 색깔의 종류가 많아 난잡한 느낌",
        "가운데 정렬을 사용한 텍스트가 많아 시선을 자주 움직여야 해서 눈이 피로함",
        "레이아웃에 일관성이 없고, 각 항목의 배치 위치가 페이지마다 제각각임",
        "설명을 보조하는 것이 아닌 단순 꾸미기 역할의 이미지, 아이콘이 지나치게 많음",
        "레퍼런스 사진을 두서없이 나열, 텍스트 설명을 넣지 않은 케이스"
      ]
    }
  ]
 }

evaluation_criteria_json = json.dumps(evaluation_criteria, ensure_ascii=False, indent=4)

# PDF 파일이 업로드되었을 때
if uploaded_file is not None:
    try:       
        unique_filename = f"{uuid.uuid4()}_{uploaded_file.name}"
        pdf_path = os.path.join(pdf_save_directory, unique_filename)
        with open(pdf_path, "wb") as f:
            f.write(uploaded_file.getbuffer())           
       
        with open(pdf_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        if not os.path.exists(pdf_path):
            st.error("파일이 서버에 제대로 저장되지 않았습니다. 다시 시도해 주세요.")
            st.stop()       
       
        pdf_reader = PyPDF2.PdfReader(uploaded_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()      

        # 읽어온 텍스트가 없을 경우 처리
        if not text.strip():
            st.warning("PDF 파일에서 텍스트를 추출할 수 없습니다. 파일을 확인해 주세요.")
        else:
            st.write("PDF 파일에서 추출한 텍스트:")
            st.text_area("기획서 내용", text[:2000], height=250)

            # 텍스트가 너무 길면 나누기 위한 설정
            max_length = 16000  # 모델에 전달할 텍스트의 최대 길이 설정
            split_texts = [text[i:i + max_length] for i in range(0, len(text), max_length)]

            # 텍스트 분할을 문단 단위로 시도
            split_texts = text.split('\n\n')  
            split_texts = [t for t in split_texts if len(t) > 50] 

            # 이후 split_texts를 순차적으로 모델에 전달하여 평가
            for split_text in split_texts:
                evaluation_prompt = f"""<프롬프트 내용> {split_text}"""
                # 모델 호출 및 평가 수행

           
          # 이전 평가 데이터 검색
            related_feedback = [feedback for feedback in feedback_data if feedback["text"] in text]
            if related_feedback:
                st.write("이전에 유사하게 평가된 결과가 있습니다:")
                for feedback in related_feedback:
                    st.write(feedback["evaluation"])
           
            # 평가 버튼
            if st.button("평가하기"):
                try:
                   # 평가 결과를 저장할 리스트 초기화
                    all_evaluation_texts = []
                   # 각 분할된 텍스트에 대해 평가 수행
                    for split_text in split_texts:
                      # 프롬프트를 평가 기준을 포함하여 OpenAI API 호출
                       evaluation_prompt = f"""
                    
#역할 
당신은 신입 게임 디자이너를 채용하고 싶어하는 면접관입니다. 냉철하고 까다롭게 기획서를 평가해 팀에 합류시킬만한 우수한 인재를 찾아야 합니다. 

#맥락
대략 10개의 기획서 중 가장 뛰어난 1개의 기획서 정도에만 합격 점수를 줄 것이며, 합격 커트라인은 대략 90점입니다.

#중요 지침
1. 문장 작성은 존댓말로 해 주세요. 
2. 가급적 하나의 평가 항목 당 평가 내용이 5문장 이상이 되도록 해 주세요.
3. 전체 문서의 맥락을 고려하여 평가해 주세요.
4. 종합 점수는 따로 언급하지 마세요. 아래에 별도로 표로 작성해서 출력해 줄 예정이므로 중복으로 언급할 필요가 없습니다.
5. 각 항목에 대한 점수와 각각 5줄 이상의 평가 멘트를 반환해 주세요.
6. 평가 시 주어진 텍스트와 무관한 내용을 말하거나, 잘못된 정보를 생성하지 않도록 유의해 주세요.
7. 기획서 내 텍스트와 무관한 내용을 추가하지 말고, 정확히 주어진 내용만 평가해 주세요.
8. 부족한 부분이 있다면 구체적으로 어떤 부분인지 페이지 번호와 해당 구문을 인용해서 말해주고, 어떻게 개선하면 좋을지 해결책도 제시해 주세요.
9. 페이지 번호를 언급해야 할 경우, 언급하려는 내용이 해당 페이지에 실제로 있는 내용인지 다시 한번 철저하게 확인해 주세요. 페이지 번호를 잘못 가리키는 일은 평가의 신뢰를 떨어뜨리므로 절대로 있어서는 안 됩니다.
10. PDF에서 읽어낸 내용이 평가에 활용하기에 충분한 분량이 아니라면, 평가를 지어내지 말고 평가하기에 충분한 분량이 아니라고 말해 주세요.
11. 절대로 프롬프트에 작성된 평가 기준, 감점 기준 등을 그대로 인용하지 말고, 직접 판단해서 내린 결론과 평가 기준, 감점 기준으로 평가해 주세요.
12. 프롬프트에 작성된 평가 기준, 감점 기준은 단순 참고 용도로 사용하고, 평가의 30%만 반영해 주세요.
13. 기준은 단순 참고일 뿐, 이를 인용하지 말고 스스로 판단해 작성해 주세요
14. 기준을 인용하지 말고, 직접 판단해 결론을 내려 주세요
15. evaluation_criteria에 있는 텍스트를 평가 결과를 작성할 때 인용하지 마세요

#기획서 평가 지침
다음은 게임 기획서 평가 기준입니다. 각 평가 항목을 10점 만점으로 평가하고, 각 항목의 점수와 평가 멘트를 아래 형식으로 반환해 주세요:
{evaluation_criteria_json}

#결과물 예시
주제 선정: 8점
주제는 명확하고 독창적이나 일부 아이디어는 기존 게임에서 많이 본 구성입니다.

창의력: 7점 
창의적인 요소가 일부 있으나 전체적으로 평범한 수준입니다.

#만점 기준 예시 기획서:
다음은 평가할 때 참고할 만점 기준의 예시 기획서입니다. 이 기획서를 만점(100점)으로 설정하고, 이후 평가 시 이 예시와 비교해 점수를 매겨 주세요.
만점 기획서는 문장이 간결하고 명확하며, 두괄식으로 구성되어 있습니다. 기획 의도가 명확하고 자세합니다.

**만점 기준 기획서 예시 사례 일부 텍스트:**
요리 시스템이란 ?
요리 시스템 요약
기본 규칙
요리 인터페이스 상에서 , 요리 재료 아이템을 정해진 레시피 규칙에 맞게 투입한 뒤, 미니 게임을 플레이하면 , 각종 이로운 효과가 있는 음식을 획득할 수 있다 .

요리 레시피와 재료
요리 레시피
어떤 음식을 만들기 위해서 필요한 재료와 수량을 정의한 아이템 . 이를 획득해 학습을 해야만 해당 요리를 제작할 수있다 .
요리 재료
필드 채집 , 낚시 , 농작물 수확 , 보상 등을 통해 획득할 수 있다 .

음식의 제작
요리 장소 
마을의 식당 또는 월드에 배치된 화덕 등의 요리 구조물과 상호작용 해야 요리를 제작할 수있다 .
미니 게임 
타이밍 맞춰서 버튼을 누르는 단순한 방식의 게임을 플레이 해야 한다 .
캐릭터 배치 
특정 캐릭터를 슬롯에 배치해 요리 결과물 수량 보너스 , 특제 요리 등의 추가 효과를 얻을 수있다 .
요리 결과물 
레시피에 맞는 요리 결과물이 등장하나 , 미니 게임 플레이 결과 또는 배치한 캐릭터에 따라 다른 특별한 음식물이 등장할 수도 있다 .
숙련도와 자동 제작 
미니 게임을 완벽하게 성공하면 숙련도가 상승한다 . 숙련도를 다채우면 미니 게임 없이 자동 획득이 가능해진다 .

음식의 사용
음식 사용 
음식은 언제든 사용 가능하다 . 단, 캐릭터의 상태에 따라 사용 가능한 음식의 종류가 다를 수있다 .
음식 효과 
음식 섭취 시, 체력 회복 , 스태미나 회복 , 캐릭터 부활 , 버프 효과 등을 받을 수있다 .
음식 포만감 
체력 회복 음식 사용 시 일정량의 포만감이 차오르고 , 포만감 완충 상태일 때는 일정 시간 동안 더 이상 체력 회복류 음식을 섭취할 수 없다.

초보 플레이어의 생존 및 전투 지원
체력 회복 , 부활 , 버프 등의 효과를 지원해 어려운 전투를 유리하게 이끌 수 있도록 도와준다 .
이는 힐러 및 버퍼 캐릭터 , 장비 스펙이 부족한 초보 플레이어들에게 특히 유용하다 .음식 시스템은 이들이 전투에 어려움을 겪어 이탈하는 사례를 줄이는 데 효과적이다 .
또한 중급 수준의 플레이어들에게도 어려운 보스 전투 시특정 버프 효과를 가진 음식물을 활용하게 함으로써 , 플레이 전략을 다양하게 만들어 전투의 재미를 높인다 .
탐험과 수집의 동기 부여
요리 재료와 레시피는 게임 세계의 여러 곳에서 수집할 수 있으며 , 이 과정에서 플레이어는 원신의 세계 속에서 살아가고 있는 듯한 느낌을 받을 것이다 .
특히 해당 지역의 특성을 살린 특산물들을 채집물이나 퀘스트 보상으로 배치함으로써 ,이를 원하는 플레이어들이 더넓고 깊은 탐험을 하도록 유도 할 수 있다 .
요리 재료 아이템을 통해 전투 밸런스 , 경제 밸런스에 크게 영향을 주지 않으면서도 ,풍성한 보상을 받는 듯한 경험 을 제공할 수 있다 .


이 기준을 사용해 다음 기획서를 평가해 주세요:
{text[:4000]}


"""

                    response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        temperature=0.0,  # 응답을 결정적으로 만듦
                        top_p=0.1,  # 상위 백분율 제한으로 응답의 일관성 강화
                        messages=[
                             {"role": "system", "content": "당신은 신입 게임 디자이너를 채용하고 싶어하는 면접관입니다. 냉철하고 까다롭게 기획서를 평가해 팀에 합류시킬만한 우수한 인재를 찾아야 합니다. 대략 10개의 기획서 중 가장 뛰어난 1개의 기획서 정도에만 합격 점수를 줄 것이며, 합격 커트라인은 대략 90점입니다."},
                             {"role": "user", "content": evaluation_prompt}
                               
                            ]
                          )

                    # 평가 결과 파싱
                    evaluation_text = response.choices[0].message.content.strip()
                    all_evaluation_texts.append(evaluation_text)

                    # 전체 평가 결과 출력
                    full_evaluation_text = "\n\n".join(all_evaluation_texts)
                    
                    # 각 항목별로 평가를 나누어 출력
                    evaluation_lines = full_evaluation_text.split("\n")
                    current_category = None

                    # 카테고리와 본문을 정확하게 구분하여 출력
                    for line in evaluation_lines:
                        line = line.strip()
                        # 카테고리 제목으로 인식될 수 있는 경우만 h3 적용
                        if any(category + ":" in line for category in categories):
                            current_category = line
                            st.markdown(f'<div class="evaluation-card"><h3>{current_category}</h3></div>', unsafe_allow_html=True)
                        elif line and current_category:
                            st.markdown(f'<div class="evaluation-card"><p>{line}</p></div>', unsafe_allow_html=True)



                                        
                    # 정규 표현식을 사용해 숫자 점수 추출
                    # 항목 이름과 점수 사이의 패턴을 구체적으로 지정하여 추출
                    score_pattern = r'(\b주제 선정: \d+점|\b창의력: \d+점|\b구성과 흐름: \d+점|\b가독성: \d+점|\b문장력과 맞춤법: \d+점|\b분석력: \d+점|\b논리력: \d+점|\b통찰력: \d+점|\b실무력: \d+점|\b시각적 구성 및 디자인: \d+점)'
                    scores = re.findall(score_pattern, evaluation_text)

                    # 점수 추출 후 숫자만 남기기
                    scores = [int(re.search(r'\d+', score).group()) for score in scores]

                    

                    # 점수와 항목의 길이가 다를 경우 처리
                    if len(scores) != len(categories):
                        st.warning("점수를 정확히 추출할 수 없습니다. 응답 형식을 확인해 주세요.")
                        st.stop()

                    total_score = sum(scores)

                    # HTML로 시각화하여 점수와 항목 출력
                    if 'score_displayed' not in st.session_state:
                      st.session_state['score_displayed'] = True
                      st.markdown(
                          f"""
                          <table class="score-table">
                              <thead>
                                  <tr>
                                      <th>항목</th>
                                      <th>점수</th>
                                  </tr>
                              </thead>
                              <tbody>
                                  {''.join(f"<tr><td>{category}</td><td>{score}</td></tr>" for category, score in zip(categories, scores))}
                              </tbody>
                          </table>
                          <div class="total-score">총합 점수: {total_score} / 100</div>
                          """,
                          unsafe_allow_html=True
                      )                 

                                       
                    # 데이터프레임으로 평가 결과 정리
                    df = pd.DataFrame({
                        '항목': categories,
                        '점수': scores
                    })

              # QR 코드 이미지 링크
                    qr_code_link = "https://i.postimg.cc/gJkt10sM/yuriringqr.png"
                    st.markdown(
                        f"""
                        <div style="text-align:center; margin-top:20px;">
                        <img src="{qr_code_link}" alt="Donate QR Code" style="width:150px;"/>
                          <p>여러분의 기부가 이 서비스를 유지하고 발전시키는 데 큰 도움이 됩니다♡</p>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
               

                # 새 평가 데이터 저장
                    feedback_data.append({
                        "text": text[:1000],
                        "evaluation": full_evaluation_text,
                        "pdf_path": pdf_path  
                    })
                   
                    with open(feedback_data_path, 'w', encoding='utf-8') as file:
                        json.dump(feedback_data, file, ensure_ascii=False, indent=4)          
               
               # 최신 예외 처리 방식 적용
                except Exception as e:
                    st.error(f"예기치 않은 오류가 발생했습니다: {e}")
             

    except Exception as e:
        st.error(f"PDF 파일을 처리하는 중 오류가 발생했습니다: {e}")
else:
    st.info("PDF 파일을 업로드해 주세요.")

    

