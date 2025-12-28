import streamlit as st
import sqlite3
import datetime
import os

# ================= 1. 数据库逻辑 =================
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
        # 注意：这里我们假设数据库里增加了 english_question 字段
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

# ================= 2. 页面配置 =================
st.set_page_config(page_title="Math Temple: Hero's Journey", page_icon="🛡️", layout="centered")

if 'login' not in st.session_state:
    st.title("🛡️ Math Temple Entrance")
    with st.form("login_form"):
        user = st.text_input("Hero Name")
        pwd = st.text_input("Password", type="password")
        if st.form_submit_button("Enter"):
            if pwd == "123456":
                st.session_state.login = True
                st.session_state.user = user
                st.rerun()
            else:
                st.error("Incorrect Password!")
else:
    # ================= 3. 主界面 =================
    points = get_total_points(st.session_state.user)
    st.sidebar.title(f"🦸‍♂️ {st.session_state.user}")
    st.sidebar.metric("Total Coins", f"{points} 🪙")
    
    menu = st.sidebar.radio("Navigation", ["🔥 Daily Quest", "🛒 Item Shop", "📈 Achievement"])

    if menu == "🔥 Daily Quest":
        st.header("📅 Daily Math Challenge")
        day_to_solve = st.number_input("Select Day", min_value=1, value=1, step=1)
        questions = load_questions(day_to_solve)
        
        if not questions:
            st.warning("Quest not available for today.")
        else:
            for q in questions:
                q_key = f"day{q['day']}_id{q['id']}"
                
                # 初始化状态
                if f"att_{q_key}" not in st.session_state: st.session_state[f"att_{q_key}"] = 0
                if f"solved_{q_key}" not in st.session_state: st.session_state[f"solved_{q_key}"] = False
                if f"translate_{q_key}" not in st.session_state: st.session_state[f"translate_{q_key}"] = False

                with st.expander(f"Quest {q['id']}: {q['title']}", expanded=not st.session_state[f"solved_{q_key}"]):
                    
                    # --- 英文/中文显示逻辑 ---
                    if not st.session_state[f"translate_{q_key}"]:
                        # 只显示英文（假设数据库 question 字段存的是英文）
                        st.markdown(f"#### {q['question']}")
                        if st.button("I need Chinese translation (-2 coins)", key=f"trans_btn_{q_key}"):
                            st.session_state[f"translate_{q_key}"] = True
                            st.rerun()
                    else:
                        # 显示中英对照
                        st.markdown(f"**English:** {q['question']}")
                        st.markdown(f"**中文:** {q['hint5']}") # 临时借用 hint5 存中文，或者看下方数据库修改方案

                    if not st.session_state[f"solved_{q_key}"]:
                        user_ans = st.text_input("Your Answer", key=f"in_{q_key}")
                        if st.button("Check Answer", key=f"btn_{q_key}"):
                            st.session_state[f"att_{q_key}"] += 1
                            att = st.session_state[f"att_{q_key}"]
                            
                            if user_ans == str(q['answer']):
                                # 核心扣分逻辑
                                # 第一次对的基础分：10 (未翻译) 或 8 (已翻译)
                                base_score = 8 if st.session_state[f"translate_{q_key}"] else 10
                                score_map = [base_score, 6, 1, -3]
                                final_pts = score_map[min(att-1, 3)]
                                
                                st.session_state[f"solved_{q_key}"] = True
                                save_score(st.session_state.user, day_to_solve, final_pts, f"Solved: {q['title']}")
                                st.balloons()
                                st.success(f"🎊 Correct! You earned {final_pts} coins!")
                                st.rerun()
                            else:
                                hints = [q['hint1'], q['hint2'], q['hint3'], q['hint4'], q['hint5']]
                                st.error(f"❌ Wrong! Hint #{att}: {hints[min(att-1, 4)]}")
                    else:
                        st.success("✅ Quest Completed!")

    # ... 商城和记录代码保持不变 ...