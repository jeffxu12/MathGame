import streamlit as st
import sqlite3
import datetime
import os

# ================= 1. 数据库核心逻辑 =================
DB_NAME = 'math_master.db'

def get_db_connection():
    if not os.path.exists(DB_NAME):
        st.error(f"找不到数据库文件 {DB_NAME}，请确保已上传 db 文件！")
        return None
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def load_questions(day):
    conn = get_db_connection()
    if conn:
        qs = conn.execute('SELECT * FROM questions WHERE day = ?', (day,)).fetchall()
        conn.close()
        return qs
    return []

def save_score(user, day, score, detail):
    conn = get_db_connection()
    if conn:
        conn.execute('INSERT INTO scores (timestamp, user, day, score, detail) VALUES (?,?,?,?,?)',
                     (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), user, day, score, detail))
        conn.commit()
        conn.close()

def get_total_points(user):
    conn = get_db_connection()
    if conn:
        result = conn.execute('SELECT SUM(score) as total FROM scores WHERE user = ?', (user,)).fetchone()
        conn.close()
        return result['total'] if result['total'] else 0
    return 0

# ================= 2. 页面配置与登录 =================
st.set_page_config(page_title="奥数神殿云端版", page_icon="🛡️", layout="centered")

# 初始化 Session State
if 'login' not in st.session_state:
    st.title("🛡️ 奥数神殿入口")
    with st.form("login_form"):
        user = st.text_input("英雄尊姓大名")
        pwd = st.text_input("通关密语 (123456)", type="password")
        if st.form_submit_button("开启挑战"):
            if pwd == "123456":
                st.session_state.login = True
                st.session_state.user = user
                st.rerun()
            else:
                st.error("密语不对哦！")
else:
    # ================= 3. 主界面 =================
    points = get_total_points(st.session_state.user)
    st.sidebar.title(f"🦸‍♂️ {st.session_state.user}")
    st.sidebar.metric("我的财富", f"{points} 🪙")
    st.sidebar.divider()
    menu = st.sidebar.radio("传送门", ["🔥 今日试炼", "🛒 积分商城", "📈 成长记录"])

    # --- 模块1：今日试炼 (带锁定机制) ---
    if menu == "🔥 今日试炼":
        st.header("📅 每日逻辑挑战")
        day_to_solve = st.number_input("选择挑战天数", min_value=1, value=1, step=1)
        questions = load_questions(day_to_solve)
        
        if not questions:
            st.warning("这一天的关卡尚未开启。")
        else:
            for q in questions:
                q_key = f"day{q['day']}_id{q['id']}"
                
                # 初始化该题的尝试次数和解决状态
                att_key = f"att_{q_key}"
                solved_key = f"solved_{q_key}"
                score_key = f"score_{q_key}" # 记录该题最终得分
                
                if att_key not in st.session_state: st.session_state[att_key] = 0
                if solved_key not in st.session_state: st.session_state[solved_key] = False
                if score_key not in st.session_state: st.session_state[score_key] = 0

                with st.expander(f"第 {q['id']} 题：{q['title']}", expanded=not st.session_state[solved_key]):
                    st.write(q['question'])
                    
                    if not st.session_state[solved_key]:
                        # 未解决状态
                        user_ans = st.text_input("输入答案", key=f"in_{q_key}")
                        if st.button("提交验证", key=f"btn_{q_key}"):
                            st.session_state[att_key] += 1
                            att = st.session_state[att_key]
                            
                            if user_ans == str(q['answer']):
                                score_map = [10, 6, 1, -3]
                                final_pts = score_map[min(att-1, 3)]
                                
                                # 锁定状态
                                st.session_state[solved_key] = True
                                st.session_state[score_key] = final_pts
                                
                                # 存入数据库
                                save_score(st.session_state.user, day_to_solve, final_pts, f"攻克：{q['title']}")
                                st.balloons()
                                st.rerun()
                            else:
                                hints = [q['hint1'], q['hint2'], q['hint3'], q['hint4'], q['hint5']]
                                st.error(f"❌ 不对！第{att}次提示：{hints[min(att-1, 4)]}")
                    else:
                        # 已解决状态：禁用输入，显示分数
                        st.success(f"✅ 已通关！本题获得积分：{st.session_state[score_key]}")
                        st.write(f"英雄的答案是: {q['answer']}")

    # --- 模块2：积分商城 ---
    elif menu == "🛒 积分商城":
        st.header("🎁 英雄补给站")
        st.subheader(f"剩余积分: {points} 🪙")
        shop_items = [
            {"name": "看动画片30分钟", "price": 50, "icon": "📺"},
            {"name": "iPad 游戏20分钟", "price": 100, "icon": "🎮"},
            {"name": "哈根达斯冰淇淋", "price": 200, "icon": "🍦"},
            {"name": "免写一次口算作业", "price": 500, "icon": "📜"},
            {"name": "乐高积木一套", "price": 1000, "icon": "🧩"}
        ]
        
        for i, item in enumerate(shop_items):
            c1, c2, c3 = st.columns([1, 3, 1])
            with c1: st.title(item['icon'])
            with c2: st.write(f"**{item['name']}**\n\n价格: {item['price']} 积分")
            with c3:
                if st.button("兑换", key=f"buy_{i}"):
                    if points >= item['price']:
                        save_score(st.session_state.user, 999, -item['price'], f"兑换：{item['name']}")
                        st.success("兑换成功！")
                        st.rerun()
                    else:
                        st.error("分数不足！")
            st.divider()

    # --- 模块3：成长记录 ---
    elif menu == "📈 成长记录":
        st.header("📜 英雄成长史")
        conn = get_db_connection()
        if conn:
            logs = conn.execute('SELECT * FROM scores WHERE user = ? ORDER BY timestamp DESC', (st.session_state.user,)).fetchall()
            conn.close()
            if not logs:
                st.info("还没有记录。")
            else:
                for log in logs:
                    color = "green" if log['score'] > 0 else "red"
                    st.write(f"⏱ `{log['timestamp']}` | :{color}[{log['score']} 分] | {log['detail']}")