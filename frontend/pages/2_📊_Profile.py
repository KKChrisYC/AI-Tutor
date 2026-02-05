"""
Student Learning Profile Page
"""
import streamlit as st
import httpx

API_BASE_URL = "http://localhost:8000/api"

st.set_page_config(page_title="学习画像 - AI Tutor", page_icon="📊", layout="wide")

st.title("📊 学习画像")
st.markdown("分析你的学习情况，发现薄弱知识点")

# Mock data for demonstration
st.subheader("📈 学习概览")
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("提问次数", "0")
with col2:
    st.metric("学习时长", "0 分钟")
with col3:
    st.metric("练习完成", "0 题")
with col4:
    st.metric("平均正确率", "0%")

st.markdown("---")

# Knowledge mastery
st.subheader("🎯 知识点掌握度")

# Placeholder knowledge points
knowledge_points = [
    {"name": "线性表", "category": "基础", "mastery": 0},
    {"name": "栈和队列", "category": "基础", "mastery": 0},
    {"name": "二叉树", "category": "树", "mastery": 0},
    {"name": "图的遍历", "category": "图", "mastery": 0},
    {"name": "排序算法", "category": "排序", "mastery": 0},
]

for kp in knowledge_points:
    col1, col2 = st.columns([3, 1])
    with col1:
        st.progress(kp["mastery"] / 100, text=f"{kp['name']} ({kp['category']})")
    with col2:
        st.caption(f"{kp['mastery']}%")

st.markdown("---")

# Weak points
st.subheader("⚠️ 薄弱知识点")
st.info("暂无数据。开始使用 AI 助教后，系统会自动分析你的薄弱环节。")

# Recommendations
st.subheader("💡 学习建议")
st.markdown("""
1. 多与 AI 助教互动，系统会记录你的提问
2. 完成智能练习题，检验学习效果
3. 关注薄弱知识点的针对性练习
""")
