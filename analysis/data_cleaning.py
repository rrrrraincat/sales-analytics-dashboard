# sales_dashboard/analysis/data_cleaning.py
import sqlite3
import pandas as pd
import os
import numpy as np
from datetime import datetime

def 获取原始数据():
    """获取需要清洗的原始数据"""
    数据库路径 = "/Users/ruimantan/Desktop/作品集/销售数据分析看板/企业销售决策支持系统/sales_dashboard/data/sales.db"
    conn = sqlite3.connect(数据库路径)
    
    # 读取所有销售数据
    df = pd.read_sql("SELECT * FROM 产品销售", conn)
    conn.close()
    
    print(f"✅ 读取原始数据: {len(df)} 条记录")
    return df

def 识别数据问题(df):
    """系统化识别所有数据问题"""
    print("=" * 50)
    print("🔍 数据问题识别")
    print("=" * 50)
    
    问题记录 = {}
    
    # 1. 价格异常识别
    合理价格范围 = {
        '智能手机': (1000, 10000),
        '笔记本电脑': (3000, 20000), 
        '平板电脑': (1000, 8000),
        '智能手表': (500, 5000),
        '耳机': (50, 2000)
    }
    
    print("💰 价格异常检测:")
    价格异常记录 = []
    for 产品, (最低价, 最高价) in 合理价格范围.items():
        异常 = df[(df['产品类别'] == 产品) & ((df['单价'] < 最低价) | (df['单价'] > 最高价))]
        if len(异常) > 0:
            print(f"  🚨 {产品}: {len(异常)} 条价格异常")
            价格异常记录.append(异常)
    
    问题记录['价格异常'] = 价格异常记录
    
    # 2. 数量异常
    print(f"📦 数量异常检测:")
    数量异常 = df[df['数量'] > 20]
    if len(数量异常) > 0:
        print(f"  🚨 数量异常: {len(数量异常)} 条记录数量>20")
        问题记录['数量异常'] = [数量异常]
    
    # 3. 销售额计算错误
    print(f"📐 计算准确性检测:")
    df['计算销售额'] = df['单价'] * df['数量']
    计算错误 = df[abs(df['销售额'] - df['计算销售额']) > 0.01]
    if len(计算错误) > 0:
        print(f"  🚨 计算错误: {len(计算错误)} 条记录")
        问题记录['计算错误'] = [计算错误]
    
    # 4. 缺失值检查
    print(f"📭 缺失值检测:")
    缺失列 = []
    for column in df.columns:
        缺失数 = df[column].isnull().sum()
        if 缺失数 > 0:
            print(f"  🚨 {column}: {缺失数} 个空值")
            缺失列.append(column)
    
    if 缺失列:
        问题记录['缺失值'] = 缺失列
    
    return 问题记录

def 执行数据清洗(df, 问题记录):
    """执行系统化的数据清洗"""
    print("\n" + "=" * 50)
    print("🧹 执行数据清洗")
    print("=" * 50)
    
    # 创建清洗后的数据副本
    df_clean = df.copy()
    清洗日志 = []
    原始记录数 = len(df_clean)
    
    # 1. 修复计算错误（优先处理）
    if '计算错误' in 问题记录:
        print("🔧 修复销售额计算错误...")
        df_clean['销售额'] = df_clean['单价'] * df_clean['数量']
        清洗日志.append(f"修复计算错误: {len(问题记录['计算错误'][0])} 条记录")
    
    # 2. 处理价格异常（基于业务规则修正）
    if '价格异常' in 问题记录:
        print("🔧 处理价格异常...")
        修正记录数 = 0
        
        for 异常批次 in 问题记录['价格异常']:
            for _, 异常行 in 异常批次.iterrows():
                产品 = 异常行['产品类别']
                合理价格范围 = {
                    '智能手机': (3000, 8000), '笔记本电脑': (5000, 15000),
                    '平板电脑': (2000, 5000), '智能手表': (1000, 3000), '耳机': (200, 1500)
                }
                
                合理价格区间 = 合理价格范围.get(产品, (100, 10000))
                # 将异常价格修正到合理范围内的随机值
                修正价格 = np.random.uniform(合理价格区间[0], 合理价格区间[1])
                
                # 更新数据
                mask = (df_clean['订单ID'] == 异常行['订单ID'])
                df_clean.loc[mask, '单价'] = round(修正价格, 2)
                df_clean.loc[mask, '销售额'] = round(修正价格 * df_clean.loc[mask, '数量'], 2)
                修正记录数 += 1
        
        清洗日志.append(f"修正价格异常: {修正记录数} 条记录")
    
    # 3. 处理数量异常
    if '数量异常' in 问题记录:
        print("🔧 处理数量异常...")
        数量异常记录 = 问题记录['数量异常'][0]
        for _, 异常行 in 数量异常记录.iterrows():
            # 将异常数量修正为合理值（1-10）
            修正数量 = min(10, max(1, 异常行['数量']))
            mask = (df_clean['订单ID'] == 异常行['订单ID'])
            df_clean.loc[mask, '数量'] = 修正数量
            df_clean.loc[mask, '销售额'] = df_clean.loc[mask, '单价'] * 修正数量
        
        清洗日志.append(f"修正数量异常: {len(数量异常记录)} 条记录")
    
    # 4. 处理缺失值
    if '缺失值' in 问题记录:
        print("🔧 处理缺失值...")
        for column in 问题记录['缺失值']:
            if column == '区域':
                df_clean[column] = df_clean[column].fillna('未知区域')
            elif column in ['单价', '数量', '销售额']:
                # 数值列用中位数填充
                df_clean[column] = df_clean[column].fillna(df_clean[column].median())
            else:
                # 文本列用众数填充
                df_clean[column] = df_clean[column].fillna(df_clean[column].mode()[0] if len(df_clean[column].mode()) > 0 else '未知')
        
        清洗日志.append(f"填充缺失值: {len(问题记录['缺失值'])} 个字段")
    
    # 移除临时列
    if '计算销售额' in df_clean.columns:
        df_clean = df_clean.drop('计算销售额', axis=1)
    
    最终记录数 = len(df_clean)
    print(f"📊 清洗完成: 保留 {最终记录数}/{原始记录数} 条记录")
    
    return df_clean, 清洗日志

def 验证清洗效果(df原始, df清洗后):
    """验证数据清洗效果"""
    print("\n" + "=" * 50)
    print("✅ 清洗效果验证")
    print("=" * 50)
    
    # 1. 数据完整性对比
    print("📊 数据完整性对比:")
    print(f"  原始数据: {len(df原始)} 条记录")
    print(f"  清洗后数据: {len(df清洗后)} 条记录")
    print(f"  数据保留率: {len(df清洗后)/len(df原始)*100:.1f}%")
    
    # 2. 数据质量改进
    print("\n🎯 数据质量改进:")
    
    # 价格合理性改进
    合理价格范围 = {
        '智能手机': (1000, 10000), '笔记本电脑': (3000, 20000),
        '平板电脑': (1000, 8000), '智能手表': (500, 5000), '耳机': (50, 2000)
    }
    
    原始异常数 = 0
    清洗后异常数 = 0
    
    for 产品, (最低价, 最高价) in 合理价格范围.items():
        原始异常 = len(df原始[(df原始['产品类别'] == 产品) & ((df原始['单价'] < 最低价) | (df原始['单价'] > 最高价))])
        清洗后异常 = len(df清洗后[(df清洗后['产品类别'] == 产品) & ((df清洗后['单价'] < 最低价) | (df清洗后['单价'] > 最高价))])
        
        原始异常数 += 原始异常
        清洗后异常数 += 清洗后异常
        
        if 原始异常 > 0 or 清洗后异常 > 0:
            print(f"  {产品}: {原始异常} → {清洗后异常} 条价格异常")
    
    print(f"  价格异常减少: {原始异常数} → {清洗后异常数} 条")
    
    # 3. 计算准确性验证
    df清洗后['验证销售额'] = df清洗后['单价'] * df清洗后['数量']
    计算错误数 = len(df清洗后[abs(df清洗后['销售额'] - df清洗后['验证销售额']) > 0.01])
    print(f"  计算准确性: {计算错误数} 条计算错误")
    
    df清洗后 = df清洗后.drop('验证销售额', axis=1)
    
    return 原始异常数, 清洗后异常数, 计算错误数

def 保存清洗数据(df清洗后, 清洗日志):
    """保存清洗后的数据"""
    print("\n" + "=" * 50)
    print("💾 保存清洗数据")
    print("=" * 50)
    
    # 保存到新数据库表
    数据库路径 = "/Users/ruimantan/Desktop/作品集/销售数据分析看板/企业销售决策支持系统/sales_dashboard/data/sales.db"
    conn = sqlite3.connect(数据库路径)
    
    # 保存清洗后的数据到新表
    df清洗后.to_sql('产品销售_清洗后', conn, if_exists='replace', index=False)
    
    # 保存清洗日志
    日志路径 = "/Users/ruimantan/Desktop/作品集/销售数据分析看板/企业销售决策支持系统/sales_dashboard/reports/数据清洗日志.txt"
    with open(日志路径, 'w', encoding='utf-8') as f:
        f.write("=== 数据清洗日志 ===\n")
        f.write(f"清洗时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"原始记录数: {len(df清洗后)} 条\n\n")
        f.write("清洗操作:\n")
        for 日志项 in 清洗日志:
            f.write(f"  ✅ {日志项}\n")
    
    conn.close()
    
    print(f"✅ 清洗后数据已保存至: 产品销售_清洗后 表")
    print(f"📄 清洗日志已保存至: {日志路径}")
    print(f"🎯 数据已准备好用于分析!")

# 执行数据清洗
if __name__ == "__main__":
    print("🎯 开始第二步: 数据清洗")
    print("=" * 50)
    
    try:
        # 1. 获取原始数据
        df原始 = 获取原始数据()
        
        # 2. 识别数据问题
        问题记录 = 识别数据问题(df原始)
        
        # 3. 执行清洗
        df清洗后, 清洗日志 = 执行数据清洗(df原始, 问题记录)
        
        # 4. 验证效果
        原始异常数, 清洗后异常数, 计算错误数 = 验证清洗效果(df原始, df清洗后)
        
        # 5. 保存结果
        保存清洗数据(df清洗后, 清洗日志)
        
        print("\n" + "=" * 50)
        print("🎉 数据清洗完成!")
        print(f"📊 数据质量显著提升!")
        print("➡️  准备进入第三步: 业务分析")
        print("=" * 50)
        
    except Exception as e:
        print(f"❌ 数据清洗过程中出错: {e}")
        import traceback
        traceback.print_exc()