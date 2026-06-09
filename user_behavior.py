import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta


@st.cache_data
def generate_behavior_data(user_ids, seed=42):
    np.random.seed(seed)
    n_users = len(user_ids)

    login_frequency = np.random.exponential(scale=15, size=n_users)
    login_frequency = np.clip(login_frequency, 0, 90).astype(int)

    online_hours = np.random.gamma(shape=2, scale=10, size=n_users)
    online_hours = np.clip(online_hours, 0, 500).round(2)

    purchase_count = np.random.poisson(lam=3, size=n_users)
    purchase_count = np.clip(purchase_count, 0, 50)

    total_spent = np.where(
        purchase_count > 0,
        np.random.exponential(scale=200, size=n_users) * purchase_count,
        0
    )
    total_spent = np.round(total_spent, 2)

    last_active_days = np.random.exponential(scale=20, size=n_users)
    last_active_days = np.clip(last_active_days, 0, 180).astype(int)

    page_views = (login_frequency * np.random.uniform(5, 50, size=n_users)).astype(int)

    click_count = (page_views * np.random.uniform(0.2, 0.8, size=n_users)).astype(int)

    df = pd.DataFrame({
        'user_id': user_ids,
        'login_frequency': login_frequency,
        'online_hours': online_hours,
        'purchase_count': purchase_count,
        'total_spent': total_spent,
        'last_active_days': last_active_days,
        'page_views': page_views,
        'click_count': click_count
    })

    return df


@st.cache_data
def calculate_behavior_scores(df):
    df = df.copy()

    max_login = df['login_frequency'].max() or 1
    max_online = df['online_hours'].max() or 1
    max_purchase = df['purchase_count'].max() or 1
    max_spent = df['total_spent'].max() or 1
    min_last_active = df['last_active_days'].min()
    max_last_active = df['last_active_days'].max() or 1

    df['login_score'] = (df['login_frequency'] / max_login) * 100
    df['online_score'] = (df['online_hours'] / max_online) * 100
    df['purchase_score'] = (df['purchase_count'] / max_purchase) * 100
    df['spent_score'] = (df['total_spent'] / max_spent) * 100

    if max_last_active != min_last_active:
        df['activity_score'] = (1 - (df['last_active_days'] - min_last_active) / (max_last_active - min_last_active)) * 100
    else:
        df['activity_score'] = 100

    df['behavior_score'] = (
        df['login_score'] * 0.25 +
        df['online_score'] * 0.20 +
        df['purchase_score'] * 0.20 +
        df['spent_score'] * 0.20 +
        df['activity_score'] * 0.15
    ).round(2)

    return df


@st.cache_data
def segment_users(df):
    df = df.copy()

    score_33 = df['behavior_score'].quantile(0.33)
    score_66 = df['behavior_score'].quantile(0.66)

    def classify_user(row):
        if row['behavior_score'] >= score_66 and row['last_active_days'] <= 14:
            return '活跃用户'
        elif row['behavior_score'] >= score_33 and row['last_active_days'] <= 60:
            return '普通用户'
        else:
            return '沉睡用户'

    df['user_segment'] = df.apply(classify_user, axis=1)

    segment_order = ['活跃用户', '普通用户', '沉睡用户']
    df['user_segment'] = pd.Categorical(df['user_segment'], categories=segment_order, ordered=True)

    return df


def get_segment_summary(df):
    summary = df.groupby('user_segment', observed=True).agg({
        'user_id': 'count',
        'login_frequency': 'mean',
        'online_hours': 'mean',
        'purchase_count': 'mean',
        'total_spent': 'mean',
        'last_active_days': 'mean',
        'page_views': 'mean',
        'click_count': 'mean',
        'behavior_score': 'mean'
    }).round(2)

    summary.columns = [
        '用户数量', '平均登录频率', '平均在线时长', '平均购买次数',
        '平均消费金额', '平均最后活跃天数', '平均页面浏览量', '平均点击量', '平均行为得分'
    ]

    total_users = summary['用户数量'].sum()
    summary['占比'] = (summary['用户数量'] / total_users * 100).round(2).astype(str) + '%'

    result = summary.reset_index()
    result = result.rename(columns={'user_segment': '行为群体'})
    return result


def get_behavior_stats(df):
    stats = {
        'total_users': len(df),
        'avg_login_freq': df['login_frequency'].mean(),
        'avg_online_hours': df['online_hours'].mean(),
        'avg_purchase_count': df['purchase_count'].mean(),
        'avg_total_spent': df['total_spent'].mean(),
        'avg_behavior_score': df['behavior_score'].mean(),
        'total_revenue': df['total_spent'].sum(),
        'total_purchases': df['purchase_count'].sum(),
        'active_users_7d': len(df[df['last_active_days'] <= 7]),
        'inactive_users_30d': len(df[df['last_active_days'] > 30])
    }
    return stats
