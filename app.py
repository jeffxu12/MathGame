import streamlit as st
import sqlite3
import datetime
import os

# ================= 1. 数据库核心逻辑 =================
DB_NAME = 'math_master.db'

def get_db_connection():
    """建立数据库连接，如果文件不存在则报错提示"""
    if not os.path.exists(DB_NAME):
        st.error(f"找不到数据库文件 {DB_NAME}，请确保已运行 init_db.py 并上传了 db 文件！")
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

# 使用 session_state 保持登录状态
if 'login' not in st.session_state:
    st.title("🛡️ 奥数神殿入口")
    st.info("出差期间，爸爸在云端守护你的每一分进步！")
    
    with st.form("login_form"):
        user = st.text_input("英雄尊姓大名")
        pwd = st.text_input("通关密语 (询问爸爸)", type="password")
        submit = st.form_submit_button("开启挑战之旅")
        
        if submit:
            if pwd == "123456":
                st.session_state.login = True
                st.session_state.user = user
                st.rerun()
            else:
                st.error("密语不对哦，再想一想！")
else:
    # ================= 3. 登录后的主界面 =================
    points = get_total_points(st.session_state.user)
    
    # 侧边栏
    st.sidebar.title(f"🦸‍♂️ 英雄: {st.session_state.user}")
    st.sidebar.markdown(f"### 当前总积分: **{points}** 🪙")
    st.sidebar.divider()
    
    menu = st.sidebar.radio(
        "传送门",
        ["🔥 今日试炼", "🛒 积分商城", "📈 成长记录"],
        index=0
    )
    
    # --- 模块1：今日试炼 ---
    if menu == "🔥 今日试炼":
        st.header("📅 每日逻辑挑战")
        day_to_solve = st.number_input("选择挑战天数", min_value=1, value=1, step=1)
        
        questions = load_questions(day_to_solve)
        
        if not questions:
            st.warning("这一天的关卡尚未开启，请联系爸爸更新题库！")
        else:
            for q in questions:
                # 唯一的 Key 防止组件冲突
                q_key = f"day{q['day']}_id{q['id']}"
                
                with st.expander(f"第 {q['id']} 题：{q['title']}", expanded=True):
                    st.write(q['question'])
                    
                    # 记录尝试次数
                    att_key = f"att_{q_key}"
                    if att_key not in st.session_state:
                        st.session_state[att_key] = 0
                    
                    user_ans = st.text_input("你的答案", key=f"in_{q_key}")
                    
                    if st.button("提交验证", key=f"btn_{q_key}"):
                        st.session_state[att_key] += 1
                        att = st.session_state[att_key]
                        
                        if user_ans == q['answer']:
                            # 10, 6, 1, -3 奖励逻辑
                            score_map = [10, 6, 1, -3]
                            # 如果超过4次，依然按-3计分
                            final_pts = score_map[min(att-1, 3)]
                            
                            st.success(f"🎉 太棒了！第{att}次挑战成功！获得积分：{final_pts}")
                            save_score(st.session_state.user, day_to_solve, final_score=final_pts, detail=f"攻克：{q['title']}")
                            st.balloons()
                        else:
                            # 错误提示逻辑：获取数据库中预设的 5 个提示
                            hints = [q['hint1'], q['hint2'], q['hint3'], q['hint4'], q['hint5']]
                            current_hint = hints[min(att-1, 4)]
                            st.error(f"❌ 答错啦！提示：{current_hint} (这是你第{att}次尝试)")

    # --- 模块2：积分商城 ---
    elif menu == "🛒 积分商城":
        st.header("🎁 英雄补给站")
        st.subheader(f"剩余可用积分: {points} 🪙")
        
        # 奖品配置
        shop_items = [
            {"name": "看动画片30分钟", "price": 50, "icon": "📺"},
            {"name": "iPad 游戏20分钟", "price": 100, "icon": "🎮"},
            {"name": "美味哈根达斯", "price": 200, "icon": "🍦"},
            {"name": "乐高积木一套", "price": 1000, "icon": "🧩"},
            {"name": "免死金牌 (免作业一次)", "price": 500, "icon": "🛡️"}
        ]
        
        for i, item in enumerate(shop_items):
            c1, c2, c3 = st.columns([1, 3, 1])
            with c1: st.title(item['icon'])
            with c2: 
                st.write(f"**{item['name']}**")
                st.write(f"价格: {item['price']} 积分")
            with c3:
                if st.button("兑换", key=f"buy_{i}"):
                    if points >= item['price']:
                        save_score(st.session_state.user, 999, -item['price'], f"兑换奖励：{item['name']}")
                        st.success("兑换成功！快去找妈妈兑现吧！")
                        st.rerun()
                    else:
                        st.error("分数还不够哦！")
            st.divider()

    # --- 模块3：成长记录 ---
    elif menu == "📈 成长记录":
        st.header("📜 英雄成长史")
        conn = get_db_connection()
        if conn:
            logs = conn.execute('SELECT * FROM scores WHERE user = ? ORDER BY timestamp DESC', (st.session_state.user,)).fetchall()
            conn.close()
            
            if not logs:
                st.info("还没有任何试炼记录，快去答题吧！")
            else:
                for log in logs:
                    timestamp = log['timestamp']
                    score = log['score']
                    detail = log['detail']
                    
                    if score > 0:
                        st.write(f"✅ `{timestamp}` | **+{score}** 分 | {detail}")
                    else:
                        st.write(f"🛒 `{timestamp}` | **{score}** 分 | {detail}")