import streamlit as st
import polars as pl
import plotly.express as px
from sqlalchemy import create_engine, text

st.set_page_config(page_title="Meteorite Landings Dashboard", layout="wide")

st.title("🌠 Meteorite Landings Dashboard")

# Create a SQLAlchemy engine
connection_string = (
    'mssql+pyodbc://JAMESKYCHOI/master?'
    'driver=SQL+Server&'
    'trusted_connection=yes'
)
engine = create_engine(connection_string)

@st.cache_data
def load_data(_sql, _engine):
    with _engine.connect() as conn:
        df = pl.read_database(_sql, conn)
    return df

def rename_columns(df):
    return df.rename({
        "name": "Name",
        "id": "ID",
        "nametype": "Name Type",
        "recclass": "Classification",
        "mass_g": "Mass (g)",
        "fall": "Fall Status",
        "year": "Year",
        "reclat": "Latitude",
        "reclong": "Longitude",
        "GeoLocation": "GeoLocation"
    })

def process_data(df):
    df = df.drop_nulls(subset=['Latitude', 'Longitude', 'Mass (g)'])
    df = df.with_columns([
        (pl.col('Mass (g)') / 1000).alias('Mass (kg)')
    ]).drop('Mass (g)')
    return df

try:
    sql = text("""SELECT *FROM data_processing.dbo.Meteorite_Landings_20240927
                WHERE year <= YEAR(GETDATE()) and nametype = 'valid'
                order by year desc
""")
    
    # Load and process data
    with st.spinner("Loading and processing data..."):
        df = process_data(rename_columns(load_data(sql, engine)))
    
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
                            color_continuous_scale=color_scale,
                            size="Mass (kg)",
                            zoom=1,
                            height=600)
    fig.update_layout(mapbox_style="open-street-map")
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    st.plotly_chart(fig, use_container_width=True)

    # 
    st.subheader("🔍 Data Explorer")
    num_rows = st.slider("Number of rows to display", 5, 50, 10)
    st.dataframe(df.head(num_rows))

    # 
    st.subheader("📊 Data Summary")
    st.write(df.describe())

    # 
    st.subheader("📈 Additional Insights")
    col1, col2 = st.columns(2)

    with col1:
        st.write("Top 10 Heaviest Meteorites")
        heaviest = df.sort("Mass (kg)", descending=True).head(10)
        fig = px.bar(heaviest.to_pandas(), x="Name", y="Mass (kg)")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.write("Meteorite Landings by Year")
        yearly_counts = df.group_by("Year").agg(pl.len()).sort("Year")
        fig = px.line(yearly_counts.to_pandas(), x="Year", y="count")
        st.plotly_chart(fig, use_container_width=True)

except Exception as e:
    st.error(f"An error occurred: {str(e)}")

st.sidebar.header("About")
st.sidebar.info("Not all meteorites are created equal. Where are they? Caveat: some meteorites without mass and location data are not included.")
st.sidebar.header("Data Source")
st.sidebar.info("This comprehensive data set from The Meteoritical Society contains information on all of the known meteorite landings. The Fusion Table is collected by Javier de la Torre.")