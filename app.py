import streamlit as st
import sqlite3
import datetime
import os

# --- 数据库连接 ---
DB_NAME = 'math_master.db'

def get_db_connection():
    if not os.path.exists(DB_NAME):
        # 尝试创建一个空的，防止报错
        conn = sqlite3.connect(DB_NAME)
        conn.execute('''CREATE TABLE IF NOT EXISTS scores 
                         (timestamp TEXT, user TEXT, day INTEGER, score INTEGER, detail TEXT)''')
        conn.commit()
        return conn
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def load_questions(day):
    conn = get_db_connection()
    try:
        qs = conn.execute('SELECT * FROM questions WHERE day = ?', (day,)).fetchall()
        return qs
    except:
        return []
    finally:
        conn.close()

def save_score(user, day, score, detail):
    conn = get_db_connection()
    conn.execute('INSERT INTO scores (timestamp, user, day, score, detail) VALUES (?,?,?,?,?)',
                 (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), user, day, score, detail))
    conn.commit()
    conn.close()

def get_total_points(user):
    conn = get_db_connection()
    try:
        result = conn.execute('SELECT SUM(score) as total FROM scores WHERE user = ?', (user,)).fetchone()
        return result['total'] if result['total'] and result['total'] else 0
    except:
        return 0
    finally:
        conn.close()

# --- 页面配置 ---
st.set_page_config(page_title="奥数神殿", page_icon="🛡️")

# --- 登录逻辑 (修复后的版本) ---
if 'login' not in st.session_state:
    st.title("🛡️ 奥数神殿入口")
    st.markdown("---")
    
    # 不使用 st.form，避免 session_state 修改冲突
    user_input = st.text_input("英雄姓名")
    pwd_input = st.text_input("通关密语", type="password")
    
    if st.button("进入神殿"):
        if pwd_input == "123456":
            # 这里的修改在 form 之外，是安全的
            st.session_state.login = True
            st.session_state.user = user_input
            st.rerun()
        else:
            st.error("密语错误！")
else:
    # --- 登录后的主界面 ---
    points = get_total_points(st.session_state.user)
    st.sidebar.title(f"🦸‍♂️ {st.session_state.user}")
    st.sidebar.metric("当前积分", f"{points} 🪙")
    
    menu = st.sidebar.radio("前往地点", ["🔥 每日挑战", "🛒 积分商城", "📈 成长记录"])

    # --- 1. 每日挑战 ---
    if menu == "🔥 每日挑战":
        st.header("📅 每日逻辑试炼")
        day_val = st.number_input("选择挑战天数", min_value=1, value=1, step=1)
        questions = load_questions(day_val)
        
        if not questions:
            st.info("今天的题目还没准备好哦。")
        else:
            for q in questions:
                q_key = f"q_{q['day']}_{q['id']}"
                
                if f"att_{q_key}" not in st.session_state: st.session_state[f"att_{q_key}"] = 0
                if f"solved_{q_key}" not in st.session_state: st.session_state[f"solved_{q_key}"] = False
                if f"trans_{q_key}" not in st.session_state: st.session_state[f"trans_{q_key}"] = False

                with st.expander(f"第 {q['id']} 题：{q['title']}", expanded=not st.session_state[f"solved_{q_key}"]):
                    if not st.session_state[f"trans_{q_key}"]:
                        st.info(f"**Question:** {q['question']}")
                        if st.button("查看中文对照 (-2分)", key=f"t_btn_{q_key}"):
                            st.session_state[f"trans_{q_key}"] = True
                            st.rerun()
                    else:
                        st.info(f"**Question:** {q['question']}\n\n**中文对照:** {q['hint5']}")

                    if not st.session_state[f"solved_{q_key}"]:
                        ans_input = st.text_input("你的答案", key=f"ans_{q_key}")
                        if st.button("提交答案", key=f"sub_{q_key}"):
                            st.session_state[f"att_{q_key}"] += 1
                            att = st.session_state[f"att_{q_key}"]
                            
                            if ans_input == str(q['answer']):
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

    # --- 2. 积分商城 ---
    elif menu == "🛒 积分商城":
        st.header("🎁 积分商城")
        shop_items = [
            {"name": "看动画片30分钟", "price": 50, "icon": "📺"},
            {"name": "iPad 游戏20分钟", "price": 100, "icon": "🎮"},
            {"name": "哈根达斯冰淇淋", "price": 200, "icon": "🍦"},
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
                        st.error("积分不足")

    # --- 3. 成长记录 (找回历史记录的关键) ---
    elif menu == "📈 成长记录":
        st.header("📜 英雄成长历史")
        conn = get_db_connection()
        try:
            logs = conn.execute('SELECT * FROM scores WHERE user = ? ORDER BY timestamp DESC', (st.session_state.user,)).fetchall()
            if not logs:
                st.info("还没有历史记录哦。")
            else:
                for log in logs:
                    color = "green" if log['score'] > 0 else "red"
                    st.write(f"⏱ `{log['timestamp']}` | :{color}[{log['score']} 分] | {log['detail']}")
        except:
            st.warning("记录加载失败，请确保数据库已上传。")
        finally:
            conn.close()