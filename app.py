import streamlit as st
import sqlite3
import datetime
import pandas as pd
import time

# ================= 1. 页面配置与视觉样式 =================
st.set_page_config(page_title="奥数英雄殿堂", page_icon="🏆", layout="wide")

st.markdown("""
    <style>
    .lesson-box { background-color: #FFF5E6; border: 2px solid #FF8C00; padding: 20px; border-radius: 15px; margin-bottom: 20px; }
    .subtitle-text { background-color: #333; color: #FFA500; padding: 10px; border-radius: 8px; font-family: 'Courier New'; margin-top: 10px; border-left: 5px solid #FF8C00; font-size: 0.9em; }
    .rank-card { background: linear-gradient(135deg, #FF8C00, #FFD700); color: white; padding: 15px; border-radius: 12px; text-align: center; box-shadow: 2px 2px 10px rgba(0,0,0,0.1); }
    .explanation-box { background-color: #e8f4f8; border-left: 5px solid #2980b9; padding: 15px; margin-top: 10px; border-radius: 5px; }
    </style>
    """, unsafe_allow_html=True)

# ================= 2. 数据库底层逻辑 =================
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
        res = cursor.fetchone()
        points = res[0] if (res and res[0] is not None) else 0
        cursor.execute('SELECT COUNT(DISTINCT day) FROM scores WHERE user = ? AND score > 0', (username,))
        days = cursor.fetchone()[0] or 0
        return int(points), int(days)
    finally:
        conn.close()

# ================= 3. 登录逻辑 =================
if 'authenticated' not in st.session_state:
    st.title("🛡️ 英雄殿堂：身份验证")
    role_choice = st.selectbox("请选择模式", ["学员模式", "管理员模式"])
    u_name = st.text_input("🦸‍♂️ 英雄代号")
    p_word = st.text_input("🔑 验证密语", type="password")
    if st.button("开启大门"):
        if role_choice == "管理员模式" and p_word == "admin888":
            st.session_state.update({"authenticated":True, "user":u_name, "role":"ADMIN"})
            st.rerun()
        elif role_choice == "学员模式" and p_word == "123456":
            st.session_state.update({"authenticated":True, "user":u_name, "role":"USER"})
            st.rerun()
        else: st.error("密语错误！")
    st.stop()

# ================= 4. 管理员控制台 (保持极简) =================
if st.session_state.role == "ADMIN":
    st.title("⚙️ 管理员后台")
    conn = get_db_connection()
    st.write("### 所有学员积分明细")
    st.dataframe(pd.read_sql_query("SELECT * FROM scores ORDER BY timestamp DESC", conn), use_container_width=True)
    if st.sidebar.button("退出"): st.session_state.clear(); st.rerun()
    st.stop()

# ================= 5. 学员主界面 =================
user = st.session_state.user
points, days_done = get_user_stats(user)

with st.sidebar:
    st.markdown(f"<div class='rank-card'><h3>🦸‍♂️ {user}</h3><h1>{points} 🪙</h1><p>能量积分</p></div>", unsafe_allow_html=True)
    st.divider()
    menu = st.radio("任务导航", ["🔥 挑战试炼", "🛒 积分商城", "📜 成长记录"])
    if st.button("🚪 退出登录"): st.session_state.clear(); st.rerun()

# --- 🔥 挑战试炼 (含 3 次失败后显示答案逻辑) ---
if menu == "🔥 挑战试炼":
    st.header(f"📅 第 {days_done + 1} 天试炼")
    day_val = st.number_input("关卡", 1, 150, value=min(days_done + 1, 150))
    
    conn = get_db_connection()
    qs = conn.execute('SELECT * FROM questions WHERE day = ?', (day_val,)).fetchall()
    conn.close()

    for q in qs:
        key = f"d{day_val}_q{q['id']}"
        if f"att_{key}" not in st.session_state: st.session_state[f"att_{key}"] = 0
        if f"done_{key}" not in st.session_state: st.session_state[f"done_{key}"] = False

        with st.container(border=True):
            st.subheader(f"Q{q['id']}: {q['title']}")
            st.info(f"🇺🇸 **English:** {q['question']}")
            
            # 翻译辅助
            with st.expander("👁️ 查看中文翻译"):
                st.write(q['h5'])

            if not st.session_state[f"done_{key}"]:
                u_ans = st.text_input("你的答案", key=f"ans_{key}")
                att = st.session_state[f"att_{key}"]

                if st.button("提交验证", key=f"btn_{key}"):
                    st.session_state[f"att_{key}"] += 1
                    att += 1
                    if u_ans.strip().lower() == str(q['answer']).lower():
                        score_map = {1: 10, 2: 6, 3: 1}
                        f_score = score_map.get(att, -3)
                        st.balloons(); st.success(f"正确！积分 +{f_score}"); st.session_state[f"done_{key}"] = True
                        c = get_db_connection()
                        c.execute('INSERT INTO scores (timestamp, user, day, score, detail) VALUES (?,?,?,?,?)',
                                 (datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), user, day_val, f_score, f"攻克:{q['title']}"))
                        c.commit(); c.close(); time.sleep(1); st.rerun()
                    else:
                        st.error(f"第 {att} 次尝试失败！")

                # --- 核心改进：失败处理逻辑 ---
                if att > 0 and not st.session_state[f"done_{key}"]:
                    if att <= 3:
                        hints = [q['h1'], q['h2'], q['h3']]
                        st.warning(f"💡 启发线索 ({att}/3): {hints[att-1]}")
                    else:
                        # 超过 3 次，展示正确答案和原理解析
                        st.error(f"⚡ 已经尝试 3 次了，英雄！正确答案是：**{q['answer']}**")
                        st.markdown(f"""
                        <div class='explanation-box'>
                            <h4>🍊 橙色火柴人深度解析：</h4>
                            <p><b>解题思路：</b>{q['h4']}</p>
                            <p><b>为什么是这个答案？</b>{q['h5']}</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
            else:
                st.success(f"✅ 已通关！正确答案是: {q['answer']}")

# --- 🛒 积分商城 (完全重写，防止白屏) ---
elif menu == "🛒 积分商城":
    st.header("🎁 英雄奖励商店")
    st.write(f"当前余额: **{points}** 🪙")
    
    # 将商品放在列表里
    shop_data = [
        {"id": "g20", "name": "20分钟游戏时间", "price": 150, "icon": "🕹️"},
        {"id": "g10", "name": "10分钟游戏时间", "price": 50, "icon": "⏱️"}
    ]

    for item in shop_data:
        # 使用列布局和明确的 Key 防止白屏
        with st.container(border=True):
            c1, c2 = st.columns([3, 1])
            c1.markdown(f"### {item['icon']} {item['name']}")
            c1.write(f"价格: {item['price']} 积分")
            
            if c2.button(f"兑换", key=f"buy_btn_{item['id']}"):
                if points >= item['price']:
                    try:
                        conn = get_db_connection()
                        conn.execute('INSERT INTO scores (timestamp, user, day, score, detail) VALUES (?,?,?,?,?)',
                                     (datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), user, 0, -item['price'], f"【商城兑换】: {item['name']}"))
                        conn.commit()
                        conn.close()
                        st.toast(f"✅ 兑换成功: {item['name']}", icon="🎉")
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"兑换失败: {e}")
                else:
                    st.error("积分不足！")

# --- 📜 成长记录 ---
elif menu == "📜 成长记录":
    st.header("📜 你的成长史诗")
    conn = get_db_connection()
    logs = pd.read_sql_query("SELECT timestamp as 时间, score as 变动, detail as 事件 FROM scores WHERE user=? ORDER BY 时间 DESC", conn, params=(user,))
    conn.close()
    st.dataframe(logs, use_container_width=True, hide_index=True)