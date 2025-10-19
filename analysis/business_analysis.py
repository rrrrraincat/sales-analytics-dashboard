# sales_dashboard/analysis/business_analysis.py
import sqlite3
import pandas as pd
import os
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签
plt.rcParams['axes.unicode_minus'] = False    # 用来正常显示负号

def 获取清洗后数据():
    """获取清洗后的干净数据"""
    数据库路径 = "/Users/ruimantan/Desktop/作品集/销售数据分析看板/企业销售决策支持系统/sales_dashboard/data/sales.db"
    conn = sqlite3.connect(数据库路径)
    
    # 读取清洗后的数据
    df = pd.read_sql("SELECT * FROM 产品销售_清洗后", conn)
    conn.close()
    
    print(f"✅ 读取清洗后数据: {len(df)} 条记录")
    return df

def 核心KPI分析(df):
    """计算核心业务指标"""
    print("=" * 50)
    print("📈 核心KPI分析")
    print("=" * 50)
    
    # 基础KPI
    总销售额 = df['销售额'].sum()
    总订单数 = len(df)
    平均订单金额 = df['销售额'].mean()
    客单价 = 总销售额 / df['客户类型'].nunique() if '客户类型' in df.columns else 总销售额 / 总订单数
    
    print(f"💰 总销售额: {总销售额:,.2f} 元")
    print(f"📦 总订单数: {总订单数} 笔")
    print(f"📊 平均订单金额: {平均订单金额:,.2f} 元")
    print(f"👤 客单价: {客单价:,.2f} 元")
    print(f"📅 分析时间范围: {df['订单日期'].min()} 到 {df['订单日期'].max()}")
    
    return {
        '总销售额': 总销售额,
        '总订单数': 总订单数,
        '平均订单金额': 平均订单金额,
        '客单价': 客单价
    }

def 销售团队分析(df):
    """销售团队业绩深度分析"""
    print("\n" + "=" * 50)
    print("👥 销售团队分析")
    print("=" * 50)
    
    # 销售员业绩排名
    销售员业绩 = df.groupby('销售员姓名').agg({
        '销售额': ['sum', 'mean', 'count'],
        '单价': 'mean',
        '数量': 'mean'
    }).round(2)
    
    # 重命名列
    销售员业绩.columns = ['总销售额', '平均订单额', '订单数', '平均单价', '平均数量']
    销售员业绩 = 销售员业绩.sort_values('总销售额', ascending=False)
    
    print("🏆 销售员业绩排名:")
    print(销售员业绩)
    
    # 计算销售员贡献度
    总销售金额 = df['销售额'].sum()
    销售员业绩['贡献度'] = (销售员业绩['总销售额'] / 总销售金额 * 100).round(2)
    
    print(f"\n📊 销售员贡献度:")
    for 销售员, 数据 in 销售员业绩.iterrows():
        print(f"  {销售员}: {数据['贡献度']}% (¥{数据['总销售额']:,.0f})")
    
    return 销售员业绩

def 产品表现分析(df):
    """产品类别和性能分析"""
    print("\n" + "=" * 50)
    print("📦 产品表现分析")
    print("=" * 50)
    
    # 产品类别分析
    产品业绩 = df.groupby('产品类别').agg({
        '销售额': ['sum', 'mean', 'count'],
        '单价': 'mean',
        '数量': 'mean'
    }).round(2)
    
    产品业绩.columns = ['总销售额', '平均订单额', '订单数', '平均单价', '平均数量']
    产品业绩 = 产品业绩.sort_values('总销售额', ascending=False)
    
    print("🔥 产品类别表现:")
    print(产品业绩)
    
    # 产品贡献度分析
    总销售额 = df['销售额'].sum()
    产品业绩['销售额占比'] = (产品业绩['总销售额'] / 总销售额 * 100).round(2)
    产品业绩['订单占比'] = (产品业绩['订单数'] / len(df) * 100).round(2)
    
    print(f"\n🎯 产品战略分析:")
    for 产品, 数据 in 产品业绩.iterrows():
        print(f"  {产品}: {数据['销售额占比']}% 销售额, {数据['订单占比']}% 订单量")
    
    return 产品业绩

def 区域市场分析(df):
    """区域销售表现分析"""
    print("\n" + "=" * 50)
    print("🌍 区域市场分析")
    print("=" * 50)
    
    # 区域业绩分析
    区域业绩 = df.groupby('区域').agg({
        '销售额': ['sum', 'mean', 'count'],
        '单价': 'mean',
        '数量': 'mean'
    }).round(2)
    
    区域业绩.columns = ['总销售额', '平均订单额', '订单数', '平均单价', '平均数量']
    区域业绩 = 区域业绩.sort_values('总销售额', ascending=False)
    
    print("📍 区域销售表现:")
    print(区域业绩)
    
    # 区域市场占有率
    总销售额 = df['销售额'].sum()
    区域业绩['市场占有率'] = (区域业绩['总销售额'] / 总销售额 * 100).round(2)
    
    print(f"\n🏆 区域市场占有率:")
    for 区域, 数据 in 区域业绩.iterrows():
        print(f"  {区域}: {数据['市场占有率']}% 市场份额")
    
    return 区域业绩

def 时间趋势分析(df):
    """销售时间趋势分析"""
    print("\n" + "=" * 50)
    print("📅 时间趋势分析")
    print("=" * 50)
    
    # 确保日期格式
    df['订单日期'] = pd.to_datetime(df['订单日期'])
    
    # 月度趋势
    df['年月'] = df['订单日期'].dt.to_period('M')
    月度趋势 = df.groupby('年月').agg({
        '销售额': 'sum',
        '订单ID': 'count',
        '单价': 'mean'
    }).round(2)
    
    月度趋势.columns = ['月销售额', '月订单数', '月平均单价']
    
    print("📈 月度销售趋势:")
    print(月度趋势)
    
    # 增长分析
    if len(月度趋势) > 1:
        首月销售额 = 月度趋势.iloc[0]['月销售额']
        末月销售额 = 月度趋势.iloc[-1]['月销售额']
        增长率 = ((末月销售额 - 首月销售额) / 首月销售额 * 100).round(2)
        
        print(f"\n🚀 销售增长分析:")
        print(f"  期初: ¥{首月销售额:,.0f}")
        print(f"  期末: ¥{末月销售额:,.0f}")
        print(f"  增长率: {增长率}%")
    
    return 月度趋势

def 生成分析报告(df, kpi, 销售员业绩, 产品业绩, 区域业绩, 月度趋势):
    """生成完整的业务分析报告"""
    print("\n" + "=" * 50)
    print("📋 业务分析总结报告")
    print("=" * 50)
    
    # 生成报告内容
    报告路径 = "/Users/ruimantan/Desktop/作品集/销售数据分析看板/企业销售决策支持系统/sales_dashboard/reports/业务分析报告.txt"
    
    with open(报告路径, 'w', encoding='utf-8') as f:
        f.write("=== 销售业务分析报告 ===\n\n")
        f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"分析周期: {df['订单日期'].min()} 到 {df['订单日期'].max()}\n")
        f.write(f"数据总量: {len(df)} 条销售记录\n\n")
        
        f.write("一、核心KPI指标\n")
        f.write("-" * 40 + "\n")
        for 指标, 数值 in kpi.items():
            if '销售额' in 指标 or '金额' in 指标 or '单价' in 指标:
                f.write(f"{指标}: ¥{数值:,.2f}\n")
            else:
                f.write(f"{指标}: {数值}\n")
        
        f.write("\n二、销售团队表现\n")
        f.write("-" * 40 + "\n")
        for 销售员, 数据 in 销售员业绩.iterrows():
            f.write(f"{销售员}: 贡献度{数据['贡献度']}% (¥{数据['总销售额']:,.0f}, {数据['订单数']}单)\n")
        
        f.write("\n三、产品战略分析\n")
        f.write("-" * 40 + "\n")
        for 产品, 数据 in 产品业绩.iterrows():
            f.write(f"{产品}: {数据['销售额占比']}%销售额, {数据['订单占比']}%订单量\n")
        
        f.write("\n四、区域市场分布\n")
        f.write("-" * 40 + "\n")
        for 区域, 数据 in 区域业绩.iterrows():
            f.write(f"{区域}: {数据['市场占有率']}%市场份额 (¥{数据['总销售额']:,.0f})\n")
        
        f.write("\n五、业务建议\n")
        f.write("-" * 40 + "\n")
        
        # 基于数据的智能建议
        最佳销售员 = 销售员业绩.index[0]
        最佳产品 = 产品业绩.index[0]
        最佳区域 = 区域业绩.index[0]
        
        f.write(f"1. 重点扶持: {最佳销售员} (Top销售员)，可分享其成功经验\n")
        f.write(f"2. 产品策略: 聚焦 {最佳产品} (明星产品)，考虑扩大库存\n")
        f.write(f"3. 区域拓展: 巩固 {最佳区域} 市场优势，复制成功模式\n")
        f.write(f"4. 资源分配: 根据各区域市场占有率合理分配营销预算\n")
    
    print("✅ 核心业务洞察:")
    print(f"  🏆 最佳销售员: {销售员业绩.index[0]} (贡献度{销售员业绩.iloc[0]['贡献度']}%)")
    print(f"  📦 明星产品: {产品业绩.index[0]} ({产品业绩.iloc[0]['销售额占比']}%销售额)")
    print(f"  🌍 优势区域: {区域业绩.index[0]} ({区域业绩.iloc[0]['市场占有率']}%市场份额)")
    print(f"  💰 总销售业绩: ¥{kpi['总销售额']:,.0f}")
    
    print(f"\n📄 详细分析报告已保存至: {报告路径}")

def 创建可视化图表(df, 销售员业绩, 产品业绩, 区域业绩, 月度趋势):
    """创建业务分析可视化图表"""
    print("\n" + "=" * 50)
    print("📊 生成可视化图表")
    print("=" * 50)
    
    try:
        # 创建图表目录
        图表目录 = "/Users/ruimantan/Desktop/作品集/销售数据分析看板/企业销售决策支持系统/sales_dashboard/reports/charts"
        os.makedirs(图表目录, exist_ok=True)
        
        # 1. 销售员业绩饼图
        plt.figure(figsize=(10, 8))
        plt.subplot(2, 2, 1)
        plt.pie(销售员业绩['总销售额'], labels=销售员业绩.index, autopct='%1.1f%%')
        plt.title('销售员业绩分布')
        
        # 2. 产品销售额柱状图
        plt.subplot(2, 2, 2)
        产品业绩['总销售额'].plot(kind='bar')
        plt.title('产品销售额对比')
        plt.xticks(rotation=45)
        
        # 3. 区域市场份额
        plt.subplot(2, 2, 3)
        plt.pie(区域业绩['总销售额'], labels=区域业绩.index, autopct='%1.1f%%')
        plt.title('区域市场份额')
        
        # 4. 月度趋势图
        plt.subplot(2, 2, 4)
        月度趋势['月销售额'].plot(kind='line', marker='o')
        plt.title('月度销售趋势')
        plt.xticks(rotation=45)
        
        plt.tight_layout()
        图表路径 = os.path.join(图表目录, '业务分析图表.png')
        plt.savefig(图表路径, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"✅ 可视化图表已保存至: {图表路径}")
        
    except Exception as e:
        print(f"⚠️  图表生成遇到问题: {e}")
        print("💡 建议: 可以稍后安装matplotlib解决")

# 执行业务分析
if __name__ == "__main__":
    print("🎯 开始第三步: 业务分析")
    print("=" * 50)
    
    try:
        # 1. 获取清洗后数据
        df = 获取清洗后数据()
        
        # 2. 核心KPI分析
        kpi = 核心KPI分析(df)
        
        # 3. 销售团队分析
        销售员业绩 = 销售团队分析(df)
        
        # 4. 产品表现分析
        产品业绩 = 产品表现分析(df)
        
        # 5. 区域市场分析
        区域业绩 = 区域市场分析(df)
        
        # 6. 时间趋势分析
        月度趋势 = 时间趋势分析(df)
        
        # 7. 生成分析报告
        生成分析报告(df, kpi, 销售员业绩, 产品业绩, 区域业绩, 月度趋势)
        
        # 8. 创建可视化图表
        创建可视化图表(df, 销售员业绩, 产品业绩, 区域业绩, 月度趋势)
        
        print("\n" + "=" * 50)
        print("🎉 业务分析完成!")
        print("📈 已获得完整的销售业务洞察")
        print("➡️  准备进入Streamlit可视化展示")
        print("=" * 50)
        
    except Exception as e:
        print(f"❌ 业务分析过程中出错: {e}")
        import traceback
        traceback.print_exc()