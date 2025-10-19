# sales_dashboard/analysis/data_review.py
import sqlite3
import pandas as pd
import os
import numpy as np
from datetime import datetime

def 获取数据():
    """连接数据库并获取销售数据"""
    数据库路径 = "/Users/ruimantan/Desktop/作品集/销售数据分析看板/企业销售决策支持系统/sales_dashboard/data/sales.db"
    conn = sqlite3.connect(数据库路径)
    
    # 读取所有销售数据
    df = pd.read_sql("SELECT * FROM 产品销售", conn)
    conn.close()
    
    print(f"✅ 成功读取 {len(df)} 条销售记录")
    return df

def 计算数据质量评分(df, 异常记录):
    """基于多维度指标计算真实的数据质量分数"""
    
    评分维度 = {}
    
    # 1. 完整性评分 (权重30%)
    完整性分数 = 0
    for column in df.columns:
        缺失比例 = df[column].isnull().sum() / len(df)
        列完整性 = (1 - 缺失比例) * 100
        完整性分数 += 列完整性
    
    完整性分数 = 完整性分数 / len(df.columns)
    评分维度['完整性'] = 完整性分数
    print(f"📊 完整性评分: {完整性分数:.1f}%")
    
    # 2. 准确性评分 (权重40%)
    # 检查销售额计算准确性
    计算销售额 = df['单价'] * df['数量']
    计算准确率 = (abs(df['销售额'] - 计算销售额) < 0.01).mean() * 100
    评分维度['计算准确性'] = 计算准确率
    print(f"📐 计算准确性: {计算准确率:.1f}%")
    
    # 3. 合理性评分 (权重30%)
    # 基于业务规则的价格合理性
    合理价格范围 = {
        '智能手机': (1000, 10000),
        '笔记本电脑': (3000, 20000), 
        '平板电脑': (1000, 8000),
        '智能手表': (500, 5000),
        '耳机': (50, 2000)
    }
    
    合理记录数 = 0
    for 产品, (最低价, 最高价) in 合理价格范围.items():
        产品数据 = df[df['产品类别'] == 产品]
        合理记录 = 产品数据[(产品数据['单价'] >= 最低价) & (产品数据['单价'] <= 最高价)]
        合理记录数 += len(合理记录)
    
    合理性分数 = (合理记录数 / len(df)) * 100
    评分维度['合理性'] = 合理性分数
    print(f"🎯 价格合理性: {合理性分数:.1f}%")
    
    # 4. 唯一性评分 (额外检查)
    重复记录 = df.duplicated(subset=['订单ID']).sum()
    唯一性分数 = (1 - 重复记录 / len(df)) * 100
    评分维度['唯一性'] = 唯一性分数
    print(f"🔍 唯一性评分: {唯一性分数:.1f}% (重复记录: {重复记录}条)")
    
    # 5. 综合评分 (加权平均)
    权重配置 = {'完整性': 0.25, '计算准确性': 0.35, '合理性': 0.30, '唯一性': 0.10}
    综合分数 = sum(评分维度[维度] * 权重配置[维度] for 维度 in 评分维度)
    
    print(f"\n⭐ 综合数据质量评分: {综合分数:.1f}%")
    
    return 综合分数, 评分维度

def 基础数据审查(df):
    """执行基础的数据质量审查"""
    print("=" * 50)
    print("📊 数据质量审查报告")
    print("=" * 50)
    
    # 1. 基础信息
    print(f"📅 时间范围: {df['订单日期'].min()} 到 {df['订单日期'].max()}")
    print(f"👥 销售员数量: {df['销售员姓名'].nunique()} 人")
    print(f"📦 产品类别: {df['产品类别'].nunique()} 种")
    print(f"🌍 区域数量: {df['区域'].nunique()} 个")
    
    # 2. 数据完整性
    print(f"\n✅ 数据完整性检查:")
    for column in df.columns:
        缺失数 = df[column].isnull().sum()
        print(f"  {column}: {缺失数} 个空值 ({缺失数/len(df)*100:.1f}%)")
    
    return df

def 业务逻辑审查(df):
    """基于业务逻辑的数据审查"""
    print(f"\n🔍 业务逻辑审查:")
    
    # 1. 价格合理性检查
    print(f"💰 价格范围审查:")
    异常记录列表 = []
    
    for 产品 in df['产品类别'].unique():
        价格数据 = df[df['产品类别'] == 产品]['单价']
        产品数量 = len(价格数据)
        
        # 定义合理价格范围
        合理价格范围 = {
            '智能手机': (1000, 10000),
            '笔记本电脑': (3000, 20000), 
            '平板电脑': (1000, 8000),
            '智能手表': (500, 5000),
            '耳机': (50, 2000)
        }
        
        最低价, 最高价 = 合理价格范围.get(产品, (0, 100000))
        价格异常 = df[(df['产品类别'] == 产品) & ((df['单价'] < 最低价) | (df['单价'] > 最高价))]
        
        if len(价格异常) > 0:
            print(f"  🚨 {产品}: {len(价格异常)}/{产品数量} 条价格异常记录")
            异常记录列表.append(价格异常)
        else:
            print(f"  ✅ {产品}: 价格全部合理")
    
    # 2. 销售额计算验证
    df['计算销售额'] = df['单价'] * df['数量']
    计算错误 = df[abs(df['销售额'] - df['计算销售额']) > 0.01]
    if len(计算错误) > 0:
        print(f"🚨 销售额计算错误: {len(计算错误)} 条记录")
        异常记录列表.append(计算错误)
    else:
        print(f"✅ 销售额计算: 全部正确")
    
    # 3. 数量合理性检查
    数量异常 = df[df['数量'] > 20]  # 单笔订单数量不应超过20
    if len(数量异常) > 0:
        print(f"🚨 数量异常: {len(数量异常)} 条记录数量>20")
        异常记录列表.append(数量异常)
    
    return df, 异常记录列表

def 销售模式审查(df):
    """审查销售业务模式"""
    print(f"\n📈 销售模式分析:")
    
    # 1. 销售员业绩分布
    print(f"👥 销售员业绩排名 (前5):")
    销售员业绩 = df.groupby('销售员姓名').agg({
        '销售额': ['sum', 'mean'],
        '订单ID': 'count',
        '单价': 'mean'
    }).round(2)
    
    # 重命名列
    销售员业绩.columns = ['总销售额', '平均订单额', '订单数', '平均单价']
    销售员业绩 = 销售员业绩.sort_values('总销售额', ascending=False)
    
    print(销售员业绩.head())
    
    # 2. 区域销售分析
    print(f"\n🌍 区域销售分析:")
    区域业绩 = df.groupby('区域').agg({
        '销售额': ['sum', 'mean'],
        '订单ID': 'count'
    }).round(2)
    
    区域业绩.columns = ['区域总销售额', '区域平均订单额', '订单数']
    区域业绩 = 区域业绩.sort_values('区域总销售额', ascending=False)
    
    print(区域业绩)
    
    # 3. 产品表现
    print(f"\n📦 产品类别表现:")
    产品业绩 = df.groupby('产品类别').agg({
        '销售额': ['sum', 'mean'], 
        '订单ID': 'count',
        '单价': 'mean'
    }).round(2)
    
    产品业绩.columns = ['产品总销售额', '产品平均订单额', '订单数', '平均单价']
    产品业绩 = 产品业绩.sort_values('产品总销售额', ascending=False)
    
    print(产品业绩)
    
    return 销售员业绩, 区域业绩, 产品业绩

def 生成审查报告(df, 异常记录):
    """生成真实的数据审查报告"""
    print("\n" + "=" * 50)
    print("📋 数据审查总结报告")
    print("=" * 50)
    
    # 使用真实算法计算评分
    质量评分, 评分明细 = 计算数据质量评分(df, 异常记录)
    
    print(f"✅ 数据质量评分: {质量评分:.1f}% (真实计算)")
    print(f"📊 评分明细: {评分明细}")
    print(f"🚨 发现异常类型: {len(异常记录)} 类")
    
    # 统计总异常记录数
    总异常记录数 = sum(len(异常df) for 异常df in 异常记录)
    print(f"📝 总异常记录: {总异常记录数} 条")
    
    # 质量等级评估
    if 质量评分 >= 90:
        等级 = "优秀"
        建议 = "数据质量很好，可直接用于业务分析和决策"
    elif 质量评分 >= 80:
        等级 = "良好"
        建议 = "数据质量良好，建议简单清洗后使用"
    elif 质量评分 >= 70:
        等级 = "一般"
        建议 = "数据质量一般，建议进行系统化数据清洗"
    else:
        等级 = "需改进"
        建议 = "数据质量较差，需要全面数据清洗和验证"
    
    print(f"🏆 数据质量等级: {等级}")
    print(f"💡 建议: {建议}")
    
    # 保存详细报告
    报告路径 = "/Users/ruimantan/Desktop/作品集/销售数据分析看板/企业销售决策支持系统/sales_dashboard/reports/数据审查报告.txt"
    with open(报告路径, 'w', encoding='utf-8') as f:
        f.write("=== 数据质量审查报告 ===\n")
        f.write(f"审查时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"总记录数: {len(df)}\n")
        f.write(f"数据质量评分: {质量评分:.1f}% ({等级})\n\n")
        
        f.write("评分明细:\n")
        for 维度, 分数 in 评分明细.items():
            f.write(f"  {维度}: {分数:.1f}%\n")
        
        f.write(f"\n异常情况:\n")
        f.write(f"  异常类型数: {len(异常记录)}\n")
        f.write(f"  总异常记录: {总异常记录数}\n")
        f.write(f"  异常比例: {总异常记录数/len(df)*100:.1f}%\n\n")
        
        f.write(f"处理建议:\n  {建议}\n")
    
    print(f"📄 详细报告已保存至: {报告路径}")
    
    return 质量评分, 等级

# 执行数据审查
if __name__ == "__main__":
    print("🎯 开始第一步: 数据审查")
    print("=" * 50)
    
    try:
        # 1. 获取数据
        df = 获取数据()
        
        # 2. 基础审查
        df = 基础数据审查(df)
        
        # 3. 业务逻辑审查  
        df, 异常记录 = 业务逻辑审查(df)
        
        # 4. 销售模式审查
        销售员业绩, 区域业绩, 产品业绩 = 销售模式审查(df)
        
        # 5. 生成报告
        质量评分, 等级 = 生成审查报告(df, 异常记录)
        
        print("\n" + "=" * 50)
        print("🎉 数据审查完成!")
        print(f"📊 数据质量: {质量评分:.1f}% ({等级})")
        print("➡️  准备进入第二步: 数据清洗")
        print("=" * 50)
        
    except Exception as e:
        print(f"❌ 数据审查过程中出错: {e}")
        import traceback
        traceback.print_exc()