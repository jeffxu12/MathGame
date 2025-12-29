import streamlit as st
import sqlite3
import datetime
import pandas as pd

# ================= 1. 界面与视觉配置 (保留所有样式) =================
st.set_page_config(page_title="奥数英雄殿堂", page_icon="🏆", layout="wide")

st.markdown("""
    <style>
    /* 橙色火柴人课程框 */
    .lesson-box { background-color: #FFF5E6; border: 2px solid #FF8C00; padding: 20px; border-radius: 15px; margin-bottom: 20px; }
    /* 中文字幕样式 */
    .subtitle-text { background-color: #444; color: #FFA500; padding: 10px; border-radius: 8px; font-family: 'Courier New'; margin-top: 10px; border-left: 5px solid #FF8C00; font-size: 0.9em; }
    /* 侧边栏积分卡片 */
    .rank-card { background: linear-gradient(135deg, #FF8C00, #FFD700); color: white; padding: 15px; border-radius: 12px; text-align: center; box-shadow: 2px 2px 10px rgba(0,0,0,0.1); }
    /* 管理员面板样式 */
    .admin-panel { background-color: #f0f2f6; border: 1px solid #d1d5db; padding: 15px; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# ================= 2. 数据库与积分找回核心 =================
DB_NAME = 'math_master.db'

def get_db_connection():
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def get_user_stats(username):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        # 确保计算该用户在 scores 表中的所有积分总和
        cursor.execute('SELECT SUM(score) FROM scores WHERE user = ?', (username,))
        result = cursor.fetchone()
        points = result[0] if (result and result[0] is not None) else 0
        # 计算已练习的天数
        cursor.execute('SELECT COUNT(DISTINCT day) FROM scores WHERE user = ? AND score > 0', (username,))
        days = cursor.fetchone()[0] or 0
        return int(points), int(days)
    except:
        return 0, 0
    finally:
        conn.close()

# ================= 3. 知识点百科 (三年级小孩视角 + 橙色火柴人) =================
KNOWLEDGE_BASE = {
    "等量代换 (1-25天)": {
        "lesson": "🧍【火柴人老师】: 嗨！想象一下，你去小超市，老板说：'1个大西瓜可以换2个哈密瓜'，'1个哈密瓜可以换3个大苹果'。那你拿1个西瓜能换几个苹果呢？<br><br>别数晕了！诀窍是：把西瓜拆开！1个西瓜变2个哈密瓜，每个哈密瓜再变3个苹果，那就是 2个3相加，也就是 2×3=6个！这叫'顺藤摸瓜'！",
        "subtitle": "中文字幕：代换就是‘中间人’牵线。1 A = 2 B, 1 B = 3 C，那么 1 A = 2 × 3 C。找到那个‘中转站’B，乘法就解决啦！"
    },
    "和差问题 (26-50天)": {
        "lesson": "🧍【火柴人老师】: 你和哥哥一共10块糖，哥哥比你多2块。你肯定在想：怎么分才公平？<br><br>火柴人秘籍：把哥哥多出来的那2块先‘藏起来’！剩下的 10-2=8块，咱俩平分，一人4块。这时候再把藏起来的2块还给哥哥，哥哥就是 4+2=6块啦！这就是‘先拿走多余的，分完再补回来’！",
        "subtitle": "中文字幕：公式是 (总数 - 差) ÷ 2 = 小数。先把‘差’减掉，剩下的平分，你就得到了较小的那个数！"
    },
    "周期规律 (51-75天)": {
        "lesson": "🧍【火柴人老师】: 就像红绿灯：红、黄、绿，红、黄、绿... 永远在绕圈。如果问你第100个是什么颜色，你不用数到100！<br><br>看！一组有3个颜色。用 100 ÷ 3 = 33组...余下1个。这个‘余数1’最关键！它说明第100个正好是一组里的第1个，也就是红灯！",
        "subtitle": "中文字幕：求 余数 = 总数 ÷ 周期长度。余数是 1 就找组里的第 1 个，余数是 0 就是最后 1 个。"
    },
    "植树问题 (101-125天)": {
        "lesson": "🧍【火柴人老师】: 伸出你的左手！数数有几个手指？5个对吧？再数数手指缝有几个？只有4个！<br><br>如果在路两头都种树，树的数量永远比缝隙（间隔）多1个。所以算出路有几个间隔，记得‘加1’哦！但如果是绕圈种树，树和缝隙就一样多了！",
        "subtitle": "中文字幕：直线植树（两端都种）：棵数 = 间隔数 + 1。封闭图形植树：棵数 = 间隔数。"
    }
}

# ================= 4. 登录逻辑 (双重模式) =================
if 'authenticated' not in st.session_state:
    st.title("🛡️ 奥数英雄殿堂")
    role = st.selectbox("请选择身份", ["学员模式", "管理员模式"])
    u_name = st.text_input("🦸‍♂️ 账号名称")
    p_word = st.text_input("🔑 验证密语", type="password")
    
    if st.button("开启大门"):
        if role == "管理员模式" and p_word == "admin888":
            st.session_state.authenticated = True
            st.session_state.user = u_name
            st.session_state.role = "ADMIN"
            st.rerun()
        elif role == "学员模式" and p_word == "123456":
            st.session_state.authenticated = True
            st.session_state.user = u_name
            st.session_state.role = "USER"
            st.rerun()
        else:
            st.error("密语错误或身份不匹配！")
    st.stop()

# ================= 5. 管理员专属后台 (新增) =================
if st.session_state.role == "ADMIN":
    st.title("⚙️ 管理员控制台")
    st.sidebar.info(f"管理员: {st.session_state.user}")
    
    tab1, tab2 = st.tabs(["📊 数据监控", "🛠️ 题库管理"])
    
    with tab1:
        st.subheader("所有学员积分明细")
        conn = get_db_connection()
        try:
            df_scores = pd.read_sql_query("SELECT * FROM scores", conn)
            st.dataframe(df_scores, use_container_width=True)
            # 积分排行榜
            st.subheader("🏆 积分排行榜")
            rank_df = pd.read_sql_query("SELECT user, SUM(score) as total FROM scores GROUP BY user ORDER BY total DESC", conn)
            st.table(rank_df)
        finally:
            conn.close()
            
    with tab2:
        st.subheader("编辑题库内容")
        day_edit = st.number_input("查看第几天题目", 1, 150, 1)
        conn = get_db_connection()
        df_qs = pd.read_sql_query("SELECT * FROM questions WHERE day = ?", conn, params=(day_edit,))
        st.data_editor(df_qs, num_rows="dynamic") # 可直接在线编辑
        st.warning("注：此编辑界面目前仅作展示，保存逻辑可根据需求扩展。")
        conn.close()

    if st.sidebar.button("切换回登录页"):
        st.session_state.clear()
        st.rerun()
    st.stop() # 管理员不进入下方学员界面

# ================= 6. 学员界面 (保留所有功能：积分、课堂、翻译、试炼) =================
user = st.session_state.user
points, days_done = get_user_stats(user)

# 侧边栏
with st.sidebar:
    st.markdown(f"<div class='rank-card'><h3>🦸‍♂️ {user}</h3><h1>{points} 🪙</h1><p>当前总积分</p></div>", unsafe_allow_html=True)
    st.divider()
    menu = st.radio("🏠 菜单", ["🔥 挑战试炼", "📈 积分明细"])
    
    st.divider()
    st.markdown("### 🍊 橙色小课堂")
    know_choice = st.selectbox("知识点目录", list(KNOWLEDGE_BASE.keys()))
    if st.button("📖 听课"):
        st.session_state.current_lesson = know_choice
    
    if st.button("🚪 退出登录"):
        st.session_state.clear()
        st.rerun()

# 知识点展示
if 'current_lesson' in st.session_state:
    l_data = KNOWLEDGE_BASE[st.session_state.current_lesson]
    st.markdown(f"""
        <div class='lesson-box'>
            <h2>{st.session_state.current_lesson}</h2>
            <p style='font-size: 1.1em;'>{l_data['lesson']}</p>
            <div class='subtitle-text'>{l_data['subtitle']}</div>
        </div>
    """, unsafe_allow_html=True)
    if st.button("关闭课堂"):
        del st.session_state.current_lesson
        st.rerun()

# 试炼功能
if menu == "🔥 挑战试炼":
    st.header(f"第 {days_done + 1} 天试炼")
    day_val = st.number_input("关卡选择", 1, 150, value=min(days_done + 1, 150))
    
    conn = get_db_connection()
    qs = conn.execute('SELECT * FROM questions WHERE day = ?', (day_val,)).fetchall()
    conn.close()

    for q in qs:
        key = f"d{day_val}_q{q['id']}"
        # 初始化状态
        if f"att_{key}" not in st.session_state: st.session_state[f"att_{key}"] = 0
        if f"done_{key}" not in st.session_state: st.session_state[f"done_{key}"] = False
        if f"trans_{key}" not in st.session_state: st.session_state[f"trans_{key}"] = False

        with st.container(border=True):
            st.subheader(f"Q{q['id']}: {q['title']}")
            
            # --- 翻译功能展示 ---
            if st.session_state[f"trans_{key}"]:
                st.success(f"🇨🇳 **中文题目:** {q['h5']}") # 假设h5字段存中文
            else:
                st.info(f"🇺🇸 **English:** {q['question']}")
            
            if st.button("🔄 翻译/还原", key=f"btn_tr_{key}"):
                st.session_state[f"trans_{key}"] = not st.session_state[f"trans_{key}"]
                st.rerun()

            # --- 答题逻辑 ---
            if not st.session_state[f"done_{key}"]:
                u_ans = st.text_input("填写你的答案", key=f"ans_{key}")
                if st.button("提交英雄证明", key=f"btn_sub_{key}"):
                    st.session_state[f"att_{key}"] += 1
                    att_count = st.session_state[f"att_{key}"]
                    
                    if u_ans.strip().lower() == str(q['answer']).lower():
                        score_map = {1: 10, 2: 6, 3: 1}
                        final_p = score_map.get(att_count, -3)
                        st.balloons()
                        st.success(f"太棒了！积分 +{final_p}")
                        st.session_state[f"done_{key}"] = True
                        
                        # 写入数据库 (确保积分找回的关键)
                        c = get_db_connection()
                        c.execute('INSERT INTO scores (timestamp, user, day, score, detail) VALUES (?,?,?,?,?)',
                                 (datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), user, day_val, final_p, f"攻克:{q['title']}"))
                        c.commit()
                        c.close()
                        st.rerun()
                    else:
                        hints = [q['h1'], q['h2'], q['h3'], q['h4'], q['h5']]
                        st.error(f"❌ 线索：{hints[min(att_count-1, 4)]}")
            else:
                st.success("✅ 任务已达成")

elif menu == "📈 积分明细":
    st.header("📜 英雄成长史")
    conn = get_db_connection()
    logs = pd.read_sql_query('SELECT timestamp, score, detail FROM scores WHERE user=? ORDER BY timestamp DESC', conn, params=(user,))
    conn.close()
    st.table(logs)