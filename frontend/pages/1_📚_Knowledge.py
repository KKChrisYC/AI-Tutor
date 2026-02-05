"""
Knowledge Base Management Page
"""
import streamlit as st
import httpx

API_BASE_URL = "http://localhost:8000/api"

st.set_page_config(page_title="知识库管理 - AI Tutor", page_icon="📚", layout="wide")

st.title("📚 知识库管理")
st.markdown("上传课程资料，构建专属知识库")

# Upload section
st.subheader("📤 上传文档")
uploaded_file = st.file_uploader(
    "选择文件上传（支持 PDF、TXT、MD）",
    type=["pdf", "txt", "md"],
    accept_multiple_files=False
)

if uploaded_file:
    if st.button("上传并处理", type="primary"):
        with st.spinner("正在处理文档..."):
            try:
                files = {"file": (uploaded_file.name, uploaded_file.getvalue())}
                with httpx.Client(timeout=120.0) as client:
                    response = client.post(f"{API_BASE_URL}/knowledge/upload", files=files)
                    if response.status_code == 200:
                        st.success(f"✅ 文档 '{uploaded_file.name}' 上传成功！")
                    else:
                        st.error(f"上传失败: {response.text}")
            except Exception as e:
                st.error(f"上传失败: {e}")

st.markdown("---")

# Document list
st.subheader("📄 已上传文档")

try:
    with httpx.Client(timeout=10.0) as client:
        response = client.get(f"{API_BASE_URL}/knowledge/documents")
        if response.status_code == 200:
            documents = response.json()
            if documents:
                for doc in documents:
                    col1, col2, col3 = st.columns([3, 1, 1])
                    with col1:
                        st.markdown(f"📄 **{doc['filename']}**")
                    with col2:
                        st.caption(f"分块数: {doc['chunk_count']}")
                    with col3:
                        if st.button("删除", key=doc['id']):
                            st.warning("删除功能待实现")
            else:
                st.info("暂无文档，请上传课程资料")
except Exception as e:
    st.warning("无法连接后端服务，请确保后端已启动")

st.markdown("---")

# Stats
st.subheader("📊 知识库统计")
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("文档总数", "0")
with col2:
    st.metric("知识块总数", "0")
with col3:
    st.metric("最后更新", "-")
