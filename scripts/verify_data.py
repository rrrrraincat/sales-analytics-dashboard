# sales_dashboard/scripts/verify_data.py
import sqlite3
import pandas as pd
import os

def 验证数据():
    # 使用绝对路径
    项目根路径 = "/Users/ruimantan/Desktop/作品集/销售数据分析看板/企业销售决策支持系统/sales_dashboard"
    数据库路径 = os.path.join(项目根路径, 'data', 'sales.db')
    
    print(f"🔍 检查数据库路径: {数据库路径}")
    print(f"📁 文件是否存在: {os.path.exists(数据库路径)}")
    
    if not os.path.exists(数据库路径):
        print("❌ 数据库文件不存在，请先运行初始化脚本")
        return False
    
    try:
        conn = sqlite3.connect(数据库路径)
        print("✅ 数据库连接成功!")
        
        # 检查表结构
        tables = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table'", conn)
        print("✅ 数据库表:", list(tables['name']))
        
        # 检查数据量
        for table in tables['name']:
            count = pd.read_sql(f"SELECT COUNT(*) as 记录数 FROM {table}", conn)
            print(f"✅ {table}: {count.iloc[0,0]} 条记录")
        
        # 查看数据样本
        print("\n📊 销售数据样本:")
        sample = pd.read_sql("SELECT * FROM 产品销售 ORDER BY RANDOM() LIMIT 3", conn)
        print(sample)
        
        conn.close()
        print("🎉 数据验证完成!")
        return True
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False

if __name__ == "__main__":
    验证数据()