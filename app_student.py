import streamlit as st
import pandas as pd
from supabase import create_client, Client
import time
import random

# ==========================================
# 🎨 0. UI 极致优化 (强制亮色模式 + 高对比度)
# ==========================================
st.set_page_config(page_title="Math Master", page_icon="🦁", layout="centered")

st.markdown("""
<style>
    /* --- 1. 强制全局配色 (防止深色模式导致白字) --- */
    [data-testid="stAppViewContainer"] {
        background-color: #f4f8fb; /* 极淡的护眼蓝灰 */
    }
    
    /* 强制所有默认字体为深色 */
    .stApp, .stMarkdown, p, h1, h2, h3, h4, h5, h6, span, div {
        color: #2c3e50 !important;
    }

    /* 隐藏菜单 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* --- 2. 题目卡片 (大字、清晰、投影) --- */
    .question-card {
        background-color: #ffffff;
        padding: 40px 30px;
        border-radius: 20px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.08); /* 柔和的高级投影 */
        border: 2px solid #eef2f6;
        margin-bottom: 25px;
        text-align: center;
    }
    
    .question-text {
        font-size: 28px !important; /* 超大字号，孩子看得清 */
        font-weight: 600;
        line-height: 1.5;
        color: #1a202c !important; /* 纯深黑，高对比度 */
        font-family: "Comic Sans MS", "PingFang SC", sans-serif;
    }

    /* --- 3. 输入框优化 (大框) --- */
    /* 强制输入框内文字为黑色，背景为白色 */
    .stTextInput input {
        font-size: 32px;
        text-align: center;
        color: #000000 !important;
        background-color: #ffffff !important;
        border: 3px solid #dfe6e9;
        border-radius: 15px;
        padding: 15px;
        height: 70px;
    }
    .stTextInput input:focus {
        border-color: #74b9ff;
        box-shadow: 0 0 10px rgba(116, 185, 255, 0.3);
    }

    /* --- 4. 按钮优化 (像果冻一样) --- */
    .stButton>button {
        width: 100%;
        background: linear-gradient(180deg, #ff9f43 0%, #ff6b6b 100%); /* 渐变橙 */
        color: white !important;
        font-size: 22px;
        font-weight: bold;
        border-radius: 50px; /* 圆角胶囊 */
        border: none;
        padding: 15px 0;
        box-shadow: 0 5px 15px rgba(255, 107, 107, 0.4);
        transition: transform 0.1s;
    }
    .stButton>button:active {
        transform: scale(0.98);
        box-shadow: 0 2px 5px rgba(255, 107, 107, 0.4);
    }
    
    /* --- 5. 勋章区域 --- */
    .badge-container {
        background: white;
        padding: 10px 20px;
        border-radius: 30px;
        border: 1px solid #eee;
        display: inline-block;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    }

</style>
""", unsafe_allow_html=True)

# ==========================================
# ⚡️ 1. 数据库连接 (带自动重连)
# ==========================================
SUPABASE_URL = "https://fohuvfuhrtdurmnqvrty.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZvaHV2ZnVocnRkdXJtbnF2cnR5Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjY5ODEwNjksImV4cCI6MjA4MjU1NzA2OX0.FkkJGaI4yt6YnkqINMgtHYnRhJBObRysYbVZh-HuUPQ"

@st.cache_resource(ttl=3600)
def init_connection():
    try:
        client = create_client(SUPABASE_URL, SUPABASE_KEY)
        client.table("users").select("id").limit(1).execute() # Ping test
        return client
    except Exception as e:
        st.cache_resource.clear()
        return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_connection()

# ==========================================
# 🧠 2. 状态管理
# ==========================================
if "quiz_active" not in st.session_state:
    st.session_state.quiz_active = False
    st.session_state.current_q_index = 0
    st.session_state.score = 0
    st.session_state.quiz_data = []
    st.session_state.user_coins = 0
    st.session_state.feedback = None 

# ==========================================
# 👤 3. 登录页 (大图标版)
# ==========================================
def login_page():
    st.markdown("<br><br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 6, 1])
    with c2:
        st.markdown("<h1 style='text-align: center; color: #ff6b6b !important; font-size: 40px;'>🦁 Math Master</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #888 !important;'>快乐奥数 · 每天进步一点点</p>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

        try:
            users = supabase.table("users").select("*").execute().data
            if not users:
                st.error("请先运行 seed 脚本生成用户数据")
                return
            
            user_map = {u['nickname']: u for u in users}
            
            # 使用 container 包裹选择框，增加白色背景
            with st.container(border=True):
                selected_name = st.selectbox("👉 请选择我是谁：", list(user_map.keys()))
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("🚀 开始我的冒险"):
                    st.session_state.user = user_map[selected_name]
                    st.session_state.user_coins = st.session_state.user['coins']
                    st.rerun()
        except:
            st.warning("正在连接云端大脑... 请稍等后刷新页面")

# ==========================================
# 🎮 4. 核心逻辑
# ==========================================
def start_quiz():
    try:
        # 随机取题逻辑
        res = supabase.table("questions").select("*").execute()
        all_q = res.data
        if len(all_q) < 5:
            st.error("题库空了，请爸爸运行生成脚本！")
            return
        st.session_state.quiz_data = random.sample(all_q, 5)
        st.session_state.quiz_active = True
        st.session_state.current_q_index = 0
        st.session_state.score = 0
        st.session_state.feedback = None
        st.rerun()
    except Exception as e:
        st.error(f"启动失败，请刷新 ({e})")
        st.cache_resource.clear()

def check_answer(user_input, correct_answer, explanation, question_id):
    is_correct = str(user_input).strip().lower() == str(correct_answer).strip().lower()
    
    # 异步写入日志 (忽略错误以保证体验)
    try:
        supabase.table("practice_logs").insert({
            "user_id": st.session_state.user['id'],
            "question_id": question_id,
            "user_answer": str(user_input),
            "is_correct": is_correct,
            "time_taken": 30
        }).execute()
        if not is_correct:
             supabase.table("mistakes").insert({"user_id": st.session_state.user['id'], "question_id": question_id, "error_count": 1}).execute()
    except: pass
    
    if is_correct:
        st.session_state.score += 1
        st.session_state.feedback = {"type": "success", "msg": "🎉 答对了！太棒了！"}
    else:
        st.session_state.feedback = {"type": "error", "msg": f"💡 正确答案是: {correct_answer}。 \n\n解析：{explanation}"}

def render_quiz():
    q_index = st.session_state.current_q_index
    total_q = len(st.session_state.quiz_data)
    question = st.session_state.quiz_data[q_index]
    
    # 顶部状态条
    cols = st.columns([1, 4, 1])
    with cols[0]:
        st.caption(f"关卡 {q_index + 1}/{total_q}")
    with cols[1]:
        st.progress((q_index) / total_q)
    with cols[2]:
        st.caption(f"得分 {st.session_state.score}")

    # 题目展示 (使用新的 CSS 类)
    st.markdown(f"""
    <div class="question-card">
        <div class="question-text">{question['content']}</div>
    </div>
    """, unsafe_allow_html=True)
    
    # 交互区
    if st.session_state.feedback is None:
        with st.form(key=f"q_form_{q_index}"):
            if question['type'] == 'choice' and question['options']:
                st.markdown("#### 请选择：")
                user_ans = st.radio("选项", question['options'], label_visibility="collapsed")
            else:
                user_ans = st.text_input("Answer", placeholder="在这里输入数字...", label_visibility="collapsed")
            
            st.markdown("<br>", unsafe_allow_html=True)
            submit = st.form_submit_button("⚡️ 确定提交")
            
            if submit:
                if not user_ans: st.warning("还没填答案呢！")
                else:
                    check_answer(user_ans, question['answer'], question['explanation'], question['id'])
                    st.rerun()
    else:
        # 结果反馈
        fb = st.session_state.feedback
        if fb['type'] == 'success':
            st.balloons()
            st.markdown(f"""
            <div style="background:#e3fcef; padding:20px; border-radius:15px; text-align:center; border:2px solid #2ecc71;">
                <h2 style="color:#27ae60 !important; margin:0;">🎉 BINGO! +10 金币</h2>
            </div>
            """, unsafe_allow_html=True)
            st.audio("https://codeskulptor-demos.commondatastorage.googleapis.com/pang/pop.mp3", autoplay=True)
        else:
            st.markdown(f"""
            <div style="background:#ffebee; padding:20px; border-radius:15px; border:2px solid #ff7675;">
                <h3 style="color:#c0392b !important; margin:0;">😥 哎呀，答错了...</h3>
                <p style="color:#333 !important; margin-top:10px;">{fb['msg']}</p>
            </div>
            """, unsafe_allow_html=True)
            st.audio("https://codeskulptor-demos.commondatastorage.googleapis.com/assets/soundboard/explode.wav", autoplay=True)

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("➡️ 下一关", type="primary"):
            if q_index + 1 < total_q:
                st.session_state.current_q_index += 1
                st.session_state.feedback = None
                st.rerun()
            else:
                st.session_state.quiz_active = False
                # 结算加币
                new_coins = st.session_state.user_coins + (st.session_state.score * 10)
                try: supabase.table("users").update({"coins": new_coins}).eq("id", st.session_state.user['id']).execute()
                except: pass
                st.session_state.user_coins = new_coins
                st.rerun()

# ==========================================
# 📱 主入口
# ==========================================
if "user" not in st.session_state:
    login_page()
else:
    # 顶部导航栏
    with st.container():
        c1, c2 = st.columns([2, 1])
        c1.markdown(f"<h3 style='margin:0'>🦁 Hi, {st.session_state.user['nickname']}</h3>", unsafe_allow_html=True)
        
        # 勋章显示
        lvl = "🌱 新手"
        if st.session_state.user_coins > 200: lvl = "🥉 青铜"
        if st.session_state.user_coins > 500: lvl = "🥇 黄金"
        
        c2.markdown(f"""
        <div class="badge-container">
            <span style="font-size:18px;">💰 {st.session_state.user_coins}</span>
            <span style="color:#ccc">|</span>
            <span style="font-weight:bold; color:#f39c12;">{lvl}</span>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")

    if not st.session_state.quiz_active:
        # 首页大卡片
        st.markdown("""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; border-radius: 20px; color: white; text-align: center; margin-bottom: 20px; box-shadow: 0 10px 20px rgba(118, 75, 162, 0.4);">
            <h2 style="color:white !important;">🔥 每日挑战</h2>
            <p style="color: #e0e0e0 !important;">随机 5 道题 · 赚取金币 · 升级勋章</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("⚔️ 立即开始"):
            start_quiz()
            
        with st.expander("👀 看看我的错题本"):
            st.info("请让爸爸去【家长控制台】查看你的详细错题哦！")
            
    else:
        render_quiz()