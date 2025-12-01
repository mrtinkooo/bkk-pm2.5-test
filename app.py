import streamlit as st
import geemap.foliumap as geemap
import ee
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Page configuration
st.set_page_config(page_title="Bangkok PM2.5 Analysis", layout="wide", page_icon="🌫️")

# Title
st.title("🌫️ Bangkok PM2.5 Pollution Analysis")
st.markdown("### Air Quality Monitoring with Google Earth Engine")

# Initialize Earth Engine
@st.cache_resource
def initialize_ee():
    try:
        # Check if running on Streamlit Cloud (service account method)
        if 'ee_service_account' in st.secrets:
            service_account = st.secrets['ee_service_account']
            credentials = ee.ServiceAccountCredentials(
                service_account['client_email'],
                key_data=service_account['private_key']
            )
            ee.Initialize(credentials=credentials, project='gee-python-419405')
            return True, "Earth Engine initialized with service account"
        else:
            # Local authentication method
            ee.Initialize(project='gee-python-419405')
            return True, "Earth Engine initialized successfully"
    except ee.ee_exception.EEException as e:
        error_msg = str(e)
        if "Not signed up" in error_msg or "not registered" in error_msg:
            return False, "registration_required"
        else:
            try:
                ee.Authenticate()
                ee.Initialize(project='gee-python-419405')
                return True, "Earth Engine initialized after authentication"
            except Exception as auth_error:
                return False, f"Authentication failed: {str(auth_error)}"
    except Exception as e:
        return False, f"Initialization error: {str(e)}"

ee_status, ee_message = initialize_ee()

# Check Earth Engine status
if not ee_status:
    if ee_message == "registration_required":
        st.error("⚠️ **Earth Engine Registration Required**")
        st.markdown("""
        ### Your Google account is authenticated, but you need to register for Earth Engine access.

        **How to Register (Free for Research & Education):**

        1. 🌐 Visit: **[Earth Engine Signup](https://signup.earthengine.google.com/)**
        2. 📝 Sign up with your Google account
        3. ⏱️ Wait for approval (usually instant, sometimes takes a few hours)
        4. 🔄 Refresh this page after registration

        **Why Register?**
        - Access to Google's massive geospatial datasets
        - Free for non-commercial research and education
        - Process terabytes of satellite imagery

        **After Registration:**
        - Restart this app: `streamlit run app.py`
        - All features will be unlocked
        """)

        st.info("📧 **Check your email** after signing up for confirmation and approval status.")

        with st.expander("🔍 What You'll Get Access To"):
            st.markdown("""
            - MODIS satellite data (AOD for PM2.5 analysis)
            - Sentinel-5P air quality data (NO2, CO, aerosols)
            - Landsat and other Earth observation datasets
            - Cloud-based geospatial processing
            - Time series analysis capabilities
            """)

        st.stop()
    else:
        st.error(f"❌ **Earth Engine Error:** {ee_message}")
        st.markdown("""
        **Troubleshooting Steps:**
        1. Run `earthengine authenticate` in your terminal
        2. Or run `ee.Authenticate()` in Python
        3. Restart this app
        """)
        st.stop()

# Bangkok coordinates
BANGKOK_CENTER = [13.7563, 100.5018]
BANGKOK_BOUNDS = ee.Geometry.Rectangle([100.3, 13.5, 100.9, 14.0])

# Sidebar configuration
st.sidebar.title("🔧 Analysis Settings")

# Date range selection
st.sidebar.markdown("### 📅 Time Period")
col1, col2 = st.sidebar.columns(2)
with col1:
    start_date = st.date_input(
        "Start Date",
        value=datetime.now() - timedelta(days=30),
        max_value=datetime.now()
    )
with col2:
    end_date = st.date_input(
        "End Date",
        value=datetime.now(),
        max_value=datetime.now()
    )

# Dataset selection
st.sidebar.markdown("### 🛰️ Data Layers")
show_aod = st.sidebar.checkbox("MODIS Aerosol Optical Depth (AOD)", value=True)
show_aerosol_index = st.sidebar.checkbox("Sentinel-5P Aerosol Index", value=False)
show_no2 = st.sidebar.checkbox("Sentinel-5P NO2", value=False)
show_co = st.sidebar.checkbox("Sentinel-5P CO", value=False)

# Air Quality Standards
st.sidebar.markdown("### 📊 Air Quality Standards")
st.sidebar.info("""
**Thai PM2.5 Standards:**
- Good: 0-25 μg/m³
- Moderate: 26-37 μg/m³
- Unhealthy (Sensitive): 38-50 μg/m³
- Unhealthy: 51-90 μg/m³
- Very Unhealthy: >90 μg/m³
""")

# Create map centered on Bangkok
st.header("🗺️ Interactive Air Quality Map")
m = geemap.Map(center=BANGKOK_CENTER, zoom=10)

# Add Bangkok boundary
m.add_child(geemap.folium.GeoJson(
    BANGKOK_BOUNDS.getInfo(),
    name='Bangkok Area',
    style_function=lambda x: {
        'fillColor': 'transparent',
        'color': 'red',
        'weight': 2,
        'dashArray': '5, 5'
    }
))

# Add MODIS AOD (correlates with PM2.5)
if show_aod:
    try:
        aod_collection = ee.ImageCollection('MODIS/061/MCD19A2_GRANULES') \
            .filterDate(str(start_date), str(end_date)) \
            .filterBounds(BANGKOK_BOUNDS) \
            .select('Optical_Depth_047') \
            .mean()

        aod_vis = {
            'min': 0,
            'max': 1,
            'palette': ['green', 'yellow', 'orange', 'red', 'purple', 'maroon']
        }
        m.addLayer(aod_collection, aod_vis, 'AOD (PM2.5 Proxy)', opacity=0.7)
        st.sidebar.success("✓ AOD layer added")
    except Exception as e:
        st.sidebar.warning(f"AOD data unavailable: {str(e)}")

# Add Sentinel-5P Aerosol Index
if show_aerosol_index:
    try:
        aerosol = ee.ImageCollection('COPERNICUS/S5P/NRTI/L3_AER_AI') \
            .filterDate(str(start_date), str(end_date)) \
            .filterBounds(BANGKOK_BOUNDS) \
            .select('absorbing_aerosol_index') \
            .mean()

        aerosol_vis = {
            'min': -1,
            'max': 2,
            'palette': ['blue', 'green', 'yellow', 'orange', 'red']
        }
        m.addLayer(aerosol, aerosol_vis, 'Aerosol Index', opacity=0.6)
        st.sidebar.success("✓ Aerosol Index added")
    except Exception as e:
        st.sidebar.warning(f"Aerosol data unavailable: {str(e)}")

# Add Sentinel-5P NO2 (traffic/industrial pollution indicator)
if show_no2:
    try:
        no2 = ee.ImageCollection('COPERNICUS/S5P/NRTI/L3_NO2') \
            .filterDate(str(start_date), str(end_date)) \
            .filterBounds(BANGKOK_BOUNDS) \
            .select('NO2_column_number_density') \
            .mean()

        no2_vis = {
            'min': 0,
            'max': 0.0002,
            'palette': ['black', 'blue', 'purple', 'cyan', 'green', 'yellow', 'red']
        }
        m.addLayer(no2, no2_vis, 'NO2 Concentration', opacity=0.6)
        st.sidebar.success("✓ NO2 layer added")
    except Exception as e:
        st.sidebar.warning(f"NO2 data unavailable: {str(e)}")

# Add Sentinel-5P CO
if show_co:
    try:
        co = ee.ImageCollection('COPERNICUS/S5P/NRTI/L3_CO') \
            .filterDate(str(start_date), str(end_date)) \
            .filterBounds(BANGKOK_BOUNDS) \
            .select('CO_column_number_density') \
            .mean()

        co_vis = {
            'min': 0,
            'max': 0.05,
            'palette': ['black', 'blue', 'purple', 'cyan', 'green', 'yellow', 'red']
        }
        m.addLayer(co, co_vis, 'CO Concentration', opacity=0.6)
        st.sidebar.success("✓ CO layer added")
    except Exception as e:
        st.sidebar.warning(f"CO data unavailable: {str(e)}")

# Add layer control and drawing tools
m.add_layer_control()

# Display map
m.to_streamlit(height=500)

# Time Series Analysis
st.header("📈 Time Series Analysis")

if st.button("Generate AOD Time Series"):
    with st.spinner("Analyzing temporal trends..."):
        try:
            # Get daily AOD values
            aod_daily = ee.ImageCollection('MODIS/061/MCD19A2_GRANULES') \
                .filterDate(str(start_date), str(end_date)) \
                .filterBounds(BANGKOK_BOUNDS) \
                .select('Optical_Depth_047')

            # Create time series
            def get_daily_mean(image):
                mean_value = image.reduceRegion(
                    reducer=ee.Reducer.mean(),
                    geometry=BANGKOK_BOUNDS,
                    scale=1000
                ).get('Optical_Depth_047')

                return ee.Feature(None, {
                    'date': image.date().format('YYYY-MM-dd'),
                    'aod': mean_value
                })

            time_series = aod_daily.map(get_daily_mean).getInfo()

            # Convert to DataFrame
            df_list = []
            for feature in time_series['features']:
                props = feature['properties']
                if props.get('aod') is not None:
                    df_list.append({
                        'Date': props['date'],
                        'AOD': props['aod']
                    })

            if df_list:
                df = pd.DataFrame(df_list)
                df['Date'] = pd.to_datetime(df['Date'])
                df = df.sort_values('Date')

                # Create plot
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=df['Date'],
                    y=df['AOD'],
                    mode='lines+markers',
                    name='AOD',
                    line=dict(color='#FF6B6B', width=2),
                    marker=dict(size=6)
                ))

                # Add threshold lines
                fig.add_hline(y=0.3, line_dash="dash", line_color="orange",
                             annotation_text="Moderate Pollution")
                fig.add_hline(y=0.5, line_dash="dash", line_color="red",
                             annotation_text="High Pollution")

                fig.update_layout(
                    title="Bangkok AOD Time Series (Proxy for PM2.5)",
                    xaxis_title="Date",
                    yaxis_title="Aerosol Optical Depth",
                    hovermode='x unified',
                    height=400
                )

                st.plotly_chart(fig, use_container_width=True)

                # Statistics
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Mean AOD", f"{df['AOD'].mean():.3f}")
                with col2:
                    st.metric("Max AOD", f"{df['AOD'].max():.3f}")
                with col3:
                    st.metric("Min AOD", f"{df['AOD'].min():.3f}")
                with col4:
                    st.metric("Std Dev", f"{df['AOD'].std():.3f}")

                # Download data
                csv = df.to_csv(index=False)
                st.download_button(
                    label="📥 Download Time Series Data (CSV)",
                    data=csv,
                    file_name=f"bangkok_aod_{start_date}_{end_date}.csv",
                    mime="text/csv"
                )
            else:
                st.warning("No data available for the selected period.")

        except Exception as e:
            st.error(f"Error generating time series: {str(e)}")

# Statistics section
st.header("📊 Regional Statistics")
col1, col2 = st.columns(2)

with col1:
    if st.button("Calculate AOD Statistics"):
        with st.spinner("Computing statistics..."):
            try:
                aod_mean = ee.ImageCollection('MODIS/061/MCD19A2_GRANULES') \
                    .filterDate(str(start_date), str(end_date)) \
                    .filterBounds(BANGKOK_BOUNDS) \
                    .select('Optical_Depth_047') \
                    .mean()

                stats = aod_mean.reduceRegion(
                    reducer=ee.Reducer.mean().combine(
                        ee.Reducer.stdDev(), '', True
                    ).combine(
                        ee.Reducer.minMax(), '', True
                    ),
                    geometry=BANGKOK_BOUNDS,
                    scale=1000
                ).getInfo()

                st.success("Statistics for Bangkok Region:")
                st.json(stats)
            except Exception as e:
                st.error(f"Error: {str(e)}")

with col2:
    if st.button("Calculate NO2 Statistics"):
        with st.spinner("Computing statistics..."):
            try:
                no2_mean = ee.ImageCollection('COPERNICUS/S5P/NRTI/L3_NO2') \
                    .filterDate(str(start_date), str(end_date)) \
                    .filterBounds(BANGKOK_BOUNDS) \
                    .select('NO2_column_number_density') \
                    .mean()

                stats = no2_mean.reduceRegion(
                    reducer=ee.Reducer.mean().combine(
                        ee.Reducer.stdDev(), '', True
                    ).combine(
                        ee.Reducer.minMax(), '', True
                    ),
                    geometry=BANGKOK_BOUNDS,
                    scale=1000
                ).getInfo()

                st.success("NO2 Statistics for Bangkok:")
                st.json(stats)
            except Exception as e:
                st.error(f"Error: {str(e)}")

# Information section
st.sidebar.markdown("---")
st.sidebar.markdown("### 📖 About")
st.sidebar.markdown("""
**PM2.5 Study App**

This tool analyzes air quality in Bangkok using:
- **MODIS AOD**: Aerosol optical depth (PM2.5 proxy)
- **Sentinel-5P**: Aerosol index, NO2, CO
- **Time series**: Temporal trends
- **Statistics**: Regional analysis

**Note**: AOD is a proxy for PM2.5. Higher AOD values generally indicate higher PM2.5 concentrations.
""")

# Footer with instructions
with st.expander("ℹ️ How to Use This App"):
    st.markdown("""
    ### Quick Guide:
    1. **Select Date Range**: Choose your study period
    2. **Toggle Layers**: Select which data layers to display
    3. **View Map**: Explore air quality patterns in Bangkok
    4. **Generate Time Series**: Click to see temporal trends
    5. **Calculate Statistics**: Get numerical summaries
    6. **Download Data**: Export results for further analysis

    ### Understanding the Data:
    - **AOD (Aerosol Optical Depth)**: Higher values = more particles in air
    - **NO2**: Indicator of traffic and industrial pollution
    - **CO**: Carbon monoxide from combustion
    - **Aerosol Index**: UV-absorbing aerosol particles

    ### Color Scale:
    - 🟢 Green: Good air quality
    - 🟡 Yellow: Moderate
    - 🟠 Orange: Unhealthy for sensitive groups
    - 🔴 Red: Unhealthy
    - 🟣 Purple: Very unhealthy
    """)

with st.expander("🔬 Research Applications"):
    st.markdown("""
    ### Research Use Cases:
    - **Temporal Analysis**: Track PM2.5 trends over time
    - **Seasonal Patterns**: Identify pollution seasons
    - **Spatial Hotspots**: Locate high pollution areas
    - **Correlation Studies**: Compare with meteorological data
    - **Policy Impact**: Assess air quality interventions
    - **Public Health**: Link pollution to health outcomes

    ### Data Export:
    - Download time series as CSV
    - Export maps as images
    - Use statistics for reports
    """)

st.markdown("---")
st.markdown("*Powered by Google Earth Engine, geemap, and Streamlit*")
