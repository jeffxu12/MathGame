import streamlit as st
import sqlite3
import datetime
import os

# --- 数据库操作函数 ---
def get_db_connection():
    conn = sqlite3.connect('math_master.db')
    conn.row_factory = sqlite3.Row
    return conn

def load_questions(day):
    conn = get_db_connection()
    qs = conn.execute('SELECT * FROM questions WHERE day = ?', (day,)).fetchall()
    conn.close()
    return qs

def save_score(user, day, score, detail):
    conn = get_db_connection()
    conn.execute('INSERT INTO scores (timestamp, user, day, score, detail) VALUES (?,?,?,?,?)',
                 (datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), user, day, score, detail))
    conn.commit()
    conn.close()

# --- 网页布局 ---
st.set_page_config(page_title="奥数云端神殿", layout="centered")

if 'login' not in st.session_state:
    st.title("🛡️ 奥数神殿入口")
    user = st.text_input("用户名")
    pwd = st.text_input("密码", type="password")
    if st.button("进入神殿"):
        if pwd == "123456":
            st.session_state.login = True
            st.session_state.user = user
            st.rerun()
else:
    st.sidebar.title(f"🦸‍♂️ {st.session_state.user}")
    menu = st.sidebar.radio("菜单", ["开始挑战", "战绩查看", "爸爸留言板"])

    if menu == "开始挑战":
        day = st.sidebar.number_input("挑战天数", min_value=1, value=1)
        qs = load_questions(day)
        
        if not qs:
            st.warning("这一天的题目还没准备好哦！")
        else:
            st.header(f"第 {day} 天：逻辑试炼")
            for q in qs:
                with st.expander(f"题目：{q['title']}", expanded=True):
                    st.write(q['question'])
                    ans = st.text_input("输入你的答案", key=f"ans_{q['day']}_{q['id']}")
                    
                    # 提示系统逻辑 (利用 session_state 记录尝试次数)
                    attempt_key = f"att_{q['day']}_{q['id']}"
                    if attempt_key not in st.session_state: st.session_state[attempt_key] = 0
                    
                    if st.button("提交答案", key=f"btn_{q['day']}_{q['id']}"):
                        st.session_state[attempt_key] += 1
                        att = st.session_state[attempt_key]
                        if ans == q['answer']:
                            pts = [10, 6, 3, 1, -3][min(att-1, 4)]
                            st.success(f"✅ 正确！获得 {pts} 分")
                            save_score(st.session_state.user, day, pts, q['title'])
                        else:
                            hints = [q['hint1'], q['hint2'], q['hint3'], q['hint4'], q['hint5']]
                            st.error(f"❌ 提示：{hints[min(att-1, 4)]}")

    elif menu == "战绩查看":
        st.header("📈 英雄成长记录")
        conn = get_db_connection()
        df = conn.execute('SELECT * FROM scores ORDER BY timestamp DESC').fetchall()
        conn.close()
        if df:
            for row in df:
                st.write(f"⏱ {row['timestamp']} | 🏆 {row['score']}分 | 📖 {row['detail']}")
        else:
            st.info("还没有战绩，加油哦！")