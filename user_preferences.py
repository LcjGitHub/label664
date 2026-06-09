import streamlit as st
import pandas as pd
import numpy as np
import os
import sys


def get_available_chinese_font():
    if sys.platform.startswith('win'):
        candidates = [
            'C:/Windows/Fonts/simhei.ttf',
            'C:/Windows/Fonts/msyh.ttc',
            'C:/Windows/Fonts/msyhbd.ttc',
            'C:/Windows/Fonts/simsun.ttc',
            'C:/Windows/Fonts/simkai.ttf',
            'C:/Windows/Fonts/simfang.ttf'
        ]
    elif sys.platform == 'darwin':
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


INTEREST_TAGS = [
    '科技数码', '运动健身', '旅游出行', '美食烹饪', '时尚美妆',
    '金融理财', '教育学习', '游戏娱乐', '影视音乐', '阅读写作',
    '家居生活', '母婴育儿', '宠物饲养', '摄影艺术', '汽车驾驶',
    '健康养生', '电商购物', '社交网络', '直播短视频', '户外探险'
]

CONSUMPTION_PREFERENCES = [
    '性价比优先', '品质至上', '品牌忠诚', '新品尝鲜', '促销敏感',
    '高端奢华', '实用主义', '个性化定制', '环保绿色', '进口偏好',
    '国货支持', '二手交易', '会员专属', '冲动消费', '理性规划'
]

CHANNEL_PREFERENCES = [
    '微信小程序', '官方App', '淘宝/天猫', '京东', '拼多多',
    '抖音小店', '快手电商', '小红书', 'B站会员购', '线下门店',
    '美团', '饿了么', '唯品会', '苏宁易购', '得物'
]

PREFERENCE_TYPES = {
    'interest': '兴趣标签',
    'consumption': '消费偏好',
    'channel': '渠道偏好'
}

TAG_CATEGORIES = {
    'interest': INTEREST_TAGS,
    'consumption': CONSUMPTION_PREFERENCES,
    'channel': CHANNEL_PREFERENCES
}


@st.cache_data
def generate_preference_data(user_ids, seed=42):
    np.random.seed(seed)
    n_users = len(user_ids)

    def assign_preferences(tags, n_tags_range=(3, 8)):
        n_tags = np.random.randint(n_tags_range[0], n_tags_range[1] + 1)
        selected = np.random.choice(tags, size=n_tags, replace=False)
        weights = np.random.dirichlet(np.ones(n_tags) * 2)
        weights = (weights * 100).round(1)
        return dict(zip(selected, weights))

    interest_prefs = [assign_preferences(INTEREST_TAGS) for _ in range(n_users)]
    consumption_prefs = [assign_preferences(CONSUMPTION_PREFERENCES, (2, 5)) for _ in range(n_users)]
    channel_prefs = [assign_preferences(CHANNEL_PREFERENCES, (2, 6)) for _ in range(n_users)]

    top_interest = [max(p, key=p.get) if p else None for p in interest_prefs]
    top_consumption = [max(p, key=p.get) if p else None for p in consumption_prefs]
    top_channel = [max(p, key=p.get) if p else None for p in channel_prefs]

    interest_concentration = np.array([
        sum(sorted(p.values(), reverse=True)[:3]) if p else 0
        for p in interest_prefs
    ])
    consumption_concentration = np.array([
        sum(sorted(p.values(), reverse=True)[:3]) if p else 0
        for p in consumption_prefs
    ])
    channel_concentration = np.array([
        sum(sorted(p.values(), reverse=True)[:3]) if p else 0
        for p in channel_prefs
    ])

    df = pd.DataFrame({
        'user_id': user_ids,
        'interest_preferences': interest_prefs,
        'consumption_preferences': consumption_prefs,
        'channel_preferences': channel_prefs,
        'top_interest': top_interest,
        'top_consumption': top_consumption,
        'top_channel': top_channel,
        'interest_concentration': interest_concentration.round(1),
        'consumption_concentration': consumption_concentration.round(1),
        'channel_concentration': channel_concentration.round(1)
    })

    return df


def aggregate_preferences(df, pref_type, group_col=None):
    pref_col = f'{pref_type}_preferences'
    all_prefs = {}

    if group_col is None:
        for prefs in df[pref_col]:
            for tag, weight in prefs.items():
                if tag in all_prefs:
                    all_prefs[tag] += weight
                else:
                    all_prefs[tag] = weight
    else:
        result = {}
        for group_val in df[group_col].unique():
            group_prefs = {}
            group_df = df[df[group_col] == group_val]
            for prefs in group_df[pref_col]:
                for tag, weight in prefs.items():
                    if tag in group_prefs:
                        group_prefs[tag] += weight
                    else:
                        group_prefs[tag] = weight
            result[group_val] = group_prefs
        return result

    sorted_prefs = dict(sorted(all_prefs.items(), key=lambda x: x[1], reverse=True))
    return sorted_prefs


def get_preference_ranking(df, pref_type, top_n=10):
    prefs = aggregate_preferences(df, pref_type)
    all_total = sum(prefs.values()) or 1
    items = list(prefs.items())[:top_n]
    result = pd.DataFrame(items, columns=['标签', '原始权重'])
    result['权重'] = result['原始权重'].round(1)
    result['占比'] = (result['原始权重'] / all_total * 100).round(1)
    result['排名'] = range(1, len(result) + 1)
    return result[['排名', '标签', '权重', '占比']]


def get_concentration_stats(df):
    stats = {
        'interest_mean': df['interest_concentration'].mean(),
        'interest_std': df['interest_concentration'].std(),
        'consumption_mean': df['consumption_concentration'].mean(),
        'consumption_std': df['consumption_concentration'].std(),
        'channel_mean': df['channel_concentration'].mean(),
        'channel_std': df['channel_concentration'].std()
    }
    return stats


def get_gender_preference_comparison(df_with_gender, pref_type, top_n=8):
    tags = TAG_CATEGORIES[pref_type]

    male_df = df_with_gender[df_with_gender['gender'] == '男']
    female_df = df_with_gender[df_with_gender['gender'] == '女']

    male_prefs = aggregate_preferences(male_df, pref_type)
    female_prefs = aggregate_preferences(female_df, pref_type)

    male_total = sum(male_prefs.values()) or 1
    female_total = sum(female_prefs.values()) or 1

    all_tags = set(list(male_prefs.keys()) + list(female_prefs.keys()))

    data = []
    for tag in all_tags:
        male_pct = male_prefs.get(tag, 0) / male_total * 100
        female_pct = female_prefs.get(tag, 0) / female_total * 100
        data.append({
            '标签': tag,
            '男': round(male_pct, 2),
            '女': round(female_pct, 2),
            '差值': round(male_pct - female_pct, 2)
        })

    result_df = pd.DataFrame(data)
    result_df = result_df.sort_values('差值', key=abs, ascending=False).head(top_n)
    return result_df.reset_index(drop=True)


def get_preference_wordcloud_data(df, pref_type):
    prefs = aggregate_preferences(df, pref_type)
    max_weight = max(prefs.values()) if prefs else 1
    normalized = {
        tag: int(weight / max_weight * 100)
        for tag, weight in prefs.items()
    }
    return normalized


def get_preference_summary(df):
    interest_ranking = get_preference_ranking(df, 'interest', top_n=5)
    consumption_ranking = get_preference_ranking(df, 'consumption', top_n=5)
    channel_ranking = get_preference_ranking(df, 'channel', top_n=5)
    concentration = get_concentration_stats(df)

    return {
        'top_interest': interest_ranking,
        'top_consumption': consumption_ranking,
        'top_channel': channel_ranking,
        'concentration': concentration
    }
