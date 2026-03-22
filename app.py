import pandas as pd
import streamlit as st
import plotly.express as px

# =========================
# Page Config
# =========================
st.set_page_config(layout="wide", page_title="TikTok Creative Dashboard")

# =========================
# Load Data
# =========================
df = pd.read_excel("/home/mazed/Downloads/preprocessed_file.xlsx")

# =========================
# Ensure Numeric Columns
# =========================
numeric_cols = [
    'product_ad_impressions',
    'product_ad_clicks',
    'product_ad_click_rate',
    'ad_conversion_rate',
    '2-second_ad_video_view_rate',
    'gross_revenue'
]

for col in numeric_cols:
    df[col] = pd.to_numeric(df[col], errors='coerce')

# =========================
# Hook Flag
# =========================
df['hook_flag'] = df['2-second_ad_video_view_rate'] > 0.35


# =========================
# Normalization Function
# =========================
def normalize(series):
    return (series - series.min()) / (series.max() - series.min())


# =========================
# Dashboard Title
# =========================
st.title("📊 TikTok Creative Performance Dashboard")

# =========================
# OVERVIEW METRICS
# =========================
st.header("Overview Metrics")

col1, col2, col3, col4 = st.columns(4)

col1.metric("Total Videos", len(df))
col2.metric("Delivering", (df['status'] == 'delivering').sum())
col3.metric("Not Delivering", (df['status'] == 'not_delivering').sum())
col4.metric("Strong Hook %", f"{(df['hook_flag'].sum()/len(df)*100):.1f}%")

# =========================
# STATUS DISTRIBUTION
# =========================
st.header("Video Status Distribution")

fig_status = px.pie(
    df,
    names='status',
    title="Delivering vs Not Delivering"
)

st.plotly_chart(fig_status, use_container_width=True)

# =========================
# KEY METRICS COMPARISON
# =========================
st.header("Key Metrics by Status")

col1, col2, col3 = st.columns(3)

fig_impressions = px.box(
    df,
    x='status',
    y='product_ad_impressions',
    title="Impressions"
)

col1.plotly_chart(fig_impressions, use_container_width=True)

fig_hook = px.box(
    df,
    x='status',
    y='2-second_ad_video_view_rate',
    title="2-sec Hook Rate"
)

col2.plotly_chart(fig_hook, use_container_width=True)

fig_clicks = px.box(
    df,
    x='status',
    y='product_ad_clicks',
    title="Clicks"
)

col3.plotly_chart(fig_clicks, use_container_width=True)

# =========================
# FUNNEL ANALYSIS
# =========================
st.header("Performance Funnel")

funnel_data = df.groupby('status')[[
    'product_ad_impressions',
    'product_ad_clicks'
]].mean().reset_index()

fig_funnel = px.bar(
    funnel_data,
    x='status',
    y=['product_ad_impressions','product_ad_clicks'],
    barmode='group',
    title="Impressions → Clicks Funnel"
)

st.plotly_chart(fig_funnel, use_container_width=True)

# =========================
# TOP PERFORMING VIDEOS
# =========================
st.header("Top Performing Videos")

top_videos = df.sort_values(
    by='product_ad_impressions',
    ascending=False
).head(10)

st.dataframe(
    top_videos[
        [
            'video_title',
            'tiktok_account',
            'status',
            'product_ad_impressions',
            'product_ad_clicks',
            '2-second_ad_video_view_rate'
        ]
    ]
)

# =========================
# WORST PERFORMING VIDEOS
# =========================
st.header("Worst Performing Videos")

worst_videos = df.sort_values(
    by='product_ad_impressions'
).head(10)

st.dataframe(
    worst_videos[
        [
            'video_title',
            'tiktok_account',
            'status',
            'product_ad_impressions',
            'product_ad_clicks',
            '2-second_ad_video_view_rate'
        ]
    ]
)

# ====================================================
# CREATOR ANALYSIS
# ====================================================
st.header("Creator Analysis")

creator_perf = df.groupby('tiktok_account').agg(
    total_videos=('video_title','count'),
    impressions=('product_ad_impressions','sum'),
    clicks=('product_ad_clicks','sum'),
    revenue=('gross_revenue','sum'),
    avg_hook=('2-second_ad_video_view_rate','mean')
).reset_index()

# =========================
# NORMALIZE CREATOR DATA
# =========================
creator_perf['norm_impressions'] = normalize(creator_perf['impressions'])
creator_perf['norm_clicks'] = normalize(creator_perf['clicks'])
creator_perf['norm_revenue'] = normalize(creator_perf['revenue'])
creator_perf['norm_hook'] = normalize(creator_perf['avg_hook'])

# =========================
# CREATOR PERFORMANCE SCORE
# =========================
creator_perf['performance_score'] = (
    0.3 * creator_perf['norm_impressions'] +
    0.3 * creator_perf['norm_clicks'] +
    0.2 * creator_perf['norm_revenue'] +
    0.2 * creator_perf['norm_hook']
)

creator_perf = creator_perf.sort_values(
    by='performance_score',
    ascending=False
)

# =========================
# TOP CREATORS
# =========================
st.subheader("Top Creators by Performance Score")

fig_score = px.bar(
    creator_perf.head(10),
    x='tiktok_account',
    y='performance_score',
    title="Top Creators (Normalized Score)"
)

st.plotly_chart(fig_score, use_container_width=True)

# =========================
# HOOK VS REVENUE MAP
# =========================
st.subheader("Creator Performance Map")

fig_map = px.scatter(
    creator_perf,
    x='avg_hook',
    y='revenue',
    size='impressions',
    hover_name='tiktok_account',
    title="Hook Rate vs Revenue (Bubble = Impressions)"
)

st.plotly_chart(fig_map, use_container_width=True)

# =========================
# REVENUE SHARE
# =========================
st.subheader("Revenue Contribution")

fig_rev = px.pie(
    creator_perf,
    names='tiktok_account',
    values='revenue',
    title="Revenue Share by Creator"
)

st.plotly_chart(fig_rev, use_container_width=True)

# =========================
# WEAK CREATORS
# =========================
st.subheader("Weak Creators")

weak_creators = creator_perf.sort_values(
    by='performance_score'
).head(5)

st.dataframe(weak_creators)

# =========================
# Viral Hook Detection
# =========================

hook_threshold = df['2-second_ad_video_view_rate'].median()
impression_threshold = df['product_ad_impressions'].median()

def classify_hook(row):

    if row['2-second_ad_video_view_rate'] >= hook_threshold and row['product_ad_impressions'] >= impression_threshold:
        return "🔥 Viral Hook"

    elif row['2-second_ad_video_view_rate'] >= hook_threshold and row['product_ad_impressions'] < impression_threshold:
        return "⚠ Untested Hook"

    elif row['2-second_ad_video_view_rate'] < hook_threshold and row['product_ad_impressions'] >= impression_threshold:
        return "🤔 Lucky Distribution"

    else:
        return "❌ Weak Hook"

df['hook_type'] = df.apply(classify_hook, axis=1)

# =========================
# VIRAL HOOK DETECTOR
# =========================
st.header("🔥 Viral Hook Detector")

fig_hook = px.scatter(
    df,
    x='2-second_ad_video_view_rate',
    y='product_ad_impressions',
    color='hook_type',
    hover_name='video_title',
    size='product_ad_clicks',
    title="Hook Rate vs Impressions"
)

st.plotly_chart(fig_hook, use_container_width=True)

st.subheader("🔥 Videos With Viral Hooks")

viral_videos = df[df['hook_type']=="🔥 Viral Hook"]

st.dataframe(
    viral_videos[
        [
            'video_title',
            'tiktok_account',
            '2-second_ad_video_view_rate',
            'product_ad_impressions',
            'product_ad_clicks'
        ]
    ].sort_values(by='product_ad_impressions', ascending=False)
)

# st.subheader("❌ Weak Hook Videos")

# weak_videos = df[df['hook_type']=="❌ Weak Hook"]

# st.dataframe(
#     weak_videos[
#         [
#             'video_title',
#             'tiktok_account',
#             '2-second_ad_video_view_rate',
#             'product_ad_impressions'
#         ]
#     ]
# )
st.subheader("Hook Type Distribution")

fig_hook_dist = px.pie(
    df,
    names='hook_type',
    title="Distribution of Hook Types"
)

st.plotly_chart(fig_hook_dist, use_container_width=True)

# =========================
# INSIGHTS & RECOMMENDATIONS
# =========================
st.header("Insights & Recommendations")

st.markdown("""
**Key Insights:**  

- Videos that fail to capture attention in the first 2 seconds (low hook rate) are not delivered by TikTok.  
- Delivering videos have high hook rate (~40–50%) and higher impressions & clicks.  
- Some creators consistently generate higher impressions and revenue.  

**Recommendations:**  

1. Focus on optimizing the first 2–3 seconds of each video to increase hook rate.  
2. Analyze top-performing creators and replicate their hook style.  
3. Encourage creators to produce content with stronger storytelling and clear CTA.  
4. Scale collaborations with top creators driving the most revenue and impressions.  
5. Re-evaluate partnerships with weak creators producing low engagement.
""")