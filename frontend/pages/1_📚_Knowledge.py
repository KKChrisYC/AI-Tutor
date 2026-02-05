"""
Knowledge Base Management Page
"""
import streamlit as st
import httpx

API_BASE_URL = "http://localhost:8000/api"

st.set_page_config(page_title="知识库管理 - AI Tutor", page_icon="📚", layout="wide")

st.title("📚 知识库管理")
st.markdown("上传课程资料，构建专属知识库")


def get_stats():
    """获取知识库统计信息"""
    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.get(f"{API_BASE_URL}/knowledge/stats")
            if response.status_code == 200:
                return response.json()
    except:
        pass
    return {"total_documents": 0, "total_chunks": 0, "collection_name": "-"}


def get_documents():
    """获取文档列表"""
    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.get(f"{API_BASE_URL}/knowledge/documents")
            if response.status_code == 200:
                return response.json()
    except:
        pass
    return []


# Stats section
st.subheader("📊 知识库统计")
stats = get_stats()
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("文档总数", stats.get("total_documents", 0))
with col2:
    st.metric("知识块总数", stats.get("total_chunks", 0))
with col3:
    st.metric("集合名称", stats.get("collection_name", "-"))

st.markdown("---")

# Upload section
st.subheader("📤 上传文档")
uploaded_file = st.file_uploader(
    "选择文件上传（支持 PDF、TXT、MD）",
    type=["pdf", "txt", "md"],
    accept_multiple_files=False
)

if uploaded_file:
    st.info(f"已选择文件: **{uploaded_file.name}** ({uploaded_file.size / 1024:.1f} KB)")
    
    if st.button("🚀 上传并处理", type="primary"):
        with st.spinner("正在处理文档，请稍候..."):
            try:
                files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                with httpx.Client(timeout=120.0) as client:
                    response = client.post(f"{API_BASE_URL}/knowledge/upload", files=files)
                    
                    if response.status_code == 200:
                        result = response.json()
                        st.success(f"""
                        ✅ **上传成功！**
                        - 文件名: {result.get('filename')}
                        - 文档ID: `{result.get('document_id')}`
                        - 知识块数: {result.get('chunks_added')}
                        """)
                        st.rerun()  # Refresh to update stats
                    else:
                        error = response.json().get("detail", "Unknown error")
                        st.error(f"上传失败: {error}")
            except Exception as e:
                st.error(f"上传失败: {e}")

st.markdown("---")

# Document list
st.subheader("📄 已上传文档")

documents = get_documents()
if documents:
    for doc in documents:
        col1, col2, col3, col4 = st.columns([3, 1, 2, 1])
        with col1:
            st.markdown(f"📄 **{doc.get('source', 'Unknown')}**")
        with col2:
            st.caption(f"分块数: {doc.get('chunk_count', 0)}")
        with col3:
            st.caption(f"ID: {doc.get('id', '')[:8]}...")
        with col4:
            if st.button("🗑️", key=f"del_{doc.get('id')}"):
                try:
                    with httpx.Client(timeout=10.0) as client:
                        response = client.delete(f"{API_BASE_URL}/knowledge/documents/{doc.get('id')}")
                        if response.status_code == 200:
                            st.success("删除成功！")
                            st.rerun()
                        else:
                            st.error("删除失败")
                except Exception as e:
                    st.error(f"删除失败: {e}")
else:
    st.info("📭 暂无文档，请上传课程资料")

st.markdown("---")

# Search test section
st.subheader("🔍 知识库搜索测试")
search_query = st.text_input("输入搜索关键词测试检索效果")

if search_query:
    with st.spinner("搜索中..."):
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(
                    f"{API_BASE_URL}/knowledge/search",
                    params={"query": search_query, "k": 3}
                )
                if response.status_code == 200:
                    results = response.json()
                    
                    if results.get("results"):
                        st.markdown("**搜索结果:**")
                        for i, r in enumerate(results["results"], 1):
                            with st.expander(f"结果 {i}: {r.get('source', 'Unknown')} (第{r.get('page', 'N/A')}页)"):
                                st.markdown(r.get("content", ""))
                                st.caption(f"相关度: {r.get('relevance_score', 0):.2%}")
                    else:
                        st.warning("未找到相关结果")
                else:
                    st.error("搜索失败")
        except Exception as e:
            st.error(f"搜索失败: {e}")
