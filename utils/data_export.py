import pandas as pd
import numpy as np
from datetime import datetime
from io import BytesIO, StringIO


def generate_export_filename(export_format, prefix="user_profile_data"):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{prefix}_{timestamp}.{export_format}"


def get_data_statistics(df):
    stats = {
        'total_records': len(df),
        'total_columns': len(df.columns),
        'file_size_estimate_kb': 0,
        'gender_distribution': {},
        'age_range': {},
        'segment_distribution': {},
        'region_count': 0,
        'province_count': 0,
        'total_revenue': 0,
        'avg_behavior_score': 0
    }

    if len(df) > 0:
        if 'gender' in df.columns:
            gender_counts = df['gender'].value_counts().to_dict()
            stats['gender_distribution'] = gender_counts

        if 'age' in df.columns:
            stats['age_range'] = {
                'min': int(df['age'].min()),
                'max': int(df['age'].max()),
                'mean': round(float(df['age'].mean()), 1)
            }

        if 'user_segment' in df.columns:
            segment_counts = df['user_segment'].value_counts().to_dict()
            stats['segment_distribution'] = {str(k): int(v) for k, v in segment_counts.items()}

        if 'region_type' in df.columns:
            stats['region_count'] = df['region_type'].nunique()

        if 'province' in df.columns:
            stats['province_count'] = df['province'].nunique()

        if 'total_spent' in df.columns:
            stats['total_revenue'] = round(float(df['total_spent'].sum()), 2)

        if 'behavior_score' in df.columns:
            stats['avg_behavior_score'] = round(float(df['behavior_score'].mean()), 2)

    return stats


def export_to_csv(df):
    csv_buffer = StringIO()
    df.to_csv(csv_buffer, index=False, encoding='utf-8-sig')
    csv_data = csv_buffer.getvalue().encode('utf-8-sig')
    return csv_data


def export_to_excel(df):
    excel_buffer = BytesIO()
    with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='用户画像数据')

        if 'user_segment' in df.columns:
            agg_dict = {}
            rename_map = {}
            if 'user_id' in df.columns:
                agg_dict['user_id'] = 'count'
                rename_map['user_id'] = '用户数量'
            if 'login_frequency' in df.columns:
                agg_dict['login_frequency'] = 'mean'
                rename_map['login_frequency'] = '平均登录频率'
            if 'online_hours' in df.columns:
                agg_dict['online_hours'] = 'mean'
                rename_map['online_hours'] = '平均在线时长'
            if 'purchase_count' in df.columns:
                agg_dict['purchase_count'] = 'mean'
                rename_map['purchase_count'] = '平均购买次数'
            if 'total_spent' in df.columns:
                agg_dict['total_spent'] = 'mean'
                rename_map['total_spent'] = '平均消费金额'
            if 'behavior_score' in df.columns:
                agg_dict['behavior_score'] = 'mean'
                rename_map['behavior_score'] = '平均行为得分'
            
            if agg_dict:
                segment_summary = df.groupby('user_segment', observed=True).agg(agg_dict).round(2)
                segment_summary = segment_summary.rename(columns=rename_map)
                segment_summary = segment_summary.reset_index()
                segment_summary = segment_summary.rename(columns={'user_segment': '行为群体'})
                segment_summary.to_excel(writer, index=False, sheet_name='行为群体统计')

        if 'gender' in df.columns:
            gender_summary = df['gender'].value_counts().reset_index()
            gender_summary.columns = ['性别', '用户数']
            gender_summary['占比(%)'] = (gender_summary['用户数'] / len(df) * 100).round(2)
            gender_summary.to_excel(writer, index=False, sheet_name='性别分布统计')

        if 'age_group' in df.columns:
            age_order = ['18-24', '25-34', '35-44', '45-54', '55+']
            age_summary = df['age_group'].value_counts().reindex(age_order).reset_index()
            age_summary.columns = ['年龄段', '用户数']
            age_summary['占比(%)'] = (age_summary['用户数'] / len(df) * 100).round(2)
            age_summary.to_excel(writer, index=False, sheet_name='年龄段分布统计')

        if 'province' in df.columns:
            province_summary = df['province'].value_counts().head(20).reset_index()
            province_summary.columns = ['省份', '用户数']
            province_summary['占比(%)'] = (province_summary['用户数'] / len(df) * 100).round(2)
            province_summary.to_excel(writer, index=False, sheet_name='省份分布统计')

    excel_data = excel_buffer.getvalue()
    return excel_data


def export_data(df, export_format='csv'):
    if export_format.lower() == 'csv':
        return export_to_csv(df)
    elif export_format.lower() in ['excel', 'xlsx', 'xls']:
        return export_to_excel(df)
    else:
        raise ValueError(f"不支持的导出格式: {export_format}")


def get_export_mime_type(export_format):
    if export_format.lower() == 'csv':
        return 'text/csv'
    elif export_format.lower() in ['excel', 'xlsx', 'xls']:
        return 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    else:
        return 'application/octet-stream'
