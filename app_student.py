import streamlit as st
import pandas as pd
from supabase import create_client, Client
import time
import random

# ==========================================
# 🎨 0. 魔法 UI 配置 (果冻风格 + 沉浸模式)
# ==========================================
st.set_page_config(page_title="Math Master", page_icon="🦁", layout="centered")

st.markdown("""
<style>
    /* 1. 全局背景：柔和护眼蓝 */
    .stApp {
        background-color: #E0F7FA;
    }
    
    /* 2. 隐藏 Streamlit 默认菜单 (沉浸式体验) */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* 3. 核心卡片：3D果冻效果 */
    .question-card {
        background-color: white;
        padding: 30px;
        border-radius: 20px;
        box-shadow: 0 8px 0px #b2ebf2; 
        border: 2px solid #4DD0E1;
        margin-bottom: 20px;
        text-align: center;
    }
    
    /* 4. 大标题字体 */
    h1 {
        color: #006064;
        font-family: 'Comic Sans MS', 'Chalkboard SE', sans-serif;
    }
    
    /* 5. 输入框美化 */
    .stTextInput>div>div>input {
        text-align: center;
        font-size: 24px;
        border-radius: 12px;
        border: 2px solid #4DD0E1;
        color: #006064;
    }
    
    /* 6. 按钮变身：活力橙色大按钮 */
    .stButton>button {
        width: 100%;
        background-color: #FF7043;
        color: white;
        font-size: 20px;
        font-weight: bold;
        border-radius: 15px;
        border: none;
        box-shadow: 0 5px 0 #D84315;
        padding: 12px 0;
        transition: all 0.1s;
    }
    .stButton>button:active {
        transform: translateY(5px);
        box-shadow: none;
    }
    
    /* 7. 进度条颜色 */
    .stProgress > div > div > div > div {
        background-color: #FFCA28;
    }
    
    /* 8. 勋章区域 */
    .badge-area {
        background: white;
        padding: 10px;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 10px;
        border: 1px dashed #ccc;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# ⚡️ 1. 连接大脑 (智能重连版) - 修复连接失败问题
# ==========================================
SUPABASE_URL = "https://fohuvfuhrtdurmnqvrty.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZvaHV2ZnVocnRkdXJtbnF2cnR5Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjY5ODEwNjksImV4cCI6MjA4MjU1NzA2OX0.FkkJGaI4yt6YnkqINMgtHYnRhJBObRysYbVZh-HuUPQ"

@st.cache_resource(ttl=3600) # 缓存1小时，过期自动刷新
def init_connection():
    try:
        # 1. 尝试建立客户端
        client = create_client(SUPABASE_URL, SUPABASE_KEY)
        # 2. 关键步骤：发送一个微小的 Ping 请求，测试连接是否真的通
        client.table("users").select("id").limit(1).execute()
        return client
    except Exception as e:
        print(f"⚠️ 连接休眠中，正在自动唤醒... ({e})")
        # 3. 如果 Ping 失败，清除缓存
        st.cache_resource.clear()
        # 4. 强制重新创建连接
        return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_connection()

# ==========================================
# 🧠 2. 游戏状态机
# ==========================================
if "quiz_active" not in st.session_state:
    st.session_state.quiz_active = False
    st.session_state.current_q_index = 0
    st.session_state.score = 0
    st.session_state.quiz_data = []
    st.session_state.user_coins = 0
    st.session_state.feedback = None 

# ==========================================
# 🎵 3. 辅助函数：勋章与音效
# ==========================================
def get_user_badge(coins):
    if coins < 100: return "🌱 奥数萌芽"
    elif coins < 300: return "🥉 青铜选手"
    elif coins < 600: return "🥈 白银学霸"
    elif coins < 1000: return "🥇 黄金大神"
    else: return "🏆 最强王者"

# ==========================================
# 👤 4. 用户登录
# ==========================================
def login_page():
    st.markdown("<br><br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1,2,1])
    with c2:
        st.image("https://cdn-icons-png.flaticon.com/512/3408/3408545.png", width=100)
        st.title("Math Master")
        st.caption("每天 5 道题，快乐学奥数")
        
        try:
            # 获取用户列表
            users = supabase.table("users").select("*").execute().data
            if not users:
                st.error("数据库为空，请运行 seed 脚本")
                return
                
            user_map = {u['nickname']: u for u in users}
            selected_name = st.selectbox("请选择你的角色", list(user_map.keys()))
            
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🚀 开始冒险"):
                st.session_state.user = user_map[selected_name]
                st.session_state.user_coins = st.session_state.user['coins']
                st.rerun()
        except Exception as e:
            st.error(f"连接中... 请稍后重试 ({e})")
            # 这里的 Cache clear 是为了防止死循环，如果真连不上，下次刷新页面再试
            st.cache_resource.clear()

# ==========================================
# 🎮 5. 游戏逻辑
# ==========================================
def start_quiz():
    try:
        response = supabase.table("questions").select("*").execute()
        all_questions = response.data
        if len(all_questions) < 5:
            st.error("题库题目不够啦！快去录题！")
            return
        st.session_state.quiz_data = random.sample(all_questions, 5)
        st.session_state.quiz_active = True
        st.session_state.current_q_index = 0
        st.session_state.score = 0
        st.session_state.feedback = None
        st.rerun()
    except Exception as e:
        st.error(f"启动失败: {e}")
        st.cache_resource.clear()

def check_answer(user_input, correct_answer, explanation, question_id):
    # 答案清洗：去空格，统一转字符串
    is_correct = str(user_input).strip().lower() == str(correct_answer).strip().lower()
    
    # 记录日志
    try:
        supabase.table("practice_logs").insert({
            "user_id": st.session_state.user['id'],
            "question_id": question_id,
            "user_answer": str(user_input),
            "is_correct": is_correct,
            "time_taken": 30
        }).execute()
    except: pass
    
    if is_correct:
        st.session_state.score += 1
        st.session_state.feedback = {"type": "success", "msg": "🎉 答对啦！金币 +10"}
        st.toast("🎉 BINGO! 金币 +10")
    else:
        # 记录错题
        try:
            supabase.table("mistakes").insert({
                "user_id": st.session_state.user['id'],
                "question_id": question_id,
                "error_count": 1
            }).execute()
        except: pass
        st.session_state.feedback = {"type": "error", "msg": f"💡 答案是 {correct_answer}。解析：{explanation}"}

def render_quiz():
    q_index = st.session_state.current_q_index
    total_q = len(st.session_state.quiz_data)
    question = st.session_state.quiz_data[q_index]
    
    # 进度与关卡显示
    st.progress((q_index) / total_q)
    c1, c2 = st.columns([3, 1])
    c1.caption(f"关卡 {q_index + 1} / {total_q}")
    c2.caption(f"得分: {st.session_state.score}")
    
    # 题目展示
    st.markdown(f"""
    <div class="question-card">
        <h3>{question['content']}</h3>
    </div>
    """, unsafe_allow_html=True)
    
    # 答题区
    if st.session_state.feedback is None:
        with st.form(key=f"q_{q_index}"):
            if question['type'] == 'choice' and question['options']:
                user_ans = st.radio("请选择：", question['options'])
            else:
                user_ans = st.text_input("在此输入答案", placeholder="例如: 42")
                
            st.markdown("<small style='color:#888; display:block; text-align:center;'>💡 输入后按 Ctrl+Enter 可直接提交</small>", unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)
            
            submit = st.form_submit_button("⚡️ 确定")
            
            if submit:
                if not user_ans:
                    st.warning("请先输入答案哦！")
                else:
                    check_answer(user_ans, question['answer'], question['explanation'], question['id'])
                    st.rerun()
    else:
        # 反馈区
        fb = st.session_state.feedback
        
        if fb['type'] == 'success':
            st.success(fb['msg'])
            st.balloons()
            # 播放成功音效 (需浏览器支持)
            st.audio("https://codeskulptor-demos.commondatastorage.googleapis.com/pang/pop.mp3", autoplay=True)
        else:
            st.error(fb['msg'])
            # 播放失败音效
            st.audio("https://codeskulptor-demos.commondatastorage.googleapis.com/assets/soundboard/explode.wav", autoplay=True)

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("➡️ 下一关", type="primary"):
            if q_index + 1 < total_q:
                st.session_state.current_q_index += 1
                st.session_state.feedback = None
                st.rerun()
            else:
                finish_quiz()

def finish_quiz():
    st.session_state.quiz_active = False
    score = st.session_state.score
    total = len(st.session_state.quiz_data)
    coins = score * 10
    
    # 更新金币
    try:
        new_total = st.session_state.user_coins + coins
        supabase.table("users").update({"coins": new_total}).eq("id", st.session_state.user['id']).execute()
        st.session_state.user_coins = new_total
    except: pass
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown(f"<h2 style='text-align:center'>挑战完成！</h2>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1,1,1])
    with col2:
        if score == total:
            st.image("https://cdn-icons-png.flaticon.com/512/864/864837.png")
            st.balloons()
        else:
            st.image("https://cdn-icons-png.flaticon.com/512/1792/1792931.png")
    
    st.metric("本次得分", f"{score} / {total}", delta=f"+{coins} 金币")
    
    if st.button("🏠 返回主页"):
        st.rerun()

# ==========================================
# 📱 主程序入口
# ==========================================
if "user" not in st.session_state:
    login_page()
else:
    # 顶部状态栏 (显示勋章)
    badge = get_user_badge(st.session_state.user_coins)
    
    # 使用 container 包裹头部，增加一点间距
    with st.container():
        c1, c2, c3 = st.columns([2, 1, 1])
        c1.markdown(f"### 🦁 Hi, {st.session_state.user['nickname']}")
        c2.metric("金币", st.session_state.user_coins)
        c3.markdown(f"<div class='badge-area'><b>{badge}</b></div>", unsafe_allow_html=True)
    
    st.divider()

    if not st.session_state.quiz_active:
        # 首页 Dashboard
        st.info("🔥 每日挑战")
        st.markdown("**规则**：随机抽取 5 道题，每题 10 金币。全对有惊喜！")
        
        if st.button("⚔️ 开始挑战", type="primary"):
            start_quiz()
            
        st.markdown("<br>", unsafe_allow_html=True)
        with st.expander("📖 游戏说明"):
            st.write("1. 答对获得金币，答错会记录到错题本。")
            st.write("2. 金币可以用来升级你的勋章。")
            st.write("3. 遇到难题可以问爸爸！")
            
        st.image("https://cdn-icons-png.flaticon.com/512/3081/3081329.png", use_column_width=True)
    else:
        render_quiz()