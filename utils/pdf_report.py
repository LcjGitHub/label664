import os
import sys
import io
import numpy as np
import pandas as pd
from datetime import datetime
from io import BytesIO
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm, cm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle,
    PageBreak, KeepTogether
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor


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


CHINESE_FONT_PATH = get_available_chinese_font()
FONT_NAME = 'ChineseFont'

if CHINESE_FONT_PATH and os.path.exists(CHINESE_FONT_PATH):
    try:
        pdfmetrics.registerFont(TTFont(FONT_NAME, CHINESE_FONT_PATH))
    except Exception:
        FONT_NAME = 'Helvetica'
else:
    FONT_NAME = 'Helvetica'


def hex_to_color(hex_str):
    if hex_str and hex_str.startswith('#'):
        try:
            return HexColor(hex_str)
        except Exception:
            return colors.black
    return colors.black


def get_theme_colors(theme):
    tc = theme.get('colors', {})
    chart = theme.get('chart', {})
    return {
        'bg': tc.get('card_background', '#ffffff'),
        'background': tc.get('background', '#f8f9fa'),
        'text': tc.get('primary_text', '#2C3E50'),
        'secondary_text': tc.get('secondary_text', '#7f8c8d'),
        'accent_blue': tc.get('accent_blue', '#3498DB'),
        'accent_red': tc.get('accent_red', '#E74C3C'),
        'accent_green': tc.get('accent_green', '#27AE60'),
        'accent_orange': tc.get('accent_orange', '#F39C12'),
        'accent_gray': tc.get('accent_gray', '#95A5A6'),
        'border': tc.get('border', '#e0e0e0'),
        'table_alt_bg': tc.get('table_alt_bg', '#f7f9fc'),
        'chart_figure_bg': chart.get('figure_facecolor', 'white'),
        'chart_axes_bg': chart.get('axes_facecolor', 'white'),
        'chart_text': chart.get('text_color', '#2C3E50'),
        'chart_label': chart.get('label_color', '#2C3E50'),
    }


def create_styles(theme_colors):
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Title'],
        fontName=FONT_NAME,
        fontSize=22,
        leading=28,
        textColor=hex_to_color(theme_colors['text']),
        alignment=TA_CENTER,
        spaceAfter=12
    )

    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontName=FONT_NAME,
        fontSize=10,
        leading=14,
        textColor=hex_to_color(theme_colors['secondary_text']),
        alignment=TA_CENTER,
        spaceAfter=20
    )

    heading1_style = ParagraphStyle(
        'CustomHeading1',
        parent=styles['Heading1'],
        fontName=FONT_NAME,
        fontSize=16,
        leading=22,
        textColor=hex_to_color(theme_colors['accent_blue']),
        alignment=TA_LEFT,
        spaceBefore=16,
        spaceAfter=10
    )

    heading2_style = ParagraphStyle(
        'CustomHeading2',
        parent=styles['Heading2'],
        fontName=FONT_NAME,
        fontSize=13,
        leading=18,
        textColor=hex_to_color(theme_colors['text']),
        alignment=TA_LEFT,
        spaceBefore=12,
        spaceAfter=8
    )

    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontName=FONT_NAME,
        fontSize=10,
        leading=14,
        textColor=hex_to_color(theme_colors['text']),
        alignment=TA_LEFT
    )

    metric_value_style = ParagraphStyle(
        'MetricValue',
        parent=styles['Normal'],
        fontName=FONT_NAME,
        fontSize=18,
        leading=22,
        textColor=hex_to_color(theme_colors['text']),
        alignment=TA_CENTER
    )

    metric_label_style = ParagraphStyle(
        'MetricLabel',
        parent=styles['Normal'],
        fontName=FONT_NAME,
        fontSize=9,
        leading=12,
        textColor=hex_to_color(theme_colors['secondary_text']),
        alignment=TA_CENTER
    )

    table_header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName=FONT_NAME,
        fontSize=9,
        leading=12,
        textColor=colors.white,
        alignment=TA_CENTER
    )

    table_cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName=FONT_NAME,
        fontSize=8,
        leading=11,
        textColor=hex_to_color(theme_colors['text']),
        alignment=TA_CENTER
    )

    return {
        'title': title_style,
        'subtitle': subtitle_style,
        'heading1': heading1_style,
        'heading2': heading2_style,
        'normal': normal_style,
        'metric_value': metric_value_style,
        'metric_label': metric_label_style,
        'table_header': table_header_style,
        'table_cell': table_cell_style,
    }


def fig_to_image(fig, width=170 * mm, height=100 * mm):
    buf = BytesIO()
    fig.savefig(buf, format='png', dpi=150, bbox_inches='tight', facecolor=fig.get_facecolor())
    buf.seek(0)
    plt.close(fig)
    img = Image(buf, width=width, height=height)
    return img


def create_metric_cards_table(metrics, theme_colors, styles):
    table_data = []
    value_row = []
    label_row = []
    colors_row = []

    for i, (label, value, accent_color) in enumerate(metrics):
        value_row.append(Paragraph(str(value), styles['metric_value']))
        label_row.append(Paragraph(str(label), styles['metric_label']))
        colors_row.append(hex_to_color(accent_color))

    table_data.append(value_row)
    table_data.append(label_row)

    n_cols = len(metrics)
    col_width = (170 * mm) / n_cols

    table = Table(table_data, colWidths=[col_width] * n_cols)

    style_cmds = [
        ('FONTNAME', (0, 0), (-1, -1), FONT_NAME),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, hex_to_color(theme_colors['border'])),
        ('BACKGROUND', (0, 0), (-1, -1), hex_to_color(theme_colors['bg'])),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]

    for i in range(n_cols):
        style_cmds.append(('LINEABOVE', (i, 0), (i, 0), 3, colors_row[i]))

    table.setStyle(TableStyle(style_cmds))
    return table


def create_data_table(df, theme_colors, styles, max_rows=20):
    if df is None or len(df) == 0:
        return None

    display_df = df.head(max_rows).copy()

    header_row = [Paragraph(str(col), styles['table_header']) for col in display_df.columns]
    table_data = [header_row]

    for _, row in display_df.iterrows():
        table_data.append([
            Paragraph(str(cell), styles['table_cell']) for cell in row.values
        ])

    n_cols = len(display_df.columns)
    col_width = (170 * mm) / n_cols

    table = Table(table_data, colWidths=[col_width] * n_cols, repeatRows=1)

    style_cmds = [
        ('FONTNAME', (0, 0), (-1, -1), FONT_NAME),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, hex_to_color(theme_colors['border'])),
        ('BACKGROUND', (0, 0), (-1, 0), hex_to_color(theme_colors['accent_blue'])),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [
            hex_to_color(theme_colors['bg']),
            hex_to_color(theme_colors['table_alt_bg'])
        ]),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]

    table.setStyle(TableStyle(style_cmds))
    return table


def compute_kpi_metrics(df, theme_colors):
    if df is None or len(df) == 0:
        return []

    total_users = len(df)
    male_count = len(df[df['gender'] == '男']) if 'gender' in df.columns else 0
    female_count = len(df[df['gender'] == '女']) if 'gender' in df.columns else 0
    avg_age = df['age'].mean() if 'age' in df.columns else 0
    province_count = df['province'].nunique() if 'province' in df.columns else 0

    total_spent = df['total_spent'].sum() if 'total_spent' in df.columns else 0
    active_count = len(df[df['user_segment'] == '活跃用户']) if 'user_segment' in df.columns else 0

    metrics = [
        ('总用户数', f'{total_users:,}', theme_colors['accent_blue']),
        ('男性用户', f'{male_count:,}', theme_colors['accent_red']),
        ('女性用户', f'{female_count:,}', theme_colors['accent_green']),
        ('平均年龄', f'{avg_age:.1f}岁', theme_colors['accent_orange']),
        ('覆盖省份', f'{province_count}', theme_colors['accent_gray']),
        ('总消费额', f'¥{total_spent:,.0f}', theme_colors['accent_blue']),
    ]

    if 'user_segment' in df.columns:
        metrics.append(('活跃用户', f'{active_count:,}', theme_colors['accent_green']))

    return metrics


def generate_gender_chart(df, theme):
    from matplotlib.font_manager import FontProperties as FP
    theme_colors = get_theme_colors(theme)
    tchart = theme.get('chart', {})

    fig, ax = plt.subplots(figsize=(8, 4))
    fig.patch.set_facecolor(tchart.get('figure_facecolor', 'white'))
    ax.set_facecolor(tchart.get('axes_facecolor', 'white'))

    fp = get_available_chinese_font()
    font_prop = FP(fname=fp, size=10) if fp else FP(family='SimHei', size=10)
    font_title = FP(fname=fp, size=13, weight='bold') if fp else FP(family='SimHei', size=13, weight='bold')
    font_label = FP(fname=fp, size=11, weight='bold') if fp else FP(family='SimHei', size=11, weight='bold')

    if 'gender' in df.columns and len(df) > 0:
        gender_counts = df['gender'].value_counts()
        colors_list = tchart.get('palette_bar', ['#3498DB', '#E74C3C'])
        bars = ax.barh(gender_counts.index, gender_counts.values, color=colors_list)
        ax.set_title('用户性别分布', fontproperties=font_title, pad=10, color=tchart.get('text_color', '#2C3E50'))
        ax.set_xlabel('用户数量', fontproperties=font_label, color=tchart.get('label_color', '#2C3E50'))

        total = len(df)
        for bar, count in zip(bars, gender_counts.values):
            pct = (count / total) * 100 if total > 0 else 0
            ax.text(bar.get_width() + max(gender_counts.values) * 0.01,
                    bar.get_y() + bar.get_height() / 2,
                    f'{count:,} ({pct:.1f}%)',
                    va='center', fontproperties=font_prop, color=tchart.get('text_color', '#2C3E50'))
    else:
        ax.text(0.5, 0.5, '暂无数据', ha='center', va='center', fontproperties=font_title)
        ax.axis('off')

    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_fontproperties(font_prop)
        label.set_color(tchart.get('tick_color', '#2C3E50'))

    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color(tchart.get('grid_color', '#cccccc'))
    ax.spines['bottom'].set_color(tchart.get('grid_color', '#cccccc'))
    ax.grid(True, alpha=0.3, linestyle='--', color=tchart.get('grid_color', '#cccccc'), axis='x')
    ax.set_axisbelow(True)
    plt.tight_layout()
    return fig


def generate_age_distribution_chart(df, theme):
    from matplotlib.font_manager import FontProperties as FP
    tchart = theme.get('chart', {})

    fig, ax = plt.subplots(figsize=(8, 4))
    fig.patch.set_facecolor(tchart.get('figure_facecolor', 'white'))
    ax.set_facecolor(tchart.get('axes_facecolor', 'white'))

    fp = get_available_chinese_font()
    font_prop = FP(fname=fp, size=10) if fp else FP(family='SimHei', size=10)
    font_title = FP(fname=fp, size=13, weight='bold') if fp else FP(family='SimHei', size=13, weight='bold')
    font_label = FP(fname=fp, size=11, weight='bold') if fp else FP(family='SimHei', size=11, weight='bold')

    if 'age_group' in df.columns and len(df) > 0:
        age_order = ['18以下', '18-24', '25-34', '35-44', '45-54', '55-64', '65+']
        age_counts = df['age_group'].value_counts().reindex(age_order).fillna(0)

        colors_list = tchart.get('palette_segment', ['#27AE60', '#3498DB', '#95A5A6'])
        ax.bar(age_counts.index, age_counts.values, color=colors_list[:len(age_counts)])
        ax.set_title('用户年龄分布', fontproperties=font_title, pad=10, color=tchart.get('text_color', '#2C3E50'))
        ax.set_xlabel('年龄段', fontproperties=font_label, color=tchart.get('label_color', '#2C3E50'))
        ax.set_ylabel('用户数量', fontproperties=font_label, color=tchart.get('label_color', '#2C3E50'))

        for i, (_, count) in enumerate(age_counts.items()):
            if count > 0:
                ax.text(i, count + max(age_counts.values) * 0.01,
                        f'{int(count):,}', ha='center', fontproperties=font_prop,
                        color=tchart.get('text_color', '#2C3E50'))
    else:
        ax.text(0.5, 0.5, '暂无数据', ha='center', va='center', fontproperties=font_title)
        ax.axis('off')

    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_fontproperties(font_prop)
        label.set_color(tchart.get('tick_color', '#2C3E50'))
    ax.tick_params(axis='x', rotation=20)

    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color(tchart.get('grid_color', '#cccccc'))
    ax.spines['bottom'].set_color(tchart.get('grid_color', '#cccccc'))
    ax.grid(True, alpha=0.3, linestyle='--', color=tchart.get('grid_color', '#cccccc'), axis='y')
    ax.set_axisbelow(True)
    plt.tight_layout()
    return fig


def generate_region_chart(df, theme):
    from matplotlib.font_manager import FontProperties as FP
    tchart = theme.get('chart', {})

    fig, ax = plt.subplots(figsize=(8, 4))
    fig.patch.set_facecolor(tchart.get('figure_facecolor', 'white'))
    ax.set_facecolor(tchart.get('axes_facecolor', 'white'))

    fp = get_available_chinese_font()
    font_prop = FP(fname=fp, size=10) if fp else FP(family='SimHei', size=10)
    font_title = FP(fname=fp, size=13, weight='bold') if fp else FP(family='SimHei', size=13, weight='bold')
    font_label = FP(fname=fp, size=11, weight='bold') if fp else FP(family='SimHei', size=11, weight='bold')

    if 'province' in df.columns and len(df) > 0:
        province_counts = df['province'].value_counts().head(10)
        import seaborn as sns
        colors_list = sns.color_palette(tchart.get('palette_province', 'viridis'), len(province_counts))

        bars = ax.barh(province_counts.index[::-1], province_counts.values[::-1], color=colors_list)
        ax.set_title('用户省份分布 TOP10', fontproperties=font_title, pad=10,
                     color=tchart.get('text_color', '#2C3E50'))
        ax.set_xlabel('用户数量', fontproperties=font_label, color=tchart.get('label_color', '#2C3E50'))

        total = len(df)
        for bar, count in zip(bars, province_counts.values[::-1]):
            pct = (count / total) * 100 if total > 0 else 0
            ax.text(bar.get_width() + max(province_counts.values) * 0.01,
                    bar.get_y() + bar.get_height() / 2,
                    f'{count:,} ({pct:.1f}%)',
                    va='center', fontproperties=font_prop, color=tchart.get('text_color', '#2C3E50'))
    else:
        ax.text(0.5, 0.5, '暂无数据', ha='center', va='center', fontproperties=font_title)
        ax.axis('off')

    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_fontproperties(font_prop)
        label.set_color(tchart.get('tick_color', '#2C3E50'))

    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color(tchart.get('grid_color', '#cccccc'))
    ax.spines['bottom'].set_color(tchart.get('grid_color', '#cccccc'))
    ax.grid(True, alpha=0.3, linestyle='--', color=tchart.get('grid_color', '#cccccc'), axis='x')
    ax.set_axisbelow(True)
    plt.tight_layout()
    return fig


def generate_behavior_segment_chart(df, theme):
    from matplotlib.font_manager import FontProperties as FP
    tchart = theme.get('chart', {})

    fig, ax = plt.subplots(figsize=(8, 4))
    fig.patch.set_facecolor(tchart.get('figure_facecolor', 'white'))
    ax.set_facecolor(tchart.get('axes_facecolor', 'white'))

    fp = get_available_chinese_font()
    font_prop = FP(fname=fp, size=10) if fp else FP(family='SimHei', size=10)
    font_title = FP(fname=fp, size=13, weight='bold') if fp else FP(family='SimHei', size=13, weight='bold')

    if 'user_segment' in df.columns and len(df) > 0:
        segment_counts = df['user_segment'].value_counts()
        segment_order = ['活跃用户', '普通用户', '沉睡用户']
        segment_counts = segment_counts.reindex(segment_order).fillna(0)
        segment_counts = segment_counts[segment_counts > 0]

        colors_list = tchart.get('palette_segment', ['#27AE60', '#3498DB', '#95A5A6'])
        explode = tuple([0.03] * len(segment_counts))

        wedges, texts, autotexts = ax.pie(
            segment_counts.values,
            labels=segment_counts.index,
            colors=colors_list[:len(segment_counts)],
            autopct='%1.1f%%',
            startangle=90,
            explode=explode,
            pctdistance=0.75
        )
        for text in texts:
            text.set_fontproperties(font_prop)
            text.set_color(tchart.get('text_color', '#2C3E50'))
        for autotext in autotexts:
            autotext.set_fontproperties(font_prop)
            autotext.set_color(tchart.get('pie_text_color', 'white'))

        ax.set_title('用户行为分群分布', fontproperties=font_title, pad=10,
                     color=tchart.get('text_color', '#2C3E50'))
    else:
        ax.text(0.5, 0.5, '暂无数据', ha='center', va='center', fontproperties=font_title)
        ax.axis('off')

    plt.tight_layout()
    return fig


def generate_preference_chart(df, theme, pref_type='interest'):
    from matplotlib.font_manager import FontProperties as FP
    from user_preferences import PREFERENCE_TYPES, get_preference_ranking
    tchart = theme.get('chart', {})

    fig, ax = plt.subplots(figsize=(8, 4))
    fig.patch.set_facecolor(tchart.get('figure_facecolor', 'white'))
    ax.set_facecolor(tchart.get('axes_facecolor', 'white'))

    fp = get_available_chinese_font()
    font_prop = FP(fname=fp, size=9) if fp else FP(family='SimHei', size=9)
    font_title = FP(fname=fp, size=13, weight='bold') if fp else FP(family='SimHei', size=13, weight='bold')
    font_label = FP(fname=fp, size=10, weight='bold') if fp else FP(family='SimHei', size=10, weight='bold')

    pref_label = PREFERENCE_TYPES.get(pref_type, '偏好')
    ranking = get_preference_ranking(df, pref_type, top_n=8)

    if len(ranking) > 0:
        import seaborn as sns
        colors_list = sns.color_palette(tchart.get('palette_ranking', 'YlOrRd_r'), len(ranking))
        bars = ax.barh(ranking['标签'][::-1], ranking['权重'][::-1], color=colors_list)

        ax.set_title(f'{pref_label}权重分布 TOP8', fontproperties=font_title, pad=10,
                     color=tchart.get('text_color', '#2C3E50'))
        ax.set_xlabel('权重', fontproperties=font_label, color=tchart.get('label_color', '#2C3E50'))

        for bar, pct in zip(bars, ranking['占比'][::-1].values):
            ax.text(bar.get_width() + ranking['权重'].max() * 0.01,
                    bar.get_y() + bar.get_height() / 2,
                    f'{pct:.1f}%',
                    va='center', fontproperties=font_prop, color=tchart.get('text_color', '#2C3E50'))
    else:
        ax.text(0.5, 0.5, '暂无数据', ha='center', va='center', fontproperties=font_title)
        ax.axis('off')

    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_fontproperties(font_prop)
        label.set_color(tchart.get('tick_color', '#2C3E50'))

    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color(tchart.get('grid_color', '#cccccc'))
    ax.spines['bottom'].set_color(tchart.get('grid_color', '#cccccc'))
    ax.grid(True, alpha=0.3, linestyle='--', color=tchart.get('grid_color', '#cccccc'), axis='x')
    ax.set_axisbelow(True)
    plt.tight_layout()
    return fig


def generate_generation_chart(df, theme):
    from matplotlib.font_manager import FontProperties as FP
    tchart = theme.get('chart', {})

    fig, ax = plt.subplots(figsize=(8, 4))
    fig.patch.set_facecolor(tchart.get('figure_facecolor', 'white'))
    ax.set_facecolor(tchart.get('axes_facecolor', 'white'))

    fp = get_available_chinese_font()
    font_prop = FP(fname=fp, size=10) if fp else FP(family='SimHei', size=10)
    font_title = FP(fname=fp, size=13, weight='bold') if fp else FP(family='SimHei', size=13, weight='bold')

    GENERATION_ORDER = ['00后', '90后', '80后', '70后', '60后', '其他']

    if 'generation' in df.columns and len(df) > 0:
        gen_counts = df['generation'].value_counts().reindex(GENERATION_ORDER).fillna(0)
        gen_counts = gen_counts[gen_counts > 0]

        if len(gen_counts) > 0:
            import seaborn as sns
            colors_list = sns.color_palette(tchart.get('palette_segment', 'viridis'), len(gen_counts))
            explode = tuple([0.03] * len(gen_counts))

            wedges, texts, autotexts = ax.pie(
                gen_counts.values,
                labels=gen_counts.index,
                colors=colors_list,
                autopct='%1.1f%%',
                startangle=90,
                explode=explode,
                pctdistance=0.75
            )
            for text in texts:
                text.set_fontproperties(font_prop)
                text.set_color(tchart.get('text_color', '#2C3E50'))
            for autotext in autotexts:
                autotext.set_fontproperties(font_prop)
                autotext.set_color(tchart.get('pie_text_color', 'white'))

            ax.set_title('各代际用户数量占比', fontproperties=font_title, pad=10,
                         color=tchart.get('text_color', '#2C3E50'))
        else:
            ax.text(0.5, 0.5, '暂无数据', ha='center', va='center', fontproperties=font_title)
            ax.axis('off')
    else:
        ax.text(0.5, 0.5, '暂无数据', ha='center', va='center', fontproperties=font_title)
        ax.axis('off')

    plt.tight_layout()
    return fig


def get_summary_tables(df, selected_charts=None):
    if selected_charts is None:
        selected_charts = ['gender', 'age', 'region', 'segment', 'preference', 'generation']

    tables = {}

    if 'gender' in selected_charts and 'gender' in df.columns and len(df) > 0:
        gender_summary = df['gender'].value_counts().reset_index()
        gender_summary.columns = ['性别', '用户数']
        total = len(df)
        gender_summary['占比(%)'] = (gender_summary['用户数'] / total * 100).round(2)
        tables['gender'] = gender_summary

    if 'age' in selected_charts and 'age_group' in df.columns and len(df) > 0:
        age_order = ['18以下', '18-24', '25-34', '35-44', '45-54', '55-64', '65+']
        age_summary = df['age_group'].value_counts().reindex(age_order).dropna().reset_index()
        age_summary.columns = ['年龄段', '用户数']
        total = len(df)
        age_summary['占比(%)'] = (age_summary['用户数'] / total * 100).round(2)
        tables['age'] = age_summary

    if 'region' in selected_charts and 'province' in df.columns and len(df) > 0:
        prov_summary = df['province'].value_counts().head(10).reset_index()
        prov_summary.columns = ['省份', '用户数']
        total = len(df)
        prov_summary['占比(%)'] = (prov_summary['用户数'] / total * 100).round(2)
        tables['region'] = prov_summary

    if 'segment' in selected_charts and 'user_segment' in df.columns and len(df) > 0:
        from user_behavior import get_segment_summary
        seg_summary = get_segment_summary(df)
        if len(seg_summary) > 0:
            tables['segment'] = seg_summary

    if 'preference' in selected_charts and len(df) > 0:
        from user_preferences import get_preference_ranking, PREFERENCE_TYPES
        pref_tables = {}
        for pref_type in PREFERENCE_TYPES.keys():
            ranking = get_preference_ranking(df, pref_type, top_n=8)
            if len(ranking) > 0:
                pref_tables[pref_type] = ranking
        if pref_tables:
            tables['preference'] = pref_tables

    if 'generation' in selected_charts and 'generation' in df.columns and len(df) > 0:
        GENERATION_ORDER = ['00后', '90后', '80后', '70后', '60后', '其他']
        gen_summary = df['generation'].value_counts().reindex(GENERATION_ORDER).dropna().reset_index()
        gen_summary.columns = ['代际', '用户数']
        total = len(df)
        gen_summary['占比(%)'] = (gen_summary['用户数'] / total * 100).round(2)
        tables['generation'] = gen_summary

    return tables


def generate_pdf_report(
    df,
    theme,
    selected_charts=None,
    filter_summary=None,
    title="用户画像分析报告"
):
    """
    生成用户画像 PDF 报告

    参数:
        df: 筛选后的用户数据 DataFrame
        theme: 主题配置字典
        selected_charts: 选择要包含的图表列表，如 ['gender', 'age', 'region', 'segment', 'preference', 'generation']
        filter_summary: 筛选条件摘要字典
        title: 报告标题

    返回:
        bytes: PDF 文件二进制数据
    """
    if selected_charts is None:
        selected_charts = ['gender', 'age', 'region', 'segment', 'preference', 'generation']

    theme_colors = get_theme_colors(theme)
    styles = create_styles(theme_colors)

    buffer = BytesIO()

    page_bg_color = hex_to_color(theme_colors['background'])

    def draw_page_bg(canvas, doc):
        canvas.saveState()
        canvas.setFillColor(page_bg_color)
        canvas.rect(0, 0, doc.pagesize[0], doc.pagesize[1], fill=1, stroke=0)
        canvas.restoreState()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
        title=title,
        author="用户画像分析系统"
    )

    story = []

    story.append(Paragraph(title, styles['title']))
    story.append(Paragraph(
        f"报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        styles['subtitle']
    ))

    if filter_summary:
        filter_text_parts = []
        if filter_summary.get('n_samples'):
            filter_text_parts.append(f"样本数: {filter_summary['n_samples']:,}")
        if filter_summary.get('selected_province') and filter_summary['selected_province'] != '全部':
            filter_text_parts.append(f"省份: {filter_summary['selected_province']}")
        if filter_summary.get('selected_segment'):
            filter_text_parts.append(f"行为群体: {'、'.join(filter_summary['selected_segment'])}")
        if filter_summary.get('selected_generation'):
            filter_text_parts.append(f"代际: {'、'.join(filter_summary['selected_generation'])}")

        if filter_text_parts:
            story.append(Paragraph("筛选条件: " + " | ".join(filter_text_parts), styles['subtitle']))

    story.append(Spacer(1, 5 * mm))

    story.append(Paragraph("一、关键指标摘要", styles['heading1']))
    kpi_metrics = compute_kpi_metrics(df, theme_colors)
    if kpi_metrics:
        metric_table = create_metric_cards_table(kpi_metrics, theme_colors, styles)
        story.append(metric_table)
    story.append(Spacer(1, 5 * mm))

    story.append(Paragraph("二、主要图表分析", styles['heading1']))

    if 'gender' in selected_charts:
        story.append(Paragraph("2.1 性别分布", styles['heading2']))
        gender_fig = generate_gender_chart(df, theme)
        story.append(fig_to_image(gender_fig, width=160 * mm, height=85 * mm))
        story.append(Spacer(1, 3 * mm))

    if 'age' in selected_charts:
        story.append(Paragraph("2.2 年龄分布", styles['heading2']))
        age_fig = generate_age_distribution_chart(df, theme)
        story.append(fig_to_image(age_fig, width=160 * mm, height=85 * mm))
        story.append(Spacer(1, 3 * mm))

    if 'region' in selected_charts:
        story.append(Paragraph("2.3 地域分布", styles['heading2']))
        region_fig = generate_region_chart(df, theme)
        story.append(fig_to_image(region_fig, width=160 * mm, height=90 * mm))
        story.append(Spacer(1, 3 * mm))

    if 'segment' in selected_charts:
        story.append(Paragraph("2.4 行为分群", styles['heading2']))
        segment_fig = generate_behavior_segment_chart(df, theme)
        story.append(fig_to_image(segment_fig, width=160 * mm, height=85 * mm))
        story.append(Spacer(1, 3 * mm))

    if 'preference' in selected_charts:
        story.append(Paragraph("2.5 偏好分析", styles['heading2']))
        pref_fig_interest = generate_preference_chart(df, theme, 'interest')
        story.append(fig_to_image(pref_fig_interest, width=160 * mm, height=85 * mm))
        story.append(Spacer(1, 2 * mm))
        pref_fig_consumption = generate_preference_chart(df, theme, 'consumption')
        story.append(fig_to_image(pref_fig_consumption, width=160 * mm, height=85 * mm))
        story.append(Spacer(1, 2 * mm))
        pref_fig_channel = generate_preference_chart(df, theme, 'channel')
        story.append(fig_to_image(pref_fig_channel, width=160 * mm, height=85 * mm))
        story.append(Spacer(1, 3 * mm))

    if 'generation' in selected_charts:
        story.append(Paragraph("2.6 代际分布", styles['heading2']))
        gen_fig = generate_generation_chart(df, theme)
        story.append(fig_to_image(gen_fig, width=160 * mm, height=85 * mm))
        story.append(Spacer(1, 3 * mm))

    story.append(PageBreak())
    story.append(Paragraph("三、数据摘要表格", styles['heading1']))

    summary_tables = get_summary_tables(df, selected_charts)

    section_num = 1

    if 'gender' in summary_tables:
        story.append(Paragraph(f"3.{section_num} 性别统计", styles['heading2']))
        tbl = create_data_table(summary_tables['gender'], theme_colors, styles)
        if tbl:
            story.append(tbl)
        story.append(Spacer(1, 3 * mm))
        section_num += 1

    if 'age' in summary_tables:
        story.append(Paragraph(f"3.{section_num} 年龄段统计", styles['heading2']))
        tbl = create_data_table(summary_tables['age'], theme_colors, styles)
        if tbl:
            story.append(tbl)
        story.append(Spacer(1, 3 * mm))
        section_num += 1

    if 'region' in summary_tables:
        story.append(Paragraph(f"3.{section_num} 省份分布统计 TOP10", styles['heading2']))
        tbl = create_data_table(summary_tables['region'], theme_colors, styles)
        if tbl:
            story.append(tbl)
        story.append(Spacer(1, 3 * mm))
        section_num += 1

    if 'segment' in summary_tables:
        story.append(Paragraph(f"3.{section_num} 行为分群统计", styles['heading2']))
        tbl = create_data_table(summary_tables['segment'], theme_colors, styles)
        if tbl:
            story.append(tbl)
        story.append(Spacer(1, 3 * mm))
        section_num += 1

    if 'preference' in summary_tables:
        from user_preferences import PREFERENCE_TYPES
        pref_tables = summary_tables['preference']
        for pref_type, pref_label in PREFERENCE_TYPES.items():
            if pref_type in pref_tables:
                story.append(Paragraph(f"3.{section_num} {pref_label}统计 TOP8", styles['heading2']))
                tbl = create_data_table(pref_tables[pref_type], theme_colors, styles)
                if tbl:
                    story.append(tbl)
                story.append(Spacer(1, 3 * mm))
                section_num += 1

    if 'generation' in summary_tables:
        story.append(Paragraph(f"3.{section_num} 代际分布统计", styles['heading2']))
        tbl = create_data_table(summary_tables['generation'], theme_colors, styles)
        if tbl:
            story.append(tbl)

    story.append(Spacer(1, 10 * mm))
    story.append(Paragraph(
        "--- 报告结束 ---",
        styles['subtitle']
    ))

    doc.build(story, onFirstPage=draw_page_bg, onLaterPages=draw_page_bg)
    pdf_data = buffer.getvalue()
    buffer.close()

    return pdf_data


AVAILABLE_PDF_CHARTS = [
    ('gender', '性别分布'),
    ('age', '年龄分布'),
    ('region', '地域分布'),
    ('segment', '行为分群'),
    ('preference', '偏好分析'),
    ('generation', '代际分布'),
]
