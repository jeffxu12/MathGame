import streamlit as st
import sqlite3
import datetime
import pandas as pd

# --- 1. 页面配置 (商业级视觉基础) ---
st.set_page_config(
    page_title="Math Olympiad Hero | 奥数英雄殿堂",
    page_icon="🏆",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. 数据库核心 (分片加载逻辑) ---
DB_NAME = 'math_master.db'

def get_db_connection():
    conn = sqlite3.connect(DB_NAME, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn

# 模拟商业版“按需加载”：只获取当前用户的积分和等级
def get_user_stats(username):
    conn = get_db_connection()
    try:
        # 获取总分
        row = conn.execute('SELECT SUM(score) as total FROM scores WHERE user = ?', (username,)).fetchone()
        points = row['total'] if row and row['total'] else 0
        # 获取已完成的天数（用于进度条）
        days_done = conn.execute('SELECT COUNT(DISTINCT day) as count FROM scores WHERE user = ?', (username,)).fetchone()['count']
        return points, days_done
    finally:
        conn.close()

# --- 3. 英雄等级系统 (成就激励机制) ---
def get_hero_rank(points):
    if points < 200: return "初级学徒", "🥚", "#9E9E9E", 200
    if points < 600: return "青铜骑士", "🛡️", "#CD7F32", 600
    if points < 1200: return "白银领主", "⚔️", "#C0C0C0", 1200
    if points < 2500: return "黄金大魔导师", "🔮", "#FFD700", 2500
    return "至尊奥数战神", "💎", "#FF4500", 99999

# --- 4. 登录系统 ---
if 'authenticated' not in st.session_state:
    st.title("🛡️ 奥数英雄殿堂")
    st.subheader("准备好开始你的 150 天逻辑征程了吗？")
    
    with st.container():
        col1, col2 = st.columns(2)
        with col1:
            user_input = st.text_input("🦸‍♂️ 输入英雄代号", placeholder="例如：小明")
            pass_input = st.text_input("🔑 输入通关密钥", type="password")
            if st.button("开启征程", use_container_width=True):
                if pass_input == "123456" and user_input: # 实际应用中可对接用户表
                    st.session_state.authenticated = True
                    st.session_state.user = user_input
                    st.rerun()
                else:
                    st.error("密钥错误，请询问导师。")
    st.stop()

# --- 5. 主界面逻辑 ---
user = st.session_state.user
points, days_completed = get_user_stats(user)
rank_name, rank_icon, rank_color, next_goal = get_hero_rank(points)

# 侧边栏：英雄状态面板
with st.sidebar:
    st.markdown(f"<h1 style='text-align: center; color: {rank_color};'>{rank_icon}<br>{rank_name}</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align: center;'>英雄: <b>{user}</b></p>", unsafe_allow_html=True)
    
    st.divider()
    st.metric("累计积分", f"{points} 🪙")
    
    # 进度条
    progress = min(points / next_goal, 1.0)
    st.write(f"升级进度: {int(progress*100)}%")
    st.progress(progress)
    
    st.divider()
    menu = st.radio("导航菜单", ["🔥 今日试炼", "📜 成长史诗", "🏆 英雄榜"])
    
    if st.button("🚪 退出殿堂"):
        del st.session_state.authenticated
        st.rerun()

# --- 6. 核心功能区 ---
if menu == "🔥 今日试炼":
    st.header(f"第 {days_completed + 1} 天挑战")
    
    # 商业优化：用户可以跳选天数，但默认显示其进度所在天数
    selected_day = st.number_input("跳转到特定天数", 1, 150, value=min(days_completed + 1, 150))
    
    # 逻辑分片加载：只从数据库读取当天的10道题
    conn = get_db_connection()
    questions = conn.execute('SELECT * FROM questions WHERE day = ?', (selected_day,)).fetchall()
    conn.close()

    if not questions:
        st.warning("该天试炼尚未装载，请联系系统管理员。")
    else:
        for q in questions:
            q_id = q['id']
            key = f"d{selected_day}_q{q_id}"
            
            with st.container():
                st.markdown(f"#### 题目 {q_id}: {q['title']}")
                st.info(f"🌐 **English:** {q['question']}")
                
                # 辅助功能卡片
                col_a, col_b = st.columns([1, 4])
                with col_a:
                    if st.button(f"👁️ 查看翻译", key=f"hint_{key}"):
                        st.toast(q['h5'], icon="🇨🇳")
                
                # 答题区
                ans_user = st.text_input("输入你的答案", key=f"input_{key}")
                
                if st.button("提交验证", key=f"btn_{key}"):
                    if ans_user.strip() == str(q['answer']):
                        st.balloons()
                        st.success("太棒了！逻辑完美！积分 +10")
                        # 记录成绩
                        c = get_db_connection()
                        c.execute('INSERT INTO scores VALUES (?, ?, ?, ?, ?)', 
                                 (datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), user, selected_day, 10, f"完成第{selected_day}天第{q_id}题"))
                        c.commit()
                        c.close()
                    else:
                        st.error("再思考一下，英雄！尝试使用翻译查看逻辑提示。")
            st.divider()

elif menu == "📜 成长史诗":
    st.header("你的成长足迹")
    conn = get_db_connection()
    logs = pd.read_sql_query('SELECT timestamp, score, detail FROM scores WHERE user = ? ORDER BY timestamp DESC', conn, params=(user,))
    conn.close()
    
    if logs.empty:
        st.write("还没有开始挑战，快去参加试炼吧！")
    else:
        st.dataframe(logs, use_container_width=True)

elif menu == "🏆 英雄榜":
    st.header("全服英雄排名")
    conn = get_db_connection()
    leaderboard = pd.read_sql_query('SELECT user, SUM(score) as total_score FROM scores GROUP BY user ORDER BY total_score DESC LIMIT 10', conn)
    conn.close()
    st.table(leaderboard)