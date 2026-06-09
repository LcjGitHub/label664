LIGHT_THEME = {
    'name': '亮色',
    'icon': '☀️',
    'colors': {
        'background': '#f8f9fa',
        'card_background': '#ffffff',
        'sidebar_background': '#2C3E50',
        'header_background': '#2C3E50',
        'primary_text': '#2C3E50',
        'secondary_text': '#7f8c8d',
        'muted_text': '#95a5a6',
        'accent_blue': '#3498DB',
        'accent_red': '#E74C3C',
        'accent_green': '#27AE60',
        'accent_orange': '#F39C12',
        'accent_gray': '#95A5A6',
        'border': '#e0e0e0',
        'grid': '#cccccc'
    },
    'chart': {
        'figure_facecolor': 'white',
        'axes_facecolor': 'white',
        'text_color': '#2C3E50',
        'label_color': '#2C3E50',
        'tick_color': '#2C3E50',
        'grid_color': '#cccccc',
        'pie_text_color': 'white',
        'wordcloud_background': 'white',
        'wordcloud_colormap': 'viridis',
        'palette_bar': ['#3498DB', '#E74C3C'],
        'palette_segment': ['#27AE60', '#3498DB', '#95A5A6'],
        'palette_region': ['#E74C3C', '#3498DB'],
        'palette_province': 'viridis',
        'palette_ranking': 'YlOrRd_r'
    },
    'css': {
        'main_bg': '#f8f9fa',
        'header_bg': '#2C3E50',
        'header_text': 'white',
        'sidebar_bg': '#2C3E50',
        'card_bg': 'white',
        'card_shadow': '0 2px 10px rgba(0,0,0,0.1)',
        'primary_text_color': '#2C3E50',
        'secondary_text_color': '#7f8c8d',
        'muted_text_color': '#95a5a6',
        'footer_text_color': '#7f8c8d'
    }
}

DARK_THEME = {
    'name': '暗色',
    'icon': '🌙',
    'colors': {
        'background': '#1a1a2e',
        'card_background': '#16213e',
        'sidebar_background': '#0f0f23',
        'header_background': '#0f0f23',
        'primary_text': '#e8e8e8',
        'secondary_text': '#a0a0b0',
        'muted_text': '#707080',
        'accent_blue': '#5dade2',
        'accent_red': '#ec7063',
        'accent_green': '#58d68d',
        'accent_orange': '#f5b041',
        'accent_gray': '#85929e',
        'border': '#2a2a4a',
        'grid': '#3a3a5a'
    },
    'chart': {
        'figure_facecolor': '#16213e',
        'axes_facecolor': '#16213e',
        'text_color': '#e8e8e8',
        'label_color': '#e8e8e8',
        'tick_color': '#e8e8e8',
        'grid_color': '#3a3a5a',
        'pie_text_color': '#16213e',
        'wordcloud_background': '#16213e',
        'wordcloud_colormap': 'plasma',
        'palette_bar': ['#5dade2', '#ec7063'],
        'palette_segment': ['#58d68d', '#5dade2', '#85929e'],
        'palette_region': ['#ec7063', '#5dade2'],
        'palette_province': 'plasma',
        'palette_ranking': 'YlOrBr'
    },
    'css': {
        'main_bg': '#1a1a2e',
        'header_bg': '#0f0f23',
        'header_text': '#e8e8e8',
        'sidebar_bg': '#0f0f23',
        'card_bg': '#16213e',
        'card_shadow': '0 2px 10px rgba(0,0,0,0.4)',
        'primary_text_color': '#e8e8e8',
        'secondary_text_color': '#a0a0b0',
        'muted_text_color': '#707080',
        'footer_text_color': '#707080'
    }
}

THEMES = {
    'light': LIGHT_THEME,
    'dark': DARK_THEME
}

DEFAULT_THEME = 'light'


def get_theme(theme_key):
    return THEMES.get(theme_key, THEMES[DEFAULT_THEME])


def get_theme_options():
    return [(key, f"{value['icon']} {value['name']}") for key, value in THEMES.items()]


def generate_css(theme):
    c = theme['css']
    return f"""
<style>
.main {{
    background-color: {c['main_bg']};
}}
.stApp > header {{
    background-color: {c['header_bg']};
}}
.stApp > header h1 {{
    color: {c['header_text']} !important;
}}
.css-1d391kg {{
    background-color: {c['sidebar_bg']};
}}
[data-testid="stSidebar"] {{
    background-color: {c['sidebar_bg']};
}}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] .stSlider label {{
    color: #e8e8e8;
}}
.metric-card {{
    background: {c['card_bg']};
    padding: 20px;
    border-radius: 10px;
    box-shadow: {c['card_shadow']};
    margin: 10px 0;
    color: {c['primary_text_color']};
}}
.metric-card p,
.metric-card h3 {{
    color: {c['primary_text_color']};
}}
.chart-container {{
    background: {c['card_bg']};
    padding: 20px;
    border-radius: 10px;
    box-shadow: {c['card_shadow']};
    margin: 10px 0;
}}
[data-testid="stMetricValue"] {{
    color: {c['primary_text_color']} !important;
}}
[data-testid="stMetricLabel"] p {{
    color: {c['secondary_text_color']} !important;
}}
[data-testid="stMetricDelta"] {{
    color: {c['secondary_text_color']} !important;
}}
h1, h2, h3, h4, h5, h6 {{
    color: {c['primary_text_color']} !important;
}}
p, span, div {{
    color: {c['primary_text_color']};
}}
[data-testid="stMarkdownContainer"] p {{
    color: {c['primary_text_color']};
}}
.stMarkdown {{
    color: {c['primary_text_color']};
}}
[data-testid="stCaptionContainer"] p {{
    color: {c['muted_text_color']} !important;
}}
footer {{
    color: {c['footer_text_color']} !important;
}}
[data-testid="stDataFrame"] {{
    background-color: {c['card_bg']};
}}
[data-testid="stDataFrame"] table {{
    background-color: {c['card_bg']};
    color: {c['primary_text_color']};
}}
[data-testid="stDataFrame"] th {{
    background-color: {c['card_bg']};
    color: {c['primary_text_color']};
}}
[data-testid="stDataFrame"] td {{
    background-color: {c['card_bg']};
    color: {c['primary_text_color']};
}}
hr {{
    border-color: {c['card_bg']};
}}
.stAlert {{
    background-color: {c['card_bg']} !important;
    color: {c['primary_text_color']} !important;
}}
.stSuccess, .stInfo, .stWarning, .stError {{
    color: {c['primary_text_color']} !important;
}}
</style>
"""
