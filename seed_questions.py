import sys
import io

# 修复终端输出编码问题 (防止 Windows 下打印中文报错)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from supabase import create_client

# ==========================================
# ⚡️ 配置 (你的 Supabase)
# ==========================================
SUPABASE_URL = "https://fohuvfuhrtdurmnqvrty.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZvaHV2ZnVocnRkdXJtbnF2cnR5Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjY5ODEwNjksImV4cCI6MjA4MjU1NzA2OX0.FkkJGaI4yt6YnkqINMgtHYnRhJBObRysYbVZh-HuUPQ"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ==========================================
# 📚 三年级奥数精选题库 (20题)
# ==========================================
questions_data = [
    # --- 1. 和差倍问题 ---
    {
        "grade": 3, "category": "Calculation", "type": "fill", "difficulty": 2,
        "content": "小明和小红一共有 20 个苹果，小明比小红多 4 个。问小明有几个苹果？",
        "answer": "12",
        "explanation": "解析：(和+差)÷2=大数。 (20+4)÷2 = 12个。"
    },
    {
        "grade": 3, "category": "Calculation", "type": "fill", "difficulty": 3,
        "content": "爸爸买回一些鸭蛋和鸡蛋，鸭蛋的个数是鸡蛋的 3 倍，鸭蛋比鸡蛋多 12 个。问鸭蛋有多少个？",
        "answer": "18",
        "explanation": "解析：差倍问题。差÷(倍数-1)=小数。12÷(3-1)=6(鸡蛋)，鸭蛋是 6×3=18个。"
    },
    
    # --- 2. 找规律 ---
    {
        "grade": 3, "category": "Logic", "type": "fill", "difficulty": 2,
        "content": "找规律填数：1，4，9，16，( )，36。",
        "answer": "25",
        "explanation": "解析：这是平方数列。1x1=1, 2x2=4, ... 5x5=25。"
    },
    {
        "grade": 3, "category": "Logic", "type": "fill", "difficulty": 3,
        "content": "找规律填数：1，2，4，7，11，( )。",
        "answer": "16",
        "explanation": "解析：相邻两数的差分别是 1, 2, 3, 4，所以下一个差是 5。11+5=16。"
    },
    {
        "grade": 3, "category": "Logic", "type": "fill", "difficulty": 4,
        "content": "找规律：1，1，2，3，5，8，( )。",
        "answer": "13",
        "explanation": "解析：斐波那契数列，前两个数相加等于后一个数。5+8=13。"
    },

    # --- 3. 鸡兔同笼与假设法 ---
    {
        "grade": 3, "category": "Logic", "type": "fill", "difficulty": 3,
        "content": "笼子里有鸡和兔子共 10 只，数一数腿共有 28 条。问兔子有几只？",
        "answer": "4",
        "explanation": "解析：假设全是鸡，10×2=20条腿，少了8条。一只兔比一只鸡多2条腿，8÷2=4只兔。"
    },
    {
        "grade": 3, "category": "Logic", "type": "fill", "difficulty": 3,
        "content": "10张纸币，由 2元 和 5元 组成，共 32 元。问 5元 纸币有几张？",
        "answer": "4",
        "explanation": "解析：假设全是2元，10×2=20元，少了12元。一张5元比2元多3元，12÷3=4张。"
    },

    # --- 4. 年龄问题 ---
    {
        "grade": 3, "category": "Calculation", "type": "fill", "difficulty": 3,
        "content": "今年妈妈 32 岁，儿子 4 岁。几年后，妈妈的年龄是儿子的 3 倍？",
        "answer": "10",
        "explanation": "解析：年龄差不变。差是 32-4=28岁。当倍数是3倍时，差是2倍。28÷2=14岁(儿子那时的年龄)。14-4=10年后。"
    },
    {
        "grade": 3, "category": "Calculation", "type": "fill", "difficulty": 2,
        "content": "小明今年 8 岁，爸爸今年 36 岁。当小明 18 岁时，爸爸多少岁？",
        "answer": "46",
        "explanation": "解析：两人一起长大，过了 18-8=10年。爸爸也长10岁，36+10=46岁。"
    },

    # --- 5. 巧算与速算 ---
    {
        "grade": 3, "category": "Calculation", "type": "fill", "difficulty": 2,
        "content": "计算：125 × 8 × 7 =",
        "answer": "7000",
        "explanation": "解析：看到 125 就找 8。125×8=1000，1000×7=7000。"
    },
    {
        "grade": 3, "category": "Calculation", "type": "fill", "difficulty": 3,
        "content": "计算：99 + 999 + 9999 =",
        "answer": "11097",
        "explanation": "解析：凑整法。(100-1) + (1000-1) + (10000-1) = 11100 - 3 = 11097。"
    },

    # --- 6. 周期问题 ---
    {
        "grade": 3, "category": "Logic", "type": "fill", "difficulty": 3,
        "content": "今天是星期一，再过 20 天是星期几？",
        "answer": "7",
        "explanation": "解析：一星期7天。20 ÷ 7 = 2 ... 6。星期一往后推6天，是星期日(填7)。"
    },
    {
        "grade": 3, "category": "Logic", "type": "choice", "difficulty": 2,
        "content": "有一串彩灯按“红、黄、蓝、红、黄、蓝……”排列，第 25 盏灯是什么颜色？",
        "answer": "红",
        "options": ["红", "黄", "蓝"],
        "explanation": "解析：周期是3。25 ÷ 3 = 8 ... 1。余数是1，所以是每组的第1个颜色：红色。"
    },

    # --- 7. 植树问题 ---
    {
        "grade": 3, "category": "Geometry", "type": "fill", "difficulty": 3,
        "content": "在一条长 20 米的绳子上挂气球，从头到尾每隔 5 米挂一个。一共挂了多少个气球？",
        "answer": "5",
        "explanation": "解析：两端都挂。段数 = 20÷5=4段。个数 = 段数 + 1 = 5个。"
    },
    {
        "grade": 3, "category": "Geometry", "type": "fill", "difficulty": 4,
        "content": "时钟敲 3 下需要 4 秒。那么敲 6 下需要几秒？",
        "answer": "10",
        "explanation": "解析：敲3下有2个间隔，4÷2=2秒(一个间隔)。敲6下有5个间隔，5×2=10秒。"
    },

    # --- 8. 还原问题 (倒推法) ---
    {
        "grade": 3, "category": "Logic", "type": "fill", "difficulty": 4,
        "content": "一个数减去 5，乘以 4，除以 2，最后等于 10。这个数是多少？",
        "answer": "10",
        "explanation": "解析：倒推。10 × 2 = 20; 20 ÷ 4 = 5; 5 + 5 = 10。"
    },

    # --- 9. 组合与逻辑 ---
    {
        "grade": 3, "category": "Combo", "type": "fill", "difficulty": 3,
        "content": "用 1、2、3 三个数字，可以组成多少个不同的三位数？",
        "answer": "6",
        "explanation": "解析：百位有3种选法，十位有2种，个位有1种。3×2×1=6个。"
    },
    {
        "grade": 3, "category": "Combo", "type": "fill", "difficulty": 3,
        "content": "小红有 3 件上衣和 4 条裤子，她有多少种不同的穿法？",
        "answer": "12",
        "explanation": "解析：乘法原理。3 × 4 = 12种。"
    },
    
    # --- 10. 等量代换 ---
    {
        "grade": 3, "category": "Logic", "type": "fill", "difficulty": 3,
        "content": "1 只猪的重量 = 2 只羊；1 只羊 = 4 只鸡。问 1 只猪等于几只鸡？",
        "answer": "8",
        "explanation": "解析：1猪 = 2羊 = 2 × (4鸡) = 8只鸡。"
    }
]

# ==========================================
# 🚀 执行导入
# ==========================================
def seed_database():
    print(f"📦 准备导入 {len(questions_data)} 道奥数题...")
    
    success_count = 0
    fail_count = 0
    
    for q in questions_data:
        try:
            # 检查是否重复 (根据题目内容)
            existing = supabase.table("questions").select("*").eq("content", q["content"]).execute()
            if existing.data:
                print(f"⚠️ 跳过重复: {q['content'][:10]}...")
            else:
                supabase.table("questions").insert(q).execute()
                print(f"✅ 导入成功: {q['content'][:10]}...")
                success_count += 1
        except Exception as e:
            print(f"❌ 导入失败: {e}")
            fail_count += 1
            
    print("-" * 30)
    print(f"🎉 任务完成！成功: {success_count}, 跳过: {len(questions_data) - success_count - fail_count}, 失败: {fail_count}")
    print("💡 现在去 admin.py 刷新一下，就能看到满满的题库了！")

if __name__ == "__main__":
    seed_database()