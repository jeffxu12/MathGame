import streamlit as st
import pandas as pd
import altair as alt
from supabase import create_client
from datetime import datetime, timedelta

# ==========================================
# 🎨 0. 商务控制台 UI 配置
# ==========================================
st.set_page_config(page_title="Math Master 控制台", page_icon="🎛️", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #f0f2f5; }
    
    /* 侧边栏样式 */
    section[data-testid="stSidebar"] {
        background-color: #001529;
        color: white;
    }
    
    /* 关键指标卡 */
    div[data-testid="stMetricValue"] {
        font-size: 24px;
        color: #1890ff;
    }
    
    /* 标题优化 */
    h1, h2, h3 { font-family: 'Inter', sans-serif; color: #333; }
    
    /* 表格优化 */
    .stDataFrame { border: 1px solid #e0e0e0; border-radius: 5px; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 🔐 1. 安全门卫 (密码登录)
# ==========================================
def check_password():
    """返回 True 如果密码正确"""
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False

    if st.session_state["password_correct"]:
        return True

    # 登录界面
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.title("🛡️ 家长管控中心")
        st.caption("Math Master Parents Console")
        pwd = st.text_input("请输入管理密码", type="password")
        
        if st.button("解锁"):
            if pwd == "admin888":  # 👈 这里设置你的密码
                st.session_state["password_correct"] = True
                st.rerun()
            else:
                st.error("密码错误")
    return False

if not check_password():
    st.stop() # 如果没登录，下面的代码都不执行

# ==========================================
# ⚡️ 2. 数据库连接
# ==========================================
SUPABASE_URL = "https://fohuvfuhrtdurmnqvrty.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZvaHV2ZnVocnRkdXJtbnF2cnR5Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjY5ODEwNjksImV4cCI6MjA4MjU1NzA2OX0.FkkJGaI4yt6YnkqINMgtHYnRhJBObRysYbVZh-HuUPQ"

@st.cache_resource
def init_connection():
    try:
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except: return None
supabase = init_connection()

# ==========================================
# 🖥️ 3. 侧边栏导航 (整合 Admin 和 Parent)
# ==========================================
with st.sidebar:
    st.title("Math Master Pro")
    st.caption(f"Admin: {datetime.now().strftime('%Y-%m-%d')}")
    st.markdown("---")
    
    menu = st.radio("功能导航", [
        "📊 学习数据分析",   # 原 app_parent
        "📝 题目内容管理",   # 原 admin
        "💊 错题与订正",     # 原 app_parent
        "⚙️ 用户与设置"      # 新功能
    ])
    
    st.markdown("---")
    if st.button("🔒 退出登录"):
        st.session_state["password_correct"] = False
        st.rerun()

# ==========================================
# 📊 模块 A: 学习数据分析 (Dashboard)
# ==========================================
if menu == "📊 学习数据分析":
    st.header("📊 学习全景看板")
    
    # 获取数据
    logs = pd.DataFrame(supabase.table("practice_logs").select("*").execute().data)
    questions = pd.DataFrame(supabase.table("questions").select("id, category, difficulty").execute().data)
    
    if logs.empty:
        st.info("暂无数据，请先去刷题。")
    else:
        # 数据清洗
        df = logs.merge(questions, left_on="question_id", right_on="id", how="left")
        df['created_at'] = pd.to_datetime(df['created_at'])
        df['date'] = df['created_at'].dt.date
        
        # 顶部 KPI
        k1, k2, k3, k4 = st.columns(4)
        total = len(df)
        acc = len(df[df['is_correct']==True]) / total * 100
        today_count = len(df[df['date'] == datetime.now().date()])
        
        k1.metric("累计刷题", total)
        k2.metric("正确率", f"{acc:.1f}%")
        k3.metric("今日刷题", today_count)
        k4.metric("掌握知识点", f"{df['category'].nunique()} 个")
        
        st.divider()
        
        # 图表区
        c1, c2 = st.columns([2, 1])
        with c1:
            st.subheader("📈 每日勤奋度")
            daily = df.groupby('date').size().reset_index(name='count')
            chart = alt.Chart(daily).mark_line(point=True).encode(
                x='date', y='count', tooltip=['date', 'count']
            ).properties(height=300)
            st.altair_chart(chart, use_container_width=True)
            
        with c2:
            st.subheader("🦁 能力分布")
            if 'category' in df.columns:
                cate = df.groupby('category')['is_correct'].mean().reset_index()
                cate['is_correct'] = cate['is_correct'] * 100
                bar = alt.Chart(cate).mark_bar().encode(
                    x='is_correct', y=alt.Y('category', sort='-x'), color='category'
                )
                st.altair_chart(bar, use_container_width=True)

# ==========================================
# 📝 模块 B: 题目内容管理 (CMS)
# ==========================================
elif menu == "📝 题目内容管理":
    st.header("📝 题库指挥中心")
    
    tab1, tab2 = st.tabs(["👁️ 查看题库", "➕ 手动录题"])
    
    with tab1:
        # 获取题库统计
        try:
            res = supabase.table("questions").select("*").execute()
            q_df = pd.DataFrame(res.data)
            
            # 统计栏
            s1, s2, s3 = st.columns(3)
            s1.metric("库存总题量", f"{len(q_df)} 道")
            s2.metric("涵盖题型", f"{q_df['category'].nunique()} 类")
            s3.metric("最高难度", f"{q_df['difficulty'].max()} 星")
            
            # 筛选
            col1, col2 = st.columns(2)
            with col1: cat_filter = st.selectbox("筛选分类", ["全部"] + list(q_df['category'].unique()))
            with col2: gd_filter = st.selectbox("筛选年级", ["全部"] + list(q_df['grade'].unique()))
            
            if cat_filter != "全部": q_df = q_df[q_df['category'] == cat_filter]
            if gd_filter != "全部": q_df = q_df[q_df['grade'] == gd_filter]
            
            st.dataframe(
                q_df[['content', 'answer', 'difficulty', 'category', 'explanation']],
                use_container_width=True,
                column_config={
                    "content": st.column_config.TextColumn("题目", width="large"),
                    "explanation": "解析"
                }
            )
        except Exception as e:
            st.error(f"读取失败: {e}")

    with tab2:
        st.markdown("#### 录入新题")
        with st.form("add_q"):
            c_text = st.text_area("题目描述")
            c_ans = st.text_input("标准答案")
            c_exp = st.text_area("解析")
            c1, c2, c3 = st.columns(3)
            with c1: diff = st.slider("难度", 1, 5, 3)
            with c2: cate = st.selectbox("分类", ["Logic", "Calculation", "Geometry", "Combo"])
            with c3: grade = st.selectbox("年级", [1,2,3,4,5,6], index=2)
            
            if st.form_submit_button("💾 保存入库"):
                if c_text and c_ans:
                    supabase.table("questions").insert({
                        "content": c_text, "answer": c_ans, "explanation": c_exp,
                        "difficulty": diff, "category": cate, "grade": grade, "type": "fill"
                    }).execute()
                    st.success("录入成功！")
                    st.rerun() # 刷新页面
                else:
                    st.error("题目和答案不能为空")

# ==========================================
# 💊 模块 C: 错题与订正
# ==========================================
elif menu == "💊 错题与订正":
    st.header("💊 错题诊疗室")
    
    # 获取错题
    logs = pd.DataFrame(supabase.table("practice_logs").select("*").execute().data)
    questions = pd.DataFrame(supabase.table("questions").select("*").execute().data)
    
    if logs.empty:
        st.success("太棒了，没有任何错题记录！")
    else:
        # 合并并筛选错误
        full = logs.merge(questions, left_on="question_id", right_on="id", how="left")
        wrongs = full[full['is_correct'] == False]
        
        if wrongs.empty:
            st.success("太棒了，没有任何错题记录！")
        else:
            st.info(f"共发现 {len(wrongs)} 道历史错题")
            for idx, row in wrongs.iterrows():
                with st.expander(f"❌ {row['category']} | {row['content'][:20]}...", expanded=False):
                    st.markdown(f"**题目**：{row['content']}")
                    st.markdown(f"**孩子答案**：:red[{row['user_answer']}]")
                    st.markdown(f"**正确答案**：:green[{row['answer']}]")
                    st.info(f"解析：{row['explanation']}")

# ==========================================
# ⚙️ 模块 D: 用户与设置
# ==========================================
elif menu == "⚙️ 用户与设置":
    st.header("⚙️ 超级管理员设置")
    
    st.subheader("💰 金币激励管理")
    st.info("如果孩子表现好（比如做家务），可以在这里手动发金币奖励他。")
    
    users = supabase.table("users").select("*").execute().data
    if users:
        target_user = st.selectbox("选择用户", [u['nickname'] for u in users])
        # 找到当前金币
        curr_coins = next(u['coins'] for u in users if u['nickname'] == target_user)
        user_id = next(u['id'] for u in users if u['nickname'] == target_user)
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric(f"{target_user} 当前金币", curr_coins)
        with col2:
            add_val = st.number_input("增加金币 (负数代表扣除)", value=0, step=10)
            if st.button("确认充值"):
                new_coins = curr_coins + add_val
                supabase.table("users").update({"coins": new_coins}).eq("id", user_id).execute()
                st.success(f"已更新！最新余额: {new_coins}")
                time.sleep(1)
                st.rerun()