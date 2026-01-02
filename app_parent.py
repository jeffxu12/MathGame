import streamlit as st
import pandas as pd
import altair as alt
from supabase import create_client
from datetime import datetime, timedelta

# ==========================================
# 🎨 0. 商务风 UI 配置
# ==========================================
st.set_page_config(page_title="Math Master 家长端", page_icon="📊", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #f5f7fa; }
    
    /* 卡片样式 */
    .metric-card {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        border: 1px solid #e1e4e8;
        text-align: center;
    }
    .metric-label { font-size: 14px; color: #666; }
    .metric-value { font-size: 28px; font-weight: bold; color: #1890ff; }
    
    /* 标题优化 */
    h1, h2, h3 { font-family: 'Helvetica Neue', sans-serif; color: #333; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# ⚡️ 1. 连接数据库
# ==========================================
# 注意：正式上线时建议使用 st.secrets
SUPABASE_URL = "https://fohuvfuhrtdurmnqvrty.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZvaHV2ZnVocnRkdXJtbnF2cnR5Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjY5ODEwNjksImV4cCI6MjA4MjU1NzA2OX0.FkkJGaI4yt6YnkqINMgtHYnRhJBObRysYbVZh-HuUPQ"

@st.cache_resource
def init_connection():
    try:
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except:
        return None
supabase = init_connection()

# ==========================================
# 🧠 2. 数据获取与处理引擎
# ==========================================
def get_study_data():
    if not supabase: return pd.DataFrame(), pd.DataFrame()
    
    # A. 获取做题日志
    logs_res = supabase.table("practice_logs").select("*").order("created_at", desc=True).limit(500).execute()
    logs_df = pd.DataFrame(logs_res.data)
    
    # B. 获取题目详情 (为了知道做的是哪类题)
    q_res = supabase.table("questions").select("id, category, difficulty, content").execute()
    q_df = pd.DataFrame(q_res.data)
    
    if not logs_df.empty and not q_df.empty:
        # 数据合并：给日志表加上题目信息
        full_df = logs_df.merge(q_df, left_on="question_id", right_on="id", how="left")
        
        # 时间转换
        full_df['created_at'] = pd.to_datetime(full_df['created_at'])
        # 简单处理时区，转为本地时间 (这里假设+8区，商业版需更严谨)
        full_df['date'] = full_df['created_at'].dt.date
        return full_df, logs_df
    
    return pd.DataFrame(), pd.DataFrame()

# ==========================================
# 🖥️ 3. 侧边栏导航
# ==========================================
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2302/2302834.png", width=80)
    st.title("家长管控中心")
    st.caption("Math Master Parents")
    st.divider()
    menu = st.radio("功能模块", ["📊 学习周报 (Report)", "💊 错题分析 (Mistakes)", "⚙️ 账号管理 (Settings)"])

df, raw_logs = get_study_data()

# ==========================================
# 📊 模块 A: 学习周报 (仪表盘)
# ==========================================
if menu == "📊 学习周报 (Report)":
    st.title("📊 学习进度总览")
    st.caption(f"数据更新于: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    
    if df.empty:
        st.info("📭 暂无学习数据，请先让孩子去【学生端】做几道题吧！")
    else:
        # 1. 核心 KPI (顶部卡片)
        total_q = len(df)
        correct_q = len(df[df['is_correct']==True])
        accuracy = (correct_q / total_q) * 100
        study_days = df['date'].nunique()
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("累计刷题", f"{total_q} 道", help="孩子做过的题目总数")
        c2.metric("正确率", f"{accuracy:.1f}%", delta="稳步上升" if accuracy > 80 else "需加强", delta_color="normal")
        c3.metric("学习天数", f"{study_days} 天", "本周")
        c4.metric("获得金币", "120 💰") # 这里暂时写死，实际应读 user 表
        
        st.divider()
        
        # 2. 图表分析区
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("📈 每日做题量趋势")
            # 按日期聚合
            daily_counts = df.groupby('date').size().reset_index(name='count')
            
            chart = alt.Chart(daily_counts).mark_bar(color='#1890ff').encode(
                x=alt.X('date', title='日期'),
                y=alt.Y('count', title='题量'),
                tooltip=['date', 'count']
            ).properties(height=300)
            st.altair_chart(chart, use_container_width=True)
            
        with col2:
            st.subheader("🦁 能力雷达图")
            # 统计各分类的正确率
            if 'category' in df.columns:
                cate_stats = df.groupby('category')['is_correct'].mean().reset_index()
                cate_stats['is_correct'] = cate_stats['is_correct'] * 100 # 转百分比
                
                # 雷达图在 Altair 较复杂，这里用横向柱状图代替，更直观
                radar = alt.Chart(cate_stats).mark_bar().encode(
                    x=alt.X('is_correct', title='正确率(%)', scale=alt.Scale(domain=[0, 100])),
                    y=alt.Y('category', title='知识点'),
                    color=alt.Color('is_correct', scale=alt.Scale(scheme='greens')),
                    tooltip=['category', 'is_correct']
                )
                st.altair_chart(radar, use_container_width=True)
            else:
                st.warning("分类数据不足")

        # 3. 详细流水
        with st.expander("📋 查看最近 10 条做题记录"):
            # 简化展示表格
            show_df = df[['created_at', 'content', 'user_answer', 'is_correct', 'category']].head(10)
            st.dataframe(
                show_df, 
                use_container_width=True,
                column_config={
                    "is_correct": st.column_config.CheckboxColumn("是否正确"),
                    "created_at": st.column_config.DatetimeColumn("时间", format="MM-DD HH:mm"),
                    "content": "题目",
                    "user_answer": "孩子填写的",
                    "category": "类型"
                }
            )

# ==========================================
# 💊 模块 B: 错题分析 (Mistakes)
# ==========================================
elif menu == "💊 错题分析 (Mistakes)":
    st.title("💊 错题本 (Mistake Clinic)")
    st.info("💡 商业版核心功能：这里汇总了孩子所有做错的题，方便家长打印或抽查。")
    
    if df.empty:
        st.warning("暂无数据")
    else:
        # 筛选错题
        wrong_df = df[df['is_correct'] == False]
        
        if wrong_df.empty:
            st.success("🎉 太棒了！目前没有错题！")
            st.balloons()
        else:
            count = len(wrong_df)
            st.markdown(f"**共发现 {count} 道错题**")
            
            for index, row in wrong_df.iterrows():
                # 错题卡片
                with st.container():
                    st.markdown(f"""
                    <div style="background: white; padding: 15px; border-left: 5px solid #ff4d4f; margin-bottom: 10px; border-radius: 4px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                        <small style="color: #999;">{row['category']} | 难度: {row['difficulty']}⭐</small>
                        <h4 style="margin: 5px 0;">{row['content']}</h4>
                        <p style="color: #666; font-size: 14px;">孩子填写的答案：<span style="color: red; font-weight: bold;">{row['user_answer']}</span></p>
                        <details>
                            <summary style="cursor: pointer; color: #1890ff;">查看正确解析</summary>
                            <p style="margin-top: 5px; background: #f9f9f9; padding: 10px; border-radius: 4px;">{row.get('explanation', '暂无解析')}</p>
                        </details>
                    </div>
                    """, unsafe_allow_html=True)

# ==========================================
# ⚙️ 模块 C: 账号管理
# ==========================================
elif menu == "⚙️ 账号管理 (Settings)":
    st.title("⚙️ 账号与设置")
    st.text_input("孩子昵称", value="奥数小状元")
    st.slider("每日目标题量", 5, 50, 10)
    st.button("💾 保存设置")
    st.divider()
    st.error("注销账号 (Danger Zone)")