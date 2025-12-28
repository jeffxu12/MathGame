import json, time, os

def run_game():
    # 自动定位文件路径，防止孩子运行环境路径不对
    base_path = os.path.dirname(__file__)
    json_path = os.path.join(base_path, 'questions.json')
    log_path = os.path.join(base_path, '学习记录.txt')

    if not os.path.exists(json_path):
        print("⚠️ 找不到题库文件 questions.json，请联系爸爸！")
        return

    with open(json_path, 'r', encoding='utf-8') as f:
        all_questions = json.load(f)

    print("========================================")
    print("🚀 欢迎登录【奥数神殿：远程挑战系统】")
    print("爸爸在远方看着你的战绩哦！加油！")
    print("========================================")
    
    day_input = input("今天要挑战第几天？(请输入数字): ")
    try:
        current_day = int(day_input)
    except:
        print("输入错误，请输入数字。")
        return

    today_qs = [q for q in all_questions if q.get('day') == current_day]
    
    if not today_qs:
        print(f"第 {current_day} 天的关卡还没解锁，请换一个日子试试。")
        return

    score = 0
    scores_rule = [10, 6, 3, 1, -3]
    logs = []

    for q in today_qs:
        print(f"\n【{q['title']}】 {q['question']}")
        for i in range(5):
            ans = input(f" ╰┈➤ 第 {i+1} 次回答: ")
            if ans == q['answer']:
                p = scores_rule[i]
                print(f" ✅ 棒极了！+{p}分")
                score += p
                logs.append(f"Q{q['id']}:{i+1}次对")
                break
            else:
                if i < 4: print(f" ❌ 锦囊：{q['hints'][i]}")
                else: print(f" 💔 最终答案是 {q['answer']}")

    # 生成汇报文本
    report = f"\n--- 🛰️ 远程战报 ({time.strftime('%m/%d %H:%M')}) ---"
    report += f"\n挑战天数：Day {current_day} | 关卡记录：{' '.join(logs)}"
    report += f"\n今日总分：{score} | 状态：{'🔥 超神' if score > 80 else '💪 继续努力'}"
    
    print(report)
    with open(log_path, 'a', encoding='utf-8') as f:
        f.write(report + "\n")
    print("\n✅ 记录已保存。请把上面的战报复制发给爸爸妈妈！")
    input("\n按回车键退出游戏...")

if __name__ == "__main__":
    run_game()