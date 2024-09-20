import streamlit as st
import openai
import PyPDF2

# OpenAI API 키 설정
openai.api_key = st.secrets["openai"]["openai_api_key"]

st.title("OpenAI API를 이용한 기획서 평가")

# PDF 파일 업로드 받기
uploaded_file = st.file_uploader("기획서 PDF 파일을 업로드하세요.", type="pdf")

if uploaded_file is not None:
    try:
        # PDF 파일의 내용을 읽기
        pdf_reader = PyPDF2.PdfReader(uploaded_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()

        # 텍스트가 추출되었는지 확인
        if not text.strip():
            st.warning("PDF 파일에서 텍스트를 추출할 수 없습니다. 파일을 확인해 주세요.")
        else:
            st.write("PDF 파일에서 추출한 텍스트:")
            st.text_area("기획서 내용", text, height=250)

            if st.button("평가하기"):
                try:
                    # OpenAI API 호출
                    response = openai.ChatCompletion.create(
                        model="gpt-4o-mini",
                        messages=[
                            {"role": "system", "content": "You are an expert in game design document evaluation."},
                            {"role": "user", "content": f"다음은 게임 기획서 내용입니다. 이 기획서를 평가해 주세요:\n\n{text}"}
                        ]
                    )
                    st.write("평가 결과:")
                    st.write(response.choices[0].message['content'].strip())
                except openai.error.AuthenticationError:
                    st.error("API 키가 올바르지 않습니다. 올바른 API 키를 입력했는지 확인하세요.")
                except openai.error.PermissionError:
                    st.error("API 사용 권한이 부족합니다. OpenAI 계정의 설정을 확인해 주세요.")
                except openai.error.OpenAIError as e:
                    st.error(f"API 요청 중 오류가 발생했습니다: {e}")

    except Exception as e:
        st.error(f"PDF 파일을 처리하는 중 오류가 발생했습니다: {e}")
else:
    st.info("PDF 파일을 업로드해 주세요.")
