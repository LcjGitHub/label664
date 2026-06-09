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
from user_behavior import (
    generate_behavior_data,
    calculate_behavior_scores,
    segment_users,
    get_segment_summary
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

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False
sns.set(font='SimHei')


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
    
    font_prop = FontProperties(family='SimHei', size=12)
    font_title = FontProperties(family='SimHei', size=16, weight='bold')
    font_label = FontProperties(family='SimHei', size=12, weight='bold')
    font_text = FontProperties(family='SimHei', size=11, weight='bold')
    
    gender_counts = df['gender'].value_counts()
    colors = ['#3498DB', '#E74C3C']
    
    bars = ax.barh(
        gender_counts.index, 
        gender_counts.values,
        color=colors,
        edgecolor='white',
        linewidth=2
    )
    
    ax.set_xlabel('用户数量', fontproperties=font_label)
    ax.set_ylabel('性别', fontproperties=font_label)
    ax.set_title('用户性别分布', fontproperties=font_title, pad=20)
    
    total = len(df)
    for i, (bar, count) in enumerate(zip(bars, gender_counts.values)):
        percentage = (count / total) * 100
        ax.text(
            bar.get_width() + 20,
            bar.get_y() + bar.get_height()/2,
            f'{count:,} ({percentage:.1f}%)',
            va='center',
            fontproperties=font_text,
            color='#2C3E50'
        )
    
    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_fontproperties(font_prop)
    
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.xaxis.grid(True, alpha=0.3, linestyle='--')
    ax.set_axisbelow(True)
    
    plt.tight_layout()
    return fig


def create_age_gender_chart(df):
    fig, ax = plt.subplots(figsize=(12, 6))
    
    font_prop = FontProperties(family='SimHei', size=11)
    font_title = FontProperties(family='SimHei', size=16, weight='bold')
    font_label = FontProperties(family='SimHei', size=12, weight='bold')
    font_text = FontProperties(family='SimHei', size=9, weight='bold')
    font_legend = FontProperties(family='SimHei', size=11)
    
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
    
    ax.set_xlabel('年龄段', fontproperties=font_label)
    ax.set_ylabel('用户数量', fontproperties=font_label)
    ax.set_title('用户年龄与性别分布', fontproperties=font_title, pad=20)
    ax.set_xticks(x)
    ax.set_xticklabels(age_order, fontproperties=font_prop)
    ax.legend(prop=font_legend, frameon=True, shadow=True)
    
    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_fontproperties(font_prop)
    
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
                fontproperties=font_text,
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
                fontproperties=font_text,
                color='#2C3E50'
            )
    
    plt.tight_layout()
    return fig


def create_province_rank_chart(df, top_n=15):
    fig, ax = plt.subplots(figsize=(12, 8))
    
    font_prop = FontProperties(family='SimHei', size=10)
    font_title = FontProperties(family='SimHei', size=16, weight='bold')
    font_label = FontProperties(family='SimHei', size=12, weight='bold')
    font_text = FontProperties(family='SimHei', size=10, weight='bold')
    
    province_counts = df['province'].value_counts().head(top_n)
    
    colors = sns.color_palette("viridis", len(province_counts))
    
    bars = ax.barh(
        province_counts.index[::-1],
        province_counts.values[::-1],
        color=colors,
        edgecolor='white',
        linewidth=1.5
    )
    
    ax.set_xlabel('用户数量', fontproperties=font_label)
    ax.set_ylabel('省份', fontproperties=font_label)
    ax.set_title(f'用户省份分布 TOP{top_n}', fontproperties=font_title, pad=20)
    
    total = len(df)
    for i, (bar, count) in enumerate(zip(bars, province_counts.values[::-1])):
        percentage = (count / total) * 100
        ax.text(
            bar.get_width() + 10,
            bar.get_y() + bar.get_height() / 2,
            f'{count:,} ({percentage:.1f}%)',
            va='center',
            fontproperties=font_text,
            color='#2C3E50'
        )
    
    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_fontproperties(font_prop)
    
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.xaxis.grid(True, alpha=0.3, linestyle='--')
    ax.set_axisbelow(True)
    
    plt.tight_layout()
    return fig


def create_region_ns_chart(df):
    fig, ax = plt.subplots(figsize=(10, 6))
    
    font_prop = FontProperties(family='SimHei', size=12)
    font_title = FontProperties(family='SimHei', size=16, weight='bold')
    font_label = FontProperties(family='SimHei', size=12, weight='bold')
    font_text = FontProperties(family='SimHei', size=12, weight='bold')
    
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
    
    ax.set_xlabel('地域', fontproperties=font_label)
    ax.set_ylabel('用户数量', fontproperties=font_label)
    ax.set_title('南北方用户分布对比', fontproperties=font_title, pad=20)
    
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
            fontproperties=font_text,
            color='#2C3E50'
        )
    
    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_fontproperties(font_prop)
    
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.yaxis.grid(True, alpha=0.3, linestyle='--')
    ax.set_axisbelow(True)
    
    plt.tight_layout()
    return fig


def create_behavior_pie_chart(df):
    fig, ax = plt.subplots(figsize=(10, 8))

    font_prop = FontProperties(family='SimHei', size=12)
    font_title = FontProperties(family='SimHei', size=16, weight='bold')
    font_text = FontProperties(family='SimHei', size=13, weight='bold')

    segment_counts = df['user_segment'].value_counts()
    segment_order = ['活跃用户', '普通用户', '沉睡用户']
    segment_counts = segment_counts.reindex(segment_order)
    segment_counts = segment_counts.fillna(0)

    colors = ['#27AE60', '#3498DB', '#95A5A6']
    explode = (0.05, 0.03, 0.03)

    wedges, texts, autotexts = ax.pie(
        segment_counts.values,
        labels=segment_counts.index,
        colors=colors,
        autopct='%1.1f%%',
        startangle=90,
        explode=explode,
        pctdistance=0.75,
        wedgeprops=dict(edgecolor='white', linewidth=3)
    )

    for text in texts:
        text.set_fontproperties(font_text)
    for autotext in autotexts:
        autotext.set_fontproperties(font_text)
        autotext.set_color('white')

    total = segment_counts.sum()
    legend_labels = [
        f'{seg}: {int(cnt)}人 ({cnt/total*100:.1f}%)'
        for seg, cnt in zip(segment_counts.index, segment_counts.values)
    ]
    ax.legend(
        wedges, legend_labels,
        loc='center left',
        bbox_to_anchor=(1, 0.5),
        prop=font_prop,
        frameon=True,
        shadow=True
    )

    ax.set_title('用户行为分群分布', fontproperties=font_title, pad=20)

    plt.tight_layout()
    return fig


def create_segment_comparison_chart(df):
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    font_prop = FontProperties(family='SimHei', size=10)
    font_title = FontProperties(family='SimHei', size=14, weight='bold')
    font_label = FontProperties(family='SimHei', size=11, weight='bold')
    font_text = FontProperties(family='SimHei', size=9, weight='bold')

    segment_order = ['活跃用户', '普通用户', '沉睡用户']
    colors = ['#27AE60', '#3498DB', '#95A5A6']

    summary = df.groupby('user_segment', observed=True).agg({
        'login_frequency': 'mean',
        'online_hours': 'mean',
        'purchase_count': 'mean',
        'total_spent': 'mean'
    }).reindex(segment_order)

    metrics = [
        ('login_frequency', '平均登录频率（次）', axes[0, 0]),
        ('online_hours', '平均在线时长（小时）', axes[0, 1]),
        ('purchase_count', '平均购买次数', axes[1, 0]),
        ('total_spent', '平均消费金额（元）', axes[1, 1])
    ]

    for col, title, ax in metrics:
        values = summary[col].values
        bars = ax.bar(
            range(len(segment_order)),
            values,
            color=colors,
            edgecolor='white',
            linewidth=2,
            width=0.6
        )

        ax.set_xticks(range(len(segment_order)))
        ax.set_xticklabels(segment_order, fontproperties=font_prop)
        ax.set_title(title, fontproperties=font_title, pad=10)
        ax.set_ylabel('数值', fontproperties=font_label)

        for label in ax.get_xticklabels() + ax.get_yticklabels():
            label.set_fontproperties(font_prop)

        for bar, val in zip(bars, values):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + max(values) * 0.02,
                f'{val:.1f}',
                ha='center',
                fontproperties=font_text,
                color='#2C3E50'
            )

        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.yaxis.grid(True, alpha=0.3, linestyle='--')
        ax.set_axisbelow(True)

    fig.suptitle('不同行为群体关键指标对比', fontproperties=font_title, fontsize=16, y=1.02)
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
        help="选择生成的模拟数据样本数量"
    )
    
    st.sidebar.subheader("🗺️ 地域筛选")
    all_provinces = get_all_provinces()
    selected_province = st.sidebar.selectbox(
        "选择省份",
        options=["全部"] + all_provinces,
        index=0,
        help="选择特定省份查看该省份的用户分布详情"
    )

    st.sidebar.subheader("🎯 行为群体筛选")
    segment_options = ["全部", "活跃用户", "普通用户", "沉睡用户"]
    selected_segment = st.sidebar.multiselect(
        "选择行为群体",
        options=segment_options[1:],
        default=[],
        help="选择一个或多个行为群体查看详细数据"
    )

    st.sidebar.subheader("📊 行为指标筛选")
    min_login_freq = st.sidebar.slider(
        "最低登录频率（次）",
        min_value=0,
        max_value=90,
        value=0,
        step=1
    )
    min_purchase = st.sidebar.slider(
        "最低购买次数",
        min_value=0,
        max_value=50,
        value=0,
        step=1
    )
    min_online_hours = st.sidebar.slider(
        "最低在线时长（小时）",
        min_value=0.0,
        max_value=500.0,
        value=0.0,
        step=1.0
    )
    
    show_data = st.sidebar.checkbox("显示原始数据", value=False)
    
    df_profile = generate_mock_data(n_samples)
    df_behavior = generate_behavior_data(df_profile['user_id'].tolist())
    df_behavior = calculate_behavior_scores(df_behavior)
    df_behavior = segment_users(df_behavior)
    
    df = df_profile.merge(df_behavior, on='user_id', how='left')
    
    df_filtered = df.copy()
    
    if selected_province != "全部":
        df_filtered = df_filtered[df_filtered['province'] == selected_province]

    if selected_segment:
        df_filtered = df_filtered[df_filtered['user_segment'].isin(selected_segment)]

    df_filtered = df_filtered[df_filtered['login_frequency'] >= min_login_freq]
    df_filtered = df_filtered[df_filtered['purchase_count'] >= min_purchase]
    df_filtered = df_filtered[df_filtered['online_hours'] >= min_online_hours]
    
    df_full = df
    
    col1, col2, col3, col4, col5, col6, col7 = st.columns(7)
    
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
    
    with col7:
        north_count = len(df_filtered[df_filtered['region_type'] == '北方'])
        st.metric(
            label="北方用户",
            value=f"{north_count:,}",
            delta=f"{north_count/len(df_filtered)*100:.1f}%"
        )

    if len(df_filtered) > 0:
        bcol1, bcol2, bcol3, bcol4, bcol5, bcol6, bcol7 = st.columns(7)

        with bcol1:
            active_count = len(df_filtered[df_filtered['user_segment'] == '活跃用户'])
            st.metric(
                label="活跃用户",
                value=f"{active_count:,}",
                delta=f"{active_count/len(df_filtered)*100:.1f}%"
            )

        with bcol2:
            normal_count = len(df_filtered[df_filtered['user_segment'] == '普通用户'])
            st.metric(
                label="普通用户",
                value=f"{normal_count:,}",
                delta=f"{normal_count/len(df_filtered)*100:.1f}%"
            )

        with bcol3:
            dormant_count = len(df_filtered[df_filtered['user_segment'] == '沉睡用户'])
            st.metric(
                label="沉睡用户",
                value=f"{dormant_count:,}",
                delta=f"{dormant_count/len(df_filtered)*100:.1f}%"
            )

        with bcol4:
            avg_login = df_filtered['login_frequency'].mean()
            st.metric(
                label="平均登录频率",
                value=f"{avg_login:.1f}次",
                delta=None
            )

        with bcol5:
            avg_online = df_filtered['online_hours'].mean()
            st.metric(
                label="平均在线时长",
                value=f"{avg_online:.1f}小时",
                delta=None
            )

        with bcol6:
            avg_purchase = df_filtered['purchase_count'].mean()
            st.metric(
                label="平均购买次数",
                value=f"{avg_purchase:.1f}次",
                delta=None
            )

        with bcol7:
            total_spent = df_filtered['total_spent'].sum()
            st.metric(
                label="总消费金额",
                value=f"¥{total_spent:,.0f}",
                delta=None
            )

    st.markdown("---")

    st.subheader("🎯 用户行为分析")
    st.markdown("#### 行为群体关键指标对比")

    seg_col1, seg_col2, seg_col3 = st.columns(3)
    segment_display = ['活跃用户', '普通用户', '沉睡用户']
    segment_colors = ['#27AE60', '#3498DB', '#95A5A6']
    segment_icons = ['🔥', '👤', '💤']

    df_behavior_view = df_filtered if len(df_filtered) > 0 else df_full

    for i, (seg, color, icon) in enumerate(zip(segment_display, segment_colors, segment_icons)):
        seg_data = df_behavior_view[df_behavior_view['user_segment'] == seg]
        if len(seg_data) > 0:
            with [seg_col1, seg_col2, seg_col3][i]:
                st.markdown(
                    f"""
                    <div class="metric-card" style="border-top: 4px solid {color};">
                        <h3 style="color: {color}; margin: 0 0 10px 0;">{icon} {seg}</h3>
                        <p style="font-size: 28px; font-weight: bold; color: #2C3E50; margin: 10px 0;">{len(seg_data):,} 人</p>
                        <p style="color: #7f8c8d; margin: 5px 0;">占比: {len(seg_data)/len(df_behavior_view)*100:.1f}%</p>
                        <hr style="margin: 15px 0;">
                        <p><strong>平均登录:</strong> {seg_data['login_frequency'].mean():.1f}次</p>
                        <p><strong>平均在线:</strong> {seg_data['online_hours'].mean():.1f}小时</p>
                        <p><strong>平均购买:</strong> {seg_data['purchase_count'].mean():.1f}次</p>
                        <p><strong>平均消费:</strong> ¥{seg_data['total_spent'].mean():,.0f}</p>
                        <p><strong>平均行为分:</strong> {seg_data['behavior_score'].mean():.1f}</p>
                    </div>
                    """,
                    unsafe_allow_html=True
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
        top_n = st.slider("显示排名靠前的省份数量", min_value=5, max_value=30, value=15, key="province_top_n")
        province_fig = create_province_rank_chart(df_full, top_n=top_n)
        st.pyplot(province_fig, use_container_width=True)
        if selected_province != "全部":
            st.caption("💡 该图表基于全量数据绘制，不受省份筛选影响")
    
    with col2:
        st.subheader("🌏 南北方用户分布对比")
        region_ns_fig = create_region_ns_chart(df_full)
        st.pyplot(region_ns_fig, use_container_width=True)
        if selected_province != "全部":
            st.caption("💡 该图表基于全量数据绘制，不受省份筛选影响")

    st.markdown("---")

    bcol1, bcol2 = st.columns(2)

    with bcol1:
        st.subheader("🥧 用户行为分群分布")
        behavior_pie_fig = create_behavior_pie_chart(df_behavior_view)
        st.pyplot(behavior_pie_fig, use_container_width=True)

    with bcol2:
        st.subheader("📊 行为群体关键指标对比")
        segment_compare_fig = create_segment_comparison_chart(df_behavior_view)
        st.pyplot(segment_compare_fig, use_container_width=True)
    
    st.markdown("---")

    st.subheader("📋 行为分群统计摘要")
    segment_summary = get_segment_summary(df_filtered if len(df_filtered) > 0 else df_full)
    st.dataframe(segment_summary, use_container_width=True, hide_index=True)
    
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
        st.markdown("### 省份统计前十")
        province_summary = df_filtered['province'].value_counts().head(10).reset_index()
        province_summary.columns = ['省份', '用户数']
        province_summary['占比'] = (province_summary['用户数'] / len(df_filtered) * 100).round(2).astype(str) + '%'
        st.dataframe(province_summary, use_container_width=True, hide_index=True)
    
    if selected_province != "全部":
        st.markdown("---")
        st.subheader(f"🏙️ {selected_province} 城市分布前十")
        city_summary = df_filtered['city'].value_counts().head(10).reset_index()
        city_summary.columns = ['城市', '用户数']
        city_summary['占比'] = (city_summary['用户数'] / len(df_filtered) * 100).round(2).astype(str) + '%'
        st.dataframe(city_summary, use_container_width=True, hide_index=True)
    
    if show_data:
        st.markdown("---")
        st.subheader("📄 原始数据预览")
        display_cols = [
            'user_id', 'gender', 'age', 'age_group', 'province', 'city', 'region_type',
            'user_segment', 'login_frequency', 'online_hours', 'purchase_count',
            'total_spent', 'last_active_days', 'page_views', 'click_count', 'behavior_score'
        ]
        available_cols = [col for col in display_cols if col in df_filtered.columns]
        st.dataframe(df_filtered[available_cols].head(100), use_container_width=True)
    
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: #7f8c8d; padding: 20px;'>
            <p>💡 用户画像分析系统 | 基于 Streamlit 与 Matplotlib 构建</p>
            <p>数据为模拟生成，仅用于演示目的</p>
        </div>
        """,
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
