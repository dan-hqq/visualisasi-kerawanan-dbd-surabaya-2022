import streamlit as st
import geopandas as gpd
import pandas as pd
import json
from streamlit_folium import st_folium
import folium
from shapely.geometry import shape

st.set_page_config(
    page_title="Kerawanan DBD Kota Surabaya 2022",
    layout="wide"
)
st.title("Tingkat Kerawanan Demam Berdarah Kecamatan-Kecamatan di Kota Surabaya Tahun 2022")

@st.cache_data
def load_gadm_json(file_path):
    with open(file_path, 'r') as f:
        data = json.load(f)
    features = []
    for feature in data['features']:
        prop = feature['properties']
        geom = shape(feature['geometry'])
        features.append({
            **prop,
            'geometry': geom
        })
    return gpd.GeoDataFrame(features)

@st.cache_data
def load_gadm():
    gdf = load_gadm_json("gadm41_IDN_3.json")
    surabaya_gdf = gdf[gdf['NAME_2'] == 'Surabaya']
    return surabaya_gdf

@st.cache_data
def load_csv():
    return pd.read_csv("dataset_dbd.csv", delimiter=",")

gdf_gadm = load_gadm()
df_csv = load_csv()
# st.write(gdf_gadm)
# st.write(df_csv.head())

gdf = gdf_gadm.merge(df_csv, left_on='NAME_3', right_on='Kecamatan', how='left')

# st.write(gdf)

avg_lat = gdf.geometry.centroid.y.mean()
avg_lon = gdf.geometry.centroid.x.mean()

m = folium.Map(
    location=[-7.2798481, 112.7860686],
    zoom_start=12,
    tiles="CartoDB Positron",
    attr="© GADM | © CartoDB"
)

def create_tooltip(row):
    return f"""
    <div style="font-family: Arial; width: 300px; background-color: #333333; color: #ffffff; border-radius: 8px; box-shadow: 0 3px 10px rgba(0,0,0,0.5);">
        <h4 style="margin:0; padding:10px; background-color:#444444; color:white; border-top-left-radius: 8px; border-top-right-radius: 8px;">
            {row['Kecamatan']}
        </h4>
        <table style="width:100%; font-size:12px; padding: 10px;">
            <tr><td><b>Kepadatan:</b></td><td>{row['kepadatan']}/km²</td></tr>
            <tr><td><b>Sanitasi:</b></td><td>{row['rumahts']}</td></tr>
            <tr><td><b>Puskesmas:</b></td><td>{row['Puskesmas']}</td></tr>
            <tr><td><b>Kasus DBD:</b></td><td>{row['Kasus DBD']}</td></tr>
            <tr style="font-size: 16px; font-weight: bold; color: #FF8C00; padding: 5px 0;">
                <td><b>Kerawanan:</b></td>
                <td>{row['Kerawanan']}</td>
            </tr>
        </table>
    </div>
    """

for idx, row in gdf.iterrows():
    tooltip_html = create_tooltip(row)
    folium.GeoJson(
        row['geometry'],
        style_function=lambda feature, kerawanan=row['Kerawanan']: {
            "fillColor": "#7bb662" if kerawanan == "Rendah" else "#ffd301" if kerawanan == "Sedang" else "#d61f1f",
            "color": "black",
            "weight": 1,
            "fillOpacity": 0.9
        },
        highlight_function=lambda feature: {
            "weight": 3,
            "fillOpacity": 0.7,
        },
        tooltip=folium.Tooltip(
            text=tooltip_html,
            sticky=True,
            permanent=False,
            direction='right'
        )
    ).add_to(m)
    folium.Marker(
        location=[row.geometry.centroid.y, row.geometry.centroid.x],
        icon=folium.DivIcon(
            html=f"""
                <div style="
                    font-size: 8px; 
                    font-weight: bold; 
                    color: #333333;
                    text-shadow: 
                        -1px -1px 0 #FFFFFF,  
                        1px -1px 0 #FFFFFF,
                        -1px 1px 0 #FFFFFF,
                        1px 1px 0 #FFFFFF;
                ">
                    {row['NAME_3']}
                </div>
            """
        )
    ).add_to(m)

st_folium(m, width=1200, height=600)

st.sidebar.header("Informasi Data")
st.sidebar.markdown("""
**Sumber Data:**
- Batas Administrasi: GADM Level 3 (https://gadm.org)
- Data Statistik: BPS Kota Surabaya Tahun 2022 (https://surabayakota.bps.go.id/id)
""")

if 'kepadatan' in gdf.columns:
    st.sidebar.header("Statistik Ringkas")
    st.sidebar.metric("Total Kasus DBD", f"{gdf['Kasus DBD'].sum():,.0f} kasus")
    st.sidebar.metric("Rata-rata Kepadatan", f"{gdf['kepadatan'].mean():,.0f}/km²")
    st.sidebar.metric("Total Puskesmas", f"{gdf['Puskesmas'].sum():,.0f} puskesmas")