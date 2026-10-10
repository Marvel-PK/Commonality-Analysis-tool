import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO

st.set_page_config(
    page_title="CSV Commonality Analysis Tool",
    layout="wide"
)

st.title("📊 Retest CSV Commonality Analysis Tool")

# -------------------------
# Upload
# -------------------------

uploaded_files = st.file_uploader(
    "Upload CSV File(s)--------(Download Retest SN from Insight)-------------------$ Developed by: Phani Kumar | Contact for better improvement",
    type=["csv"],
    accept_multiple_files=True
)

if not uploaded_files:
    st.stop()

# -------------------------
# Load Files
# -------------------------

dfs = []

for file in uploaded_files:
    try:
        df = pd.read_csv(file)
        dfs.append(df)
    except Exception as e:
        st.error(f"Error reading {file.name}: {e}")

data = pd.concat(dfs, ignore_index=True)

# Replace NaN
text_cols = [
    "Test",
    "Sub-test",
    "Sub-sub-test",
    "Fail Message",
    "Fixture ID",
    "Station ID",
    "Test Software Version",
    "Station Type",
    "Test Head ID",
    "Product Code"
]

for col in text_cols:
    if col in data.columns:
        data[col] = data[col].fillna("").astype(str)

st.success(f"{len(data)} records loaded")

# -------------------------
# Sidebar Filters
# -------------------------

st.sidebar.header("Filters")

# Product Filter

product_list = ["All"] + sorted(
    data["Product Code"].astype(str).unique().tolist()
)

product = st.sidebar.selectbox(
    "Product Code",
    product_list
)

if product != "All":
    data = data[data["Product Code"] == product]

# Station Type

station_type_list = ["All"] + sorted(
    data["Station Type"].astype(str).unique().tolist()
)

station_type = st.sidebar.selectbox(
    "Station Type",
    station_type_list
)

if station_type != "All":
    data = data[data["Station Type"] == station_type]

# Station ID

station_list = ["All"] + sorted(
    data["Station ID"].astype(str).unique()
)

selected_station = st.sidebar.selectbox(
    "Station ID",
    station_list
)

if selected_station != "All":
    data = data[
        data["Station ID"].astype(str)
        == selected_station
    ]

# -------------------------
# Failure Level
# -------------------------

failure_level = st.sidebar.radio(
    "Failure Level",
    [
        "Test",
        "Test + Sub-test",
        "Test + Sub-test + Sub-sub-test"
    ]
)

if failure_level == "Test":
    data["Retest Symptoms"] = data["Test"]

elif failure_level == "Test + Sub-test":
    data["Retest Symptoms"] = (
        data["Test"]
        + " ^"
        + data["Sub-test"]
    )

else:
    data["Retest Symptoms"] = (
        data["Test"]
        + " ^"
        + data["Sub-test"]
        + " ^"
        + data["Sub-sub-test"]
    )

# -------------------------
# Commonality Based On
# -------------------------

st.sidebar.header("Commonality")

commonality_fields = st.sidebar.multiselect(
    "Commonality Based On",
    [
        "Station ID",
        "Fixture ID",
        "Test Head ID",
        "Test Software Version",
        "Station Type"
    ]
)

threshold = st.sidebar.number_input(
    "Minimum Count",
    min_value=1,
    value=2
)

# -------------------------
# Summary
# -------------------------

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Records", len(data))

with col2:
    st.metric(
        "Stations",
        data["Station ID"].nunique()
    )

with col3:
    st.metric(
        "Fixtures",
        data["Fixture ID"].nunique()
    )

with col4:
    st.metric(
        "Failure Types",
        data["Retest Symptoms"].nunique()
    )

# -------------------------
# Retest Pareto
# -------------------------

st.subheader("Retest Pareto")

pareto = (
    data.groupby("Retest Symptoms")
    .size()
    .reset_index(name="Count")
    .sort_values("Count", ascending=False)
)

st.dataframe(pareto, use_container_width=True)

fig = px.bar(
    pareto.head(20),
    x="Count",
    y="Retest Symptoms",
    orientation="h",
    title="Top Retest Symptoms"
)

st.plotly_chart(
    fig,
    use_container_width=True
)
# -------------------------
# Station ID Commonality
# -------------------------

st.subheader("Station ID Commonality")

station_commonality = (
    data.groupby("Station ID")
    .size()
    .reset_index(name="Count")
    .sort_values(
        by="Count",
        ascending=False
    )
)

total_failures = station_commonality["Count"].sum()

station_commonality["Percentage"] = (
    station_commonality["Count"]
    / total_failures
    * 100
).round(2)

st.dataframe(
    station_commonality,
    use_container_width=True
)

fig_station = px.bar(
    station_commonality,
    x="Station ID",
    y="Count",
    text="Count",
    color="Percentage",
    title="Station ID Commonality"
)

st.plotly_chart(
    fig_station,
    use_container_width=True
)
# -------------------------
# Commonality Analysis
# -------------------------

st.subheader("Commonality Analysis")

if len(commonality_fields) > 0:

    group_cols = ["Retest Symptoms"] + commonality_fields

    common_df = (
        data.groupby(group_cols)
        .size()
        .reset_index(name="Count")
        .sort_values("Count", ascending=False)
    )

    common_df = common_df[
        common_df["Count"] >= threshold
    ]

    st.dataframe(
        common_df,
        use_container_width=True
    )

    # Alerts
    
else:
    st.info(
        "Select at least one Commonality field."
    )
# -------------------------
# Heatmap Analysis
# -------------------------

st.subheader("Heatmap - Failure vs Station vs Test Head")

failure_options = ["ALL"] + sorted(
    data["Retest Symptoms"].unique()
)

selected_failure = st.selectbox(
    "Select Failure for Heatmap",
    failure_options
)

# -------------------------
# Build Dataset
# -------------------------

if selected_failure == "ALL":

    hm = (
        data.groupby(
            ["Station ID", "Test Head ID"]
        )
        .size()
        .reset_index(name="Count")
    )

else:

    hm = (
        data[data["Retest Symptoms"] == selected_failure]
        .groupby(
            ["Station ID", "Test Head ID"]
        )
        .size()
        .reset_index(name="Count")
    )

# -------------------------
# Create Pivot
# -------------------------

pivot = hm.pivot_table(
    index="Station ID",
    columns="Test Head ID",
    values="Count",
    aggfunc="sum",
    fill_value=0
)

# -------------------------
# Create Complete TH List
# -------------------------

all_test_heads = []

for th in data["Test Head ID"].unique():

    try:
        all_test_heads.append(
            int(float(str(th)))
        )
    except:
        pass

if len(all_test_heads) > 1:

    max_th = max(all_test_heads)

    full_test_head_list = list(
        range(0, max_th + 1)
    )

    pivot.columns = [
        int(float(str(x)))
        for x in pivot.columns
    ]

    pivot = pivot.reindex(
        columns=full_test_head_list,
        fill_value=0
    )

# -------------------------
# Build Heatmap
# -------------------------

fig_heatmap = px.imshow(
    pivot,
    text_auto=True,
    color_continuous_scale="Reds",
    aspect="auto",
    labels={
        "x": "Test Head ID",
        "y": "Station ID",
        "color": "Failure Count"
    }
)

# -------------------------
# Show EVERY Test Head
# -------------------------

fig_heatmap.update_xaxes(
    side="bottom",
    tickmode="array",
    tickvals=list(range(len(pivot.columns))),
    ticktext=[str(x) for x in pivot.columns],
    tickangle=0,
    title="Test Head ID"
)

fig_heatmap.update_yaxes(
    title="Station ID"
)

# -------------------------
# Dynamic Size
# -------------------------

fig_heatmap.update_layout(
    height=max(
        600,
        len(pivot.index) * 40
    ),
    width=max(
        1200,
        len(pivot.columns) * 90
    ),
    margin=dict(
        l=20,
        r=20,
        t=50,
        b=50
    )
)

st.plotly_chart(
    fig_heatmap,
    use_container_width=True
)

# -------------------------
# View Heatmap Data
# -------------------------

with st.expander("View Heatmap Data"):
    st.dataframe(
        pivot,
        use_container_width=True
    )
# -------------------------
# Export Excel
# -------------------------

st.subheader("Export")

excel_buffer = BytesIO()

with pd.ExcelWriter(
    excel_buffer,
    engine="openpyxl"
) as writer:

    pareto.to_excel(
        writer,
        index=False,
        sheet_name="Retest Pareto"
    )

    if len(commonality_fields) > 0:
        common_df.to_excel(
            writer,
            index=False,
            sheet_name="Commonality"
        )

excel_buffer.seek(0)

st.download_button(
    label="📥 Export Excel Report",
    data=excel_buffer,
    file_name="Commonality_Report.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
