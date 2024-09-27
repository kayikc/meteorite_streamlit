import streamlit as st
import polars as pl
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="Meteorite Landings Dashboard", layout="wide")
st.title("🌠 Meteorite Landings Dashboard")

@st.cache_data
def load_data():
    df = pl.read_csv("Meteorite_Landings_20240927.csv")
    return df

def rename_columns(df):
    rename_dict = {
        "name": "Name",
        "id": "ID",
        "nametype": "Name Type",
        "recclass": "Classification",
        "fall": "Fall Status",
        "year": "Year",
        "reclat": "Latitude",
        "reclong": "Longitude",
        "GeoLocation": "GeoLocation"
    }
    # Only rename columns that exist in the dataframe
    return df.rename({col: new_name for col, new_name in rename_dict.items() if col in df.columns})

def process_data(df):
    current_year = datetime.now().year
    
    # Check if 'Mass (g)' column exists, if not, look for 'mass (g)'
    mass_column = 'Mass (g)' if 'Mass (g)' in df.columns else 'mass (g)'
    
    df = df.drop_nulls(subset=['Latitude', 'Longitude', mass_column, 'Year'])
    
    # Filter out rows where Year is larger than current year
    df = df.filter(pl.col('Year') <= current_year)
    
    df = df.with_columns([
        (pl.col(mass_column) / 1000).alias('Mass (kg)')
    ]).drop(mass_column)
    
    return df

try:
    df = load_data()
    df = rename_columns(df)
    df = process_data(df)
    
    st.success("Data loaded successfully!")

    # Display cards visuals
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Meteorites", df.shape[0])
    col2.metric("Date Range", f"{df['Year'].min()} - {df['Year'].max()}")
    col3.metric("Heaviest Meteorite", f"{df['Mass (kg)'].max():.2f} kg")

    st.subheader("Understanding Meteorite Classifications")
    st.write("""
    In meteorite classification, the terms "Relict" and "Valid" refer to the naming status of the meteorite:
    
    - **Valid**: These are meteorites with officially recognized and approved names.
    - **Relict**: This term is used for meteorites that were once considered valid but have been reclassified or merged with other meteorites. 
    They are no longer considered separate, valid meteorites but are kept in the database for historical reasons.
    """)

    # Interactive map
    st.subheader("Meteorite Landings Map")
    df_pandas = df.to_pandas()
    color_scale = [(0, 'orange'), (1,'red')]
    fig = px.scatter_mapbox(data_frame=df_pandas,
                            lat="Latitude",
                            lon="Longitude",
                            hover_name="Name",
                            hover_data=["Year", "Mass (kg)", "Classification"],
                            color="Fall Status",
                            color_discrete_map={"Fell": "#1E88E5", "Found": "#FFA000"},
                            size="Mass (kg)",
                            zoom=1,
                            height=600)
    fig.update_layout(mapbox_style="open-street-map")
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    st.plotly_chart(fig, use_container_width=True)

    # Data explorer
    st.subheader("🔍 Data Explorer")
    num_rows = st.slider("Number of rows to display", 5, 50, 10)
    st.dataframe(df.head(num_rows))

    # Data summary
    st.subheader("📊 Data Summary")
    st.write(df.describe())

    # Additional insights
    st.subheader("📈 Additional Insights")
    col1, col2 = st.columns(2)

    with col1:
        st.write("Top 10 Heaviest Meteorites")
        heaviest = df.sort("Mass (kg)", descending=True).head(10)
        fig = px.bar(heaviest.to_pandas(), x="Name", y="Mass (kg)")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.write("Meteorite Landings by Year")
        yearly_counts = df.group_by("Year").agg(pl.count()).sort("Year")
        fig = px.line(yearly_counts.to_pandas(), x="Year", y="count")
        st.plotly_chart(fig, use_container_width=True)

except Exception as e:
    st.error(f"An error occurred: {str(e)}")
    st.write("Current DataFrame Schema:")
    st.write(df.schema) if 'df' in locals() else st.write("DataFrame not created")

st.sidebar.header("About")
st.sidebar.info("Not all meteorites are created equal. Where are they? Caveat: some meteorites without mass and location data are not included. Data is filtered to include only meteorites up to the current year.")
st.sidebar.header("Data Source")
st.sidebar.info("This comprehensive data set from The Meteoritical Society contains information on all of the known meteorite landings. The Fusion Table is collected by Javier de la Torre.")
