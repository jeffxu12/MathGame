import streamlit as st
import sqlite3
import datetime
import pandas as pd

# --- 1. 页面配置 ---
st.set_page_config(page_title="奥数英雄殿堂", page_icon="🏆", layout="wide")

# --- 2. 数据库工具 ---
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

# --- 3. 英雄等级 (视觉激励) ---
def get_hero_rank(points):
    if points < 200: return "初级学徒", "🥚", "#9E9E9E", 200
    if points < 600: return "青铜骑士", "🛡️", "#CD7F32", 600
    if points < 1200: return "白银领主", "⚔️", "#C0C0C0", 1200
    if points < 2500: return "黄金大魔导师", "🔮", "#FFD700", 2500
    return "至尊奥数战神", "💎", "#FF4500", 99999

# --- 4. 登录验证 ---
if 'authenticated' not in st.session_state:
    st.title("🛡️ 奥数英雄殿堂")
    u_in = st.text_input("🦸‍♂️ 英雄姓名")
    p_in = st.text_input("🔑 密语", type="password")
    if st.button("开启征程"):
        if p_in == "123456" and u_in:
            st.session_state.authenticated = True
            st.session_state.user = u_in
            st.rerun()
    st.stop()

# --- 5. 主界面逻辑 ---
user = st.session_state.user
points, days_completed = get_user_stats(user)
rank_name, rank_icon, rank_color, next_goal = get_hero_rank(points)

# 侧边栏
with st.sidebar:
    st.markdown(f"<h2 style='text-align:center;color:{rank_color}'>{rank_icon} {rank_name}</h2>", unsafe_allow_html=True)
    st.metric("我的能量积分", f"{points} 🪙")
    st.divider()
    menu = st.radio("前往地点", ["🔥 今日试炼", "🛒 积分商城", "📈 成长记录", "🏆 英雄榜"])
    if st.button("🚪 离开殿堂"):
        del st.session_state.authenticated
        st.rerun()

# --- 6. 核心功能：今日试炼 ---
if menu == "🔥 今日试炼":
    st.header(f"第 {days_completed + 1} 天逻辑挑战")
    day_val = st.number_input("跳转天数", 1, 150, value=min(days_completed + 1, 150))
    
    conn = get_db_connection()
    questions = conn.execute('SELECT * FROM questions WHERE day = ?', (day_val,)).fetchall()
    conn.close()

    for q in questions:
        q_id = q['id']
        key = f"d{day_val}_q{q_id}"
        
        # 初始化该题的尝试次数
        if f"att_{key}" not in st.session_state: st.session_state[f"att_{key}"] = 0
        if f"done_{key}" not in st.session_state: st.session_state[f"done_{key}"] = False

        with st.container(border=True):
            st.subheader(f"题目 {q_id}: {q['title']}")
            st.info(f"**English:** {q['question']}")
            
            # 翻译与提示逻辑 (翻译不再扣分，由答题次数决定)
            with st.expander("👁️ 查看中英文对照及线索"):
                st.write(f"**中文翻译:** {q['h5']}")
            
            if not st.session_state[f"done_{key}"]:
                ans_user = st.text_input("输入答案", key=f"in_{key}")
                if st.button("提交验证", key=f"btn_{key}"):
                    st.session_state[f"att_{key}"] += 1
                    attempts = st.session_state[f"att_{key}"]
                    
                    if ans_user.strip().lower() == str(q['answer']).lower():
                        # --- 核心扣分逻辑 (不随版本改变) ---
                        score_map = {1: 10, 2: 6, 3: 1}
                        final_score = score_map.get(attempts, -3) # 第4次及以后扣3分
                        
                        st.balloons()
                        st.success(f"正确！第 {attempts} 次尝试成功，获得 {final_score} 积分！")
                        st.session_state[f"done_{key}"] = True
                        
                        # 存入数据库
                        c = get_db_connection()
                        c.execute('INSERT INTO scores (timestamp, user, day, score, detail) VALUES (?,?,?,?,?)',
                                 (datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), user, day_val, final_score, f"攻克: {q['title']}"))
                        c.commit()
                        c.close()
                        st.rerun()
                    else:
                        hints = [q['h1'], q['h2'], q['h3'], q['h4'], q['h5']]
                        current_hint = hints[min(attempts-1, 4)]
                        st.error(f"第 {attempts} 次回答错误！线索：{current_hint}")
            else:
                st.success("✅ 本题试炼已完成")

# --- 7. 积分商城 ---
elif menu == "🛒 积分商城":
    st.header("🎁 英雄补给站")
    st.write(f"当前余额: **{points}** 🪙")
    
    # 模拟商业版商品列表
    shop_items = [
        {"name": "iPad 游戏时间 15分钟", "price": 100, "icon": "🎮"},
        {"name": "看动画片 30分钟", "price": 150, "icon": "📺"},
        {"name": "美味冰淇淋一颗", "price": 200, "icon": "🍦"},
        {"name": "周末免写作业券", "price": 1000, "icon": "🎟️"}
    ]
    
    for i, item in enumerate(shop_items):
        col1, col2, col3 = st.columns([1, 3, 1])
        with col1: st.title(item['icon'])
        with col2: st.markdown(f"### {item['name']}\n价格: **{item['price']}** 🪙")
        with col3:
            if st.button(f"兑换", key=f"buy_{i}"):
                if points >= item['price']:
                    c = get_db_connection()
                    # 扣分存入记录（负分表示支出）
                    c.execute('INSERT INTO scores (timestamp, user, day, score, detail) VALUES (?,?,?,?,?)',
                             (datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), user, 999, -item['price'], f"兑换: {item['name']}"))
                    c.commit()
                    c.close()
                    st.toast(f"成功兑换 {item['name']}！", icon="✅")
                    st.rerun()
                else:
                    st.error("能量积分不足！")
        st.divider()

# --- 8. 成长记录 ---
elif menu == "📈 成长记录":
    st.header("📜 英雄史诗")
    conn = get_db_connection()
    logs = pd.read_sql_query('SELECT timestamp as 时间, score as 变动, detail as 事件 FROM scores WHERE user = ? ORDER BY timestamp DESC', conn, params=(user,))
    conn.close()
    st.dataframe(logs, use_container_width=True, hide_index=True)

# --- 9. 英雄榜 ---
elif menu == "🏆 英雄榜":
    st.header("🏆 全服英雄排名")
    conn = get_db_connection()
    board = pd.read_sql_query('SELECT user as 英雄, SUM(score) as 总积分 FROM scores GROUP BY user ORDER BY 总积分 DESC', conn)
    conn.close()
    st.table(board)