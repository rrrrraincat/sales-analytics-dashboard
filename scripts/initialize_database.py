#initialize_database
# 创建文件: sales_dashboard/scripts/initialize_database.py
import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def 创建数据库结构():
    """创建真实的业务数据库表结构"""
    conn = sqlite3.connect('sales_dashboard/data/sales.db')
    cursor = conn.cursor()
    
    # 销售团队表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS 销售团队 (
            销售员ID INTEGER PRIMARY KEY,
            姓名 TEXT NOT NULL,
            部门 TEXT,
            入职日期 TEXT,
            基本工资 DECIMAL(10,2)
        )
    ''')
    
    # 产品销售表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS 产品销售 (
            订单ID TEXT PRIMARY KEY,
            销售员ID INTEGER,
            销售员姓名 TEXT,
            产品类别 TEXT,
            单价 DECIMAL(10,2),
            数量 INTEGER,
            销售额 DECIMAL(10,2),
            订单日期 TEXT,
            区域 TEXT,
            客户类型 TEXT,
            FOREIGN KEY (销售员ID) REFERENCES 销售团队(销售员ID)
        )
    ''')
    
    conn.commit()
    return conn

def 生成真实测试数据(conn):
    """生成半真实业务数据"""
    # 销售团队基础数据
    销售团队数据 = [
        (1, '张三', '电子部', '2023-01-15', 8000),
        (2, '李四', '电子部', '2023-03-20', 7500),
        (3, '王五', '服装部', '2024-01-10', 7000),
        (4, '赵六', '家居部', '2024-02-01', 7200),
        (5, '钱七', '电子部', '2024-03-15', 6800)
    ]
    
    cursor = conn.cursor()
    cursor.executemany('INSERT OR REPLACE INTO 销售团队 VALUES (?,?,?,?,?)', 销售团队数据)
    
    # 生成6个月销售数据
    dates = pd.date_range('2025-04-01', '2025-10-15', freq='D')
    records = []
    
    for i, date in enumerate(dates):
        # 每日订单量波动
        daily_orders = max(1, int(np.random.normal(8, 3)))
        
        for j in range(daily_orders):
            销售员 = 销售团队数据[np.random.choice([0,1,2,3,4], p=[0.3, 0.25, 0.2, 0.15, 0.1])]
            销售员ID, 销售员姓名 = 销售员[0], 销售员[1]
            
            产品类别 = np.random.choice(['智能手机', '笔记本电脑', '平板电脑', '智能手表', '耳机'])
            区域 = np.random.choice(['华北', '华东', '华南', '西部'], p=[0.4, 0.3, 0.2, 0.1])
            
            # 真实价格逻辑
            价格映射 = {'智能手机': (3000, 8000), '笔记本电脑': (5000, 15000), 
                     '平板电脑': (2000, 5000), '智能手表': (1000, 3000), '耳机': (200, 1500)}
            单价 = round(np.random.uniform(*价格映射[产品类别]), 2)
            
            # 数量逻辑
            数量 = max(1, int(np.random.poisson(3 if 单价 < 2000 else 1.5)))
            销售额 = 单价 * 数量
            
            # 5%数据异常
            if np.random.random() < 0.05:
                销售额 = 销售额 * 10 if np.random.random() < 0.5 else 销售额 * 0.1
            
            订单ID = f'ORD{date.strftime("%Y%m%d")}{j:03d}'
            
            records.append((
                订单ID, 销售员ID, 销售员姓名, 产品类别, 单价, 数量, 
                销售额, date.strftime('%Y-%m-%d'), 区域, 
                np.random.choice(['新客户', '老客户'], p=[0.4, 0.6])
            ))
    
    # 批量插入销售数据
    cursor.executemany('''
        INSERT OR REPLACE INTO 产品销售 
        VALUES (?,?,?,?,?,?,?,?,?,?)
    ''', records)
    
    conn.commit()
    print(f"✅ 生成销售记录: {len(records)} 条")
    return records

# 执行初始化
if __name__ == "__main__":
    print("=== 开始环境搭建 ===")
    conn = 创建数据库结构()
    生成真实测试数据(conn)
    
    # 验证数据
    df = pd.read_sql('SELECT * FROM 产品销售 LIMIT 5', conn)
    print("✅ 数据样本:")
    print(df)
    
    conn.close()
    print("🎉 环境搭建完成!")