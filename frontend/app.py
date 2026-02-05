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
</style>
""", unsafe_allow_html=True)


def init_session_state():
    """Initialize session state variables"""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "conversation_id" not in st.session_state:
        st.session_state.conversation_id = None
    if "user_id" not in st.session_state:
        st.session_state.user_id = None


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
    except httpx.HTTPError as e:
        st.error(f"API 调用失败: {e}")
        return None


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
    st.caption("你可以询问《数据结构》课程相关的任何问题")
    
    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"], avatar="🧑‍🎓" if message["role"] == "user" else "🤖"):
            st.markdown(message["content"])
            # Display sources if available
            if message.get("sources"):
                with st.expander("📖 参考来源"):
                    for source in message["sources"]:
                        st.markdown(f"- {source['source']}")
    
    # Chat input
    if prompt := st.chat_input("输入你的问题..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar="🧑‍🎓"):
            st.markdown(prompt)
        
        # Get AI response
        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("思考中..."):
                response = call_api("chat/", method="POST", data={
                    "message": prompt,
                    "conversation_id": st.session_state.conversation_id,
                    "use_rag": True
                })
                
                if response:
                    answer = response.get("answer", "抱歉，无法获取回答。")
                    sources = response.get("sources", [])
                    st.session_state.conversation_id = response.get("conversation_id")
                    
                    st.markdown(answer)
                    
                    if sources:
                        with st.expander("📖 参考来源"):
                            for source in sources:
                                st.markdown(f"- {source['source']}")
                    
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
