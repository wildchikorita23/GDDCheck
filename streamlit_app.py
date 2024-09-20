import streamlit as st
import openai
import PyPDF2

# OpenAI API 키 설정
try:
    openai.api_key = st.secrets["openai"]["openai_api_key"]
except KeyError:
    st.error("API 키가 설정되지 않았습니다. secrets.toml 파일을 확인하세요.")

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
            st.text_area("기획서 내용", text[:2000], height=250)

            if st.button("평가하기"):
                try:
                    response = openai.ChatCompletion.create(
                        model="gpt-4o-mini",
                        messages=[
                            {"role": "system", "content": "You are an expert in game design document evaluation."},
                            {"role": "user", "content": f"다음은 기획서 내용입니다. 평가해 주세요:\n\n{text[:4000]}"}
                        ]
                    )
                    st.write("평가 결과:")
                    st.write(response.choices[0].message['content'].strip())

                except openai.AuthenticationError:
                    st.error("API 키가 잘못되었거나 권한이 없습니다. API 키를 확인하세요.")
                except openai.PermissionError:
                    st.error("API 사용 권한이 부족합니다. 계정 상태를 확인해 주세요.")
                except openai.error.RateLimitError:
                    st.error("API 요청 한도를 초과했습니다. 요금제를 확인하세요.")
                except openai.InvalidRequestError as e:
                    st.error(f"잘못된 요청입니다: {e}")
                except openai.OpenAIError as e:
                    st.error(f"API 요청 중 일반 오류가 발생했습니다: {e}")

    except Exception as e:
        st.error(f"PDF 파일을 처리하는 중 오류가 발생했습니다: {e}")
else:
    st.info("PDF 파일을 업로드해 주세요.")
