import streamlit as st
import os
import openai

def rfile(name_file):
    try:
        with open(name_file, "r", encoding="utf-8") as file:
            return file.read().strip()
    except FileNotFoundError:
        return ""

# Kiểm tra và hiển thị logo
logo_path = "logo.png"
if os.path.exists(logo_path):
    st.image(logo_path, use_container_width=True)

# Hiển thị tiêu đề
st.markdown(
    f"""
    <h1 style="text-align: center; font-size: 24px;">{rfile("00.xinchao.txt")}</h1>
    """,
    unsafe_allow_html=True
)

# Kiểm tra OpenAI API Key
openai_api_key = st.secrets.get("OPENAI_API_KEY")
if not openai_api_key:
    st.error("Không tìm thấy OpenAI API Key. Hãy kiểm tra lại `secrets.toml`.")
    st.stop()

client = openai.OpenAI(api_key=openai_api_key)

# Kiểm tra và lấy mô hình AI
model_name = rfile("module_chatgpt.txt") or "gpt-4o-mini"

# Tạo tin nhắn khởi tạo
INITIAL_SYSTEM_MESSAGE = {"role": "system", "content": rfile("01.system_trainning.txt")}
INITIAL_ASSISTANT_MESSAGE = {"role": "assistant", "content": rfile("02.assistant.txt")}

# Lưu trữ hội thoại trong session
if "messages" not in st.session_state:
    st.session_state.messages = [INITIAL_SYSTEM_MESSAGE, INITIAL_ASSISTANT_MESSAGE]

MAX_USER_SESSIONS = 100
if 'user_sessions' not in st.session_state:
    st.session_state.user_sessions = {}
while len(st.session_state.user_sessions) > MAX_USER_SESSIONS:
    oldest_session = list(st.session_state.user_sessions.keys())[0]
    del st.session_state.user_sessions[oldest_session]

# Giới hạn số lượng tin nhắn
MAX_MESSAGES = 50
session_id = st.session_state.get("session_id", hash(st.query_params.get('user', ['anonymous'])[0]))
st.session_state.session_id = session_id
if session_id in st.session_state.user_sessions:
    st.session_state.messages.extend(st.session_state.user_sessions[session_id])
st.session_state.messages = st.session_state.messages[-MAX_MESSAGES:]

# Hiển thị lịch sử hội thoại
for message in st.session_state.messages:
    if message["role"] != "system":
        with st.chat_message(message["role"]):
            st.markdown(f"{message['content']}")

# Tạo ô nhập liệu
prompt = st.chat_input("Bạn nhập nội dung cần trao đổi ở đây nhé?")
if prompt:
    session_id = st.session_state.get("session_id", hash(st.query_params.get('user', ['anonymous'])[0]))
    if session_id not in st.session_state.user_sessions:
        st.session_state.user_sessions[session_id] = []
    st.session_state.user_sessions[session_id].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(f"{prompt}")
    
    # Gửi tin nhắn tới OpenAI API
    response_text = "Không có phản hồi từ hệ thống."
    MAX_HISTORY_MESSAGES = 20
    recent_messages = st.session_state.messages[-MAX_HISTORY_MESSAGES:]
    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[{"role": m["role"], "content": m["content"]} for m in recent_messages],
            stream=True,
            timeout=30
        )
        response_text = response.choices[0].message.content if response.choices else "Không có phản hồi từ hệ thống."
    except openai.error.OpenAIError as e:
        response_text = f"Lỗi API: {str(e)}"
    
    with st.chat_message("assistant"):
        st.markdown(f"{response_text}")
    if session_id in st.session_state.user_sessions:
        st.session_state.user_sessions[session_id].append({"role": "assistant", "content": response_text})
