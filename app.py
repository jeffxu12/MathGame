import streamlit as st
import sqlite3
import datetime
import os

# --- 数据库连接 ---
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

# --- 页面配置 ---
st.set_page_config(page_title="奥数神殿", page_icon="🛡️")

if 'login' not in st.session_state:
    st.title("🛡️ 奥数神殿入口")
    with st.form("login"):
        user = st.text_input("英雄姓名")
        pwd = st.text_input("通关密语", type="password")
        if st.form_submit_button("进入神殿"):
            if pwd == "123456":
                st.session_state.login = True
                st.session_state.user = user
                st.rerun()
            else:
                st.error("密语错误！")
else:
    # --- 主界面 ---
    points = get_total_points(st.session_state.user)
    st.sidebar.title(f"🦸‍♂️ {st.session_state.user}")
    st.sidebar.metric("当前积分", f"{points} 🪙")
    
    menu = st.sidebar.radio("前往地点", ["🔥 每日挑战", "🛒 积分商城", "📈 成长记录"])

    if menu == "🔥 每日挑战":
        st.header("📅 每日逻辑试炼")
        day_val = st.number_input("选择挑战天数", min_value=1, value=1, step=1)
        questions = load_questions(day_val)
        
        if not questions:
            st.info("今天的题目还没准备好哦。")
        else:
            for q in questions:
                q_key = f"q_{q['day']}_{q['id']}"
                
                # 初始化状态
                if f"att_{q_key}" not in st.session_state: st.session_state[f"att_{q_key}"] = 0
                if f"solved_{q_key}" not in st.session_state: st.session_state[f"solved_{q_key}"] = False
                if f"trans_{q_key}" not in st.session_state: st.session_state[f"trans_{q_key}"] = False

                with st.expander(f"第 {q['id']} 题：{q['title']}", expanded=not st.session_state[f"solved_{q_key}"]):
                    
                    # 题目显示：默认英文，点翻译显示双语
                    if not st.session_state[f"trans_{q_key}"]:
                        st.info(f"**Question:** {q['question']}")
                        if st.button("查看中文对照 (-2分)", key=f"t_btn_{q_key}"):
                            st.session_state[f"trans_{q_key}"] = True
                            st.rerun()
                    else:
                        st.info(f"**Question:** {q['question']}\n\n**中文对照:** {q['hint5']}")

                    if not st.session_state[f"solved_{q_key}"]:
                        ans = st.text_input("你的答案", key=f"ans_{q_key}")
                        if st.button("提交答案", key=f"sub_{q_key}"):
                            st.session_state[f"att_{q_key}"] += 1
                            att = st.session_state[f"att_{q_key}"]
                            
                            if ans == str(q['answer']):
                                # 计算分数：翻译过起步8分，没翻译起步10分
                                start_score = 8 if st.session_state[f"trans_{q_key}"] else 10
                                score_rules = [start_score, 6, 1, -3]
                                final_p = score_rules[min(att-1, 3)]
                                
                                st.session_state[f"solved_{q_key}"] = True
                                save_score(st.session_state.user, day_val, final_p, f"完成题目：{q['title']}")
                                st.balloons()
                                st.rerun()
                            else:
                                hints = [q['hint1'], q['hint2'], q['hint3'], q['hint4'], q['hint5']]
                                st.error(f"❌ 不对哦！提示：{hints[min(att-1, 4)]}")
                    else:
                        st.success("✅ 已挑战成功！")

    elif menu == "🛒 积分商城":
        st.header("🎁 积分商城")
        # ... (此处保持之前的商城代码即可) ...

    elif menu == "📈 成长记录":
        st.header("📜 英雄成长历史")
        conn = get_db_connection()
        logs = conn.execute('SELECT * FROM scores WHERE user = ? ORDER BY timestamp DESC', (st.session_state.user,)).fetchall()
        conn.close()
        for log in logs:
            st.write(f"⏱ `{log['timestamp']}` | {log['score']} 分 | {log['detail']}")