import streamlit as st
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
import warnings
from region_data import (
    PROVINCE_CITY_MAP,
    PROVINCE_WEIGHTS,
    get_region_type,
    get_all_provinces,
    get_cities_by_province
)

warnings.filterwarnings('ignore')

st.set_page_config(
    page_title="用户画像分析",
    page_icon="👥",
    layout="wide",
    initial_sidebar_state="expanded"
)

custom_css = """
<style>
.main {
    background-color: #f8f9fa;
}
.stApp > header {
    background-color: #2C3E50;
}
.stApp > header h1 {
    color: white !important;
}
.css-1d391kg {
    background-color: #2C3E50;
}
.metric-card {
    background: white;
    padding: 20px;
    border-radius: 10px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    margin: 10px 0;
}
.chart-container {
    background: white;
    padding: 20px;
    border-radius: 10px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    margin: 10px 0;
}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)


@st.cache_data
def generate_mock_data(n_samples=3000):
    np.random.seed(42)
    
    user_ids = range(1, n_samples + 1)
    
    genders = np.random.choice(
        ['男', '女'], 
        size=n_samples, 
        p=[0.52, 0.48]
    )
    
    ages = np.random.normal(loc=32, scale=10, size=n_samples)
    ages = np.clip(ages, 18, 65).astype(int)
    
    def get_age_group(age):
        if age < 25:
            return '18-24'
        elif age < 35:
            return '25-34'
        elif age < 45:
            return '35-44'
        elif age < 55:
            return '45-54'
        else:
            return '55+'
    
    age_groups = [get_age_group(age) for age in ages]
    
    provinces_list = list(PROVINCE_WEIGHTS.keys())
    weights_list = list(PROVINCE_WEIGHTS.values())
    total_weight = sum(weights_list)
    weights_list = [w / total_weight for w in weights_list]
    
    provinces = np.random.choice(provinces_list, size=n_samples, p=weights_list)
    
    cities = []
    for province in provinces:
        city_list = get_cities_by_province(province)
        if city_list:
            city = np.random.choice(city_list)
        else:
            city = "未知"
        cities.append(city)
    
    region_types = [get_region_type(p) for p in provinces]
    
    df = pd.DataFrame({
        'user_id': user_ids,
        'gender': genders,
        'age': ages,
        'age_group': age_groups,
        'province': provinces,
        'city': cities,
        'region_type': region_types
    })
    
    return df


def create_gender_chart(df):
    fig, ax = plt.subplots(figsize=(10, 5))
    
    gender_counts = df['gender'].value_counts()
    colors = ['#3498DB', '#E74C3C']
    
    bars = ax.barh(
        gender_counts.index, 
        gender_counts.values,
        color=colors,
        edgecolor='white',
        linewidth=2
    )
    
    ax.set_xlabel('用户数量', fontsize=12, fontweight='bold')
    ax.set_ylabel('性别', fontsize=12, fontweight='bold')
    ax.set_title('用户性别分布', fontsize=16, fontweight='bold', pad=20)
    
    total = len(df)
    for i, (bar, count) in enumerate(zip(bars, gender_counts.values)):
        percentage = (count / total) * 100
        ax.text(
            bar.get_width() + 20,
            bar.get_y() + bar.get_height()/2,
            f'{count:,} ({percentage:.1f}%)',
            va='center',
            fontsize=11,
            fontweight='bold',
            color='#2C3E50'
        )
    
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.xaxis.grid(True, alpha=0.3, linestyle='--')
    ax.set_axisbelow(True)
    
    plt.tight_layout()
    return fig


def create_age_gender_chart(df):
    fig, ax = plt.subplots(figsize=(12, 6))
    
    age_order = ['18-24', '25-34', '35-44', '45-54', '55+']
    
    age_gender_data = df.groupby(['age_group', 'gender']).size().unstack(fill_value=0)
    age_gender_data = age_gender_data.reindex(age_order)
    
    x = np.arange(len(age_order))
    width = 0.35
    
    male_counts = age_gender_data.get('男', pd.Series([0]*len(age_order), index=age_order)).values
    female_counts = age_gender_data.get('女', pd.Series([0]*len(age_order), index=age_order)).values
    
    bars1 = ax.bar(x - width/2, male_counts, width, 
                   label='男', color='#3498DB', edgecolor='white', linewidth=1.5)
    bars2 = ax.bar(x + width/2, female_counts, width, 
                   label='女', color='#E74C3C', edgecolor='white', linewidth=1.5)
    
    ax.set_xlabel('年龄段', fontsize=12, fontweight='bold')
    ax.set_ylabel('用户数量', fontsize=12, fontweight='bold')
    ax.set_title('用户年龄与性别分布', fontsize=16, fontweight='bold', pad=20)
    ax.set_xticks(x)
    ax.set_xticklabels(age_order, fontsize=11)
    ax.legend(fontsize=11, frameon=True, shadow=True)
    
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.yaxis.grid(True, alpha=0.3, linestyle='--')
    ax.set_axisbelow(True)
    
    total = len(df)
    for bar in bars1:
        height = bar.get_height()
        if height > 0:
            percentage = (height / total) * 100
            ax.text(
                bar.get_x() + bar.get_width()/2.,
                height + 10,
                f'{int(height)}',
                ha='center', va='bottom',
                fontsize=9, fontweight='bold',
                color='#2C3E50'
            )
    
    for bar in bars2:
        height = bar.get_height()
        if height > 0:
            percentage = (height / total) * 100
            ax.text(
                bar.get_x() + bar.get_width()/2.,
                height + 10,
                f'{int(height)}',
                ha='center', va='bottom',
                fontsize=9, fontweight='bold',
                color='#2C3E50'
            )
    
    plt.tight_layout()
    return fig


def create_province_rank_chart(df, top_n=15):
    fig, ax = plt.subplots(figsize=(12, 8))
    
    province_counts = df['province'].value_counts().head(top_n)
    
    colors = sns.color_palette("viridis", len(province_counts))
    
    bars = ax.barh(
        province_counts.index[::-1],
        province_counts.values[::-1],
        color=colors,
        edgecolor='white',
        linewidth=1.5
    )
    
    ax.set_xlabel('用户数量', fontsize=12, fontweight='bold')
    ax.set_ylabel('省份', fontsize=12, fontweight='bold')
    ax.set_title(f'用户省份分布 TOP{top_n}', fontsize=16, fontweight='bold', pad=20)
    
    total = len(df)
    for i, (bar, count) in enumerate(zip(bars, province_counts.values[::-1])):
        percentage = (count / total) * 100
        ax.text(
            bar.get_width() + 10,
            bar.get_y() + bar.get_height() / 2,
            f'{count:,} ({percentage:.1f}%)',
            va='center',
            fontsize=10,
            fontweight='bold',
            color='#2C3E50'
        )
    
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.xaxis.grid(True, alpha=0.3, linestyle='--')
    ax.set_axisbelow(True)
    
    plt.tight_layout()
    return fig


def create_region_ns_chart(df):
    fig, ax = plt.subplots(figsize=(10, 6))
    
    region_counts = df['region_type'].value_counts()
    region_order = ['南方', '北方']
    region_counts = region_counts.reindex(region_order)
    region_counts = region_counts.fillna(0)
    
    colors = ['#E74C3C', '#3498DB']
    
    bars = ax.bar(
        region_counts.index,
        region_counts.values,
        color=colors,
        edgecolor='white',
        linewidth=2,
        width=0.5
    )
    
    ax.set_xlabel('地域', fontsize=12, fontweight='bold')
    ax.set_ylabel('用户数量', fontsize=12, fontweight='bold')
    ax.set_title('南北方用户分布对比', fontsize=16, fontweight='bold', pad=20)
    
    total = len(df)
    for bar, count in zip(bars, region_counts.values):
        height = bar.get_height()
        percentage = (count / total) * 100
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            height + 20,
            f'{int(count):,} ({percentage:.1f}%)',
            ha='center',
            va='bottom',
            fontsize=12,
            fontweight='bold',
            color='#2C3E50'
        )
    
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.yaxis.grid(True, alpha=0.3, linestyle='--')
    ax.set_axisbelow(True)
    
    plt.tight_layout()
    return fig


def main():
    st.title("👥 用户画像分析")
    st.markdown("---")
    
    st.sidebar.header("⚙️ 配置选项")
    
    n_samples = st.sidebar.slider(
        "样本数量",
        min_value=500,
        max_value=5000,
        value=3000,
        step=100,
        help="选择生成的 mock 数据样本数量"
    )
    
    st.sidebar.subheader("🗺️ 地域筛选")
    all_provinces = get_all_provinces()
    selected_province = st.sidebar.selectbox(
        "选择省份",
        options=["全部"] + all_provinces,
        index=0,
        help="选择特定省份查看用户分布"
    )
    
    show_data = st.sidebar.checkbox("显示原始数据", value=False)
    
    df = generate_mock_data(n_samples)
    
    if selected_province != "全部":
        df_filtered = df[df['province'] == selected_province]
    else:
        df_filtered = df
    
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    with col1:
        st.metric(
            label="总用户数",
            value=f"{len(df_filtered):,}",
            delta=None
        )
    
    with col2:
        male_count = len(df_filtered[df_filtered['gender'] == '男'])
        st.metric(
            label="男性用户",
            value=f"{male_count:,}",
            delta=f"{male_count/len(df_filtered)*100:.1f}%"
        )
    
    with col3:
        female_count = len(df_filtered[df_filtered['gender'] == '女'])
        st.metric(
            label="女性用户",
            value=f"{female_count:,}",
            delta=f"{female_count/len(df_filtered)*100:.1f}%"
        )
    
    with col4:
        avg_age = df_filtered['age'].mean()
        st.metric(
            label="平均年龄",
            value=f"{avg_age:.1f}岁",
            delta=None
        )
    
    with col5:
        province_count = df_filtered['province'].nunique()
        st.metric(
            label="覆盖省份数",
            value=f"{province_count}",
            delta=None
        )
    
    with col6:
        south_count = len(df_filtered[df_filtered['region_type'] == '南方'])
        st.metric(
            label="南方用户",
            value=f"{south_count:,}",
            delta=f"{south_count/len(df_filtered)*100:.1f}%"
        )
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 性别分布")
        gender_fig = create_gender_chart(df_filtered)
        st.pyplot(gender_fig, use_container_width=True)
    
    with col2:
        st.subheader("📈 年龄与性别分布")
        age_gender_fig = create_age_gender_chart(df_filtered)
        st.pyplot(age_gender_fig, use_container_width=True)
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🏆 省份用户数量排名")
        top_n = st.slider("显示 TOP N 省份", min_value=5, max_value=30, value=15, key="province_top_n")
        province_fig = create_province_rank_chart(df_filtered, top_n=top_n)
        st.pyplot(province_fig, use_container_width=True)
    
    with col2:
        st.subheader("🌏 南北方用户分布对比")
        region_ns_fig = create_region_ns_chart(df_filtered)
        st.pyplot(region_ns_fig, use_container_width=True)
    
    st.markdown("---")
    
    st.subheader("📋 数据摘要")
    
    summary_col1, summary_col2, summary_col3 = st.columns(3)
    
    with summary_col1:
        st.markdown("### 性别统计")
        gender_summary = df_filtered['gender'].value_counts().reset_index()
        gender_summary.columns = ['性别', '用户数']
        gender_summary['占比'] = (gender_summary['用户数'] / len(df_filtered) * 100).round(2).astype(str) + '%'
        st.dataframe(gender_summary, use_container_width=True, hide_index=True)
    
    with summary_col2:
        st.markdown("### 年龄段统计")
        age_summary = df_filtered['age_group'].value_counts().reindex(['18-24', '25-34', '35-44', '45-54', '55+']).reset_index()
        age_summary.columns = ['年龄段', '用户数']
        age_summary['占比'] = (age_summary['用户数'] / len(df_filtered) * 100).round(2).astype(str) + '%'
        st.dataframe(age_summary, use_container_width=True, hide_index=True)
    
    with summary_col3:
        st.markdown("### 省份统计 TOP10")
        province_summary = df_filtered['province'].value_counts().head(10).reset_index()
        province_summary.columns = ['省份', '用户数']
        province_summary['占比'] = (province_summary['用户数'] / len(df_filtered) * 100).round(2).astype(str) + '%'
        st.dataframe(province_summary, use_container_width=True, hide_index=True)
    
    if selected_province != "全部":
        st.markdown("---")
        st.subheader(f"🏙️ {selected_province} 城市分布 TOP10")
        city_summary = df_filtered['city'].value_counts().head(10).reset_index()
        city_summary.columns = ['城市', '用户数']
        city_summary['占比'] = (city_summary['用户数'] / len(df_filtered) * 100).round(2).astype(str) + '%'
        st.dataframe(city_summary, use_container_width=True, hide_index=True)
    
    if show_data:
        st.markdown("---")
        st.subheader("📄 原始数据预览")
        display_cols = ['user_id', 'gender', 'age', 'age_group', 'province', 'city', 'region_type']
        st.dataframe(df_filtered[display_cols].head(100), use_container_width=True)
    
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: #7f8c8d; padding: 20px;'>
            <p>💡 用户画像分析系统 | 基于 Streamlit + Seaborn 构建</p>
            <p>数据为 Mock 生成，仅用于演示目的</p>
        </div>
        """,
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
