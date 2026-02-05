"""
Quiz and Practice Page
"""
import streamlit as st
import httpx

API_BASE_URL = "http://localhost:8000/api"

st.set_page_config(page_title="智能练习 - AI Tutor", page_icon="📝", layout="wide")

st.title("📝 智能练习")
st.markdown("针对你的薄弱知识点，生成个性化练习题")

# Quiz generation settings
st.subheader("⚙️ 练习设置")

col1, col2, col3 = st.columns(3)
with col1:
    knowledge_point = st.selectbox(
        "选择知识点",
        ["自动推荐（基于薄弱点）", "线性表", "栈和队列", "二叉树", "图", "排序算法"]
    )
with col2:
    difficulty = st.selectbox(
        "难度等级",
        ["自适应", "简单", "中等", "困难"]
    )
with col3:
    question_count = st.number_input("题目数量", min_value=1, max_value=20, value=5)

if st.button("🎲 生成练习题", type="primary"):
    with st.spinner("正在生成题目..."):
        st.info("出题功能待实现。完成 RAG 核心功能后将启用此功能。")

st.markdown("---")

# Quiz area (placeholder)
st.subheader("📋 练习题目")
st.markdown("点击上方按钮生成练习题")

# Example quiz format
with st.expander("题目格式示例"):
    st.markdown("""
    **题目 1** (选择题 - 简单)
    
    在单链表中，要删除某一指定结点，必须知道该结点的：
    
    - A. 直接前驱结点
    - B. 直接后继结点  
    - C. 数据域
    - D. 头指针
    
    ---
    
    **题目 2** (代码题 - 中等)
    
    请补全以下二叉树前序遍历的递归代码：
    
    ```c
    void preOrder(BiTree T) {
        if (T != NULL) {
            visit(T);
            _______;  // 填空
            _______;  // 填空
        }
    }
    ```
    """)

st.markdown("---")

# Quiz history
st.subheader("📚 练习历史")
st.info("暂无练习记录")
