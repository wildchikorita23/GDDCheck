import streamlit as st
import openai
import PyPDF2

# OpenAI API 키 설정: secrets.toml 파일에서 API 키를 가져옵니다.
openai.api_key = st.secrets["openai"]["openai_api_key"]

# 스트림릿 앱 제목 설정
st.title("OpenAI API를 이용한 기획서 평가")

# PDF 파일 업로드 받기
uploaded_file = st.file_uploader("기획서 PDF 파일을 업로드하세요.", type="pdf")

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
            # 추출된 텍스트를 OpenAI API로 평가하기
            st.write("PDF 파일에서 추출한 텍스트:")
            st.text_area("기획서 내용", text, height=250)

            # 평가 버튼
            if st.button("평가하기"):
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are an expert in game design document evaluation."},
                        {"role": "user", "content": f"다음은 게임 기획서 내용입니다. 이 기획서를 평가해 주세요:\n\n{text}"}
                    ],
                    max_tokens=500,
                    temperature=0.7
                )
                st.write("평가 결과:")
                st.write(response.choices[0].message['content'].strip())

    except Exception as e:
        st.error(f"PDF 파일을 처리하는 중 오류가 발생했습니다: {e}")
else:
    st.info("PDF 파일을 업로드해 주세요.")
