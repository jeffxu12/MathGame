import streamlit as st
import pandas as pd
from supabase import create_client
import time
import random

# ==========================================
# 🎨 0. 魔法 UI 配置 (果冻风格)
# ==========================================
st.set_page_config(page_title="Math Master", page_icon="🦁", layout="centered")

st.markdown("""
<style>
    /* 全局字体：卡通一点 */
    .stApp {
        background-color: #E0F7FA; /* 淡蓝背景 */
    }
    
    /* 顶栏隐藏 */
    header {visibility: hidden;}
    
    /* 核心卡片 */
    .question-card {
        background-color: white;
        padding: 30px;
        border-radius: 20px;
        box-shadow: 0 8px 0px #b2ebf2; /* 3D果冻效果 */
        border: 2px solid #4DD0E1;
        margin-bottom: 20px;
        text-align: center;
    }
    
    /* 大标题 */
    h1 {
        color: #006064;
        font-family: 'Comic Sans MS', 'Chalkboard SE', sans-serif;
    }
    
    /* 答案输入框优化 */
    .stTextInput>div>div>input {
        text-align: center;
        font-size: 24px;
        border-radius: 12px;
        border: 2px solid #4DD0E1;
    }
    
    /* 按钮变身：像游戏按钮 */
    .stButton>button {
        width: 100%;
        background-color: #FF7043; /* 活力橙 */
        color: white;
        font-size: 20px;
        font-weight: bold;
        border-radius: 15px;
        border: none;
        box-shadow: 0 5px 0 #D84315;
        padding: 10px 0;
        transition: all 0.1s;
    }
    .stButton>button:active {
        transform: translateY(5px);
        box-shadow: none;
    }
    
    /* 进度条 */
    .stProgress > div > div > div > div {
        background-color: #FFCA28;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# ⚡️ 1. 连接大脑 (数据库)
# ==========================================
SUPABASE_URL = "https://fohuvfuhrtdurmnqvrty.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZvaHV2ZnVocnRkdXJtbnF2cnR5Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjY5ODEwNjksImV4cCI6MjA4MjU1NzA2OX0.FkkJGaI4yt6YnkqINMgtHYnRhJBObRysYbVZh-HuUPQ"

@st.cache_resource
def init_connection():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_connection()

# ==========================================
# 🧠 2. 游戏状态机 (Session State)
# ==========================================
# 我们需要记住孩子做到了第几题，得了多少分
if "quiz_active" not in st.session_state:
    st.session_state.quiz_active = False
    st.session_state.current_q_index = 0
    st.session_state.score = 0
    st.session_state.quiz_data = []
    st.session_state.user_coins = 0
    st.session_state.feedback = None # 用于存 "答对了/错了" 的提示

# ==========================================
# 👤 3. 用户登录 (简化版)
# ==========================================
def login_page():
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    st.image("https://cdn-icons-png.flaticon.com/512/3408/3408545.png", width=120)
    st.title("Math Master")
    st.caption("快乐奥数，每天进步一点点！")
    
    # 获取用户列表
    try:
        users = supabase.table("users").select("*").execute().data
        user_map = {u['nickname']: u for u in users}
        selected_name = st.selectbox("请选择你的角色", list(user_map.keys()))
        
        if st.button("🚀 开始冒险"):
            st.session_state.user = user_map[selected_name]
            # 刷新金币
            st.session_state.user_coins = st.session_state.user['coins']
            st.rerun()
    except:
        st.error("连接服务器失败，请检查网络")

# ==========================================
# 🎮 4. 游戏主逻辑
# ==========================================

# --- A. 抽取题目 ---
def start_quiz():
    # 随机抽取 5 道题 (商业逻辑：根据用户等级推题，这里先由简单随机代替)
    response = supabase.table("questions").select("*").execute()
    all_questions = response.data
    if len(all_questions) < 5:
        st.error("题库题目不够啦！快叫爸爸去录题！")
        return
    
    st.session_state.quiz_data = random.sample(all_questions, 5)
    st.session_state.quiz_active = True
    st.session_state.current_q_index = 0
    st.session_state.score = 0
    st.session_state.feedback = None
    st.rerun()

# --- B. 提交答案处理 ---
def check_answer(user_input, correct_answer, explanation, question_id):
    # 去除空格，忽略大小写
    is_correct = str(user_input).strip() == str(correct_answer).strip()
    
    # 记录日志 (Practice Logs)
    log_data = {
        "user_id": st.session_state.user['id'],
        "question_id": question_id,
        "user_answer": str(user_input),
        "is_correct": is_correct,
        "time_taken": 30 # 暂时写死，以后可以做计时器
    }
    supabase.table("practice_logs").insert(log_data).execute()
    
    if is_correct:
        st.session_state.score += 1
        st.session_state.feedback = {"type": "success", "msg": "🎉 太棒了！答对啦！"}
        st.toast("金币 +10 💰")
    else:
        # 记录错题本
        try:
            # 尝试更新错题次数+1
            # (注意：真实商业代码这里要用 upsert 逻辑，Supabase python SDK 的 upsert 写法略有不同，这里简化处理)
            supabase.table("mistakes").insert({
                "user_id": st.session_state.user['id'],
                "question_id": question_id,
                "error_count": 1
            }).execute()
        except:
            pass # 如果已经存在，就不报错了（简化逻辑）
            
        st.session_state.feedback = {"type": "error", "msg": f"💡 再接再厉！解析：{explanation}"}

# --- C. 渲染做题界面 ---
def render_quiz():
    q_index = st.session_state.current_q_index
    total_q = len(st.session_state.quiz_data)
    
    # 1. 进度条
    progress = (q_index / total_q)
    st.progress(progress)
    st.caption(f"第 {q_index + 1} / {total_q} 关")
    
    question = st.session_state.quiz_data[q_index]
    
    # 2. 题目卡片
    st.markdown(f"""
    <div class="question-card">
        <h3>{question['content']}</h3>
    </div>
    """, unsafe_allow_html=True)
    
    # 3. 答题区
    if st.session_state.feedback is None:
        # 还没答题
        with st.form(key=f"q_{q_index}"):
            if question['type'] == 'choice' and question['options']:
                user_ans = st.radio("请选择：", question['options'])
            else:
                user_ans = st.text_input("你的答案是？", placeholder="在此输入数字...")
            
            submit = st.form_submit_button("⚡️ 提交答案")
            
            if submit:
                check_answer(user_ans, question['answer'], question['explanation'], question['id'])
                st.rerun()
    else:
        # 已经答完，显示反馈
        fb = st.session_state.feedback
        if fb['type'] == 'success':
            st.success(fb['msg'])
            st.balloons()
        else:
            st.error(fb['msg'])
            
        # 下一题按钮
        if st.button("➡️ 继续挑战"):
            if q_index + 1 < total_q:
                st.session_state.current_q_index += 1
                st.session_state.feedback = None
                st.rerun()
            else:
                finish_quiz()

# --- D. 结算界面 ---
def finish_quiz():
    st.session_state.quiz_active = False
    final_score = st.session_state.score
    total = len(st.session_state.quiz_data)
    earned_coins = final_score * 10
    
    # 更新金币到数据库
    new_coins = st.session_state.user_coins + earned_coins
    supabase.table("users").update({"coins": new_coins}).eq("id", st.session_state.user['id']).execute()
    st.session_state.user_coins = new_coins # 更新本地缓存
    
    # 结算动画
    st.markdown("<br>", unsafe_allow_html=True)
    if final_score == total:
        st.markdown("## 🏆 全对！奥数小天才！")
        st.image("https://cdn-icons-png.flaticon.com/512/864/864837.png", width=150)
    elif final_score >= total/2:
        st.markdown("## 👍 很不错！继续加油！")
    else:
        st.markdown("## 💪 别灰心，复习一下错题！")
        
    st.metric("本局得分", f"{final_score} / {total}")
    st.metric("获得金币", f"+ {earned_coins} 💰")
    
    if st.button("🏠 回到主页"):
        st.rerun()

# ==========================================
# 📱 主程序入口
# ==========================================
if "user" not in st.session_state:
    login_page()
else:
    # 顶部状态栏
    c1, c2, c3 = st.columns([2, 1, 1])
    c1.markdown(f"### Hi, {st.session_state.user['nickname']}")
    c2.metric("金币", st.session_state.user_coins)
    c3.metric("等级", "Lv.1")
    st.divider()

    if not st.session_state.quiz_active:
        # 首页 Dashboard
        col1, col2 = st.columns(2)
        with col1:
            st.info("🔥 每日挑战")
            st.caption("随机 5 道题，保持手感")
            if st.button("⚔️ 开始挑战", type="primary"):
                start_quiz()
        with col2:
            st.warning("🏥 我的错题")
            st.caption("消灭错题，快速提分")
            st.button("💊 错题特训 (开发中)", disabled=True)
            
        st.image("https://cdn-icons-png.flaticon.com/512/3081/3081329.png", use_column_width=True)
        
    else:
        # 做题中
        render_quiz()