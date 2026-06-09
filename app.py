import streamlit as st
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from wordcloud import WordCloud
import warnings
from region_data import (
    PROVINCE_CITY_MAP,
    PROVINCE_WEIGHTS,
    get_region_type,
    get_all_provinces,
    get_cities_by_province,
    get_city_type,
    get_province_capital
)
from user_behavior import (
    generate_behavior_data,
    calculate_behavior_scores,
    segment_users,
    get_segment_summary
)
from theme_config import (
    THEMES,
    DEFAULT_THEME,
    get_theme,
    get_theme_options,
    generate_css
)
import os
import sys as _sys
def get_available_chinese_font():
    if _sys.platform.startswith('win'):
        candidates = [
            'C:/Windows/Fonts/simhei.ttf',
            'C:/Windows/Fonts/msyh.ttc',
            'C:/Windows/Fonts/msyhbd.ttc',
            'C:/Windows/Fonts/simsun.ttc',
            'C:/Windows/Fonts/simkai.ttf',
            'C:/Windows/Fonts/simfang.ttf'
        ]
    elif _sys.platform == 'darwin':
        candidates = [
            '/System/Library/Fonts/PingFang.ttc',
            '/System/Library/Fonts/STHeiti Light.ttc',
            '/System/Library/Fonts/Hiragino Sans GB.ttc',
            '/Library/Fonts/Arial Unicode.ttf'
        ]
    else:
        candidates = [
            '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc',
            '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
            '/usr/share/fonts/truetype/arphic/uming.ttc',
            '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
        ]
    for font_path in candidates:
        if os.path.exists(font_path):
            return font_path
    return None

from user_preferences import (
    generate_preference_data,
    get_preference_ranking,
    get_concentration_stats,
    get_gender_preference_comparison,
    get_preference_wordcloud_data,
    PREFERENCE_TYPES,
    TAG_CATEGORIES
)
from utils import (
    export_data,
    generate_export_filename,
    get_data_statistics,
    get_export_mime_type
)

warnings.filterwarnings('ignore')

if 'theme' not in st.session_state:
    st.session_state.theme = DEFAULT_THEME

current_theme = get_theme(st.session_state.theme)

st.set_page_config(
    page_title="用户画像分析",
    page_icon="👥",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown(generate_css(current_theme), unsafe_allow_html=True)

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
    
    def get_generation(age):
        current_year = 2026
        birth_year = current_year - age
        if 2000 <= birth_year <= 2009:
            return '00后'
        elif 1990 <= birth_year <= 1999:
            return '90后'
        elif 1980 <= birth_year <= 1989:
            return '80后'
        elif 1970 <= birth_year <= 1979:
            return '70后'
        elif 1960 <= birth_year <= 1969:
            return '60后'
        else:
            return '其他'
    
    GENERATION_ORDER = ['00后', '90后', '80后', '70后', '60后', '其他']
    
    age_groups = [get_age_group(age) for age in ages]
    generations = [get_generation(age) for age in ages]
    
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
    city_types = [get_city_type(p, c) for p, c in zip(provinces, cities)]
    
    df = pd.DataFrame({
        'user_id': user_ids,
        'gender': genders,
        'age': ages,
        'age_group': age_groups,
        'generation': generations,
        'province': provinces,
        'city': cities,
        'region_type': region_types,
        'city_type': city_types
    })
    
    return df


def create_gender_chart(df, theme=None):
    if theme is None:
        theme = get_theme(st.session_state.get('theme', DEFAULT_THEME))
    tc = theme['colors']
    tchart = theme['chart']

    fig, ax = plt.subplots(figsize=(10, 5))
    fig.patch.set_facecolor(tchart['figure_facecolor'])
    ax.set_facecolor(tchart['axes_facecolor'])

    font_prop = FontProperties(family='SimHei', size=12)
    font_title = FontProperties(family='SimHei', size=16, weight='bold')
    font_label = FontProperties(family='SimHei', size=12, weight='bold')
    font_text = FontProperties(family='SimHei', size=11, weight='bold')

    gender_counts = df['gender'].value_counts()
    colors = tchart['palette_bar']

    bars = ax.barh(
        gender_counts.index,
        gender_counts.values,
        color=colors,
        edgecolor=tchart['axes_facecolor'],
        linewidth=2
    )

    ax.set_xlabel('用户数量', fontproperties=font_label, color=tchart['label_color'])
    ax.set_ylabel('性别', fontproperties=font_label, color=tchart['label_color'])
    ax.set_title('用户性别分布', fontproperties=font_title, pad=20, color=tchart['text_color'])

    total = len(df)
    for i, (bar, count) in enumerate(zip(bars, gender_counts.values)):
        percentage = (count / total) * 100
        ax.text(
            bar.get_width() + 20,
            bar.get_y() + bar.get_height()/2,
            f'{count:,} ({percentage:.1f}%)',
            va='center',
            fontproperties=font_text,
            color=tchart['text_color']
        )

    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_fontproperties(font_prop)
        label.set_color(tchart['tick_color'])

    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color(tchart['grid_color'])
    ax.spines['bottom'].set_color(tchart['grid_color'])
    ax.xaxis.grid(True, alpha=0.3, linestyle='--', color=tchart['grid_color'])
    ax.set_axisbelow(True)

    plt.tight_layout()
    return fig


def create_age_gender_chart(df, theme=None):
    if theme is None:
        theme = get_theme(st.session_state.get('theme', DEFAULT_THEME))
    tchart = theme['chart']

    fig, ax = plt.subplots(figsize=(12, 6))
    fig.patch.set_facecolor(tchart['figure_facecolor'])
    ax.set_facecolor(tchart['axes_facecolor'])

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
                   label='男', color=tchart['palette_bar'][0], edgecolor=tchart['axes_facecolor'], linewidth=1.5)
    bars2 = ax.bar(x + width/2, female_counts, width,
                   label='女', color=tchart['palette_bar'][1], edgecolor=tchart['axes_facecolor'], linewidth=1.5)

    ax.set_xlabel('年龄段', fontproperties=font_label, color=tchart['label_color'])
    ax.set_ylabel('用户数量', fontproperties=font_label, color=tchart['label_color'])
    ax.set_title('用户年龄与性别分布', fontproperties=font_title, pad=20, color=tchart['text_color'])
    ax.set_xticks(x)
    ax.set_xticklabels(age_order, fontproperties=font_prop)
    legend = ax.legend(prop=font_legend, frameon=True, shadow=True)
    legend.get_frame().set_facecolor(tchart['axes_facecolor'])
    for text in legend.get_texts():
        text.set_color(tchart['text_color'])

    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_fontproperties(font_prop)
        label.set_color(tchart['tick_color'])

    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color(tchart['grid_color'])
    ax.spines['bottom'].set_color(tchart['grid_color'])
    ax.yaxis.grid(True, alpha=0.3, linestyle='--', color=tchart['grid_color'])
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
                color=tchart['text_color']
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
                color=tchart['text_color']
            )

    plt.tight_layout()
    return fig


def create_province_rank_chart(df, top_n=15, theme=None):
    if theme is None:
        theme = get_theme(st.session_state.get('theme', DEFAULT_THEME))
    tchart = theme['chart']

    fig, ax = plt.subplots(figsize=(12, 8))
    fig.patch.set_facecolor(tchart['figure_facecolor'])
    ax.set_facecolor(tchart['axes_facecolor'])

    font_prop = FontProperties(family='SimHei', size=10)
    font_title = FontProperties(family='SimHei', size=16, weight='bold')
    font_label = FontProperties(family='SimHei', size=12, weight='bold')
    font_text = FontProperties(family='SimHei', size=10, weight='bold')

    province_counts = df['province'].value_counts().head(top_n)

    colors = sns.color_palette(tchart['palette_province'], len(province_counts))

    bars = ax.barh(
        province_counts.index[::-1],
        province_counts.values[::-1],
        color=colors,
        edgecolor=tchart['axes_facecolor'],
        linewidth=1.5
    )

    ax.set_xlabel('用户数量', fontproperties=font_label, color=tchart['label_color'])
    ax.set_ylabel('省份', fontproperties=font_label, color=tchart['label_color'])
    ax.set_title(f'用户省份分布前{top_n}名', fontproperties=font_title, pad=20, color=tchart['text_color'])

    total = len(df)
    for i, (bar, count) in enumerate(zip(bars, province_counts.values[::-1])):
        percentage = (count / total) * 100
        ax.text(
            bar.get_width() + 10,
            bar.get_y() + bar.get_height() / 2,
            f'{count:,} ({percentage:.1f}%)',
            va='center',
            fontproperties=font_text,
            color=tchart['text_color']
        )

    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_fontproperties(font_prop)
        label.set_color(tchart['tick_color'])

    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color(tchart['grid_color'])
    ax.spines['bottom'].set_color(tchart['grid_color'])
    ax.xaxis.grid(True, alpha=0.3, linestyle='--', color=tchart['grid_color'])
    ax.set_axisbelow(True)

    plt.tight_layout()
    return fig


def create_region_ns_chart(df, theme=None):
    if theme is None:
        theme = get_theme(st.session_state.get('theme', DEFAULT_THEME))
    tchart = theme['chart']

    fig, ax = plt.subplots(figsize=(10, 6))
    fig.patch.set_facecolor(tchart['figure_facecolor'])
    ax.set_facecolor(tchart['axes_facecolor'])

    font_prop = FontProperties(family='SimHei', size=12)
    font_title = FontProperties(family='SimHei', size=16, weight='bold')
    font_label = FontProperties(family='SimHei', size=12, weight='bold')
    font_text = FontProperties(family='SimHei', size=12, weight='bold')

    region_counts = df['region_type'].value_counts()
    region_order = ['南方', '北方']
    region_counts = region_counts.reindex(region_order)
    region_counts = region_counts.fillna(0)

    colors = tchart['palette_region']

    bars = ax.bar(
        region_counts.index,
        region_counts.values,
        color=colors,
        edgecolor=tchart['axes_facecolor'],
        linewidth=2,
        width=0.5
    )

    ax.set_xlabel('地域', fontproperties=font_label, color=tchart['label_color'])
    ax.set_ylabel('用户数量', fontproperties=font_label, color=tchart['label_color'])
    ax.set_title('南北方用户分布对比', fontproperties=font_title, pad=20, color=tchart['text_color'])

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
            color=tchart['text_color']
        )

    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_fontproperties(font_prop)
        label.set_color(tchart['tick_color'])

    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color(tchart['grid_color'])
    ax.spines['bottom'].set_color(tchart['grid_color'])
    ax.yaxis.grid(True, alpha=0.3, linestyle='--', color=tchart['grid_color'])
    ax.set_axisbelow(True)

    plt.tight_layout()
    return fig


def create_city_distribution_chart(df, province, top_n=10, theme=None):
    if theme is None:
        theme = get_theme(st.session_state.get('theme', DEFAULT_THEME))
    tchart = theme['chart']

    fig, ax = plt.subplots(figsize=(12, 8))
    fig.patch.set_facecolor(tchart['figure_facecolor'])
    ax.set_facecolor(tchart['axes_facecolor'])

    font_prop = FontProperties(family='SimHei', size=10)
    font_title = FontProperties(family='SimHei', size=16, weight='bold')
    font_label = FontProperties(family='SimHei', size=12, weight='bold')
    font_text = FontProperties(family='SimHei', size=10, weight='bold')

    city_counts = df['city'].value_counts().head(top_n)

    colors = sns.color_palette(tchart['palette_province'], len(city_counts))

    bars = ax.barh(
        city_counts.index[::-1],
        city_counts.values[::-1],
        color=colors,
        edgecolor=tchart['axes_facecolor'],
        linewidth=1.5
    )

    ax.set_xlabel('用户数量', fontproperties=font_label, color=tchart['label_color'])
    ax.set_ylabel('城市', fontproperties=font_label, color=tchart['label_color'])
    ax.set_title(f'{province} 城市用户分布前{top_n}名', fontproperties=font_title, pad=20, color=tchart['text_color'])

    total = len(df)
    for i, (bar, count) in enumerate(zip(bars, city_counts.values[::-1])):
        percentage = (count / total) * 100 if total > 0 else 0
        ax.text(
            bar.get_width() + max(city_counts.values) * 0.01,
            bar.get_y() + bar.get_height() / 2,
            f'{count:,} ({percentage:.1f}%)',
            va='center',
            fontproperties=font_text,
            color=tchart['text_color']
        )

    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_fontproperties(font_prop)
        label.set_color(tchart['tick_color'])

    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color(tchart['grid_color'])
    ax.spines['bottom'].set_color(tchart['grid_color'])
    ax.xaxis.grid(True, alpha=0.3, linestyle='--', color=tchart['grid_color'])
    ax.set_axisbelow(True)

    plt.tight_layout()
    return fig


def create_city_type_comparison_chart(df, province, theme=None):
    if theme is None:
        theme = get_theme(st.session_state.get('theme', DEFAULT_THEME))
    tchart = theme['chart']

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.patch.set_facecolor(tchart['figure_facecolor'])

    font_prop = FontProperties(family='SimHei', size=10)
    font_title = FontProperties(family='SimHei', size=14, weight='bold')
    font_label = FontProperties(family='SimHei', size=11, weight='bold')
    font_text = FontProperties(family='SimHei', size=9, weight='bold')

    city_type_order = ['省会城市', '地级市', '县级市', '直辖市辖区']
    available_types = [t for t in city_type_order if t in df['city_type'].unique()]

    if not available_types:
        available_types = list(df['city_type'].unique())

    colors = tchart['palette_segment']
    if len(colors) < len(available_types):
        colors = sns.color_palette(tchart['palette_province'], len(available_types))

    summary = df.groupby('city_type', observed=True).agg({
        'user_id': 'count',
        'total_spent': 'sum',
        'behavior_score': 'mean',
        'login_frequency': 'mean'
    })

    summary = summary.reindex(available_types).fillna(0)

    metrics = [
        ('user_id', '用户数量（人）', axes[0, 0]),
        ('total_spent', '总消费金额（元）', axes[0, 1]),
        ('behavior_score', '平均行为得分', axes[1, 0]),
        ('login_frequency', '平均登录频率（次）', axes[1, 1])
    ]

    for col, title, ax in metrics:
        ax.set_facecolor(tchart['axes_facecolor'])
        values = summary[col].values
        bars = ax.bar(
            range(len(available_types)),
            values,
            color=colors[:len(available_types)],
            edgecolor=tchart['axes_facecolor'],
            linewidth=2,
            width=0.6
        )

        ax.set_xticks(range(len(available_types)))
        ax.set_xticklabels(available_types, fontproperties=font_prop)
        ax.set_title(title, fontproperties=font_title, pad=10, color=tchart['text_color'])
        ax.set_ylabel('数值', fontproperties=font_label, color=tchart['label_color'])

        for label in ax.get_xticklabels() + ax.get_yticklabels():
            label.set_fontproperties(font_prop)
            label.set_color(tchart['tick_color'])

        for bar, val in zip(bars, values):
            display_val = f'{val:,.0f}' if col in ['user_id', 'total_spent'] else f'{val:.1f}'
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + max(values) * 0.02 if max(values) > 0 else 0.1,
                display_val,
                ha='center',
                fontproperties=font_text,
                color=tchart['text_color']
            )

        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color(tchart['grid_color'])
        ax.spines['bottom'].set_color(tchart['grid_color'])
        ax.yaxis.grid(True, alpha=0.3, linestyle='--', color=tchart['grid_color'])
        ax.set_axisbelow(True)

    fig.suptitle(f'{province} 不同城市类型对比分析', fontproperties=font_title, fontsize=16, y=1.02, color=tchart['text_color'])
    plt.tight_layout()
    return fig


def get_city_level_stats(df):
    city_stats = df.groupby('city', observed=True).agg({
        'user_id': 'count',
        'total_spent': ['sum', 'mean'],
        'behavior_score': 'mean',
        'login_frequency': 'mean',
        'online_hours': 'mean',
        'purchase_count': 'mean'
    }).round(2)

    city_stats.columns = [
        '用户数量', '总消费金额', '平均消费金额',
        '平均行为得分', '平均登录频率', '平均在线时长', '平均购买次数'
    ]
    city_stats = city_stats.reset_index()
    city_stats = city_stats.rename(columns={'city': '城市'})

    total_users = city_stats['用户数量'].sum()
    city_stats['用户占比(%)'] = (city_stats['用户数量'] / total_users * 100).round(2)
    city_stats = city_stats.sort_values('用户数量', ascending=False).reset_index(drop=True)
    city_stats.insert(0, '排名', range(1, len(city_stats) + 1))

    return city_stats


def get_province_city_overview(df):
    overview = df.groupby('province', observed=True).agg({
        'city': 'nunique',
        'user_id': 'count',
        'total_spent': ['sum', 'mean'],
        'behavior_score': 'mean'
    }).round(2)

    overview.columns = [
        '覆盖城市数', '用户数量', '总消费金额', '平均消费金额', '平均行为得分'
    ]
    overview = overview.reset_index()
    overview = overview.rename(columns={'province': '省份'})

    total_users = overview['用户数量'].sum()
    overview['用户占比(%)'] = (overview['用户数量'] / total_users * 100).round(2)
    overview = overview.sort_values('用户数量', ascending=False).reset_index(drop=True)
    overview.insert(0, '排名', range(1, len(overview) + 1))

    return overview


def get_city_top10_table(df):
    stats = get_city_level_stats(df)
    top10 = stats.head(10).copy()

    result = top10[['排名', '城市', '用户数量', '总消费金额', '平均行为得分']].copy()
    result = result.rename(columns={'平均行为得分': '活跃度'})
    result['总消费金额'] = result['总消费金额'].apply(lambda x: f"¥{x:,.2f}")
    result['活跃度'] = result['活跃度'].round(1)

    return result


def create_behavior_pie_chart(df, theme=None):
    if theme is None:
        theme = get_theme(st.session_state.get('theme', DEFAULT_THEME))
    tchart = theme['chart']

    fig, ax = plt.subplots(figsize=(10, 8))
    fig.patch.set_facecolor(tchart['figure_facecolor'])
    ax.set_facecolor(tchart['axes_facecolor'])

    font_prop = FontProperties(family='SimHei', size=12)
    font_title = FontProperties(family='SimHei', size=16, weight='bold')
    font_text = FontProperties(family='SimHei', size=13, weight='bold')

    segment_counts = df['user_segment'].value_counts()
    segment_order = ['活跃用户', '普通用户', '沉睡用户']
    segment_counts = segment_counts.reindex(segment_order)
    segment_counts = segment_counts.fillna(0)

    colors = tchart['palette_segment']
    explode = (0.05, 0.03, 0.03)

    wedges, texts, autotexts = ax.pie(
        segment_counts.values,
        labels=segment_counts.index,
        colors=colors,
        autopct='%1.1f%%',
        startangle=90,
        explode=explode,
        pctdistance=0.75,
        wedgeprops=dict(edgecolor=tchart['figure_facecolor'], linewidth=3)
    )

    for text in texts:
        text.set_fontproperties(font_text)
        text.set_color(tchart['text_color'])
    for autotext in autotexts:
        autotext.set_fontproperties(font_text)
        autotext.set_color(tchart['pie_text_color'])

    total = segment_counts.sum()
    legend_labels = [
        f'{seg}: {int(cnt)}人 ({cnt/total*100:.1f}%)'
        for seg, cnt in zip(segment_counts.index, segment_counts.values)
    ]
    legend = ax.legend(
        wedges, legend_labels,
        loc='center left',
        bbox_to_anchor=(1, 0.5),
        prop=font_prop,
        frameon=True,
        shadow=True
    )
    legend.get_frame().set_facecolor(tchart['axes_facecolor'])
    for text in legend.get_texts():
        text.set_color(tchart['text_color'])

    ax.set_title('用户行为分群分布', fontproperties=font_title, pad=20, color=tchart['text_color'])

    plt.tight_layout()
    return fig


def create_segment_comparison_chart(df, theme=None):
    if theme is None:
        theme = get_theme(st.session_state.get('theme', DEFAULT_THEME))
    tchart = theme['chart']

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.patch.set_facecolor(tchart['figure_facecolor'])

    font_prop = FontProperties(family='SimHei', size=10)
    font_title = FontProperties(family='SimHei', size=14, weight='bold')
    font_label = FontProperties(family='SimHei', size=11, weight='bold')
    font_text = FontProperties(family='SimHei', size=9, weight='bold')

    segment_order = ['活跃用户', '普通用户', '沉睡用户']
    colors = tchart['palette_segment']

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
        ax.set_facecolor(tchart['axes_facecolor'])
        values = summary[col].values
        bars = ax.bar(
            range(len(segment_order)),
            values,
            color=colors,
            edgecolor=tchart['axes_facecolor'],
            linewidth=2,
            width=0.6
        )

        ax.set_xticks(range(len(segment_order)))
        ax.set_xticklabels(segment_order, fontproperties=font_prop)
        ax.set_title(title, fontproperties=font_title, pad=10, color=tchart['text_color'])
        ax.set_ylabel('数值', fontproperties=font_label, color=tchart['label_color'])

        for label in ax.get_xticklabels() + ax.get_yticklabels():
            label.set_fontproperties(font_prop)
            label.set_color(tchart['tick_color'])

        for bar, val in zip(bars, values):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + max(values) * 0.02,
                f'{val:.1f}',
                ha='center',
                fontproperties=font_text,
                color=tchart['text_color']
            )

        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color(tchart['grid_color'])
        ax.spines['bottom'].set_color(tchart['grid_color'])
        ax.yaxis.grid(True, alpha=0.3, linestyle='--', color=tchart['grid_color'])
        ax.set_axisbelow(True)

    fig.suptitle('不同行为群体关键指标对比', fontproperties=font_title, fontsize=16, y=1.02, color=tchart['text_color'])
    plt.tight_layout()
    return fig


GENERATION_ORDER = ['00后', '90后', '80后', '70后', '60后', '其他']


def create_generation_pie_chart(df, theme=None):
    if theme is None:
        theme = get_theme(st.session_state.get('theme', DEFAULT_THEME))
    tchart = theme['chart']

    fig, ax = plt.subplots(figsize=(10, 8))
    fig.patch.set_facecolor(tchart['figure_facecolor'])
    ax.set_facecolor(tchart['axes_facecolor'])

    font_prop = FontProperties(family='SimHei', size=12)
    font_title = FontProperties(family='SimHei', size=16, weight='bold')
    font_text = FontProperties(family='SimHei', size=13, weight='bold')

    generation_counts = df['generation'].value_counts()
    generation_counts = generation_counts.reindex(GENERATION_ORDER)
    generation_counts = generation_counts.fillna(0)
    generation_counts = generation_counts[generation_counts > 0]

    colors = sns.color_palette(tchart['palette_segment'], len(generation_counts))
    if len(colors) < len(generation_counts):
        colors = sns.color_palette(tchart['palette_province'], len(generation_counts))

    explode = tuple([0.05] * len(generation_counts))

    wedges, texts, autotexts = ax.pie(
        generation_counts.values,
        labels=generation_counts.index,
        colors=colors,
        autopct='%1.1f%%',
        startangle=90,
        explode=explode,
        pctdistance=0.75,
        wedgeprops=dict(edgecolor=tchart['figure_facecolor'], linewidth=3)
    )

    for text in texts:
        text.set_fontproperties(font_text)
        text.set_color(tchart['text_color'])
    for autotext in autotexts:
        autotext.set_fontproperties(font_text)
        autotext.set_color(tchart['pie_text_color'])

    total = generation_counts.sum()
    legend_labels = [
        f'{gen}: {int(cnt)}人 ({cnt/total*100:.1f}%)'
        for gen, cnt in zip(generation_counts.index, generation_counts.values)
    ]
    legend = ax.legend(
        wedges, legend_labels,
        loc='center left',
        bbox_to_anchor=(1, 0.5),
        prop=font_prop,
        frameon=True,
        shadow=True
    )
    legend.get_frame().set_facecolor(tchart['axes_facecolor'])
    for text in legend.get_texts():
        text.set_color(tchart['text_color'])

    ax.set_title('各代际用户数量占比', fontproperties=font_title, pad=20, color=tchart['text_color'])

    plt.tight_layout()
    return fig


def create_generation_consumption_chart(df, theme=None):
    if theme is None:
        theme = get_theme(st.session_state.get('theme', DEFAULT_THEME))
    tchart = theme['chart']

    from user_preferences import aggregate_preferences, TAG_CATEGORIES

    fig, ax = plt.subplots(figsize=(14, 8))
    fig.patch.set_facecolor(tchart['figure_facecolor'])
    ax.set_facecolor(tchart['axes_facecolor'])

    font_prop = FontProperties(family='SimHei', size=10)
    font_title = FontProperties(family='SimHei', size=16, weight='bold')
    font_label = FontProperties(family='SimHei', size=12, weight='bold')
    font_text = FontProperties(family='SimHei', size=9, weight='bold')
    font_legend = FontProperties(family='SimHei', size=11)

    available_generations = [g for g in GENERATION_ORDER if g in df['generation'].unique()]
    consumption_tags = TAG_CATEGORIES['consumption'][:8]

    generation_prefs = aggregate_preferences(df, 'consumption', group_col='generation')

    data = {}
    for gen in available_generations:
        gen_prefs = generation_prefs.get(gen, {})
        gen_total = sum(gen_prefs.values()) or 1
        data[gen] = {tag: gen_prefs.get(tag, 0) / gen_total * 100 for tag in consumption_tags}

    result_df = pd.DataFrame(data)
    result_df = result_df.fillna(0)

    x = np.arange(len(consumption_tags))
    width = 0.12
    n_gens = len(available_generations)
    total_width = width * n_gens
    start_x = x - (total_width - width) / 2

    colors = sns.color_palette(tchart['palette_segment'], n_gens)
    if len(colors) < n_gens:
        colors = sns.color_palette(tchart['palette_province'], n_gens)

    bars_list = []
    for i, gen in enumerate(available_generations):
        bars = ax.bar(
            start_x + i * width,
            result_df[gen].values,
            width,
            label=gen,
            color=colors[i],
            edgecolor=tchart['axes_facecolor'],
            linewidth=1
        )
        bars_list.append(bars)

    ax.set_xlabel('消费偏好标签', fontproperties=font_label, color=tchart['label_color'])
    ax.set_ylabel('偏好占比 (%)', fontproperties=font_label, color=tchart['label_color'])
    ax.set_title('不同代际消费偏好对比', fontproperties=font_title, pad=20, color=tchart['text_color'])
    ax.set_xticks(x)
    ax.set_xticklabels(consumption_tags, fontproperties=font_prop, rotation=20, ha='right')

    legend = ax.legend(prop=font_legend, frameon=True, shadow=True)
    legend.get_frame().set_facecolor(tchart['axes_facecolor'])
    for text in legend.get_texts():
        text.set_color(tchart['text_color'])

    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_fontproperties(font_prop)
        label.set_color(tchart['tick_color'])

    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color(tchart['grid_color'])
    ax.spines['bottom'].set_color(tchart['grid_color'])
    ax.yaxis.grid(True, alpha=0.3, linestyle='--', color=tchart['grid_color'])
    ax.set_axisbelow(True)

    plt.tight_layout()
    return fig


def create_generation_interest_area_chart(df, theme=None):
    if theme is None:
        theme = get_theme(st.session_state.get('theme', DEFAULT_THEME))
    tchart = theme['chart']

    from user_preferences import aggregate_preferences, TAG_CATEGORIES

    fig, ax = plt.subplots(figsize=(14, 8))
    fig.patch.set_facecolor(tchart['figure_facecolor'])
    ax.set_facecolor(tchart['axes_facecolor'])

    font_prop = FontProperties(family='SimHei', size=10)
    font_title = FontProperties(family='SimHei', size=16, weight='bold')
    font_label = FontProperties(family='SimHei', size=12, weight='bold')
    font_legend = FontProperties(family='SimHei', size=11)

    available_generations = [g for g in GENERATION_ORDER if g in df['generation'].unique()]
    interest_tags = TAG_CATEGORIES['interest'][:10]

    generation_prefs = aggregate_preferences(df, 'interest', group_col='generation')

    data = {}
    for gen in available_generations:
        gen_prefs = generation_prefs.get(gen, {})
        gen_total = sum(gen_prefs.values()) or 1
        data[gen] = {tag: gen_prefs.get(tag, 0) / gen_total * 100 for tag in interest_tags}

    result_df = pd.DataFrame(data)
    result_df = result_df.fillna(0)

    colors = sns.color_palette(tchart['palette_segment'], len(available_generations))
    if len(colors) < len(available_generations):
        colors = sns.color_palette(tchart['palette_province'], len(available_generations))

    ax.stackplot(
        range(len(interest_tags)),
        [result_df[gen].values for gen in available_generations],
        labels=available_generations,
        colors=colors,
        alpha=0.85,
        edgecolor=tchart['axes_facecolor'],
        linewidth=0.5
    )

    ax.set_xlabel('兴趣标签', fontproperties=font_label, color=tchart['label_color'])
    ax.set_ylabel('偏好占比 (%)', fontproperties=font_label, color=tchart['label_color'])
    ax.set_title('代际与兴趣标签关系', fontproperties=font_title, pad=20, color=tchart['text_color'])
    ax.set_xticks(range(len(interest_tags)))
    ax.set_xticklabels(interest_tags, fontproperties=font_prop, rotation=30, ha='right')

    legend = ax.legend(prop=font_legend, frameon=True, shadow=True, loc='upper right')
    legend.get_frame().set_facecolor(tchart['axes_facecolor'])
    for text in legend.get_texts():
        text.set_color(tchart['text_color'])

    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_fontproperties(font_prop)
        label.set_color(tchart['tick_color'])

    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color(tchart['grid_color'])
    ax.spines['bottom'].set_color(tchart['grid_color'])
    ax.yaxis.grid(True, alpha=0.3, linestyle='--', color=tchart['grid_color'])
    ax.set_axisbelow(True)

    plt.tight_layout()
    return fig


def get_generation_summary(df):
    summary = df.groupby('generation', observed=True).agg({
        'user_id': 'count',
        'age': ['mean', 'min', 'max'],
        'login_frequency': 'mean',
        'online_hours': 'mean',
        'purchase_count': 'mean',
        'total_spent': 'mean',
        'behavior_score': 'mean'
    }).round(2)

    summary.columns = [
        '用户数量', '平均年龄', '最小年龄', '最大年龄',
        '平均登录频率', '平均在线时长', '平均购买次数',
        '平均消费金额', '平均行为得分'
    ]
    summary = summary.reset_index()
    summary = summary.rename(columns={'generation': '代际'})

    total_users = summary['用户数量'].sum()
    summary['用户占比(%)'] = (summary['用户数量'] / total_users * 100).round(2)
    summary['平均消费金额'] = summary['平均消费金额'].apply(lambda x: f"¥{x:,.2f}")

    ordered = []
    for gen in GENERATION_ORDER:
        gen_row = summary[summary['代际'] == gen]
        if len(gen_row) > 0:
            ordered.append(gen_row)
    if ordered:
        summary = pd.concat(ordered).reset_index(drop=True)

    return summary


def create_preference_wordcloud(df, pref_type, _version=3, theme=None):
    if theme is None:
        theme = get_theme(st.session_state.get('theme', DEFAULT_THEME))
    tchart = theme['chart']

    fig, ax = plt.subplots(figsize=(12, 8))
    fig.patch.set_facecolor(tchart['figure_facecolor'])
    ax.set_facecolor(tchart['axes_facecolor'])

    _fp = get_available_chinese_font()
    font_prop = FontProperties(fname=_fp, size=14, weight='bold') if _fp else FontProperties(family='SimHei', size=14, weight='bold')
    font_title = FontProperties(fname=_fp, size=16, weight='bold') if _fp else FontProperties(family='SimHei', size=16, weight='bold')

    word_freq = get_preference_wordcloud_data(df, pref_type)
    chinese_font_path = get_available_chinese_font()
    print(f"[DEBUG WordCloud] font_path={chinese_font_path}")

    wc_kwargs = dict(
        width=800,
        height=500,
        background_color=tchart['wordcloud_background'],
        colormap=tchart['wordcloud_colormap'],
        max_words=100,
        prefer_horizontal=0.9,
        min_font_size=10,
        max_font_size=100,
        margin=10,
        random_state=42
    )
    if chinese_font_path:
        wc_kwargs['font_path'] = chinese_font_path

    wc = WordCloud(**wc_kwargs)

    if word_freq:
        wc.generate_from_frequencies(word_freq)
        ax.imshow(wc, interpolation='bilinear')
    else:
        ax.text(0.5, 0.5, '暂无数据', fontproperties=font_prop,
                ha='center', va='center', transform=ax.transAxes, color=tchart['text_color'])

    ax.axis('off')
    ax.set_title(f'{PREFERENCE_TYPES[pref_type]}词云', fontproperties=font_title, pad=20, color=tchart['text_color'])

    plt.tight_layout()
    return fig


def create_gender_preference_chart(df_with_gender, pref_type, top_n=8, theme=None):
    if theme is None:
        theme = get_theme(st.session_state.get('theme', DEFAULT_THEME))
    tchart = theme['chart']

    fig, ax = plt.subplots(figsize=(12, 7))
    fig.patch.set_facecolor(tchart['figure_facecolor'])
    ax.set_facecolor(tchart['axes_facecolor'])

    _fp = get_available_chinese_font()
    font_prop = FontProperties(fname=_fp, size=11) if _fp else FontProperties(family='SimHei', size=11)
    font_title = FontProperties(fname=_fp, size=16, weight='bold') if _fp else FontProperties(family='SimHei', size=16, weight='bold')
    font_label = FontProperties(fname=_fp, size=12, weight='bold') if _fp else FontProperties(family='SimHei', size=12, weight='bold')
    font_text = FontProperties(fname=_fp, size=10, weight='bold') if _fp else FontProperties(family='SimHei', size=10, weight='bold')
    font_legend = FontProperties(fname=_fp, size=11) if _fp else FontProperties(family='SimHei', size=11)

    comp_df = get_gender_preference_comparison(df_with_gender, pref_type, top_n=top_n)

    if comp_df.empty:
        ax.text(0.5, 0.5, '暂无数据', fontproperties=font_prop,
                ha='center', va='center', transform=ax.transAxes, color=tchart['text_color'])
        ax.axis('off')
        ax.set_title(f'{PREFERENCE_TYPES[pref_type]}性别对比', fontproperties=font_title, pad=20, color=tchart['text_color'])
        plt.tight_layout()
        return fig

    y = np.arange(len(comp_df))
    width = 0.35

    male_values = comp_df['男'].values
    female_values = comp_df['女'].values
    labels = comp_df['标签'].values

    bars1 = ax.barh(y - width/2, male_values, width,
                    label='男', color=tchart['palette_bar'][0], edgecolor=tchart['axes_facecolor'], linewidth=1.5)
    bars2 = ax.barh(y + width/2, female_values, width,
                    label='女', color=tchart['palette_bar'][1], edgecolor=tchart['axes_facecolor'], linewidth=1.5)

    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontproperties=font_prop)
    ax.set_xlabel('偏好占比 (%)', fontproperties=font_label, color=tchart['label_color'])
    ax.set_title(f'{PREFERENCE_TYPES[pref_type]}性别对比前{top_n}名', fontproperties=font_title, pad=20, color=tchart['text_color'])
    legend = ax.legend(prop=font_legend, frameon=True, shadow=True)
    legend.get_frame().set_facecolor(tchart['axes_facecolor'])
    for text in legend.get_texts():
        text.set_color(tchart['text_color'])

    for bar in bars1:
        w = bar.get_width()
        if w > 0:
            ax.text(w + 0.1, bar.get_y() + bar.get_height()/2,
                    f'{w:.1f}%', va='center', fontproperties=font_text, color=tchart['text_color'])

    for bar in bars2:
        w = bar.get_width()
        if w > 0:
            ax.text(w + 0.1, bar.get_y() + bar.get_height()/2,
                    f'{w:.1f}%', va='center', fontproperties=font_text, color=tchart['text_color'])

    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_fontproperties(font_prop)
        label.set_color(tchart['tick_color'])

    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color(tchart['grid_color'])
    ax.spines['bottom'].set_color(tchart['grid_color'])
    ax.xaxis.grid(True, alpha=0.3, linestyle='--', color=tchart['grid_color'])
    ax.set_axisbelow(True)

    plt.tight_layout()
    return fig


def main():
    if 'export_result' not in st.session_state:
        st.session_state.export_result = None

    if 'theme' not in st.session_state:
        st.session_state.theme = DEFAULT_THEME

    st.sidebar.header("🎨 主题设置")
    theme_options = get_theme_options()
    theme_keys = [opt[0] for opt in theme_options]
    theme_labels = [opt[1] for opt in theme_options]
    current_theme_idx = theme_keys.index(st.session_state.theme) if st.session_state.theme in theme_keys else 0

    selected_theme = st.sidebar.selectbox(
        "选择主题",
        options=theme_keys,
        index=current_theme_idx,
        format_func=lambda x: theme_labels[theme_keys.index(x)],
        help="切换亮色或暗色主题"
    )

    if selected_theme != st.session_state.theme:
        st.session_state.theme = selected_theme
        st.rerun()

    theme = get_theme(st.session_state.theme)
    tc = theme['colors']

    st.title("👥 用户画像分析")
    st.markdown("---")

    st.sidebar.markdown("---")
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

    st.sidebar.subheader("👶 代际筛选")
    generation_options = GENERATION_ORDER
    selected_generation = st.sidebar.multiselect(
        "选择代际",
        options=generation_options,
        default=[],
        help="选择一个或多个代际查看该代际的详细画像数据"
    )

    st.sidebar.subheader("🎨 偏好分析")
    pref_type_options = list(PREFERENCE_TYPES.keys())
    pref_type_labels = list(PREFERENCE_TYPES.values())
    selected_pref_type = st.sidebar.selectbox(
        "选择偏好类型",
        options=pref_type_options,
        format_func=lambda x: PREFERENCE_TYPES[x],
        index=0,
        help="选择要查看的偏好维度：兴趣标签、消费偏好或渠道偏好"
    )
    gender_compare_top_n = st.sidebar.slider(
        "性别对比显示数量",
        min_value=3,
        max_value=15,
        value=8,
        step=1,
        help="性别偏好对比图中显示的标签数量"
    )
    ranking_top_n = st.sidebar.slider(
        "偏好排名显示数量",
        min_value=3,
        max_value=20,
        value=10,
        step=1,
        help="热门偏好标签排名显示的数量"
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

    st.sidebar.subheader("📥 数据导出")
    export_format = st.sidebar.selectbox(
        "选择导出格式",
        options=["CSV", "Excel"],
        index=0,
        help="选择要导出的数据格式"
    )
    export_scope = st.sidebar.selectbox(
        "导出范围",
        options=["用户明细数据", "省份级别汇总", "城市级别汇总"],
        index=0,
        help="选择要导出的数据范围：用户明细、省份汇总或城市汇总"
    )
    export_clicked = st.sidebar.button(
        "📤 导出数据",
        use_container_width=True,
        help="根据当前筛选条件导出数据"
    )

    df_profile = generate_mock_data(n_samples)
    df_behavior = generate_behavior_data(df_profile['user_id'].tolist())
    df_behavior = calculate_behavior_scores(df_behavior)
    df_behavior = segment_users(df_behavior)
    df_preferences = generate_preference_data(df_profile['user_id'].tolist())
    
    df = df_profile.merge(df_behavior, on='user_id', how='left')
    df = df.merge(df_preferences, on='user_id', how='left')
    
    df_filtered = df.copy()
    
    if selected_province != "全部":
        df_filtered = df_filtered[df_filtered['province'] == selected_province]

    if selected_segment:
        df_filtered = df_filtered[df_filtered['user_segment'].isin(selected_segment)]

    if selected_generation:
        df_filtered = df_filtered[df_filtered['generation'].isin(selected_generation)]

    df_filtered = df_filtered[df_filtered['login_frequency'] >= min_login_freq]
    df_filtered = df_filtered[df_filtered['purchase_count'] >= min_purchase]
    df_filtered = df_filtered[df_filtered['online_hours'] >= min_online_hours]
    
    df_full = df

    if export_clicked:
        if len(df_filtered) == 0:
            st.warning("⚠️ 当前筛选条件下没有数据可导出，请调整筛选条件后重试。")
        else:
            try:
                export_format_ext = 'csv' if export_format == 'CSV' else 'xlsx'
                
                if export_scope == "城市级别汇总":
                    export_df = df_filtered.groupby(['province', 'city', 'city_type'], observed=True).agg({
                        'user_id': 'count',
                        'total_spent': ['sum', 'mean'],
                        'behavior_score': 'mean',
                        'login_frequency': 'mean',
                        'online_hours': 'mean',
                        'purchase_count': 'mean'
                    }).round(2)
                    export_df.columns = [
                        '用户数量', '总消费金额', '平均消费金额',
                        '平均行为得分', '平均登录频率', '平均在线时长', '平均购买次数'
                    ]
                    export_df = export_df.reset_index()
                    export_df = export_df.rename(columns={
                        'province': '省份', 'city': '城市', 'city_type': '城市类型'
                    })
                    total_users_city = export_df['用户数量'].sum()
                    export_df['用户占比(%)'] = (export_df['用户数量'] / total_users_city * 100).round(2)
                    export_df = export_df.sort_values(['省份', '用户数量'], ascending=[True, False]).reset_index(drop=True)
                    export_df.insert(0, '序号', range(1, len(export_df) + 1))
                    export_prefix = "city_level_summary"
                    
                elif export_scope == "省份级别汇总":
                    export_df = df_filtered.groupby(['province', 'region_type'], observed=True).agg({
                        'user_id': 'count',
                        'city': 'nunique',
                        'total_spent': ['sum', 'mean'],
                        'behavior_score': 'mean',
                        'login_frequency': 'mean',
                        'online_hours': 'mean',
                        'purchase_count': 'mean'
                    }).round(2)
                    export_df.columns = [
                        '用户数量', '覆盖城市数', '总消费金额', '平均消费金额',
                        '平均行为得分', '平均登录频率', '平均在线时长', '平均购买次数'
                    ]
                    export_df = export_df.reset_index()
                    export_df = export_df.rename(columns={
                        'province': '省份', 'region_type': '地域类型'
                    })
                    total_users_prov = export_df['用户数量'].sum()
                    export_df['用户占比(%)'] = (export_df['用户数量'] / total_users_prov * 100).round(2)
                    export_df = export_df.sort_values('用户数量', ascending=False).reset_index(drop=True)
                    export_df.insert(0, '排名', range(1, len(export_df) + 1))
                    export_prefix = "province_level_summary"
                    
                else:
                    export_df = df_filtered.copy()
                    display_cols = [
                        'user_id', 'gender', 'age', 'age_group', 'generation', 'province', 'city', 'region_type', 'city_type',
                        'user_segment', 'login_frequency', 'online_hours', 'purchase_count',
                        'total_spent', 'last_active_days', 'page_views', 'click_count',
                        'login_score', 'online_score', 'purchase_score', 'spent_score',
                        'activity_score', 'behavior_score',
                        'top_interest', 'top_consumption', 'top_channel',
                        'interest_concentration', 'consumption_concentration', 'channel_concentration'
                    ]
                    available_cols = [col for col in display_cols if col in export_df.columns]
                    export_df = export_df[available_cols]
                    export_prefix = "user_profile_data"
                
                exported_data = export_data(export_df, export_format_ext, export_scope)
                filename = generate_export_filename(export_format_ext, prefix=export_prefix)
                mime_type = get_export_mime_type(export_format_ext)
                stats = get_data_statistics(export_df)
                file_size_kb = round(len(exported_data) / 1024, 2)
                
                filter_summary = {
                    'n_samples': n_samples,
                    'selected_province': selected_province,
                    'selected_segment': selected_segment,
                    'selected_generation': selected_generation,
                    'min_login_freq': min_login_freq,
                    'min_purchase': min_purchase,
                    'min_online_hours': min_online_hours,
                    'export_scope': export_scope
                }

                st.session_state.export_result = {
                    'exported_data': exported_data,
                    'filename': filename,
                    'mime_type': mime_type,
                    'stats': stats,
                    'file_size_kb': file_size_kb,
                    'export_format': export_format,
                    'export_scope': export_scope,
                    'filter_summary': filter_summary,
                    'success': True
                }

            except Exception as e:
                st.session_state.export_result = {
                    'success': False,
                    'error': str(e),
                    'export_format': export_format
                }
    
    if st.session_state.export_result is not None:
        result = st.session_state.export_result
        if not result.get('success', False):
            st.error(f"❌ 导出失败: {result.get('error', '未知错误')}")
            if result.get('export_format') == 'Excel' and 'openpyxl' in result.get('error', '').lower():
                st.info("💡 提示: Excel 导出需要安装 openpyxl 库，请运行 `pip install openpyxl` 安装后重试。")
        else:
            st.success("✅ 数据导出成功！")
            
            export_container = st.container()
            with export_container:
                st.markdown("### 📦 导出文件信息")
                st.markdown("---")
                
                download_key = f"download_{result['filename']}_{hash(result['filename'])}"
                st.download_button(
                    label=f"⬇️ 下载 {result['filename']}",
                    data=result['exported_data'],
                    file_name=result['filename'],
                    mime=result['mime_type'],
                    use_container_width=True,
                    key=download_key
                )
                
                st.markdown("#### 🔍 导出时筛选条件")
                fs = result['filter_summary']
                filter_col1, filter_col2, filter_col3, filter_col4 = st.columns(4)
                with filter_col1:
                    st.markdown(f"- **样本数量**: {fs['n_samples']:,}")
                    st.markdown(f"- **选择省份**: {fs['selected_province']}")
                with filter_col2:
                    segment_text = '、'.join(fs['selected_segment']) if fs['selected_segment'] else '全部'
                    gen_text = '、'.join(fs.get('selected_generation', [])) if fs.get('selected_generation') else '全部'
                    st.markdown(f"- **行为群体**: {segment_text}")
                    st.markdown(f"- **代际**: {gen_text}")
                    st.markdown(f"- **最低登录频率**: {fs['min_login_freq']} 次")
                with filter_col3:
                    st.markdown(f"- **最低购买次数**: {fs['min_purchase']} 次")
                    st.markdown(f"- **最低在线时长**: {fs['min_online_hours']:.1f} 小时")
                with filter_col4:
                    st.markdown(f"- **导出范围**: {fs.get('export_scope', '用户明细数据')}")
                
                st.markdown("---")
                st.markdown("#### 📊 导出数据统计")
                stat_scope = result.get('export_scope', '用户明细数据')
                
                stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)
                with stat_col1:
                    if stat_scope == "城市级别汇总":
                        st.metric("城市数", f"{result['stats']['total_records']:,}")
                    elif stat_scope == "省份级别汇总":
                        st.metric("省份记录数", f"{result['stats']['total_records']:,}")
                    else:
                        st.metric("用户数", f"{result['stats']['total_records']:,}")
                with stat_col2:
                    st.metric("字段数", f"{result['stats']['total_columns']}")
                with stat_col3:
                    st.metric("文件大小", f"{result['file_size_kb']} KB")
                with stat_col4:
                    st.metric("导出格式", result['export_format'])
                
                st.markdown("---")
                detail_col1, detail_col2 = st.columns(2)
                
                with detail_col1:
                    if stat_scope in ["城市级别汇总", "省份级别汇总"]:
                        st.markdown("##### 🏙️ 汇总覆盖范围")
                        if result['stats'].get('province_count'):
                            st.markdown(f"- **覆盖省份**: {result['stats']['province_count']} 个")
                        if stat_scope == "城市级别汇总" and result['stats'].get('city_count'):
                            st.markdown(f"- **覆盖城市**: {result['stats']['city_count']} 个")
                        if result['stats'].get('total_revenue'):
                            st.markdown(f"- **汇总消费总额**: ¥{result['stats']['total_revenue']:,.2f}")
                        if result['stats'].get('avg_behavior_score'):
                            st.markdown(f"- **平均行为得分**: {result['stats']['avg_behavior_score']}")
                    else:
                        st.markdown("##### 🎯 用户群体分布")
                        if result['stats']['segment_distribution']:
                            total = result['stats']['total_records']
                            for seg, cnt in result['stats']['segment_distribution'].items():
                                pct = round(cnt / total * 100, 1) if total > 0 else 0
                                st.markdown(f"- **{seg}**: {cnt:,} 人 ({pct}%)")
                        else:
                            st.markdown("- 无分群数据")
                
                with detail_col2:
                    if stat_scope in ["城市级别汇总", "省份级别汇总"]:
                        st.markdown("##### 📋 汇总说明")
                        if stat_scope == "城市级别汇总":
                            st.markdown("- 每条记录代表一个城市的汇总数据")
                            st.markdown("- 用户数量为该城市覆盖的用户总数")
                            st.markdown("- 总消费金额为该城市用户消费总和")
                            if result['export_format'] == 'Excel':
                                st.markdown("- Excel 包含多工作表：汇总、各省明细、城市类型统计")
                        elif stat_scope == "省份级别汇总":
                            st.markdown("- 每条记录代表一个省份的汇总数据")
                            st.markdown("- 用户数量为该省份覆盖的用户总数")
                            if result['export_format'] == 'Excel':
                                st.markdown("- Excel 包含多工作表：汇总、南北方统计")
                    else:
                        st.markdown("##### 📈 关键指标")
                        if result['stats']['age_range']:
                            st.markdown(f"- **年龄范围**: {result['stats']['age_range']['min']} - {result['stats']['age_range']['max']} 岁 (平均: {result['stats']['age_range']['mean']}岁)")
                        if result['stats']['province_count']:
                            st.markdown(f"- **覆盖省份**: {result['stats']['province_count']} 个")
                        if result['stats']['total_revenue']:
                            st.markdown(f"- **总消费金额**: ¥{result['stats']['total_revenue']:,.2f}")
                        if result['stats']['avg_behavior_score']:
                            st.markdown(f"- **平均行为得分**: {result['stats']['avg_behavior_score']}")
                        
                        st.markdown("##### 👥 性别分布")
                        if result['stats']['gender_distribution']:
                            total = result['stats']['total_records']
                            for gender, cnt in result['stats']['gender_distribution'].items():
                                pct = round(cnt / total * 100, 1) if total > 0 else 0
                                st.markdown(f"- **{gender}**: {cnt:,} 人 ({pct}%)")
                
            st.markdown("---")
    
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
    segment_colors = [tc['accent_green'], tc['accent_blue'], tc['accent_gray']]
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
                        <p style="font-size: 28px; font-weight: bold; color: {tc['primary_text']}; margin: 10px 0;">{len(seg_data):,} 人</p>
                        <p style="color: {tc['secondary_text']}; margin: 5px 0;">占比: {len(seg_data)/len(df_behavior_view)*100:.1f}%</p>
                        <hr style="margin: 15px 0; border-color: {tc['border']};">
                        <p style="color: {tc['primary_text']};"><strong>平均登录:</strong> {seg_data['login_frequency'].mean():.1f}次</p>
                        <p style="color: {tc['primary_text']};"><strong>平均在线:</strong> {seg_data['online_hours'].mean():.1f}小时</p>
                        <p style="color: {tc['primary_text']};"><strong>平均购买:</strong> {seg_data['purchase_count'].mean():.1f}次</p>
                        <p style="color: {tc['primary_text']};"><strong>平均消费:</strong> ¥{seg_data['total_spent'].mean():,.0f}</p>
                        <p style="color: {tc['primary_text']};"><strong>平均行为分:</strong> {seg_data['behavior_score'].mean():.1f}</p>
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

    st.subheader("👶 代际分析")
    st.markdown("#### 代际分组说明：00后(17-26岁)、90后(27-36岁)、80后(37-46岁)、70后(47-56岁)、60后(57-66岁)")
    
    df_gen_view = df_filtered if len(df_filtered) > 0 else df_full

    gen_col1, gen_col2, gen_col3, gen_col4, gen_col5, gen_col6 = st.columns(6)
    gen_display = GENERATION_ORDER
    gen_colors = [tc['accent_blue'], tc['accent_green'], tc['accent_orange'], tc['accent_red'], tc['accent_green'], tc['accent_gray']]
    gen_icons = ['🆕', '🎯', '💼', '🏆', '🌟', '👴']

    for i, (gen, color, icon) in enumerate(zip(gen_display, gen_colors, gen_icons)):
        gen_data = df_gen_view[df_gen_view['generation'] == gen]
        if len(gen_data) > 0:
            with [gen_col1, gen_col2, gen_col3, gen_col4, gen_col5, gen_col6][i]:
                st.markdown(
                    f"""
                    <div class="metric-card" style="border-top: 4px solid {color};">
                        <h3 style="color: {color}; margin: 0 0 10px 0;">{icon} {gen}</h3>
                        <p style="font-size: 24px; font-weight: bold; color: {tc['primary_text']}; margin: 10px 0;">{len(gen_data):,} 人</p>
                        <p style="color: {tc['secondary_text']}; margin: 5px 0;">占比: {len(gen_data)/len(df_gen_view)*100:.1f}%</p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

    st.markdown("---")

    gen_pcol1, gen_pcol2 = st.columns([1, 1.5])

    with gen_pcol1:
        st.subheader("🥧 各代际用户数量占比")
        generation_pie_fig = create_generation_pie_chart(df_gen_view)
        st.pyplot(generation_pie_fig, use_container_width=True)

    with gen_pcol2:
        st.subheader("📊 不同代际消费偏好对比")
        generation_consumption_fig = create_generation_consumption_chart(df_gen_view)
        st.pyplot(generation_consumption_fig, use_container_width=True)

    st.markdown("---")

    st.subheader("📈 代际与兴趣标签关系")
    generation_area_fig = create_generation_interest_area_chart(df_gen_view)
    st.pyplot(generation_area_fig, use_container_width=True)

    st.markdown("---")

    st.subheader("📋 代际统计摘要")
    generation_summary = get_generation_summary(df_gen_view)
    st.dataframe(generation_summary, use_container_width=True, hide_index=True)

    if selected_generation:
        st.markdown("---")
        st.subheader(f"🔍 代际详细画像")
        st.info(f"💡 当前已筛选代际: {'、'.join(selected_generation)}，以下为所选代际的详细画像数据")
        
        gen_detail_col1, gen_detail_col2, gen_detail_col3 = st.columns(3)
        
        for i, sel_gen in enumerate(selected_generation):
            gen_detail_data = df_filtered[df_filtered['generation'] == sel_gen]
            if len(gen_detail_data) > 0:
                col_idx = i % 3
                color_blue = tc['accent_blue']
                color_green = tc['accent_green']
                color_orange = tc['accent_orange']
                color_primary = tc['primary_text']
                color_secondary = tc['secondary_text']
                
                gen_user_count = f"{len(gen_detail_data):,}"
                gen_avg_age = f"{gen_detail_data['age'].mean():.1f}"
                gen_age_min = gen_detail_data['age'].min()
                gen_age_max = gen_detail_data['age'].max()
                male_count = len(gen_detail_data[gen_detail_data['gender'] == '男'])
                female_count = len(gen_detail_data[gen_detail_data['gender'] == '女'])
                gen_male_pct = f"{male_count / len(gen_detail_data) * 100:.1f}"
                gen_female_pct = f"{female_count / len(gen_detail_data) * 100:.1f}"
                
                gen_avg_login = f"{gen_detail_data['login_frequency'].mean():.1f}"
                gen_avg_online = f"{gen_detail_data['online_hours'].mean():.1f}"
                gen_avg_purchase = f"{gen_detail_data['purchase_count'].mean():.1f}"
                gen_avg_spent = f"¥{gen_detail_data['total_spent'].mean():,.0f}"
                gen_avg_behavior = f"{gen_detail_data['behavior_score'].mean():.1f}"
                
                top_interest = gen_detail_data['top_interest'].value_counts().head(3)
                top_consumption = gen_detail_data['top_consumption'].value_counts().head(3)
                top_channel = gen_detail_data['top_channel'].value_counts().head(3)
                
                interest_items = ""
                if len(top_interest) > 0:
                    for idx, (tag, cnt) in enumerate(top_interest.items()):
                        interest_items += f'<p style="color: {color_secondary};">&nbsp;&nbsp;{idx+1}. {tag} ({cnt}人)</p>'
                else:
                    interest_items = f'<p style="color: {color_secondary};">&nbsp;&nbsp;暂无数据</p>'
                
                consumption_items = ""
                if len(top_consumption) > 0:
                    for idx, (tag, cnt) in enumerate(top_consumption.items()):
                        consumption_items += f'<p style="color: {color_secondary};">&nbsp;&nbsp;{idx+1}. {tag} ({cnt}人)</p>'
                else:
                    consumption_items = f'<p style="color: {color_secondary};">&nbsp;&nbsp;暂无数据</p>'
                
                channel_items = ""
                if len(top_channel) > 0:
                    for idx, (tag, cnt) in enumerate(top_channel.items()):
                        channel_items += f'<p style="color: {color_secondary};">&nbsp;&nbsp;{idx+1}. {tag} ({cnt}人)</p>'
                else:
                    channel_items = f'<p style="color: {color_secondary};">&nbsp;&nbsp;暂无数据</p>'
                
                with [gen_detail_col1, gen_detail_col2, gen_detail_col3][col_idx]:
                    st.markdown(f"### {sel_gen} 详细画像")
                    st.markdown(
                        f"""
                        <div class="metric-card" style="border-top: 4px solid {color_blue};">
                            <p style="font-size: 20px; font-weight: bold; color: {color_primary};">基础信息</p>
                            <p style="color: {color_primary};"><strong>用户数量:</strong> {gen_user_count} 人</p>
                            <p style="color: {color_primary};"><strong>平均年龄:</strong> {gen_avg_age}岁</p>
                            <p style="color: {color_primary};"><strong>年龄范围:</strong> {gen_age_min} - {gen_age_max}岁</p>
                            <p style="color: {color_primary};"><strong>男性占比:</strong> {gen_male_pct}%</p>
                            <p style="color: {color_primary};"><strong>女性占比:</strong> {gen_female_pct}%</p>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                    st.markdown(
                        f"""
                        <div class="metric-card" style="border-top: 4px solid {color_green};">
                            <p style="font-size: 20px; font-weight: bold; color: {color_primary};">行为数据</p>
                            <p style="color: {color_primary};"><strong>平均登录频率:</strong> {gen_avg_login}次</p>
                            <p style="color: {color_primary};"><strong>平均在线时长:</strong> {gen_avg_online}小时</p>
                            <p style="color: {color_primary};"><strong>平均购买次数:</strong> {gen_avg_purchase}次</p>
                            <p style="color: {color_primary};"><strong>平均消费金额:</strong> {gen_avg_spent}</p>
                            <p style="color: {color_primary};"><strong>平均行为得分:</strong> {gen_avg_behavior}</p>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                    st.markdown(
                        f"""
                        <div class="metric-card" style="border-top: 4px solid {color_orange};">
                            <p style="font-size: 20px; font-weight: bold; color: {color_primary};">偏好TOP3</p>
                            <p style="color: {color_primary};"><strong>兴趣偏好:</strong></p>
                            {interest_items}
                            <p style="color: {color_primary};"><strong>消费偏好:</strong></p>
                            {consumption_items}
                            <p style="color: {color_primary};"><strong>渠道偏好:</strong></p>
                            {channel_items}
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

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

    if selected_province == "全部":
        st.markdown("---")
        st.subheader("📋 各省份城市数据总览")
        province_overview = get_province_city_overview(df_filtered)
        display_overview = province_overview.copy()
        display_overview['总消费金额'] = display_overview['总消费金额'].apply(lambda x: f"¥{x:,.0f}")
        display_overview['平均消费金额'] = display_overview['平均消费金额'].apply(lambda x: f"¥{x:,.2f}")
        display_overview['平均行为得分'] = display_overview['平均行为得分'].round(1)
        display_overview['用户占比(%)'] = display_overview['用户占比(%)'].round(2)
        st.dataframe(display_overview, use_container_width=True, hide_index=True)
    else:
        st.markdown("---")
        st.subheader(f"🏙️ {selected_province} 城市分布前十")
        city_top10 = get_city_top10_table(df_filtered)
        st.dataframe(city_top10, use_container_width=True, hide_index=True)

    if selected_province != "全部":
        st.markdown("---")
        st.subheader(f"🏙️ {selected_province} 城市级别分析")

        city_stats = get_city_level_stats(df_filtered)
        capital = get_province_capital(selected_province)

        metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
        with metric_col1:
            st.metric("覆盖城市数", f"{city_stats['城市'].nunique()}")
        with metric_col2:
            total_city_revenue = city_stats['总消费金额'].sum()
            st.metric("城市总消费", f"¥{total_city_revenue:,.0f}")
        with metric_col3:
            if capital and capital in city_stats['城市'].values:
                capital_users = city_stats[city_stats['城市'] == capital]['用户数量'].values[0]
                st.metric(f"省会({capital})用户", f"{capital_users:,}")
            else:
                st.metric("省会城市用户", "暂无数据")
        with metric_col4:
            avg_behavior = city_stats['平均行为得分'].mean()
            st.metric("城市平均行为分", f"{avg_behavior:.1f}")

        st.markdown("---")

        city_col1, city_col2 = st.columns(2)

        with city_col1:
            st.markdown(f"### 📊 {selected_province} 城市用户分布")
            city_top_n = st.slider(
                "显示城市数量",
                min_value=3,
                max_value=min(20, len(city_stats)),
                value=min(10, len(city_stats)),
                key="city_top_n_slider"
            )
            city_dist_fig = create_city_distribution_chart(
                df_filtered, selected_province, top_n=city_top_n
            )
            st.pyplot(city_dist_fig, use_container_width=True)

        with city_col2:
            st.markdown(f"### 📈 {selected_province} 城市类型对比分析")
            if 'city_type' in df_filtered.columns and df_filtered['city_type'].nunique() > 0:
                city_type_fig = create_city_type_comparison_chart(
                    df_filtered, selected_province
                )
                st.pyplot(city_type_fig, use_container_width=True)
            else:
                st.info("暂无城市类型数据")

        st.markdown("---")

        st.markdown(f"### 📋 {selected_province} 城市详细统计")

        display_city_stats = city_stats.copy()
        for col in ['总消费金额', '平均消费金额']:
            if col in display_city_stats.columns:
                display_city_stats[col] = display_city_stats[col].apply(
                    lambda x: f"¥{x:,.2f}"
                )
        for col in ['平均行为得分', '平均登录频率', '平均在线时长', '平均购买次数', '用户占比(%)']:
            if col in display_city_stats.columns:
                display_city_stats[col] = display_city_stats[col].round(2)

        st.dataframe(display_city_stats, use_container_width=True, hide_index=True)

        st.markdown("---")

        city_type_col1, city_type_col2 = st.columns(2)

        with city_type_col1:
            st.markdown("#### 🏷️ 城市类型分布")
            if 'city_type' in df_filtered.columns:
                city_type_summary = df_filtered.groupby('city_type', observed=True).agg({
                    'user_id': 'count',
                    'total_spent': 'sum',
                    'behavior_score': 'mean'
                }).round(2)
                city_type_summary = city_type_summary.reset_index()
                city_type_summary.columns = ['城市类型', '用户数量', '总消费金额', '平均行为得分']
                total_type_users = city_type_summary['用户数量'].sum()
                city_type_summary['用户占比(%)'] = (city_type_summary['用户数量'] / total_type_users * 100).round(2)
                city_type_summary['总消费金额'] = city_type_summary['总消费金额'].apply(lambda x: f"¥{x:,.2f}")
                city_type_summary['平均行为得分'] = city_type_summary['平均行为得分'].round(2)
                st.dataframe(city_type_summary, use_container_width=True, hide_index=True)
            else:
                st.info("暂无城市类型数据")

        with city_type_col2:
            st.markdown("#### 🏆 各指标领先城市")
            if len(city_stats) > 0:
                top_users = city_stats.iloc[0]
                top_revenue = city_stats.loc[city_stats['总消费金额'].idxmax()]
                top_behavior = city_stats.loc[city_stats['平均行为得分'].idxmax()]
                top_spending = city_stats.loc[city_stats['平均消费金额'].idxmax()]

                st.markdown(f"- **用户最多**: {top_users['城市']} ({top_users['用户数量']:,} 人)")
                st.markdown(f"- **总消费最高**: {top_revenue['城市']} (¥{top_revenue['总消费金额']:,.2f})")
                st.markdown(f"- **最活跃**: {top_behavior['城市']} (行为分 {top_behavior['平均行为得分']:.1f})")
                st.markdown(f"- **人均消费最高**: {top_spending['城市']} (¥{top_spending['平均消费金额']:,.2f})")
            else:
                st.info("暂无数据")

        if export_format == "Excel":
            st.markdown("---")
            st.info(f"💡 提示：选择侧边栏 **导出范围** 为 **城市级别汇总**，可将 {selected_province} 的城市数据导出到 Excel 中")

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

    st.subheader("🎨 用户偏好分析")

    df_pref_view = df_filtered if len(df_filtered) > 0 else df_full

    pcol1, pcol2, pcol3, pcol4 = st.columns(4)
    concentration = get_concentration_stats(df_pref_view)

    with pcol1:
        st.markdown(
            f"""
            <div class="metric-card" style="border-top: 4px solid {tc['accent_blue']};">
                <p style="color: {tc['secondary_text']}; margin: 0 0 5px 0; font-size: 14px;">兴趣偏好集中度</p>
                <p style="font-size: 28px; font-weight: bold; color: {tc['primary_text']}; margin: 5px 0;">{concentration['interest_mean']:.1f}%</p>
                <p style="color: {tc['muted_text']}; margin: 5px 0 0 0; font-size: 12px;">标准差 ±{concentration['interest_std']:.1f}%</p>
            </div>
            """,
            unsafe_allow_html=True
        )

    with pcol2:
        st.markdown(
            f"""
            <div class="metric-card" style="border-top: 4px solid {tc['accent_red']};">
                <p style="color: {tc['secondary_text']}; margin: 0 0 5px 0; font-size: 14px;">消费偏好集中度</p>
                <p style="font-size: 28px; font-weight: bold; color: {tc['primary_text']}; margin: 5px 0;">{concentration['consumption_mean']:.1f}%</p>
                <p style="color: {tc['muted_text']}; margin: 5px 0 0 0; font-size: 12px;">标准差 ±{concentration['consumption_std']:.1f}%</p>
            </div>
            """,
            unsafe_allow_html=True
        )

    with pcol3:
        st.markdown(
            f"""
            <div class="metric-card" style="border-top: 4px solid {tc['accent_green']};">
                <p style="color: {tc['secondary_text']}; margin: 0 0 5px 0; font-size: 14px;">渠道偏好集中度</p>
                <p style="font-size: 28px; font-weight: bold; color: {tc['primary_text']}; margin: 5px 0;">{concentration['channel_mean']:.1f}%</p>
                <p style="color: {tc['muted_text']}; margin: 5px 0 0 0; font-size: 12px;">标准差 ±{concentration['channel_std']:.1f}%</p>
            </div>
            """,
            unsafe_allow_html=True
        )

    top_interest_tag = get_preference_ranking(df_pref_view, 'interest', top_n=1)
    with pcol4:
        if len(top_interest_tag) > 0:
            st.markdown(
                f"""
                <div class="metric-card" style="border-top: 4px solid {tc['accent_orange']};">
                    <p style="color: {tc['secondary_text']}; margin: 0 0 5px 0; font-size: 14px;">热门兴趣标签</p>
                    <p style="font-size: 28px; font-weight: bold; color: {tc['primary_text']}; margin: 5px 0;">{top_interest_tag.iloc[0]['标签']}</p>
                    <p style="color: {tc['muted_text']}; margin: 5px 0 0 0; font-size: 12px;">占比 {top_interest_tag.iloc[0]['占比']:.1f}%</p>
                </div>
                """,
                unsafe_allow_html=True
            )

    pref_info_col1, pref_info_col2 = st.columns(2)
    with pref_info_col1:
        st.info(
            f"📊 当前分析维度: **{PREFERENCE_TYPES[selected_pref_type]}**\n\n"
            f"共 {len(TAG_CATEGORIES[selected_pref_type])} 个可选标签\n\n"
            f"偏好集中度表示用户前三名偏好权重之和的平均值，越高说明用户偏好越集中"
        )
    with pref_info_col2:
        st.success(
            f"🏆 热门 {PREFERENCE_TYPES[selected_pref_type]} 前三名:\n\n"
            + "\n".join([
                f"{i+1}. {row['标签']} ({row['占比']:.1f}%)"
                for i, row in get_preference_ranking(df_pref_view, selected_pref_type, top_n=3).iterrows()
            ])
        )

    st.markdown("---")

    pref_col1, pref_col2 = st.columns(2)

    with pref_col1:
        st.subheader(f"☁️ {PREFERENCE_TYPES[selected_pref_type]}词云")
        wordcloud_fig = create_preference_wordcloud(df_pref_view, selected_pref_type)
        st.pyplot(wordcloud_fig, use_container_width=True)

    with pref_col2:
        st.subheader(f"👫 性别{PREFERENCE_TYPES[selected_pref_type]}对比")
        gender_pref_fig = create_gender_preference_chart(
            df_pref_view, selected_pref_type, top_n=gender_compare_top_n
        )
        st.pyplot(gender_pref_fig, use_container_width=True)

    st.markdown("---")

    st.subheader(f"🏆 热门{PREFERENCE_TYPES[selected_pref_type]}排名前{ranking_top_n}名")
    pref_ranking = get_preference_ranking(df_pref_view, selected_pref_type, top_n=ranking_top_n)

    rank_col1, rank_col2 = st.columns([2, 3])

    with rank_col1:
        st.dataframe(pref_ranking, use_container_width=True, hide_index=True)

    with rank_col2:
        tchart = theme['chart']
        fig_rank, ax_rank = plt.subplots(figsize=(10, 8))
        fig_rank.patch.set_facecolor(tchart['figure_facecolor'])
        ax_rank.set_facecolor(tchart['axes_facecolor'])

        _fp = get_available_chinese_font()
        font_prop = FontProperties(fname=_fp, size=10) if _fp else FontProperties(family='SimHei', size=10)
        font_title = FontProperties(fname=_fp, size=14, weight='bold') if _fp else FontProperties(family='SimHei', size=14, weight='bold')
        font_label = FontProperties(fname=_fp, size=12, weight='bold') if _fp else FontProperties(family='SimHei', size=12, weight='bold')
        font_text = FontProperties(fname=_fp, size=10, weight='bold') if _fp else FontProperties(family='SimHei', size=10, weight='bold')

        colors = sns.color_palette(tchart['palette_ranking'], len(pref_ranking))
        bars = ax_rank.barh(
            pref_ranking['标签'][::-1],
            pref_ranking['权重'][::-1],
            color=colors,
            edgecolor=tchart['axes_facecolor'],
            linewidth=1.5
        )

        for bar, pct in zip(bars, pref_ranking['占比'][::-1].values):
            ax_rank.text(
                bar.get_width() + pref_ranking['权重'].max() * 0.01,
                bar.get_y() + bar.get_height() / 2,
                f'{pct:.1f}%',
                va='center',
                fontproperties=font_text,
                color=tchart['text_color']
            )

        ax_rank.set_xlabel('权重', fontproperties=font_label, color=tchart['label_color'])
        ax_rank.set_ylabel('标签', fontproperties=font_label, color=tchart['label_color'])
        ax_rank.set_title(
            f'{PREFERENCE_TYPES[selected_pref_type]}权重分布',
            fontproperties=font_title,
            pad=15,
            color=tchart['text_color']
        )

        for label in ax_rank.get_xticklabels() + ax_rank.get_yticklabels():
            label.set_fontproperties(font_prop)
            label.set_color(tchart['tick_color'])

        ax_rank.spines['top'].set_visible(False)
        ax_rank.spines['right'].set_visible(False)
        ax_rank.spines['left'].set_color(tchart['grid_color'])
        ax_rank.spines['bottom'].set_color(tchart['grid_color'])
        ax_rank.xaxis.grid(True, alpha=0.3, linestyle='--', color=tchart['grid_color'])
        ax_rank.set_axisbelow(True)

        plt.tight_layout()
        st.pyplot(fig_rank, use_container_width=True)

    st.markdown("---")

    st.subheader("📊 三类偏好对比统计")
    compare_col1, compare_col2, compare_col3 = st.columns(3)

    pref_type_list = ['interest', 'consumption', 'channel']
    pref_col_list = [compare_col1, compare_col2, compare_col3]

    for pt, pc in zip(pref_type_list, pref_col_list):
        with pc:
            st.markdown(f"##### 🔝 {PREFERENCE_TYPES[pt]} 前五名")
            top5 = get_preference_ranking(df_pref_view, pt, top_n=5)
            display_top5 = top5[['排名', '标签', '占比']].copy()
            display_top5['占比'] = display_top5['占比'].astype(str) + '%'
            st.dataframe(display_top5, use_container_width=True, hide_index=True)

    st.markdown("---")

    st.subheader("📋 行为分群统计摘要")
    segment_summary = get_segment_summary(df_filtered if len(df_filtered) > 0 else df_full)
    st.dataframe(segment_summary, use_container_width=True, hide_index=True)

    st.markdown("---")

    st.subheader("📋 数据摘要")
    
    summary_col1, summary_col2, summary_col3, summary_col4 = st.columns(4)
    
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
        st.markdown("### 代际统计")
        gen_summary = df_filtered['generation'].value_counts().reindex(GENERATION_ORDER).reset_index()
        gen_summary.columns = ['代际', '用户数']
        gen_summary['占比'] = (gen_summary['用户数'] / len(df_filtered) * 100).round(2).astype(str) + '%'
        gen_summary = gen_summary.dropna(subset=['用户数'])
        st.dataframe(gen_summary, use_container_width=True, hide_index=True)
    
    with summary_col4:
        st.markdown("### 省份统计前十")
        province_summary = df_filtered['province'].value_counts().head(10).reset_index()
        province_summary.columns = ['省份', '用户数']
        province_summary['占比'] = (province_summary['用户数'] / len(df_filtered) * 100).round(2).astype(str) + '%'
        st.dataframe(province_summary, use_container_width=True, hide_index=True)
    
    if show_data:
        st.markdown("---")
        st.subheader("📄 原始数据预览")
        display_cols = [
            'user_id', 'gender', 'age', 'age_group', 'generation', 'province', 'city', 'region_type',
            'user_segment', 'login_frequency', 'online_hours', 'purchase_count',
            'total_spent', 'last_active_days', 'page_views', 'click_count', 'behavior_score',
            'top_interest', 'top_consumption', 'top_channel',
            'interest_concentration', 'consumption_concentration', 'channel_concentration'
        ]
        available_cols = [col for col in display_cols if col in df_filtered.columns]
        st.dataframe(df_filtered[available_cols].head(100), use_container_width=True)
    
    st.markdown("---")
    st.markdown(
        f"""
        <div style='text-align: center; color: {tc['secondary_text']}; padding: 20px;'>
            <p>💡 用户画像分析系统 | 基于 Streamlit 与 Matplotlib 构建</p>
            <p>数据为模拟生成，仅用于演示目的</p>
        </div>
        """,
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
