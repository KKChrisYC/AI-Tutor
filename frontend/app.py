"""
Streamlit Frontend - Main Entry Point
"""
import streamlit as st
import httpx
from typing import Optional

# Configuration
API_BASE_URL = "http://localhost:8000/api"

st.set_page_config(
    page_title="AI Tutor - 智能助教",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
.main-header {
    font-size: 2.5rem;
    font-weight: bold;
    color: #1E3A8A;
    text-align: center;
    padding: 1rem 0;
}
.sub-header {
    font-size: 1.2rem;
    color: #64748B;
    text-align: center;
    margin-bottom: 2rem;
}
.stChatMessage {
    padding: 1rem;
}
.login-box {
    padding: 2rem;
    border-radius: 10px;
    background: #f8f9fa;
}
</style>
""", unsafe_allow_html=True)


def init_session_state():
    """Initialize session state variables"""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "conversation_id" not in st.session_state:
        st.session_state.conversation_id = None
    if "user" not in st.session_state:
        st.session_state.user = None
    if "token" not in st.session_state:
        st.session_state.token = None


def call_api(endpoint: str, method: str = "GET", data: dict = None) -> Optional[dict]:
    """Call backend API"""
    try:
        url = f"{API_BASE_URL}/{endpoint}"
        with httpx.Client(timeout=60.0) as client:
            if method == "GET":
                response = client.get(url)
            else:
                response = client.post(url, json=data)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        error_detail = "未知错误"
        try:
            error_detail = e.response.json().get("detail", str(e))
        except:
            error_detail = str(e)
        st.error(f"API 错误: {error_detail}")
        return None
    except httpx.HTTPError as e:
        st.error(f"网络错误: {e}")
        return None


def login_form():
    """Display login form in sidebar"""
    with st.sidebar.expander("🔐 登录 / 注册", expanded=not st.session_state.user):
        tab1, tab2 = st.tabs(["登录", "注册"])
        
        with tab1:
            with st.form("login_form"):
                username = st.text_input("用户名/邮箱")
                password = st.text_input("密码", type="password")
                submitted = st.form_submit_button("登录")
                
                if submitted:
                    if username and password:
                        result = call_api("user/login", "POST", {
                            "username": username,
                            "password": password
                        })
                        if result and result.get("success"):
                            st.session_state.user = result["user"]
                            st.session_state.token = result["token"]
                            st.success(f"欢迎回来，{result['user']['display_name']}！")
                            st.rerun()
                        elif result:
                            st.error(result.get("error", "登录失败"))
                    else:
                        st.warning("请输入用户名和密码")
        
        with tab2:
            with st.form("register_form"):
                new_username = st.text_input("用户名", key="reg_username")
                new_email = st.text_input("邮箱", key="reg_email")
                new_password = st.text_input("密码", type="password", key="reg_password")
                display_name = st.text_input("昵称（可选）", key="reg_display")
                submitted = st.form_submit_button("注册")
                
                if submitted:
                    if new_username and new_email and new_password:
                        result = call_api("user/register", "POST", {
                            "username": new_username,
                            "email": new_email,
                            "password": new_password,
                            "display_name": display_name or new_username
                        })
                        if result and result.get("success"):
                            st.session_state.user = result["user"]
                            st.session_state.token = result["token"]
                            st.success("注册成功！")
                            st.rerun()
                        elif result:
                            st.error(result.get("error", "注册失败"))
                    else:
                        st.warning("请填写所有必填项")


def logout():
    """Logout current user"""
    st.session_state.user = None
    st.session_state.token = None
    st.session_state.messages = []
    st.session_state.conversation_id = None


def main():
    """Main application"""
    init_session_state()
    
    # Header
    st.markdown('<h1 class="main-header">🎓 AI Tutor - 智能助教</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">基于大模型与 RAG 技术的个性化智能学习系统</p>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("📚 AI Tutor")
        st.markdown("---")
        
        # User section
        if st.session_state.user:
            st.success(f"👤 {st.session_state.user['display_name']}")
            if st.button("退出登录"):
                logout()
                st.rerun()
        else:
            login_form()
        
        st.markdown("---")
        
        # Navigation
        st.subheader("功能导航")
        st.page_link("app.py", label="💬 智能问答", icon="💬")
        st.page_link("pages/1_📚_Knowledge.py", label="📚 知识库管理", icon="📚")
        st.page_link("pages/2_📊_Profile.py", label="📊 学习画像", icon="📊")
        st.page_link("pages/3_📝_Quiz.py", label="📝 智能练习", icon="📝")
        
        st.markdown("---")
        
        # System status
        st.subheader("系统状态")
        try:
            with httpx.Client(timeout=5.0) as client:
                response = client.get("http://localhost:8000/health")
                if response.status_code == 200:
                    st.success("✅ 后端服务正常")
                else:
                    st.warning("⚠️ 后端服务异常")
        except:
            st.error("❌ 后端服务未启动")
            st.caption("请运行: `uvicorn backend.main:app --reload`")
        
        st.markdown("---")
        st.caption("Made with ❤️ by AI Tutor Team")
    
    # Main chat interface
    st.subheader("💬 与 AI 助教对话")
    
    if st.session_state.user:
        st.caption(f"当前用户: {st.session_state.user['display_name']} | 对话会被保存")
    else:
        st.caption("💡 登录后可保存对话历史")
    
    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"], avatar="🧑‍🎓" if message["role"] == "user" else "🤖"):
            st.markdown(message["content"])
            # Display sources if available
            if message.get("sources"):
                with st.expander("📖 参考来源"):
                    for source in message["sources"]:
                        st.markdown(f"- {source.get('source', 'Unknown')}")
    
    # Chat input
    if prompt := st.chat_input("输入你的问题..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar="🧑‍🎓"):
            st.markdown(prompt)
        
        # Get AI response
        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("思考中..."):
                request_data = {
                    "message": prompt,
                    "conversation_id": st.session_state.conversation_id,
                    "use_rag": True
                }
                if st.session_state.user:
                    request_data["user_id"] = st.session_state.user["id"]
                
                response = call_api("chat/", method="POST", data=request_data)
                
                if response:
                    answer = response.get("answer", "抱歉，无法获取回答。")
                    sources = response.get("sources", [])
                    st.session_state.conversation_id = response.get("conversation_id")
                    
                    st.markdown(answer)
                    
                    if sources:
                        with st.expander("📖 参考来源"):
                            for source in sources:
                                st.markdown(f"- {source.get('source', 'Unknown')}")
                    
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": answer,
                        "sources": sources
                    })
                else:
                    error_msg = "抱歉，服务暂时不可用，请稍后重试。"
                    st.error(error_msg)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": error_msg
                    })


if __name__ == "__main__":
    main()
