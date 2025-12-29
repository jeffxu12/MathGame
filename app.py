import streamlit as st
import sqlite3
import datetime
import pandas as pd

# ================= 1. 页面配置与视觉样式 =================
st.set_page_config(page_title="奥数英雄殿堂", page_icon="🏆", layout="wide")

st.markdown("""
    <style>
    .lesson-box { background-color: #FFF5E6; border: 2px solid #FF8C00; padding: 20px; border-radius: 15px; margin-bottom: 20px; }
    .subtitle-text { background-color: #333; color: #FFA500; padding: 10px; border-radius: 8px; font-family: 'Courier New'; margin-top: 10px; border-left: 5px solid #FF8C00; font-size: 0.9em; }
    .rank-card { background: linear-gradient(135deg, #FF8C00, #FFD700); color: white; padding: 15px; border-radius: 12px; text-align: center; box-shadow: 2px 2px 10px rgba(0,0,0,0.1); }
    .admin-panel { background-color: #f8f9fa; border: 2px dashed #ff4b4b; padding: 20px; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# ================= 2. 数据库与用户验证 =================
DB_NAME = 'math_master.db'

def get_db_connection():
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def get_user_stats(username):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT SUM(score) FROM scores WHERE user = ?', (username,))
        points = cursor.fetchone()[0] or 0
        cursor.execute('SELECT COUNT(DISTINCT day) FROM scores WHERE user = ? AND score > 0', (username,))
        days = cursor.fetchone()[0] or 0
        return int(points), int(days)
    except:
        return 0, 0
    finally:
        conn.close()

# ================= 3. 知识点百科 (三年级视角) =================
KNOWLEDGE_BASE = {
    "等量代换": {
        "lesson": "🧍【火柴人老师】: 想象一下，1条龙换3只老虎，1只老虎换4只猫。那1条龙能换几只猫？把老虎拆开，3个4相加，3×4=12只猫！",
        "subtitle": "中文字幕：代换就是找‘中间人’。A换B，B换C，用乘法把它们串起来。"
    },
    "和差问题": {
        "lesson": "🧍【火柴人老师】: 两人共10颗糖，你比她多2颗。把你多出的2颗先藏起来！剩下的平分，最后再把2颗还给你。这就是和差逻辑！",
        "subtitle": "中文字幕：(总数 - 差) ÷ 2 = 较小的数。先把多余的‘砍掉’，平分后再补给大数。"
    },
    "周期规律": {
        "lesson": "🧍【火柴人老师】: 红绿灯循环。想知道第101个是什么？用 101 ÷ 周期长度，看余数！余数是几，就是组里的第几个。",
        "subtitle": "中文字幕：求 余数 = 总数 ÷ 周期长度。余数决定位置，余0是最后一个。"
    },
    "植树问题": {
        "lesson": "🧍【火柴人老师】: 5个手指有4个缝隙。两头都种树：树 = 间隔 + 1。封闭圆圈种树：树 = 间隔。",
        "subtitle": "中文字幕：直线植树：棵数 = 间隔 + 1；封闭植树：棵数 = 间隔。"
    }
}

# ================= 4. 登录验证 =================
if 'authenticated' not in st.session_state:
    st.title("🛡️ 英雄殿堂：身份验证")
    role_choice = st.selectbox("选择身份", ["学员模式", "管理员模式"])
    u_name = st.text_input("🦸‍♂️ 账号名称")
    p_word = st.text_input("🔑 验证密语", type="password")
    
    if st.button("开启大门"):
        if role_choice == "管理员模式" and p_word == "admin888":
            st.session_state.authenticated, st.session_state.user, st.session_state.role = True, u_name, "ADMIN"
            st.rerun()
        elif role_choice == "学员模式" and p_word == "123456":
            st.session_state.authenticated, st.session_state.user, st.session_state.role = True, u_name, "USER"
            st.rerun()
        else:
            st.error("密语错误！")
    st.stop()

# ================= 5. 管理员控制台 =================
if st.session_state.role == "ADMIN":
    st.title("⚙️ 管理员后台中心")
    admin_tab1, admin_tab2 = st.tabs(["📊 数据监控", "🛠️ 题库编辑"])
    
    with admin_tab1:
        st.subheader("学员积分与兑换全记录")
        conn = get_db_connection()
        all_logs = pd.read_sql_query("SELECT * FROM scores ORDER BY timestamp DESC", conn)
        st.dataframe(all_logs, use_container_width=True)
        # 统计排名
        st.subheader("🏆 全员积分榜")
        ranks = pd.read_sql_query("SELECT user, SUM(score) as total FROM scores GROUP BY user ORDER BY total DESC", conn)
        st.table(ranks)
        conn.close()

    with admin_tab2:
        st.subheader("实时题库调整")
        day_edit = st.number_input("查看第几天题目", 1, 150)
        conn = get_db_connection()
        qs_edit = pd.read_sql_query("SELECT * FROM questions WHERE day = ?", conn, params=(day_edit,))
        st.data_editor(qs_edit, use_container_width=True)
        conn.close()

    if st.sidebar.button("登出系统"):
        st.session_state.clear()
        st.rerun()
    st.stop()

# ================= 6. 学员主界面 =================
user = st.session_state.user
points, days_done = get_user_stats(user)

with st.sidebar:
    st.markdown(f"<div class='rank-card'><h3>🦸‍♂️ {user}</h3><h1>{points} 🪙</h1><p>能量积分</p></div>", unsafe_allow_html=True)
    st.divider()
    menu = st.radio("导航", ["🔥 挑战试炼", "🛒 积分商城", "📜 成长记录"])
    
    st.divider()
    st.markdown("### 🍊 橙色小课堂")
    know_choice = st.selectbox("知识点目录", list(KNOWLEDGE_BASE.keys()))
    if st.button("📖 听课"): st.session_state.current_lesson = know_choice
    
    if st.button("退出登录"):
        st.session_state.clear()
        st.rerun()

# 课堂弹出
if 'current_lesson' in st.session_state:
    l_data = KNOWLEDGE_BASE[st.session_state.current_lesson]
    st.markdown(f"<div class='lesson-box'><h3>{st.session_state.current_lesson}</h3><p>{l_data['lesson']}</p><div class='subtitle-text'>{l_data['subtitle']}</div></div>", unsafe_allow_html=True)
    if st.button("关闭课堂"): del st.session_state.current_lesson; st.rerun()

# 挑战试炼
if menu == "🔥 挑战试炼":
    st.header(f"📅 第 {days_done + 1} 天试炼")
    day_val = st.number_input("关卡选择", 1, 150, value=min(days_done + 1, 150))
    
    # 自动开启小课堂提醒
    if day_val in [1, 26, 51, 76, 101, 126]:
        st.warning("🍊 这一章有新知识！点击左侧【听课】学习橙色火柴人的绝招。")

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
            if st.session_state[f"trans_{key}"]:
                st.success(f"🇨🇳 **中文题目:** {q['h5']}")
            else:
                st.info(f"🇺🇸 **English:** {q['question']}")
            
            if st.button("🔄 翻译", key=f"t_{key}"):
                st.session_state[f"trans_{key}"] = not st.session_state[f"trans_{key}"]; st.rerun()

            if not st.session_state[f"done_{key}"]:
                ans = st.text_input("答案", key=f"in_{key}")
                if st.button("提交", key=f"b_{key}"):
                    st.session_state[f"att_{key}"] += 1
                    att = st.session_state[f"att_{key}"]
                    if ans.strip().lower() == str(q['answer']).lower():
                        score_map = {1: 10, 2: 6, 3: 1}
                        final_p = score_map.get(att, -3)
                        st.balloons(); st.success(f"正确！积分 +{final_p}")
                        st.session_state[f"done_{key}"] = True
                        c = get_db_connection()
                        c.execute('INSERT INTO scores (timestamp, user, day, score, detail) VALUES (?,?,?,?,?)', 
                                 (datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), user, day_val, final_p, f"攻克:{q['title']}"))
                        c.commit(); c.close(); st.rerun()
                    else:
                        hints = [q['h1'], q['h2'], q['h3'], q['h4'], q['h5']]
                        st.error(f"❌ 提示：{hints[min(att-1, 4)]}")
            else: st.success("✅ 通关")

# 积分商城
elif menu == "🛒 积分商城":
    st.header("🎁 英雄奖励商店")
    shop_items = [
        {"n": "🎮 20分钟游戏时间", "p": 150, "i": "🕹️"},
        {"n": "🎮 10分钟游戏时间", "p": 50, "i": "⏱️"},
        {"n": "🍦 美味冰淇淋", "p": 100, "i": "🍦"}
    ]
    for idx, item in enumerate(shop_items):
        col1, col2 = st.columns([4, 1])
        with col1: st.write(f"### {item['i']} {item['n']} (需 {item['p']} 🪙)")
        with col2:
            if st.button(f"兑换", key=f"buy_{idx}"):
                if points >= item['p']:
                    c = get_db_connection()
                    c.execute('INSERT INTO scores VALUES (?,?,?,?,?)', 
                             (datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), user, 999, -item['p'], f"【商城兑换】:{item['n']}"))
                    c.commit(); c.close(); st.success("兑换成功！"); st.rerun()
                else: st.error("能量不足！")

elif menu == "📜 成长记录":
    st.header("成长足迹")
    conn = get_db_connection()
    logs = pd.read_sql_query("SELECT timestamp as 时间, score as 变动, detail as 事件 FROM scores WHERE user=? ORDER BY 时间 DESC", conn, params=(user,))
    conn.close()
    st.table(logs)