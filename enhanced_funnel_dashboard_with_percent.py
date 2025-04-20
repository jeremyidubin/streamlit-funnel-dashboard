
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# Set Streamlit page config
st.set_page_config(page_title="MQL and SQL with filters", layout="wide")

# Load Google Sheet data
@st.cache_data
def load_data():
    url = "https://docs.google.com/spreadsheets/d/1VA-ls42pPT8qEiW1KmY5S_JdVomU9C2HitGbYnwZw5U/export?format=csv&gid=1739898264"
    return pd.read_csv(url)

df = load_data()

# Normalize country field
df["Country Group"] = df["Country"].replace({"US": "United States"}).fillna("Unknown")
df["Region"] = df["Country Group"].apply(lambda x: "US" if x == "United States" else "Non-US")

# Identify freemail column automatically
freemail_col = [col for col in df.columns if 'freemail' in col.lower()]
if freemail_col:
    df["is_freemail"] = df[freemail_col[0]]
else:
    st.error("Could not find a column containing 'freemail'.")

# Funnel stages (binary indicators)
df["entered_stage_2"] = df["Enters Lead Stage 2"].notna()
df["entered_stage_3"] = df["Enters Lead Stage 3"].notna()
df["converted_to_opportunity"] = df["Converted to Sales Opportunity"] == True
df["opp_stage_1"] = df["Enters Opportunity Stage 1"].notna()
df["opp_stage_2"] = df["Enters Opportunity Stage 2"].notna()
df["opp_stage_3"] = df["Enters Opportunity Stage 3"].notna()
df["opp_stage_4"] = df["Enters Opportunity Stage 4"].notna()
df["opp_stage_5"] = df["Enters Opportunity Stage 5"].notna()
df["closed_won"] = df["Closed Won Date"].notna()

# Filters
st.sidebar.header("Filters")
region_filter = st.sidebar.selectbox("Region", ["All", "US only", "Non-US only"])
company_filter = st.sidebar.multiselect("Filter by Company Size", df["Company Size"].dropna().unique())
freemail_filter = st.sidebar.selectbox("Email Type", ["All", "Freemail only", "Corporate only"])

filtered_df = df.copy()
if region_filter == "US only":
    filtered_df = filtered_df[filtered_df["Region"] == "US"]
elif region_filter == "Non-US only":
    filtered_df = filtered_df[filtered_df["Region"] == "Non-US"]

if company_filter:
    filtered_df = filtered_df[filtered_df["Company Size"].isin(company_filter)]
if freemail_filter == "Freemail only":
    filtered_df = filtered_df[filtered_df["is_freemail"] == True]
elif freemail_filter == "Corporate only":
    filtered_df = filtered_df[filtered_df["is_freemail"] == False]

# Funnel 1: MQL → Sales Opportunity
mql_total = len(filtered_df)
stage_2 = filtered_df["entered_stage_2"].sum()
stage_3 = filtered_df["entered_stage_3"].sum()
opps = filtered_df["converted_to_opportunity"].sum()

mql_funnel = pd.DataFrame({
    "Stage": ["MQLs", "Lead Stage 2", "Lead Stage 3", "Converted to Opportunity"],
    "Count": [mql_total, stage_2, stage_3, opps]
})
mql_funnel["% of Previous"] = mql_funnel["Count"].pct_change().fillna(1).apply(lambda x: f"({x:.0%})")
mql_funnel["Label"] = mql_funnel.apply(lambda row: f"{row['Count']:,}\n{row['% of Previous']}", axis=1)

# Funnel 2: Sales Pipeline
opp_stage_1 = filtered_df["opp_stage_1"].sum()
opp_stage_2 = filtered_df["opp_stage_2"].sum()
opp_stage_3 = filtered_df["opp_stage_3"].sum()
opp_stage_4 = filtered_df["opp_stage_4"].sum()
opp_stage_5 = filtered_df["opp_stage_5"].sum()
won = filtered_df["closed_won"].sum()

sales_funnel = pd.DataFrame({
    "Stage": [
        "Opportunity Stage 1", "Stage 2", "Stage 3", "Stage 4", "Stage 5", "Closed Won"
    ],
    "Count": [opp_stage_1, opp_stage_2, opp_stage_3, opp_stage_4, opp_stage_5, won]
})
sales_funnel["% of Previous"] = sales_funnel["Count"].pct_change().fillna(1).apply(lambda x: f"({x:.0%})")
sales_funnel["Label"] = sales_funnel.apply(lambda row: f"{row['Count']:,}\n{row['% of Previous']}", axis=1)

# Layout and plotting
st.title("📈 Enhanced Funnel Dashboard with Percentages")
st.markdown("Visualize drop-offs across Marketing and Sales pipelines, including conversion percentages.")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Marketing Funnel: MQL → Sales Opportunity")
    fig1 = go.Figure(go.Funnel(
        y=mql_funnel["Stage"],
        x=mql_funnel["Count"],
        text=mql_funnel["Label"],
        textposition="inside",
        textfont=dict(size=16),
        marker=dict(color="#00A376")
    ))
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    st.subheader("Sales Funnel: Sales Opportunity → Closed Won")
    fig2 = go.Figure(go.Funnel(
        y=sales_funnel["Stage"],
        x=sales_funnel["Count"],
        text=sales_funnel["Label"],
        textposition="inside",
        textfont=dict(size=16),
        marker=dict(color="#00303F")
    ))
    st.plotly_chart(fig2, use_container_width=True)
