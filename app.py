import streamlit as st
import json
import datetime

# --- 配置与数据加载 ---
st.set_page_config(page_title="奥数神殿云端版", layout="centered")

def load_data():
    with open('questions.json', 'r', encoding='utf-8') as f:
        return json.load(f)

# 简单的模拟数据库（实际可保存为CSV或JSON）
def save_score(user, day, score, log):
    with open('cloud_scores.csv', 'a', encoding='utf-8') as f:
        f.write(f"{datetime.datetime.now()},{user},{day},{score},{log}\n")

# --- 登录界面 ---
if 'login' not in st.session_state:
    st.title("🛡️ 奥数神殿入口")
    user = st.text_input("用户名")
    pwd = st.text_input("密码", type="password")
    if st.button("进入神殿"):
        if pwd == "123456": # 爸爸可以修改密码
            st.session_state.login = True
            st.session_state.user = user
            st.rerun()
else:
    # --- 游戏主界面 ---
    st.sidebar.title(f"🦸‍♂️ 英雄: {st.session_state.user}")
    menu = st.sidebar.radio("菜单", ["开始挑战", "战绩查看"])

    questions = load_data()

    if menu == "开始挑战":
        day = st.number_input("选择挑战天数", min_value=1, max_value=200, step=1)
        today_qs = [q for q in questions if q['day'] == day]

        if today_qs:
            st.header(f"📅 第 {day} 天挑战")
            total_score = 0
            
            for idx, q in enumerate(today_qs):
                st.subheader(f"第 {idx+1} 题: {q['title']}")
                st.write(q['question'])
                
                # 记录每道题的尝试次数
                key = f"q_{day}_{idx}"
                if key not in st.session_state:
                    st.session_state[key] = 0
                
                user_ans = st.text_input("请输入答案", key=f"input_{key}")
                
                if st.button("提交答案", key=f"btn_{key}"):
                    st.session_state[key] += 1
                    attempts = st.session_state[key]
                    
                    if user_ans == q['answer']:
                        scores = [10, 6, 3, 1, -3]
                        p = scores[min(attempts-1, 4)]
                        st.success(f"✅ 正确！第{attempts}次成功，获得 {p} 分")
                        save_score(st.session_state.user, day, p, f"Q{idx+1} OK")
                    else:
                        if attempts < 5:
                            st.warning(f"❌ 不对哦！锦囊提示：{q['hints'][attempts-1]}")
                        else:
                            st.error(f"💔 机会用完，答案是：{q['answer']}")

    elif menu == "战绩查看":
        st.header("📈 英雄成长记录")
        if os.path.exists('cloud_scores.csv'):
            with open('cloud_scores.csv', 'r') as f:
                st.text(f.read())
        else:
            st.write("暂无记录，快去挑战吧！")