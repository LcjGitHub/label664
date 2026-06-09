import pandas as pd
import numpy as np
from datetime import datetime
from io import BytesIO, StringIO


COLUMN_NAME_MAP = {
    'user_id': '用户ID',
    'gender': '性别',
    'age': '年龄',
    'age_group': '年龄段',
    'province': '省份',
    'city': '城市',
    'city_type': '城市类型',
    'region_type': '地域类型',
    'user_segment': '用户群体',
    'login_frequency': '登录频率(次)',
    'online_hours': '在线时长(小时)',
    'purchase_count': '购买次数',
    'total_spent': '消费金额(元)',
    'last_active_days': '距上次活跃天数',
    'page_views': '页面浏览量',
    'click_count': '点击次数',
    'login_score': '登录得分',
    'online_score': '在线得分',
    'purchase_score': '购买得分',
    'spent_score': '消费得分',
    'activity_score': '活跃得分',
    'behavior_score': '行为综合得分'
}


def map_columns_to_chinese(df):
    rename_dict = {}
    for col in df.columns:
        if col in COLUMN_NAME_MAP:
            rename_dict[col] = COLUMN_NAME_MAP[col]
    return df.rename(columns=rename_dict)


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
        'city_count': 0,
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

        province_col = 'province' if 'province' in df.columns else ('省份' if '省份' in df.columns else None)
        if province_col:
            stats['province_count'] = df[province_col].nunique()

        city_col = 'city' if 'city' in df.columns else ('城市' if '城市' in df.columns else None)
        if city_col:
            stats['city_count'] = df[city_col].nunique()

        revenue_col = 'total_spent' if 'total_spent' in df.columns else ('总消费金额' if '总消费金额' in df.columns else None)
        if revenue_col:
            stats['total_revenue'] = round(float(df[revenue_col].sum()), 2)

        behavior_col = 'behavior_score' if 'behavior_score' in df.columns else ('平均行为得分' if '平均行为得分' in df.columns else None)
        if behavior_col:
            stats['avg_behavior_score'] = round(float(df[behavior_col].mean()), 2)

    return stats


def export_to_csv(df):
    df_cn = map_columns_to_chinese(df)
    csv_buffer = StringIO()
    df_cn.to_csv(csv_buffer, index=False, encoding='utf-8-sig')
    csv_data = csv_buffer.getvalue().encode('utf-8-sig')
    return csv_data


def export_to_excel(df, export_scope="用户明细数据"):
    df_cn = map_columns_to_chinese(df)
    excel_buffer = BytesIO()
    with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
        if export_scope == "城市级别汇总":
            df.to_excel(writer, index=False, sheet_name='城市级别汇总')
            if '省份' in df.columns and '城市类型' in df.columns:
                for province in df['省份'].unique():
                    province_df = df[df['省份'] == province]
                    safe_sheet_name = province[:28].replace('/', '_').replace('\\', '_')
                    province_df.to_excel(writer, index=False, sheet_name=f'{safe_sheet_name}城市明细')
                city_type_summary = df.groupby('城市类型', observed=True).agg({
                    '用户数量': 'sum',
                    '总消费金额': 'sum',
                    '平均消费金额': 'mean',
                    '平均行为得分': 'mean',
                    '平均登录频率': 'mean'
                }).round(2).reset_index()
                total_city_type = city_type_summary['用户数量'].sum()
                city_type_summary['用户占比(%)'] = (city_type_summary['用户数量'] / total_city_type * 100).round(2)
                city_type_summary.to_excel(writer, index=False, sheet_name='城市类型统计')
        elif export_scope == "省份级别汇总":
            df.to_excel(writer, index=False, sheet_name='省份级别汇总')
            if '地域类型' in df.columns:
                region_summary = df.groupby('地域类型', observed=True).agg({
                    '用户数量': 'sum',
                    '覆盖城市数': 'sum',
                    '总消费金额': 'sum',
                    '平均消费金额': 'mean',
                    '平均行为得分': 'mean'
                }).round(2).reset_index()
                total_region = region_summary['用户数量'].sum()
                region_summary['用户占比(%)'] = (region_summary['用户数量'] / total_region * 100).round(2)
                region_summary.to_excel(writer, index=False, sheet_name='南北方统计')
        else:
            df_cn.to_excel(writer, index=False, sheet_name='用户画像数据')

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

            if 'city' in df.columns and 'province' in df.columns:
                city_summary = df.groupby(['province', 'city'], observed=True).agg({
                    'user_id': 'count'
                }).reset_index()
                city_summary.columns = ['省份', '城市', '用户数']
                city_summary = city_summary.sort_values(['省份', '用户数'], ascending=[True, False])
                city_summary.to_excel(writer, index=False, sheet_name='城市分布统计')

            if 'city_type' in df.columns:
                city_type_summary_raw = df.groupby('city_type', observed=True).agg({
                    'user_id': 'count',
                    'total_spent': 'sum',
                    'behavior_score': 'mean'
                }).round(2).reset_index()
                city_type_summary_raw.columns = ['城市类型', '用户数', '总消费金额', '平均行为得分']
                total_ct = city_type_summary_raw['用户数'].sum()
                city_type_summary_raw['占比(%)'] = (city_type_summary_raw['用户数'] / total_ct * 100).round(2)
                city_type_summary_raw.to_excel(writer, index=False, sheet_name='城市类型统计')

    excel_data = excel_buffer.getvalue()
    return excel_data


def export_data(df, export_format='csv', export_scope="用户明细数据"):
    if export_format.lower() == 'csv':
        return export_to_csv(df)
    elif export_format.lower() in ['excel', 'xlsx', 'xls']:
        return export_to_excel(df, export_scope)
    else:
        raise ValueError(f"不支持的导出格式: {export_format}")


def get_export_mime_type(export_format):
    if export_format.lower() == 'csv':
        return 'text/csv'
    elif export_format.lower() in ['excel', 'xlsx', 'xls']:
        return 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    else:
        return 'application/octet-stream'
