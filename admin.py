import streamlit as st
import pandas as pd
from supabase import create_client
import json

# ==========================================
# ⚡️ 0. 配置与连接 (复用之前的配置)
# ==========================================
st.set_page_config(page_title="Math Master 教研后台", page_icon="🎓", layout="wide")

# 你的 Supabase 配置 (请确保和之前的一样)
SUPABASE_URL = "https://fohuvfuhrtdurmnqvrty.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZvaHV2ZnVocnRkdXJtbnF2cnR5Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjY5ODEwNjksImV4cCI6MjA4MjU1NzA2OX0.FkkJGaI4yt6YnkqINMgtHYnRhJBObRysYbVZh-HuUPQ"

@st.cache_resource
def init_connection():
    try:
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        st.error(f"连接数据库失败: {e}")
        return None

supabase = init_connection()

# ==========================================
# 🎨 1. 侧边栏：功能导航
# ==========================================
with st.sidebar:
    st.title("🎓 奥数教研中心")
    st.caption("Content Management System")
    menu = st.radio("功能模块", ["📝 录入新题", "🗂️ 题库管理"])

# ==========================================
# 📝 模块 A：录入新题 (Data Entry)
# ==========================================
if menu == "📝 录入新题":
    st.header("📝 录入新题目")
    st.info("💡 请将您儿子奥数书上的题目录入到这里。越详细越好。")

    with st.form("new_question_form", clear_on_submit=True):
        col1, col2 = st.columns([2, 1])
        
        with col1:
            content = st.text_area("题目内容 (支持文字描述)", height=150, placeholder="例如：小明有5个苹果...")
            explanation = st.text_area("题目解析 (用于错题讲解)", height=100, placeholder="解析：这道题的关键在于...")
        
        with col2:
            grade = st.selectbox("适用年级", [1, 2, 3, 4, 5, 6], index=2) # 默认3年级
            category = st.selectbox("知识点标签", ["计算 (Calculation)", "逻辑 (Logic)", "几何 (Geometry)", "行程 (Travel)", "组合 (Combo)"])
            difficulty = st.slider("难度系数 (星级)", 1, 5, 3)
            q_type = st.radio("题型", ["填空题 (Fill)", "选择题 (Choice)"])
            
            answer = st.text_input("标准答案", placeholder="例如：4")
        
        # 提交按钮
        submitted = st.form_submit_button("💾 保存题目到云端")
        
        if submitted:
            if not content or not answer:
                st.error("❌ 题目内容和答案不能为空！")
            else:
                new_q = {
                    "content": content,
                    "answer": answer,
                    "type": "fill" if "Fill" in q_type else "choice",
                    "difficulty": difficulty,
                    "category": category.split(" ")[0], # 只取英文前的中文
                    "grade": grade,
                    "explanation": explanation
                }
                
                try:
                    # 写入 Supabase
                    supabase.table("questions").insert(new_q).execute()
                    st.success("✅ 录入成功！题目已存入题库。")
                except Exception as e:
                    st.error(f"保存失败: {e}")

# ==========================================
# 🗂️ 模块 B：题库管理 (Data Grid)
# ==========================================
elif menu == "🗂️ 题库管理":
    st.header("🗂️ 现有题库一览")
    
    # 1. 筛选栏
    c1, c2, c3 = st.columns(3)
    with c1: filter_grade = st.selectbox("筛选年级", ["全部", 1, 2, 3, 4, 5, 6], index=3)
    with c2: filter_cate = st.selectbox("筛选知识点", ["全部", "计算", "逻辑", "几何", "行程"])
    with c3: 
        if st.button("🔄 刷新列表"): st.rerun()

    # 2. 从数据库拉取数据
    query = supabase.table("questions").select("*").order("created_at", desc=True)
    
    if filter_grade != "全部":
        query = query.eq("grade", filter_grade)
    # (Supabase 简单的筛选演示，实际可以做更复杂)
    
    response = query.execute()
    
    if response.data:
        df = pd.DataFrame(response.data)
        
        # 简单美化表格
        display_df = df[['content', 'answer', 'category', 'difficulty', 'grade']]
        display_df.columns = ['题目内容', '答案', '分类', '难度', '年级']
        
        st.dataframe(
            display_df, 
            use_container_width=True,
            column_config={
                "难度": st.column_config.NumberColumn("难度", format="%d ⭐"),
                "题目内容": st.column_config.TextColumn("题目", width="large"),
            }
        )
        
        st.caption(f"共找到 {len(df)} 道题目")
    else:
        st.info("📭 题库里还没有题目，快去【录入新题】吧！")