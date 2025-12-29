import streamlit as st
import sqlite3
import datetime
import pandas as pd

# ================= 1. 页面配置 =================
st.set_page_config(page_title="奥数英雄殿堂", page_icon="🏆", layout="wide")

# 自定义 CSS：优化火柴人课堂视觉效果
st.markdown("""
    <style>
    .stickman-box { background-color: #FFF5E6; border-left: 5px solid #FF8C00; padding: 15px; border-radius: 10px; margin-bottom: 20px;}
    .subtitle-bar { background-color: #333; color: #fff; padding: 5px 12px; border-radius: 4px; font-size: 0.85em; margin-top: 10px;}
    .sidebar-rank { background: linear-gradient(135deg, #FF8C00, #FFA500); color: white; padding: 10px; border-radius: 8px; text-align: center;}
    </style>
    """, unsafe_allow_html=True)

# ================= 2. 数据库与基础逻辑 =================
DB_NAME = 'math_master.db'

def get_db_connection():
    conn = sqlite3.connect(DB_NAME, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn

def get_user_stats(username):
    conn = get_db_connection()
    try:
        row = conn.execute('SELECT SUM(score) as total FROM scores WHERE user = ?', (username,)).fetchone()
        pts = row['total'] if row and row['total'] else 0
        days = conn.execute('SELECT COUNT(DISTINCT day) as count FROM scores WHERE user = ?', (username,)).fetchone()['count']
        return pts, days
    finally:
        conn.close()

# ================= 3. 知识点小课堂数据源 =================
KNOWLEDGE_BASE = {
    "计算：等量代换": {
        "tag": "Day 1-25",
        "lesson": "嘿！我是橙色火柴人！'代换'就像变魔术。如果1个苹果换2个梨，1个梨换3个李子，那1个苹果能换几个李子？公式就是：2 × 3 = 6！我们要找到那个‘中间人’。",
        "subtitle": "核心：通过中间量建立连乘关系，把复杂的物体关系简化。"
    },
    "建模：和差问题": {
        "tag": "Day 26-50",
        "lesson": "我是橙色火柴人！知道两个人的总数，又知道谁比谁多。秘诀是：(和 + 差) ÷ 2 = 大数；(和 - 差) ÷ 2 = 小数。画出线段图，一眼就能看出来！",
        "subtitle": "核心：利用线段图实现‘移多补少’，将差异平衡化。"
    },
    "逻辑：周期规律": {
        "tag": "Day 51-75",
        "lesson": "我是橙色火柴人！规律就是转圈圈。用总数除以一圈的长度，余数是几，就是这圈里的第几个。如果余数是0，说明正好是这一圈的最后一个！",
        "subtitle": "核心：通过余数定位周期内的具体位置。"
    },
    "几何：巧求周长": {
        "tag": "Day 76-100",
        "lesson": "我是橙色火柴人！看到锯齿形的周长别害怕，用‘平移法’把横线往上推，纵线往外推，它就变成了一个整齐的长方形！",
        "subtitle": "核心：平移不改变总长度，将不规则转化为标准规则计算。"
    },
    "应用：植树问题": {
        "tag": "Day 101-125",
        "lesson": "我是橙色火柴人！路两端都种树，就像手指和缝隙：5个手指有4个缝。所以：树的数量 = 间隔数 + 1。如果是封闭的圆圈，树和缝隙一样多哦！",
        "subtitle": "核心：区分直线植树（+1）与封闭图形植树（相等）。"
    },
    "高阶：假设法": {
        "tag": "Day 126-150",
        "lesson": "我是橙色火柴人！鸡兔同笼最经典。先假设全是鸡，算出缺了多少条腿，每把一只鸡换成兔子，就会多出2条腿。用‘缺的腿’除以2就是兔子数！",
        "subtitle": "核心：通过假设统一变量，根据差异反推另一种变量。"
    }
}

# ================= 4. 英雄身份校验 =================
if 'authenticated' not in st.session_state:
    st.title("🛡️ 奥数英雄殿堂")
    u_in = st.text_input("🦸‍♂️ 英雄姓名")
    p_in = st.text_input("🔑 密语", type="password")
    if st.button("进入神殿"):
        if p_in == "123456" and u_in:
            st.session_state.authenticated = True
            st.session_state.user = u_in
            st.rerun()
    st.stop()

# ================= 5. 侧边栏常驻模块 =================
user = st.session_state.user
points, days_done = get_user_stats(user)

with st.sidebar:
    # 英雄信息卡片
    st.markdown(f"<div class='sidebar-rank'><h3>🦸‍♂️ {user}</h3><small>当前积分：{points}</small></div>", unsafe_allow_html=True)
    st.divider()
    
    # 功能导航
    menu = st.radio("🏠 传送门", ["🔥 今日试炼", "🛒 积分商城", "📈 成长记录"])
    
    st.divider()
    
    # 🍊 知识点百科（目录与查询）
    st.markdown("### 🍊 知识点百科")
    search_query = st.text_input("🔍 搜索知识点...", placeholder="如：植树")
    
    # 根据搜索或列表显示目录
    all_lessons = list(KNOWLEDGE_BASE.keys())
    filtered_lessons = [l for l in all_lessons if search_query in l] if search_query else all_lessons
    
    selected_lesson = st.selectbox("📚 课程目录", filtered_lessons)
    
    # 在侧边栏下方展示火柴人教学（缩略版）
    if selected_lesson:
        data = KNOWLEDGE_BASE[selected_lesson]
        st.markdown(f"""
        <div class='stickman-box'>
            <b style='color:#FF8C00;'>🧍 {selected_lesson}</b><br>
            <small style='color:#666;'>{data['lesson'][:60]}...</small>
        </div>
        """, unsafe_allow_html=True)
        if st.button("📖 阅读全文"):
            st.session_state.show_lesson = selected_lesson

    st.divider()
    if st.button("🚪 退出"):
        st.session_state.clear()
        st.rerun()

# ================= 6. 主内容区逻辑 =================

# 如果点击了“阅读全文”，先弹出教学弹窗
if 'show_lesson' in st.session_state:
    l_name = st.session_state.show_lesson
    l_data = KNOWLEDGE_BASE[l_name]
    with st.expander(f"🍊 橙色火柴人小课堂：{l_name}", expanded=True):
        st.markdown(f"""
        <div class='stickman-box'>
            <div style='display:flex; align-items:center;'>
                <div style='font-size:50px; margin-right:15px;'>🧍</div>
                <div>
                    <p>{l_data['lesson']}</p>
                    <div class='subtitle-bar'>中文字幕：{l_data['subtitle']}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("关闭课堂"):
            del st.session_state.show_lesson
            st.rerun()

# 根据主菜单显示页面
if menu == "🔥 今日试炼":
    st.header(f"📅 第 {days_done + 1} 天逻辑试炼")
    day_val = st.number_input("调整试炼天数", 1, 150, value=min(days_done + 1, 150))
    
    # 自动提醒：如果是新章节第一天，主动建议阅读百科
    if day_val in [1, 26, 51, 76, 101, 126]:
        st.warning("⚡ 英雄！新章节开始了，建议先查看左侧的【🍊 知识点百科】学习技巧。")

    conn = get_db_connection()
    questions = conn.execute('SELECT * FROM questions WHERE day = ?', (day_val,)).fetchall()
    conn.close()

    for q in questions:
        key = f"d{day_val}_q{q['id']}"
        if f"att_{key}" not in st.session_state: st.session_state[f"att_{key}"] = 0
        if f"done_{key}" not in st.session_state: st.session_state[f"done_{key}"] = False

        with st.container(border=True):
            st.subheader(f"Q{q['id']}: {q['title']}")
            st.info(f"**English:** {q['question']}")
            
            if not st.session_state[f"done_{key}"]:
                ans = st.text_input("你的答案", key=f"in_{key}")
                if st.button("提交验证", key=f"btn_{key}"):
                    st.session_state[f"att_{key}"] += 1
                    att = st.session_state[f"att_{key}"]
                    
                    if ans.strip().lower() == str(q['answer']).lower():
                        score_map = {1: 10, 2: 6, 3: 1}
                        final_p = score_map.get(att, -3)
                        st.balloons()
                        st.success(f"正确！获得 {final_p} 积分！")
                        st.session_state[f"done_{key}"] = True
                        
                        c = get_db_connection()
                        c.execute('INSERT INTO scores VALUES (?,?,?,?,?)',
                                 (datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), user, day_val, final_p, f"攻克: {q['title']}"))
                        c.commit()
                        c.close()
                        st.rerun()
                    else:
                        hints = [q['h1'], q['h2'], q['h3'], q['h4'], q['h5']]
                        st.error(f"❌ 提示：{hints[min(att-1, 4)]}")
            else:
                st.success("✅ 已通关")

elif menu == "🛒 积分商城":
    # (保持之前商城逻辑不变，此处略)
    st.header("🎁 积分商城")
    st.write("使用你的积分为英雄兑换奖励！")

elif menu == "📈 成长记录":
    st.header("📜 英雄成长史")
    conn = get_db_connection()
    logs = pd.read_sql_query('SELECT timestamp as 时间, score as 积分, detail as 详情 FROM scores WHERE user=? ORDER BY 时间 DESC', conn, params=(user,))
    conn.close()
    st.dataframe(logs, use_container_width=True)