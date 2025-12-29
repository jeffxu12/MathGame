import streamlit as st
import sqlite3
import datetime
import pandas as pd
import time

# ================= 1. 页面配置与视觉样式 =================
st.set_page_config(page_title="奥数英雄殿堂", page_icon="🏆", layout="wide")

# 注入自定义 CSS (增加商城卡片样式)
st.markdown("""
    <style>
    .lesson-box { background-color: #FFF5E6; border: 2px solid #FF8C00; padding: 20px; border-radius: 15px; margin-bottom: 20px; }
    .subtitle-text { background-color: #333; color: #FFA500; padding: 10px; border-radius: 8px; font-family: 'Courier New'; margin-top: 10px; border-left: 5px solid #FF8C00; font-size: 0.9em; }
    .rank-card { background: linear-gradient(135deg, #FF8C00, #FFD700); color: white; padding: 15px; border-radius: 12px; text-align: center; box-shadow: 2px 2px 10px rgba(0,0,0,0.1); }
    .shop-card { background-color: white; border: 1px solid #e0e0e0; padding: 15px; border-radius: 10px; text-align: center; transition: 0.3s; }
    .shop-card:hover { border-color: #FF8C00; box-shadow: 0 4px 8px rgba(0,0,0,0.1); }
    </style>
    """, unsafe_allow_html=True)

# ================= 2. 数据库底层逻辑 (支持事务与找回) =================
DB_NAME = 'math_master.db'

def get_db_connection():
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def get_user_stats(username):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        # 核心：SUM(score) 实现积分绝对找回（包含所有正负记录）
        cursor.execute('SELECT SUM(score) FROM scores WHERE user = ?', (username,))
        res = cursor.fetchone()
        points = res[0] if (res and res[0] is not None) else 0
        
        cursor.execute('SELECT COUNT(DISTINCT day) FROM scores WHERE user = ? AND score > 0', (username,))
        days = cursor.fetchone()[0] or 0
        return int(points), int(days)
    except Exception:
        return 0, 0
    finally:
        conn.close()

# ================= 3. 知识点百科数据 (三年级火柴人版) =================
KNOWLEDGE_BASE = {
    "等量代换 (1-25天)": {
        "lesson": "🧍【火柴人老师】: 嗨！想象一下，1条龙换3只老虎，1只老虎换4只猫。那1条龙能换几只猫？把老虎拆开，3个4连加，3×4=12只猫！这就是乘法的魔力！",
        "subtitle": "中文字幕：代换就是找‘中间人’。A换B，B换C，我们用乘法把它们串起来。"
    },
    "和差问题 (26-50天)": {
        "lesson": "🧍【火柴人老师】: 两人共10颗糖，你比她多2颗。把你多出的2颗先藏在口袋里！剩下的平分，最后再把2颗还给你。这就是和差逻辑！",
        "subtitle": "中文字幕：(总数 - 差) ÷ 2 = 较小的数。先把多余的‘砍掉’，平分后再补给大数。"
    },
    "周期规律 (51-75天)": {
        "lesson": "🧍【火柴人老师】: 红黄蓝绿循环。想知道第101个是什么？用 101 ÷ 周期长度(4)，余数是1，就是组里的第1个(红)。",
        "subtitle": "中文字幕：求 余数 = 总数 ÷ 周期长度。余数决定位置，余0是最后一个。"
    },
    "植树问题 (101-125天)": {
        "lesson": "🧍【火柴人老师】: 5个手指只有4个缝隙。两头都种树：树 = 间隔 + 1。如果是封闭的圆圈种树，树和缝隙就正好一样多！",
        "subtitle": "中文字幕：直线植树：棵数 = 间隔 + 1；封闭植树：棵数 = 间隔。"
    }
}

# ================= 4. 登录验证逻辑 (多角色分流) =================
if 'authenticated' not in st.session_state:
    st.title("🛡️ 英雄殿堂：身份验证")
    col_login_a, col_login_b = st.columns(2)
    with col_login_a:
        role_choice = st.selectbox("请选择进入模式", ["学员模式 (Student)", "管理员模式 (Admin)"])
        u_name = st.text_input("🦸‍♂️ 英雄代号/账号")
        p_word = st.text_input("🔑 验证密语", type="password")
        if st.button("开启传送门", use_container_width=True):
            if role_choice == "管理员模式 (Admin)" and p_word == "admin888":
                st.session_state.authenticated, st.session_state.user, st.session_state.role = True, u_name, "ADMIN"
                st.rerun()
            elif role_choice == "学员模式 (Student)" and p_word == "123456":
                st.session_state.authenticated, st.session_state.user, st.session_state.role = True, u_name, "USER"
                st.rerun()
            else:
                st.error("密语不正确，请询问导师！")
    st.stop()

# ================= 5. 管理员控制台 (数据管理与监控) =================
if st.session_state.role == "ADMIN":
    st.title("⚙️ 管理员上帝视角")
    adm_tab1, adm_tab2, adm_tab3 = st.tabs(["📊 数据总览", "🛠️ 题库编辑", "🎁 奖惩操作"])
    
    with adm_tab1:
        st.subheader("所有学员练习与兑换记录")
        conn = get_db_connection()
        logs_all = pd.read_sql_query("SELECT timestamp, user, score, detail FROM scores ORDER BY timestamp DESC", conn)
        st.dataframe(logs_all, use_container_width=True)
        # 积分排行
        ranks = pd.read_sql_query("SELECT user, SUM(score) as total FROM scores GROUP BY user ORDER BY total DESC", conn)
        st.bar_chart(ranks.set_index('user'))
        conn.close()

    with adm_tab2:
        st.subheader("实时修正题库内容")
        day_edit = st.number_input("查看哪一天的题目？", 1, 150)
        conn = get_db_connection()
        qs_edit = pd.read_sql_query("SELECT * FROM questions WHERE day = ?", conn, params=(day_edit,))
        st.data_editor(qs_edit, use_container_width=True, key="admin_q_editor")
        conn.close()
        st.info("提示：管理员可在此直接发现错别字并修改（保存功能需配合 UPDATE 语句）")

    if st.sidebar.button("退出管理后台"):
        st.session_state.clear()
        st.rerun()
    st.stop()

# ================= 6. 学员界面核心 =================
user = st.session_state.user
points, days_done = get_user_stats(user)

with st.sidebar:
    st.markdown(f"<div class='rank-card'><h3>🦸‍♂️ {user}</h3><h1>{points} 🪙</h1><p>当前总能量</p></div>", unsafe_allow_html=True)
    st.divider()
    menu = st.radio("🏠 任务导航", ["🔥 今日试炼", "🛒 积分商城", "📈 成长足迹"])
    
    st.divider()
    st.markdown("### 🍊 橙色小课堂 (百科)")
    know_choice = st.selectbox("查阅知识点", list(KNOWLEDGE_BASE.keys()))
    if st.button("📖 立即听课"):
        st.session_state.current_lesson = know_choice
    
    if st.button("🚪 退出登录"):
        st.session_state.clear()
        st.rerun()

# --- 课堂弹出逻辑 ---
if 'current_lesson' in st.session_state:
    l_data = KNOWLEDGE_BASE[st.session_state.current_lesson]
    st.markdown(f"""
        <div class='lesson-box'>
            <h3>🍊 火柴人老师：{st.session_state.current_lesson}</h3>
            <p style='font-size:1.1em;'>{l_data['lesson']}</p>
            <div class='subtitle-text'>{l_data['subtitle']}</div>
        </div>
    """, unsafe_allow_html=True)
    if st.button("关闭课堂"):
        del st.session_state.current_lesson
        st.rerun()

# --- 🔥 今日试炼逻辑 (含翻译与阶梯扣分) ---
if menu == "🔥 今日试炼":
    st.header(f"📅 第 {days_done + 1} 天逻辑试炼")
    day_val = st.number_input("调整试炼天数", 1, 150, value=min(days_done + 1, 150))
    
    # 提醒功能
    if day_val in [1, 26, 51, 76, 101, 126]:
        st.warning("⚠️ 英雄！这是新篇章的第一天，建议先查看左侧【小课堂】学习本章秘籍。")

    conn = get_db_connection()
    qs = conn.execute('SELECT * FROM questions WHERE day = ?', (day_val,)).fetchall()
    conn.close()

    for q in qs:
        key = f"d{day_val}_q{q['id']}"
        # 初始化状态锁
        if f"att_{key}" not in st.session_state: st.session_state[f"att_{key}"] = 0
        if f"done_{key}" not in st.session_state: st.session_state[f"done_{key}"] = False
        if f"trans_{key}" not in st.session_state: st.session_state[f"trans_{key}"] = False

        with st.container(border=True):
            st.subheader(f"Q{q['id']}: {q['title']}")
            
            # 翻译切换
            if st.session_state[f"trans_{key}"]:
                st.success(f"🇨🇳 **中文:** {q['h5']}")
            else:
                st.info(f"🇺🇸 **English:** {q['question']}")
            
            col_t, col_s = st.columns([1, 5])
            with col_t:
                if st.button("🔄 翻译", key=f"t_{key}"):
                    st.session_state[f"trans_{key}"] = not st.session_state[f"trans_{key}"]
                    st.rerun()

            if not st.session_state[f"done_{key}"]:
                u_ans = st.text_input("输入答案", key=f"in_{key}")
                if st.button("提交验证", key=f"btn_{key}"):
                    st.session_state[f"att_{key}"] += 1
                    att = st.session_state[f"att_{key}"]
                    if u_ans.strip().lower() == str(q['answer']).lower():
                        # --- 核心计分逻辑 (10-6-1-负3) ---
                        score_map = {1: 10, 2: 6, 3: 1}
                        f_score = score_map.get(att, -3)
                        st.balloons()
                        st.success(f"正确！第 {att} 次尝试，获得 {f_score} 积分")
                        st.session_state[f"done_{key}"] = True
                        # 写入数据库
                        c = get_db_connection()
                        c.execute('INSERT INTO scores (timestamp, user, day, score, detail) VALUES (?,?,?,?,?)',
                                 (datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), user, day_val, f_score, f"攻克: {q['title']}"))
                        c.commit(); c.close()
                        st.rerun()
                    else:
                        hints = [q['h1'], q['h2'], q['h3'], q['h4'], q['h5']]
                        st.error(f"❌ 线索：{hints[min(att-1, 4)]}")
            else:
                st.success("✅ 试炼已完成")

# --- 🛒 积分商城 (防止白屏重写版) ---
elif menu == "🛒 积分商城":
    st.header("🎁 英雄奖励补给站")
    st.subheader(f"当前可用能量: {points} 🪙")
    
    # 商品定义
    shop_list = [
        {"name": "🎮 20分钟游戏时间", "price": 150, "icon": "🕹️"},
        {"name": "🎮 10分钟游戏时间", "price": 50, "icon": "⏱️"},
        {"name": "🍦 奖励一个冰淇淋", "price": 100, "icon": "🍦"}
    ]
    
    shop_col1, shop_col2 = st.columns(2)
    for idx, item in enumerate(shop_list):
        with (shop_col1 if idx % 2 == 0 else shop_col2):
            st.markdown(f"""<div class='shop-card'><h2>{item['icon']}</h2><h4>{item['name']}</h4><p>价格: {item['price']} 积分</p></div>""", unsafe_allow_html=True)
            if st.button(f"确认兑换", key=f"shop_buy_{idx}"):
                if points >= item['price']:
                    try:
                        conn = get_db_connection()
                        conn.execute('INSERT INTO scores (timestamp, user, day, score, detail) VALUES (?,?,?,?,?)',
                                     (datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), user, 999, -item['price'], f"【商城兑换】: {item['name']}"))
                        conn.commit(); conn.close()
                        st.success(f"✅ 成功！已消耗 {item['price']} 积分，去领奖吧！")
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"兑换失败: {e}")
                else:
                    st.error("❌ 积分不足！多去练习题目吧！")

# --- 📈 成长足迹 ---
elif menu == "📈 成长足迹":
    st.header("📜 你的成长史诗")
    conn = get_db_connection()
    logs_df = pd.read_sql_query("SELECT timestamp as 时间, score as 变动, detail as 事件 FROM scores WHERE user=? ORDER BY 时间 DESC", conn, params=(user,))
    conn.close()
    if not logs_df.empty:
        st.dataframe(logs_df, use_container_width=True, hide_index=True)
    else:
        st.info("还没有足迹，开启第一场战斗吧！")