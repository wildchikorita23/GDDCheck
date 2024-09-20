import streamlit as st
# import openai
from openai import OpenAI
import PyPDF2
import pandas as pd
import matplotlib.pyplot as plt

# OpenAI API 키 설정
try:
   api_key = st.secrets.openai.openai_api_key
except KeyError:
    st.error("API 키가 설정되지 않았습니다. secrets.toml 파일을 확인하세요.")
client = OpenAI(api_key=api_key)

st.title("OpenAI API를 이용한 기획서 평가")

# PDF 파일 업로드 받기
uploaded_file = st.file_uploader("기획서 PDF 파일을 업로드하세요.", type="pdf")

# 각 평가 항목 초기화
categories = [
    "주제 선정", "창의력", "구성과 흐름", "가독성", "문장력과 맞춤법",
    "분석력", "논리력", "통찰력", "실무력", "시각적 구성 및 디자인"
]

# PDF 파일이 업로드되었을 때
if uploaded_file is not None:
    try:
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

            # 평가 버튼
            if st.button("평가하기"):
                try:
                    # 프롬프트를 평가 기준을 포함하여 OpenAI API 호출
                    evaluation_prompt = f"""
다음은 게임 기획서 평가 기준입니다. 각 평가 항목을 10점 만점으로 평가하고, 각 항목의 점수와 총합 점수를 출력해 주세요:

1. **주제 선정**: 
   - 평가 요소: 주제가 명확하고 독창적인가? 특정 게임이나 유저를 대상으로 하는지, 기획 의도가 분명한지 확인합니다. 
   - 감점 요소: 창작 기획서인데 대상으로 삼은 게임이 없음, 주제가 너무 뻔함, 다양한 역량을 보여주기 어려운 주제, 분량이 30페이지 이상 충분히 나오기 어려운 주제, 다루는 범위가 지나치게 넓은 주제 (예: 길드 시스템 전체).

2. **창의력**: 
   - 평가 요소: 기존 게임에서 볼 수 없는 창의적인 아이디어나 메커니즘이 있는가? 독창적인 접근 방식이 돋보이는지. 
   - 감점 요소: 너무 뻔한 논리 전개 흐름, 너무 당연한 기획 의도 (예: 매출 증대, 리텐션 증가, 캐릭터 애착 형성), 공통적으로 보이는 내용과 문서의 구성.
   - 추가 평가: 제안된 아이디어가 게임의 핵심 재미 요소를 강화하고, 새로운 유저 경험을 창출할 수 있는지.

3. **구성과 흐름**: 
   - 평가 요소: 문서가 논리적 순서에 따라 잘 구성되어 있는지, 각 섹션이 유기적으로 연결되어 있는지. 
   - 감점 요소: 필요한 내용을 찾기 어렵거나, 내용이 뒤죽박죽인 구성, 불필요하거나 중복된 내용으로 페이지를 낭비하는 것.

4. **가독성**: 
   - 평가 요소: 텍스트가 읽기 쉽고, 시각적 구성 요소가 적절히 사용되었는지. 레이아웃이 정돈되어 있는지 평가합니다.
   - 감점 요소: 불필요한 공백 또는 너무 공백이 없는 빼곡한 느낌, 본문 페이지에 사진을 배경으로 쓰거나 어두운 색을 배경색으로 깔아놓은 것, 가독성이 떨어지는 폰트, 너무 크거나 작은 폰트 크기.

5. **문장력과 맞춤법**: 
   - 평가 요소: 문장이 간결하고 명확한지, 맞춤법과 문법 오류가 없는지 확인합니다.
   - 감점 요소: 한 문장이 한 줄 이상 넘어가는 문장, 주어와 술어 관계가 대응되지 않는 문장, 수식어가 많고 장황해 이해하기 어려운 문장, 맞춤법 오류.

6. **분석력**: 
   - 평가 요소: 게임 메커니즘에 대한 이해가 깊고, 기획에 대한 분석이 잘 이루어졌는지. 데이터나 사례를 통해 설득력 있게 기획 의도를 뒷받침하는지.
   - 감점 요소: 누구나 보면 알만한 겉핥기식의 뻔한 분석, 게임 메커니즘 이해도 부족.

7. **논리력**: 
   - 평가 요소: 제안한 시스템과 메커니즘이 논리적이고 일관성 있게 제시되었는지 평가합니다. 논리적 비약 없이 단계적으로 설명되며, 목표 달성을 위한 설득력 있는 설명이 포함되어 있는지.
   - 감점 요소: 논리적 비약 (예: 근거 없이 이 시스템을 도입하면 매출이 상승할거라 기대하는 것), 설득력 부족한 근거.

8. **통찰력**: 
   - 평가 요소: 기획서가 게임의 문제를 파악하고, 해결책을 제시하는 통찰력을 보여주는지 확인합니다. 문제 해결력과 기획의 실행 가능성 평가.
   - 감점 요소: 너무 뻔한 내용, 게임 디자이너가 아니라도 누구나 쓸 수 있는 내용, 문제 해결력 부족.

9. **실무력**: 
   - 평가 요소: 실제 게임 개발 환경에서 바로 적용할 수 있는 실용적인 기획 요소가 포함되었는지 평가합니다.
   - 감점 요소: 플로우차트에 텍스트 설명이 없는 것, 테이블 설계 의도를 작성하지 않은 채 테이블만 달랑 넣어 놓는 것, 출력, 해제 같은 애매모호한 용어 사용, 숫자로만 이루어진 스트링 테이블 아이디.

10. **시각적 구성 및 디자인**: 
    - 평가 요소: 문서의 시각적 디자인이 독자를 고려하고, 가독성을 높이는 방향으로 잘 설계되었는지. 시각적 요소가 기획 의도를 잘 전달하며, 정보 전달을 효과적으로 돕는지.
    - 감점 요소: 시각적 구성의 부재, 디자인이 일관되지 않거나 조잡한 경우.

이 기준을 사용해 다음 기획서를 평가해 주세요:

{text[:4000]}
"""

                    response = client.chat.completions.create(
                        model="gpt-4-turbo",
                        messages=[
                            {"role": "system", "content": "You are an expert in game design document evaluation."},
                            {"role": "user", "content": evaluation_prompt}
                        ]
                    )

                    # 평가 결과 파싱
                    evaluation_text = response.choices[0].message.content.strip()
                    st.write("평가 결과:")
                    st.write(evaluation_text)

                    # 예시 데이터: 실제로는 AI의 평가 결과에서 각 항목별 점수를 추출해야 함
                    scores = [8, 7, 9, 6, 7, 8, 9, 6, 8, 7]  # 이 부분은 실제 결과에 따라 조정 필요
                    total_score = sum(scores)

                    # 데이터프레임으로 평가 결과 정리
                    df = pd.DataFrame({
                        '항목': categories,
                        '점수': scores
                    })

                    # 시각화
                    st.write(f"**총합 점수: {total_score} / 100**")

                    # 막대 그래프 그리기
                    fig, ax = plt.subplots()
                    df.plot(kind='bar', x='항목', y='점수', legend=False, ax=ax)
                    plt.ylim(0, 10)
                    plt.title('평가 항목별 점수')
                    plt.xlabel('항목')
                    plt.ylabel('점수')
                    plt.xticks(rotation=45, ha='right')
                    st.pyplot(fig)

                # 최신 예외 처리 방식 적용
                except Exception as e:
                    st.error(f"예기치 않은 오류가 발생했습니다: {e}")

    except Exception as e:
        st.error(f"PDF 파일을 처리하는 중 오류가 발생했습니다: {e}")
else:
    st.info("PDF 파일을 업로드해 주세요.")
