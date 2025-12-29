import streamlit as st
import sqlite3
import datetime
import pandas as pd

# ================= 1. 页面配置与视觉 (橙色火柴人风格) =================
st.set_page_config(page_title="奥数英雄殿堂", page_icon="🏆", layout="wide")

st.markdown("""
    <style>
    .lesson-box { background-color: #FFF5E6; border: 2px solid #FF8C00; padding: 20px; border-radius: 15px; }
    .subtitle-text { background-color: #444; color: #FFA500; padding: 10px; border-radius: 8px; font-family: 'Courier New'; margin-top: 10px; border-left: 5px solid #FF8C00; }
    .rank-card { background: linear-gradient(135deg, #FF8C00, #FFD700); color: white; padding: 15px; border-radius: 12px; text-align: center; box-shadow: 2px 2px 10px rgba(0,0,0,0.1); }
    .stButton>button { width: 100%; }
    </style>
    """, unsafe_allow_html=True)

# ================= 2. 积分找回核心逻辑 (加强版) =================
DB_NAME = 'math_master.db'

def get_db_connection():
    # 增加 check_same_thread=False 确保多线程安全
    conn = sqlite3.connect(DB_NAME, timeout=10, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def get_user_stats(username):
    conn = get_db_connection()
    try:
        # 自动检测 scores 表是否存在
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='scores'")
        if not cursor.fetchone():
            # 如果表不存在，创建一个，防止报错
            cursor.execute('CREATE TABLE scores (timestamp TEXT, user TEXT, day INTEGER, score INTEGER, detail TEXT)')
            conn.commit()
            return 0, 0

        # 执行积分求和
        cursor.execute('SELECT SUM(score) FROM scores WHERE user = ?', (username,))
        result = cursor.fetchone()
        points = result[0] if (result and result[0] is not None) else 0
        
        # 计算已完成的天数
        cursor.execute('SELECT COUNT(DISTINCT day) FROM scores WHERE user = ? AND score > 0', (username,))
        days = cursor.fetchone()[0]
        return int(points), int(days)
    except Exception as e:
        st.sidebar.error(f"数据读取异常: {e}")
        return 0, 0
    finally:
        conn.close()

# ================= 3. 橙色火柴人小课堂：三年级白话版 =================
KNOWLEDGE_BASE = {
    "等量代换 (1-25天)": {
        "lesson": "🧍【火柴人老师】: 嗨！今天我们玩‘变魔术’。如果1条龙能换3只老虎，1只老虎能换4只猫，那1条龙能换几只猫？<br><br>别数手指头了！秘诀是：把‘中转站’老虎拆开！每只老虎都变出4只猫，3只老虎就是 3×4=12只猫。看，龙就直接变成猫了！这就是乘法的魔力！",
        "subtitle": "中文字幕：代换就是找‘中间人’。A换B，B换C，我们用乘法把它们串起来。"
    },
    "和差问题 (26-50天)": {
        "lesson": "🧍【火柴人老师】: 你和妹妹一共10颗糖，你比她多2颗。怎么分才不吵架？<br><br>火柴人绝招：把你多出来的2颗先藏在兜里！剩下的 10-2=8颗，咱俩一人一半，就是 8÷2=4颗。这时候你再把兜里的2颗拿出来，你就是 4+2=6颗。瞧！多出的部分最后加，这就是和差逻辑！",
        "subtitle": "中文字幕：(总数 - 差) ÷ 2 = 较小的数。先把多余的‘砍掉’，平分后再补给大数。"
    },
    "周期规律 (51-75天)": {
        "lesson": "🧍【火柴人老师】: 红黄蓝绿，红黄蓝绿... 就像转圈圈。如果你想知道第101个是什么色，不用数到天黑！<br><br>这组规律有4个颜色。用 101 ÷ 4 = 25组...余下1个。这个‘余数1’就是钥匙！它代表第101个和每组的第1个一模一样。如果余数是0，就是这组的最后一个！",
        "subtitle": "中文字幕：求 余数 = 总数 ÷ 周期长度。余数决定位置。"
    },
    "植树问题 (101-125天)": {
        "lesson": "🧍【火柴人老师】: 伸出你的左手，看！5个手指中间只有4个缝隙对吧？<br><br>如果路两头都种树，树的数量永远比缝隙多1个。所以只要算出路有几个间隔，最后记得‘加1’，就是树的数量！但如果是绕着圆形花坛种，手拉手连成圈，树和缝隙就正好一样多啦！",
        "subtitle": "中文字幕：直线植树：棵数 = 间隔 + 1；封闭植树：棵数 = 间隔。"
    }
}

# ================= 4. App 主流程 (集成翻译功能) =================
if 'authenticated' not in st.session_state:
    st.title("🛡️ 奥数英雄殿堂")
    u_name = st.text_input("🦸‍♂️ 英雄代号")
    p_word = st.text_input("🔑 密语", type="password")
    if st.button("进入神殿"):
        if p_word == "123456" and u_name:
            st.session_state.authenticated = True
            st.session_state.user = u_name
            st.rerun()
    st.stop()

user = st.session_state.user
points, days_done = get_user_stats(user)

with st.sidebar:
    st.markdown(f"<div class='rank-card'><h3>🦸‍♂️ {user}</h3><h1>{points} 🪙</h1><p>累计总积分</p></div>", unsafe_allow_html=True)
    st.divider()
    menu = st.radio("🏠 任务导航", ["🔥 挑战试炼", "🛒 积分商城", "📜 成长史诗"])
    
    st.divider()
    st.markdown("### 🍊 橙色小课堂")
    know_choice = st.selectbox("知识点目录", list(KNOWLEDGE_BASE.keys()))
    if st.button("📖 听课"): st.session_state.show_lesson = know_choice

# 课程弹窗逻辑
if 'show_lesson' in st.session_state:
    l_data = KNOWLEDGE_BASE[st.session_state.show_lesson]
    st.markdown(f"<div class='lesson-box'><h3>{st.session_state.show_lesson}</h3><p>{l_data['lesson']}</p><div class='subtitle-text'>{l_data['subtitle']}</div></div>", unsafe_allow_html=True)
    if st.button("关闭课堂"):
        del st.session_state.show_lesson
        st.rerun()

if menu == "🔥 挑战试炼":
    st.header(f"📅 第 {days_done + 1} 天挑战")
    day_val = st.number_input("选择天数", 1, 150, value=min(days_done + 1, 150))
    
    conn = get_db_connection()
    qs = conn.execute('SELECT * FROM questions WHERE day = ?', (day_val,)).fetchall()
    conn.close()

    for q in qs:
        key = f"d{day_val}_q{q['id']}"
        if f"att_{key}" not in st.session_state: st.session_state[f"att_{key}"] = 0
        if f"done_{key}" not in st.session_state: st.session_state[f"done_{key}"] = False
        if f"trans_{key}" not in st.session_state: st.session_state[f"trans_{key}"] = False

        with st.container(border=True):
            st.subheader(f"Q{q['id']}: {q['title']}")
            
            # 翻译开关逻辑
            if st.session_state[f"trans_{key}"]:
                st.success(f"🇨🇳 **中文题目:** {q['h5']}") # 数据库中h5存的是中文
            else:
                st.info(f"🇺🇸 **English:** {q['question']}")
            
            col1, col2 = st.columns([1, 4])
            with col1:
                if st.button("🔄 翻译", key=f"t_{key}"):
                    st.session_state[f"trans_{key}"] = not st.session_state[f"trans_{key}"]
                    st.rerun()

            if not st.session_state[f"done_{key}"]:
                u_ans = st.text_input("请输入答案", key=f"a_{key}")
                if st.button("提交", key=f"b_{key}"):
                    st.session_state[f"att_{key}"] += 1
                    att = st.session_state[f"att_{key}"]
                    if u_ans.strip().lower() == str(q['answer']).lower():
                        score_map = {1: 10, 2: 6, 3: 1}
                        final_p = score_map.get(att, -3)
                        st.balloons()
                        st.success(f"正确！积分 +{final_p}")
                        st.session_state[f"done_{key}"] = True
                        
                        c = get_db_connection()
                        c.execute('INSERT INTO scores VALUES (?,?,?,?,?)', (datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), user, day_val, final_p, f"攻克:{q['title']}"))
                        c.commit()
                        c.close()
                        st.rerun()
                    else:
                        hints = [q['h1'], q['h2'], q['h3'], q['h4'], q['h5']]
                        st.error(f"❌ 线索：{hints[min(att-1, 4)]}")
            else:
                st.success("✅ 通关")

elif menu == "📜 成长史诗":
    st.header("成长记录")
    conn = get_db_connection()
    logs = pd.read_sql_query('SELECT timestamp, score, detail FROM scores WHERE user=? ORDER BY timestamp DESC', conn, params=(user,))
    conn.close()
    st.table(logs)