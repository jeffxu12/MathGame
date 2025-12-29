Python
import streamlit as st
import sqlite3
import datetime
import pandas as pd

# ================= 1. 界面与视觉配置 =================
st.set_page_config(page_title="奥数英雄殿堂", page_icon="🏆", layout="wide")

st.markdown("""
    <style>
    .lesson-box { background-color: #FFF5E6; border: 2px solid #FF8C00; padding: 20px; border-radius: 15px; }
    .subtitle-text { background-color: #444; color: #FFA500; padding: 10px; border-radius: 8px; font-family: 'Courier New'; margin-top: 10px; border-left: 5px solid #FF8C00; }
    .rank-card { background: linear-gradient(135deg, #FF8C00, #FFD700); color: white; padding: 15px; border-radius: 12px; text-align: center; box-shadow: 2px 2px 10px rgba(0,0,0,0.1); }
    </style>
    """, unsafe_allow_html=True)

# ================= 2. 积分找回与数据库核心 =================
DB_NAME = 'math_master.db'

def get_db_connection():
    # 增加 check_same_thread=False 提高 Streamlit 稳定性
    conn = sqlite3.connect(DB_NAME, timeout=10, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def get_user_stats(username):
    conn = get_db_connection()
    try:
        # 核心：确保从 scores 表读取所有历史记录并求和
        cursor = conn.cursor()
        cursor.execute('SELECT SUM(score) FROM scores WHERE user = ?', (username,))
        result = cursor.fetchone()
        points = result[0] if result[0] is not None else 0
        
        cursor.execute('SELECT COUNT(DISTINCT day) FROM scores WHERE user = ? AND score > 0', (username,))
        days = cursor.fetchone()[0]
        return int(points), int(days)
    except Exception as e:
        return 0, 0
    finally:
        conn.close()

# ================= 3. 三年级视角：橙色火柴人深度讲解 =================
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
        "lesson": "🧍【火柴人老师】: 就像红绿灯：红、黄、绿，红、黄、绿... 永远在绕圈。如果问你第100个是什么颜色，你不用数到100！<br><br>看！一组有3个颜色。用 100 ÷ 3 = 33组...余下1个。这个‘余数1’最关键！它说明第100个正好是一组里的第1个，也就是红灯！如果余数是0，那就是这一组的老末！",
        "subtitle": "中文字幕：找周期长度 L，求 总数 ÷ L 的余数。余数是 1 就找组里的第 1 个，余数是 0 就是最后 1 个。"
    },
    "植树问题 (101-125天)": {
        "lesson": "🧍【火柴人老师】: 伸出你的左手！数数有几个手指？5个对吧？再数数手指缝有几个？只有4个！<br><br>种树也一样！如果在直路上两头都种，树的数量永远比缝隙（间隔）多1个。如果你算出路有10个间隔，那记得加1，要准备11棵树哦！如果是在圆形的池塘边种，手指和缝隙就一样多了！",
        "subtitle": "中文字幕：直线植树（两端都种）：棵数 = 间隔数 + 1。封闭图形植树：棵数 = 间隔数。"
    },
    "假设法：鸡兔同笼 (126-150天)": {
        "lesson": "🧍【火柴人老师】: 笼子里有鸡有兔，一共10个头，32条腿。兔子太跳了数不清？<br><br>咱们先‘变魔术’：吹哨子让兔子全把前腿抬起来！现在大家全变成‘两条腿’走路了。10个头就有 10×2=20条腿。可是地上一共有32条腿呀，多出来的 32-20=12条腿是谁的？当然是兔子抬起来的那两只手呀！12条腿除以2，就有6只兔子！",
        "subtitle": "中文字幕：假设全是鸡（2腿），算出腿的差额，用差额 ÷ 2 = 兔子的数量。因为每只兔子比鸡多 2 条腿。"
    }
}

# ================= 4. App 主流程 =================
if 'authenticated' not in st.session_state:
    st.title("🛡️ 奥数英雄殿堂")
    u_name = st.text_input("🦸‍♂️ 英雄代号")
    p_word = st.text_input("🔑 密语 (123456)", type="password")
    if st.button("进入神殿"):
        if p_word == "123456" and u_name:
            st.session_state.authenticated = True
            st.session_state.user = u_name
            st.rerun()
    st.stop()

user = st.session_state.user
points, days_done = get_user_stats(user)

# 侧边栏：积分状态与百科
with st.sidebar:
    st.markdown(f"<div class='rank-card'><h3>🦸‍♂️ {user}</h3><h1>{points} 🪙</h1><p>当前总积分</p></div>", unsafe_allow_html=True)
    st.divider()
    menu = st.radio("🏠 菜单", ["🔥 挑战试炼", "🛒 积分商城", "📈 积分明细"])
    
    st.divider()
    st.markdown("### 🍊 橙色小课堂")
    know_choice = st.selectbox("选择知识点目录", list(KNOWLEDGE_BASE.keys()))
    if st.button("📖 听课"):
        st.session_state.current_lesson = know_choice

# 主内容显示
if 'current_lesson' in st.session_state:
    lesson_data = KNOWLEDGE_BASE[st.session_state.current_lesson]
    st.markdown(f"""
        <div class='lesson-box'>
            <h2>{st.session_state.current_lesson}</h2>
            <p style='font-size: 1.1em;'>{lesson_data['lesson']}</p>
            <div class='subtitle-text'>{lesson_data['subtitle']}</div>
        </div>
    """, unsafe_allow_html=True)
    if st.button("关闭小课堂"):
        del st.session_state.current_lesson
        st.rerun()

if menu == "🔥 挑战试炼":
    st.header(f"第 {days_done + 1} 天挑战")
    day_val = st.number_input("日期选择", 1, 150, value=min(days_done + 1, 150))
    
    conn = get_db_connection()
    qs = conn.execute('SELECT * FROM questions WHERE day = ?', (day_val,)).fetchall()
    conn.close()

    for q in qs:
        key = f"d{day_val}_q{q['id']}"
        if f"att_{key}" not in st.session_state: st.session_state[f"att_{key}"] = 0
        if f"done_{key}" not in st.session_state: st.session_state[f"done_{key}"] = False

        with st.container(border=True):
            st.subheader(f"Q{q['id']}: {q['title']}")
            st.info(f"**English:** {q['question']}")
            
            if not st.session_state[f"done_{key}"]:
                user_ans = st.text_input("答案", key=f"ans_{key}")
                if st.button("提交", key=f"btn_{key}"):
                    st.session_state[f"att_{key}"] += 1
                    att = st.session_state[f"att_{key}"]
                    if user_ans.strip().lower() == str(q['answer']).lower():
                        score_map = {1: 10, 2: 6, 3: 1}
                        final_p = score_map.get(att, -3)
                        st.balloons()
                        st.success(f"正确！获得 {final_p} 积分")
                        st.session_state[f"done_{key}"] = True
                        
                        c = get_db_connection()
                        c.execute('INSERT INTO scores (timestamp, user, day, score, detail) VALUES (?,?,?,?,?)',
                                 (datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), user, day_val, final_p, f"攻克:{q['title']}"))
                        c.commit()
                        c.close()
                        st.rerun()
                    else:
                        hints = [q['h1'], q['h2'], q['h3'], q['h4'], q['h5']]
                        st.error(f"❌ 线索：{hints[min(att-1, 4)]}")
            else:
                st.success("✅ 通关")

elif menu == "📈 积分明细":
    st.header("📜 能量变化记录")
    conn = get_db_connection()
    logs = pd.read_sql_query('SELECT timestamp, score, detail FROM scores WHERE user=? ORDER BY timestamp DESC', conn, params=(user,))
    conn.close()
    st.table(logs)