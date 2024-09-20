import streamlit as st
import os

# 패키지가 설치되어 있지 않다면 설치하는 코드
if 'openai' not in st.session_state:
    st.session_state['openai'] = False
    os.system('pip install openai')  # 패키지 설치 명령

# 이후에 openai를 임포트할 수 있도록 설정
try:
    import openai
    st.session_state['openai'] = True
except ModuleNotFoundError:
    st.error("OpenAI 패키지 설치가 실패했습니다. 다시 시도해 주세요.")

# API 키 설정 및 스트림릿 앱 코드 작성
if st.session_state['openai']:
    openai.api_key = st.secrets["openai"]["openai_api_key"]

    st.title("OpenAI API를 이용한 기획서 평가")
    prompt = st.text_area("평가할 기획서 내용 입력", "")

    if st.button("평가하기"):
        if prompt:
            response = openai.Completion.create(
                model="text-davinci-003",
                prompt=prompt,
                max_tokens=500,
                temperature=0.7
            )
            st.write(response.choices[0].text.strip())
        else:
            st.warning("기획서 내용을 입력해 주세요.")
