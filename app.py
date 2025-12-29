import streamlit as st
import sqlite3
import datetime
import pandas as pd

# ================= 1. 页面配置 =================
st.set_page_config(page_title="奥数英雄殿堂", page_icon="🏆", layout="wide")

# 自定义 CSS：让火柴人和字幕更好看
st.markdown("""
    <style>
    .stickman-box { background-color: #FFF5E6; border-left: 5px solid #FF8C00; padding: 20px; border-radius: 10px; }
    .subtitle { background-color: #333; color: #fff; padding: 5px 15px; border-radius: 5px; font-size: 0.9em; }
    </style>
    """, unsafe_allow_html=True)

# ================= 2. 数据库逻辑 =================
DB_NAME = 'math_master.db'

def get_db_connection():
    conn = sqlite3.connect(DB_NAME, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn

def get_user_stats(username):
    conn = get_db_connection()
    try:
        row = conn.execute('SELECT SUM(score) as total FROM scores WHERE user = ?', (username,)).fetchone()
        points = row['total'] if row and row['total'] else 0
        days_done = conn.execute('SELECT COUNT(DISTINCT day) as count FROM scores WHERE user = ?', (username,)).fetchone()['count']
        return points, days_done
    finally:
        conn.close()

# ================= 3. 橙色火柴人小课堂 (字幕版) =================
def show_orange_stickman_lesson(day):
    lessons = {
        1: ("等量代换", "嘿！我是橙色火柴人！今天我们要学'代换'。只要找到中间那个‘中转站’，就能把两样东西连起来。记住：1个A换2个B，2个B换4个C，那A就直接换4个C！", "字幕：代换的核心是找到中间量，建立连乘关系。"),
        26: ("和差问题", "我是橙色火柴人！‘和差’其实就是移多补少。把‘差’补给小的，它们就一样大了！公式：(和+差)÷2=大数。", "字幕：线段图是解决和差问题的核武器，画图即解题。"),
        51: ("周期规律", "我是橙色火柴人！规律就像时钟，转完一圈又回来。用总数除以一圈的长度，余数是几，就对应这一圈里的第几个！", "字幕：周期问题的关键是确定循环长度和处理余数。"),
        76: ("几何周长", "我是橙色火柴人！复杂的楼梯形别害怕，把横线往上推，纵线往右推，它就变成了一个完美的长方形！", "字幕：平移法可以将不规则图形转化为标准长方形计算。"),
        101: ("植树逻辑", "我是橙色火柴人！两端都种树，就像你的手：5个手指中间只有4个缝。所以：树木数量 = 间隔数 + 1。", "字幕：注意区分直路植树（+1）和封闭图形植树（不加）。"),
        126: ("假设法", "我是橙色火柴人！鸡兔同笼？先假设全是鸡！算出少了多少条腿，再把鸡换成兔，每换一只就多出2条腿！", "字幕：假设法能化繁为简，将两种变量转化为一种变量。")
    }
    
    if day in lessons:
        title, content, sub = lessons[day]
        st.markdown(f"""
        <div class='stickman-box'>
            <h2 style='color: #FF8C00; margin-top: 0;'>🍊 橙色火柴人小课堂：{title}</h2>
            <div style='display: flex; align-items: center;'>
                <div style='font-size: 80px; margin-right: 20px;'>🧍</div>
                <div>
                    <p style='font-size: 1.2em; color: #555;'>{content}</p>
                    <div class='subtitle'>中文字幕：{sub}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.divider()

# ================= 4. 英雄等级 =================
def get_hero_rank(points):
    if points < 200: return "见习骑士", "🥚", "#9E9E9E", 200
    if points < 600: return "逻辑领主", "🛡️", "#CD7F32", 600
    if points < 1200: return "白银智者", "⚔️", "#C0C0C0", 1200
    return "战神至尊", "💎", "#FF4500", 9999
    
# ================= 5. 登录界面 =================
if 'authenticated' not in st.session_state:
    st.title("🛡️ 奥数英雄殿堂")
    u_in = st.text_input("🦸‍♂️ 英雄姓名")
    p_in = st.text_input("🔑 密语 (123456)", type="password")
    if st.button("进入神殿"):
        if p_in == "123456" and u_in:
            st.session_state.authenticated = True
            st.session_state.user = u_in
            st.rerun()
    st.stop()

# ================= 6. 主逻辑 =================
user = st.session_state.user
points, days_completed = get_user_stats(user)
rank_name, rank_icon, rank_color, next_goal = get_hero_rank(points)

with st.sidebar:
    st.markdown(f"<h2 style='text-align:center;color:{rank_color}'>{rank_icon} {rank_name}</h2>", unsafe_allow_html=True)
    st.metric("持有能量积分", f"{points} 🪙")
    st.divider()
    menu = st.radio("前往地点", ["🔥 今日试炼", "🛒 积分商城", "📈 成长记录", "🏆 英雄榜"])
    if st.button("🚪 离开"):
        del st.session_state.authenticated
        st.rerun()

if menu == "🔥 今日试炼":
    day_val = st.number_input("跳转试炼天数", 1, 150, value=min(days_completed + 1, 150))
    
    # 自动开启小课堂
    if day_val in [1, 26, 51, 76, 101, 126]:
        show_orange_stickman_lesson(day_val)
    
    conn = get_db_connection()
    questions = conn.execute('SELECT * FROM questions WHERE day = ?', (day_val,)).fetchall()
    conn.close()

    for q in questions:
        key = f"d{day_val}_q{q['id']}"
        if f"att_{key}" not in st.session_state: st.session_state[f"att_{key}"] = 0
        if f"done_{key}" not in st.session_state: st.session_state[f"done_{key}"] = False

        with st.container(border=True):
            st.subheader(f"题目 {q['id']}: {q['title']}")
            st.info(f"**English:** {q['question']}")
            
            # 答题逻辑
            if not st.session_state[f"done_{key}"]:
                ans_user = st.text_input("输入答案", key=f"in_{key}")
                if st.button("提交验证", key=f"btn_{key}"):
                    st.session_state[f"att_{key}"] += 1
                    att = st.session_state[f"att_{key}"]
                    
                    if ans_user.strip().lower() == str(q['answer']).lower():
                        # --- 核心计分逻辑 (10-6-1-3) ---
                        score_map = {1: 10, 2: 6, 3: 1}
                        f_score = score_map.get(att, -3)
                        
                        st.balloons()
                        st.success(f"正确！第{att}次尝试，积分 +{f_score}")
                        st.session_state[f"done_{key}"] = True
                        
                        c = get_db_connection()
                        c.execute('INSERT INTO scores (timestamp, user, day, score, detail) VALUES (?,?,?,?,?)',
                                 (datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), user, day_val, f_score, f"攻克: {q['title']}"))
                        c.commit()
                        c.close()
                        st.rerun()
                    else:
                        # 答错给出阶梯式提示
                        hints = [q['h1'], q['h2'], q['h3'], q['h4'], q['h5']]
                        st.error(f"❌ 不对哦！线索提示: {hints[min(att-1, 4)]}")
            else:
                st.success("✅ 本题已通关")

elif menu == "🛒 积分商城":
    st.header("🎁 英雄补给站")
    shop = [{"n": "玩游戏15分钟", "p": 100, "i": "🎮"}, {"n": "吃冰淇淋", "p": 200, "i": "🍦"}]
    for item in shop:
        col1, col2 = st.columns([4, 1])
        with col1: st.write(f"### {item['i']} {item['n']} (价格: {item['p']}🪙)")
        with col2:
            if st.button(f"兑换", key=item['n']):
                if points >= item['p']:
                    c = get_db_connection()
                    c.execute('INSERT INTO scores VALUES (?,?,?,?,?)', 
                             (datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), user, 999, -item['p'], f"兑换:{item['n']}"))
                    c.commit()
                    c.close()
                    st.rerun()
                else: st.error("积分不足！")

elif menu == "📈 成长记录":
    st.header("📜 英雄成长史")
    conn = get_db_connection()
    logs = pd.read_sql_query('SELECT timestamp, score, detail FROM scores WHERE user=? ORDER BY timestamp DESC', conn, params=(user,))
    conn.close()
    st.table(logs)