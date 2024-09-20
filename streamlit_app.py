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
    <h1 style="text-align:center; font-family:Arial, sans-serif;">
        게임 기획서 평가 AI
    </h1>
    
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

# PDF 파일 저장 디렉토리 생성
os.makedirs(pdf_save_directory, exist_ok=True)

# 기존 피드백 데이터 불러오기
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
    
    # 평가 데이터 조회 버튼 추가 (관리자만 볼 수 있음)
    if st.sidebar.button("저장된 평가 데이터 보기"):
        if feedback_data:
            st.write("저장된 평가 데이터:")
            for idx, feedback in enumerate(feedback_data, 1):
                st.write(f"**평가 {idx}:**")
                st.write(f"**텍스트:** {feedback['text'][:200]}...")  # 길이가 긴 텍스트는 일부만 표시
                st.write(f"**평가 내용:** {feedback['evaluation']}")
              # PDF 파일 다운로드 링크 제공 (고유한 key 추가)
                pdf_path = feedback.get('pdf_path', None)
                if pdf_path and os.path.exists(pdf_path):
                    with open(pdf_path, "rb") as pdf_file:
                        st.download_button(
                            label=f"PDF 다운로드 ({os.path.basename(pdf_path)})",
                            data=pdf_file,
                            file_name=os.path.basename(pdf_path),
                            mime='application/pdf',
                            key=f"download_{idx}"  # 고유한 key 지정
                        )
                st.write("---")
        else:
            st.write("저장된 평가 데이터가 없습니다.")
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
        "가상의 게임을 대상으로 한 것이 아닌, 실제 있는 게임을 대상으로 한 기획서인가"
      ],
      "deduction_factors": [
        "창작 기획서인데 대상으로 삼은 게임이 없고, 가상의 게임을 주제로 삼아, 독자의 공감을 얻기 어려움",
        "너무 흔한 주제",
        "다양한 역량을 보여주기 어려운 주제",
        "분량이 30페이지 이상 충분히 나오기 어려운 주제",
        "다루는 범위가 지나치게 넓은 주제 (예: 길드 시스템 전체)"
      ]
    },
    {
      "name": "창의력",
      "evaluation_factors": [
        "기존 기획서에서 볼 수 없는 창의적인 아이디어가 있는가?",
        "독창적인 접근 방식이 돋보이는지"
      ],
      "deduction_factors": [
        "너무 뻔한 논리 전개 흐름",
        "너무 당연한 기획 의도 (예: 매출 증대, 리텐션 증가, 캐릭터 애착 형성)",
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
        "게임사, 출시일, 플랫폼, 장르 같은 맥락 상 불필요한 정보를 기계적으로 제공하는 것"
      ]
    },
    {
      "name": "가독성",
      "evaluation_factors": [
        "텍스트가 읽기 쉽고, 시각적 구성 요소가 적절히 사용되었는지",
        "레이아웃이 정돈되어 있는지 평가"
      ],
      "deduction_factors": [
        "불필요한 공백 또는 너무 공백이 없는 빼곡한 느낌",
        "본문 페이지에 사진을 배경으로 쓰거나 어두운 색을 배경색으로 깔아놓은 것",
        "가독성이 떨어지는 폰트, 너무 크거나 작은 폰트 크기"
      ]
    },
    {
      "name": "문장력과 맞춤법",
      "evaluation_factors": [
        "문장이 간결하고 명확한지",
        "맞춤법과 문법 오류가 없는지 확인"
      ],
      "deduction_factors": [
        "한 문장이 한 줄 이상 넘어가는 문장",
        "주어와 술어 관계가 대응되지 않는 문장",
        "수식어가 많고 장황해 이해하기 어려운 문장",
        "맞춤법 오류"
      ]
    },
    {
      "name": "분석력",
      "evaluation_factors": [
        "게임의 기획 의도와 메커니즘에 대한 이해가 깊고, 기획에 대한 분석이 잘 이루어졌는지",
        "데이터나 사례를 통해 설득력 있게 기획 의도를 뒷받침하는지"
      ],
      "deduction_factors": [
        "누구나 보면 알만한 겉핥기식의 뻔한 분석",
        "게임 메커니즘 이해도 부족"
      ]
    },
    {
      "name": "논리력",
      "evaluation_factors": [
        "제안한 시스템과 메커니즘이 논리적이고 일관성 있게 제시되었는지 평가",
        "논리적 비약 없이 단계적으로 설명되며, 목표 달성을 위한 설득력 있는 설명이 포함되어 있는지"
      ],
      "deduction_factors": [
        "논리적 비약 (예: 근거 없이 이 시스템을 도입하면 매출이 상승할거라 기대하는 것)",
        "설득력 부족한 근거"
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
        "실제 게임 개발 환경에서 바로 적용할 수 있는 실용적인 기획 요소가 포함되었는지 평가"
      ],
      "deduction_factors": [
        "플로우차트에 텍스트 설명이 없는 것",
        "테이블 설계 의도를 작성하지 않은 채 테이블만 달랑 넣어 놓는 것",
        "출력, 해제 같은 애매모호한 용어 사용",
        "숫자로만 이루어진 스트링 테이블 아이디"
      ]
    },
    {
      "name": "시각적 구성 및 디자인",
      "evaluation_factors": [
        "문서의 시각적 디자인이 독자를 고려하고, 가독성을 높이는 방향으로 잘 설계되었는지",
        "시각적 요소가 기획 의도를 잘 전달하며, 정보 전달을 효과적으로 돕는지"
      ],
      "deduction_factors": [
        "시각적 구성의 부재",
        "디자인이 일관되지 않거나 조잡한 경우"
      ]
    }
  ]
 }

evaluation_criteria_json = json.dumps(evaluation_criteria, ensure_ascii=False, indent=4)

# PDF 파일이 업로드되었을 때
if uploaded_file is not None:
    try:
       # PDF 파일 저장 (UUID를 사용해 고유한 파일 이름 생성)
        unique_filename = f"{uuid.uuid4()}_{uploaded_file.name}"
        pdf_path = os.path.join(pdf_save_directory, unique_filename)
        with open(pdf_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
           
       # 파일이 실제로 저장되는지 확인
        with open(pdf_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        if not os.path.exists(pdf_path):
            st.error("파일이 서버에 제대로 저장되지 않았습니다. 다시 시도해 주세요.")
            st.stop()
       
       # PDF 파일의 내용을 읽기
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
            max_length = 3500  # 모델에 전달할 텍스트의 최대 길이 설정
            split_texts = [text[i:i + max_length] for i in range(0, len(text), max_length)]

           
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
                    
다음은 게임 기획서 평가 기준입니다. 각 평가 항목을 10점 만점으로 평가하고, 각 항목의 점수와 평가 멘트를 아래 형식으로 반환해 주세요:

예시: 
주제 선정: 8점
주제는 명확하고 독창적이나 일부 아이디어는 기존 게임에서 많이 본 구성입니다.

창의력: 7점 
창의적인 요소가 일부 있으나 전체적으로 평범한 수준입니다.

각 항목에 대한 점수와 각각 5줄 이상의 평가 멘트를 반환해 주세요.



{evaluation_criteria_json}

이 기준을 사용해 다음 기획서를 평가해 주세요:
{text[:4000]}

"""

                    response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        temperature=0.0,  # 응답을 결정적으로 만듦
                        top_p=0.1,  # 상위 백분율 제한으로 응답의 일관성 강화
                        messages=[
                             {"role": "system", "content": "You are an expert in game design document evaluation."},
                             {"role": "user", "content": evaluation_prompt}
                               
                            ]
                          )

                    # 평가 결과 파싱
                    evaluation_text = response.choices[0].message.content.strip()
                    all_evaluation_texts.append(evaluation_text)

                    # 전체 평가 결과 출력
                    full_evaluation_text = "\n\n".join(all_evaluation_texts)
                    st.write("평가 결과:")
                    st.write(full_evaluation_text)
                                        
                    # 정규 표현식을 사용해 숫자 점수 추출
                    # 항목 이름과 점수 사이의 패턴을 구체적으로 지정하여 추출
                    score_pattern = r'(\b주제 선정: \d+점|\b창의력: \d+점|\b구성과 흐름: \d+점|\b가독성: \d+점|\b문장력과 맞춤법: \d+점|\b분석력: \d+점|\b논리력: \d+점|\b통찰력: \d+점|\b실무력: \d+점|\b시각적 구성 및 디자인: \d+점)'
                    scores = re.findall(score_pattern, evaluation_text)

                    # 점수 추출 후 숫자만 남기기
                    scores = [int(re.search(r'\d+', score).group()) for score in scores]

                    # 점수를 정확히 확인하고 출력
                    st.write(f"추출된 점수: {scores}")
                    st.write(f"개별 점수 합산: {sum(scores)}")

                    # 점수와 항목의 길이가 다를 경우 처리
                    if len(scores) != len(categories):
                        st.warning("점수를 정확히 추출할 수 없습니다. 응답 형식을 확인해 주세요.")
                        st.stop()

                    total_score = sum(scores)

                    # 데이터프레임으로 평가 결과 정리
                    df = pd.DataFrame({
                        '항목': categories,
                        '점수': scores
                    })

                    # 시각화
                    st.write(f"**총합 점수: {total_score} / 100**")
                   

                # 새 평가 데이터 저장
                    feedback_data.append({
                        "text": text[:1000],
                        "evaluation": full_evaluation_text,
                        "pdf_path": pdf_path  # PDF 파일 경로 저장
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


