# sales_dashboard/streamlit_app/sales_dashboard.py
import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os

# 页面配置
st.set_page_config(
    page_title="智能销售监控系统",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS样式
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
    }
    .positive {
        color: #00cc96;
    }
    .negative {
        color: #ef553b;
    }
</style>
""", unsafe_allow_html=True)

def 获取数据():
    """从数据库获取清洗后的数据"""
    数据库路径 = "data/sales.db"
    conn = sqlite3.connect(数据库路径)
    df = pd.read_sql("SELECT * FROM 产品销售_清洗后", conn)
    conn.close()
    
    # 数据预处理
    df['订单日期'] = pd.to_datetime(df['订单日期'])
    df['年月'] = df['订单日期'].dt.to_period('M')
    
    return df

def 显示KPI指标(df):
    """显示核心KPI指标卡片"""
    st.markdown('<div class="main-header">📊 智能销售监控系统</div>', unsafe_allow_html=True)
    
    # 计算核心指标
    总销售额 = df['销售额'].sum()
    总订单数 = len(df)
    平均订单金额 = df['销售额'].mean()
    销售员数量 = df['销售员姓名'].nunique()
    
    # 创建指标列
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="总销售额",
            value=f"¥{总销售额:,.0f}",
            delta="📈"
        )
    
    with col2:
        st.metric(
            label="总订单数", 
            value=f"{总订单数}",
            delta="📦"
        )
    
    with col3:
        st.metric(
            label="平均订单金额",
            value=f"¥{平均订单金额:,.0f}",
            delta="💰"
        )
    
    with col4:
        st.metric(
            label="销售员数量",
            value=f"{销售员数量}",
            delta="👥"
        )

def 侧边栏过滤器(df):
    """创建侧边栏过滤器"""
    st.sidebar.title("🔧 数据过滤器")
    
    # 日期范围过滤
    min_date = df['订单日期'].min().date()
    max_date = df['订单日期'].max().date()
    
    date_range = st.sidebar.date_input(
        "选择日期范围",
        [min_date, max_date],
        min_value=min_date,
        max_value=max_date
    )
    
    # 销售员多选
    所有销售员 = ['全部'] + sorted(df['销售员姓名'].unique().tolist())
    选中销售员 = st.sidebar.multiselect(
        "选择销售员",
        所有销售员,
        default=['全部']
    )
    
    # 产品类别过滤
    所有产品 = ['全部'] + sorted(df['产品类别'].unique().tolist())
    选中产品 = st.sidebar.multiselect(
        "选择产品类别",
        所有产品, 
        default=['全部']
    )
    
    # 区域过滤
    所有区域 = ['全部'] + sorted(df['区域'].unique().tolist())
    选中区域 = st.sidebar.multiselect(
        "选择区域",
        所有区域,
        default=['全部']
    )
    
    # 应用过滤
    过滤后数据 = df.copy()
    
    # 日期过滤
    if len(date_range) == 2:
        过滤后数据 = 过滤后数据[
            (过滤后数据['订单日期'].dt.date >= date_range[0]) & 
            (过滤后数据['订单日期'].dt.date <= date_range[1])
        ]
    
    # 销售员过滤
    if '全部' not in 选中销售员 and 选中销售员:
        过滤后数据 = 过滤后数据[过滤后数据['销售员姓名'].isin(选中销售员)]
    
    # 产品过滤  
    if '全部' not in 选中产品 and 选中产品:
        过滤后数据 = 过滤后数据[过滤后数据['产品类别'].isin(选中产品)]
    
    # 区域过滤
    if '全部' not in 选中区域 and 选中区域:
        过滤后数据 = 过滤后数据[过滤后数据['区域'].isin(选中区域)]
    
    return 过滤后数据

def 销售趋势分析(过滤后数据):
    """销售趋势分析图表"""
    st.subheader("📈 销售趋势分析")
    
    # 月度趋势
    月度数据 = 过滤后数据.groupby(过滤后数据['订单日期'].dt.to_period('M')).agg({
        '销售额': 'sum',
        '订单ID': 'count'
    }).reset_index()
    月度数据['订单日期'] = 月度数据['订单日期'].astype(str)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # 销售额趋势
        fig_sales = px.line(
            月度数据, 
            x='订单日期', 
            y='销售额',
            title='月度销售额趋势',
            labels={'销售额': '销售额 (元)', '订单日期': '月份'}
        )
        fig_sales.update_traces(line=dict(color='#1f77b4', width=3))
        st.plotly_chart(fig_sales, use_container_width=True)
    
    with col2:
        # 订单数趋势
        fig_orders = px.bar(
            月度数据,
            x='订单日期',
            y='订单ID', 
            title='月度订单数趋势',
            labels={'订单ID': '订单数', '订单日期': '月份'}
        )
        fig_orders.update_traces(marker_color='#ff7f0e')
        st.plotly_chart(fig_orders, use_container_width=True)

def 销售团队分析(过滤后数据):
    """销售团队表现分析"""
    st.subheader("👥 销售团队表现")
    
    # 销售员业绩排名
    销售员业绩 = 过滤后数据.groupby('销售员姓名').agg({
        '销售额': 'sum',
        '订单ID': 'count',
        '单价': 'mean'
    }).round(2).sort_values('销售额', ascending=False)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # 销售员销售额饼图
        fig_pie = px.pie(
            values=销售员业绩['销售额'],
            names=销售员业绩.index,
            title='销售员销售额分布'
        )
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with col2:
        # 销售员业绩柱状图
        fig_bar = px.bar(
            x=销售员业绩.index,
            y=销售员业绩['销售额'],
            title='销售员销售额排名',
            labels={'x': '销售员', 'y': '销售额 (元)'}
        )
        fig_bar.update_traces(marker_color='#2ca02c')
        st.plotly_chart(fig_bar, use_container_width=True)

def 产品区域分析(过滤后数据):
    """产品和区域分析"""
    st.subheader("📦 产品与区域分析")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # 产品类别分析
        产品业绩 = 过滤后数据.groupby('产品类别').agg({
            '销售额': 'sum',
            '订单ID': 'count'
        }).sort_values('销售额', ascending=False)
        
        fig_products = px.bar(
            x=产品业绩.index,
            y=产品业绩['销售额'],
            title='产品类别销售额',
            labels={'x': '产品类别', 'y': '销售额 (元)'}
        )
        st.plotly_chart(fig_products, use_container_width=True)
    
    with col2:
        # 区域销售分析
        区域业绩 = 过滤后数据.groupby('区域').agg({
            '销售额': 'sum',
            '订单ID': 'count' 
        }).sort_values('销售额', ascending=False)
        
        fig_regions = px.pie(
            values=区域业绩['销售额'],
            names=区域业绩.index,
            title='区域销售额分布'
        )
        st.plotly_chart(fig_regions, use_container_width=True)

def 详细数据表格(过滤后数据):
    """显示详细数据表格"""
    st.subheader("📋 详细数据")
    
    # 数据统计
    st.write(f"显示 {len(过滤后数据)} 条记录")
    
    # 交互式数据表格
    st.dataframe(
        过滤后数据,
        use_container_width=True,
        hide_index=True,
        column_config={
            "订单ID": "订单ID",
            "销售员姓名": "销售员", 
            "产品类别": "产品类别",
            "单价": st.column_config.NumberColumn("单价", format="¥%.2f"),
            "数量": "数量",
            "销售额": st.column_config.NumberColumn("销售额", format="¥%.2f"),
            "订单日期": "订单日期",
            "区域": "区域"
        }
    )
    
    # 数据下载
    csv = 过滤后数据.to_csv(index=False)
    st.download_button(
        label="📥 下载CSV数据",
        data=csv,
        file_name=f"销售数据_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )

def 主要():
    """主函数"""
    # 加载数据
    df = 获取数据()
    
    # 显示KPI指标
    显示KPI指标(df)
    
    # 侧边栏过滤器
    过滤后数据 = 侧边栏过滤器(df)
    
    # 显示过滤后数据量
    st.sidebar.write(f"📊 过滤后数据: {len(过滤后数据)} 条记录")
    
    # 分析图表
    销售趋势分析(过滤后数据)
    销售团队分析(过滤后数据) 
    产品区域分析(过滤后数据)
    
    # 详细数据表格
    详细数据表格(过滤后数据)
    
    # 页脚
    st.markdown("---")
    st.markdown("**智能销售监控系统** | 基于真实业务数据分析 | 生成时间: {}".format(
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))

if __name__ == "__main__":
    主要()