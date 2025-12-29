import streamlit as st
import sqlite3
import datetime
import pandas as pd
import time

# ================= 1. 页面配置 =================
st.set_page_config(page_title="奥数英雄殿堂", page_icon="🏆", layout="wide")

# 自定义样式：增加火柴人教学框和商城美化
st.markdown("""
    <style>
    .lesson-box { background-color: #FFF5E6; border: 2px solid #FF8C00; padding: 20px; border-radius: 15px; margin-bottom: 20px; }
    .subtitle-text { background-color: #333; color: #FFA500; padding: 10px; border-radius: 8px; margin-top: 10px; border-left: 5px solid #FF8C00; font-size: 0.9em; }
    .rank-card { background: linear-gradient(135deg, #FF8C00, #FFD700); color: white; padding: 15px; border-radius: 12px; text-align: center; }
    .explanation-box { background-color: #f0f8ff; border-left: 5px solid #007bff; padding: 15px; border-radius: 5px; margin-top: 10px; }
    </style>
    """, unsafe_allow_html=True)

# ================= 2. 数据库工具 =================
DB_NAME = 'math_master.db'

def get_db_connection():
    # 增加 timeout 防止数据库死锁
    conn = sqlite3.connect(DB_NAME, check_same_thread=False, timeout=30)
    conn.row_factory = sqlite3.Row
    return conn

def get_user_stats(username):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        # 核心：SUM(score) 找回所有积分（包含正分奖励和负分兑换）
        cursor.execute('SELECT SUM(score) FROM scores WHERE user = ?', (username,))
        row = cursor.fetchone()
        points = row[0] if (row and row[0] is not None) else 0
        
        cursor.execute('SELECT COUNT(DISTINCT day) FROM scores WHERE user = ? AND score > 0', (username,))
        days = cursor.fetchone()[0] or 0
        return int(points), int(days)
    finally:
        conn.close()

# ================= 3. 登录权限系统 =================
if 'auth_status' not in st.session_state:
    st.title("🛡️ 英雄殿堂：身份验证")
    col_l, col_r = st.columns(2)
    with col_l:
        role = st.selectbox("请选择模式", ["学员模式", "管理员模式"])
        u_name = st.text_input("🦸‍♂️ 英雄代号")
        p_word = st.text_input("🔑 验证密语", type="password")
        if st.button("开启大门", use_container_width=True):
            if role == "管理员模式" and p_word == "admin888":
                st.session_state.update({"auth_status":True, "user":u_name, "role":"ADMIN"})
                st.rerun()
            elif role == "学员模式" and p_word == "123456":
                st.session_state.update({"auth_status":True, "user":u_name, "role":"USER"})
                st.rerun()
            else: st.error("密语错误！")
    st.stop()

# ================= 4. 管理员界面 =================
if st.session_state.role == "ADMIN":
    st.title("⚙️ 管理员后台")
    conn = get_db_connection()
    st.subheader("📊 学员全量数据记录")
    st.dataframe(pd.read_sql_query("SELECT * FROM scores ORDER BY timestamp DESC", conn), use_container_width=True)
    if st.sidebar.button("登出"): st.session_state.clear(); st.rerun()
    st.stop()

# ================= 5. 学员主逻辑 =================
user = st.session_state.user
points, days_done = get_user_stats(user)

# 侧边栏：积分卡片始终显示
with st.sidebar:
    st.markdown(f"<div class='rank-card'><h3>🦸‍♂️ {user}</h3><h1>{points} 🪙</h1><p>能量总值</p></div>", unsafe_allow_html=True)
    st.divider()
    # 使用独立状态控制菜单，防止切换白屏
    menu = st.radio("导航菜单", ["🔥 挑战试炼", "🛒 积分商城", "📜 成长记录"], key="main_menu")
    st.divider()
    if st.button("🚪 退出登录"): st.session_state.clear(); st.rerun()

# --- 模块 A: 挑战试炼 (解析与计分) ---
if menu == "🔥 挑战试炼":
    st.header(f"📅 第 {days_done + 1} 天挑战")
    day_val = st.number_input("关卡跳转", 1, 150, value=min(days_done + 1, 150))
    
    conn = get_db_connection()
    qs = conn.execute('SELECT * FROM questions WHERE day = ?', (day_val,)).fetchall()
    conn.close()

    for q in qs:
        q_key = f"q_{day_val}_{q['id']}"
        if f"att_{q_key}" not in st.session_state: st.session_state[f"att_{q_key}"] = 0
        if f"done_{q_key}" not in st.session_state: st.session_state[f"done_{q_key}"] = False

        with st.container(border=True):
            st.subheader(f"Q{q['id']}: {q['title']}")
            st.info(f"🇺🇸 **English:** {q['question']}")
            with st.expander("👁️ 翻译"): st.write(q['h5'])

            if not st.session_state[f"done_{q_key}"]:
                u_ans = st.text_input("请输入答案", key=f"ans_in_{q_key}")
                if st.button("提交验证", key=f"btn_sub_{q_key}"):
                    st.session_state[f"att_{q_key}"] += 1
                    att = st.session_state[f"att_{q_key}"]
                    if u_ans.strip().lower() == str(q['answer']).lower():
                        score_map = {1: 10, 2: 6, 3: 1}
                        f_score = score_map.get(att, -3)
                        st.balloons()
                        c = get_db_connection()
                        c.execute('INSERT INTO scores VALUES (?,?,?,?,?)', (datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), user, day_val, f_score, f"攻克:{q['title']}"))
                        c.commit(); c.close()
                        st.session_state[f"done_{q_key}"] = True
                        st.success(f"正确！积分 +{f_score}")
                        time.sleep(1); st.rerun()
                    else: st.error("不对哦，请查看下方线索！")

                # 失败反馈逻辑
                att_now = st.session_state[f"att_{q_key}"]
                if att_now > 0 and not st.session_state[f"done_{q_key}"]:
                    if att_now <= 3:
                        hints = [q['h1'], q['h2'], q['h3']]
                        st.warning(f"💡 线索 ({att_now}/3): {hints[att_now-1]}")
                    else:
                        st.error(f"英雄，正确答案是: **{q['answer']}**")
                        st.markdown(f"<div class='explanation-box'><h4>🍊 解析:</h4>{q['h4']}<br><b>详解:</b> {q['h5']}</div>", unsafe_allow_html=True)
            else:
                st.success(f"✅ 已通关！正确答案: {q['answer']}")

# --- 模块 B: 积分商城 (防白屏专项优化版) ---
elif menu == "🛒 积分商城":
    st.header("🎁 英雄补给站")
    st.write(f"当前可用余额: **{points}** 🪙")
    
    # 核心商品列表
    shop_list = [
        {"id": "play_20", "name": "20分钟游戏时间", "price": 150, "icon": "🕹️"},
        {"id": "play_10", "name": "10分钟游戏时间", "price": 50, "icon": "⏱️"},
        {"id": "ice_cream", "name": "美味冰淇淋奖励", "price": 100, "icon": "🍦"}
    ]

    # 使用分列显示，确保 UI 稳定
    cols = st.columns(len(shop_list))
    for i, item in enumerate(shop_list):
        with cols[i]:
            with st.container(border=True):
                st.title(item['icon'])
                st.markdown(f"**{item['name']}**")
                st.write(f"价格: {item['price']} 🪙")
                
                # 增加独立 key 并使用 confirm 模式防止白屏
                if st.button(f"兑换", key=f"shop_item_{item['id']}"):
                    if points >= item['price']:
                        try:
                            conn = get_db_connection()
                            conn.execute('INSERT INTO scores (timestamp, user, day, score, detail) VALUES (?,?,?,?,?)',
                                         (datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), user, 0, -item['price'], f"【商城兑换】: {item['name']}"))
                            conn.commit()
                            conn.close()
                            st.toast(f"🎉 兑换成功！去领奖吧！", icon="✅")
                            time.sleep(1.5)
                            st.rerun()
                        except Exception as e:
                            st.error(f"数据库繁忙: {e}")
                    else:
                        st.error("积分不够哦！")

# --- 模块 C: 成长记录 ---
elif menu == "📜 成长记录":
    st.header("📜 英雄成长史诗")
    conn = get_db_connection()
    logs_df = pd.read_sql_query("SELECT timestamp as 时间, score as 变动, detail as 事件 FROM scores WHERE user=? ORDER BY 时间 DESC", conn, params=(user,))
    conn.close()
    if not logs_df.empty:
        st.dataframe(logs_df, use_container_width=True, hide_index=True)
    else:
        st.info("还没有足迹，快去开始第一场战斗吧！")