import streamlit as st
import pandas as pd
import requests
from merge_lift_wind_data import get_lift_data  # Your function that fetches & filters lift data
from streamlit_autorefresh import st_autorefresh

# Set the page layout to wide (must be the first Streamlit command)
st.set_page_config(page_title="Lift Status Dashboard", layout="wide")

# Inject custom CSS for overall styling, background, and table formatting
st.markdown(
    """
    <style>
    /* Set background color for the main app */
    .stApp {
        background-color: #F2F1F1;
    }
    .reportview-container .main .block-container{
        background-color: #F2F1F1;
    }
    
    /* Import Google Font (optional) */
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap');
    body {
        font-family: 'Roboto', sans-serif;
    }
    
    /* Center headings in company red */
    h1, h2, h3, h4, h5, h6 {
        color: #871b0bff !important;
        text-align: center;
    }
    
    /* Table styling */
    table {
        width: 100%;
        border-collapse: collapse;
    }
    table th {
        text-align: center !important;
        background-color: #F8F8F8;  /* Softer white background */
        border-bottom: 2px solid #ddd;
        color: #333333;  /* Dark grey header text for readability */
    }
    table td {
        text-align: center;
        color: #333333;  /* Dark grey for table data text */
    }
    
    /* Highlight important lifts */
    .feeder-lift {
        background-color: #FFCCCC !important;  /* Light red for feeder lifts */
    }
    .upper-mountain-lift {
        background-color: #CCE5FF !important;  /* Light blue for upper mountain lifts */
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Add a debug section in the sidebar
with st.sidebar:
    st.title("Debug Info")
    show_debug = st.checkbox("Show Debug Info", value=True)

# ----------------------------
# NOAA Wind Forecast Function (with gusts and trend)
def get_noaa_hourly_wind(url, num_hours=5):
    """
    Fetch the next num_hours of hourly wind forecast data from a NOAA grid point.
    Returns a tuple: (DataFrame with Hour, Wind Speed (mph), Wind Gust (mph), Wind Direction) and a trend string.
    """
    response = requests.get(url).json()
    periods = response["properties"]["periods"]
    wind_data = []
    for period in periods[:num_hours]:
        # Format time to show only the hour and minute (assumes forecast is for today)
        dt = pd.to_datetime(period["startTime"])
        hour_str = dt.strftime('%I:%M %p')  # e.g., "08:00 AM"
        
        # Extract and convert wind speed (assumes format like "5 mph")
        wind_speed_str = period.get("windSpeed", "")
        try:
            wind_speed = int(wind_speed_str.split()[0])
        except:
            wind_speed = None
        
        # Extract and convert wind gust (if available)
        wind_gust_str = period.get("windGust", "")
        try:
            wind_gust = int(wind_gust_str.split()[0])
        except:
            wind_gust = None

        wind_direction = period.get("windDirection", "N/A")
        
        wind_data.append({
            "Hour": hour_str,
            "Wind Speed (mph)": wind_speed,
            "Wind Gust (mph)": wind_gust,
            "Wind Direction": wind_direction
        })
    
    # Determine overall trend based on first and third period wind speed (if available)
    if len(wind_data) >= 3 and wind_data[0]["Wind Speed (mph)"] is not None and wind_data[2]["Wind Speed (mph)"] is not None:
        diff = wind_data[2]["Wind Speed (mph)"] - wind_data[0]["Wind Speed (mph)"]
        if diff > 0.5:
            trend = "Increasing"
        elif diff < -0.5:
            trend = "Decreasing"
        else:
            trend = "No Change"
    else:
        trend = "N/A"
    
    return pd.DataFrame(wind_data), trend

# ----------------------------
# Define NOAA grid point endpoints for each side of the resort
noaa_grid_points = {
    "MV Wind Forecast": "https://api.weather.gov/gridpoints/SLC/112,168/forecast/hourly",
    "CV Wind Forecast": "https://api.weather.gov/gridpoints/SLC/111,170/forecast/hourly",
}

# ----------------------------
# Define lists for Village assignments (update these lists with your actual lift names)
mountain_village_lifts = [
    "First Time", "Town", "Payday", "Crescent", "3 Kings", "Bonanza", "Silverlode",
    "Motherlode", "King Con", "Eagle", "Eaglet", "Silver Star", "McConkey's",
    "Pioneer", "Thaynes", "Jupiter", "Little Miners", "Mine Cart", "Tommy Knocker", "Mule Train"
]
canyons_village_lifts  = [
    "Cabriolet", "Frostwood", "Sunrise", "Red Pine Gondola", "Orange Bubble", "Saddleback",
    "High Meadow", "Short Cut", "Sun Peak", "Condor", "9990", "Peak 5", "Tombstone",
    "Iron Mountain", "Timberline", "Flat Iron", "Sweet Pea", "Rip Cord", "Day Break",
    "Dreamscape", "Dreamcatcher", "Quicksilver", "Over and Out", "Silver Lining",
    "Hang Ten", "Magic Carpet", "Ripperoo"
]

# Define the important lift lists
feeder_lifts = ["Red Pine Gondola", "Orange Bubble", "Crescent", "Payday", "Eagle"]
upper_mountain_lifts = ["Pioneer", "Thaynes", "McConkey's", "Jupiter"]

def assign_village(lift_name):
    if lift_name in mountain_village_lifts:
        return "Mountain Village"
    elif lift_name in canyons_village_lifts:
        return "Canyons Village"
    else:
        return "Unknown"

# Check if lift is a special category for highlighting
def get_lift_category(lift_name):
    if lift_name in feeder_lifts:
        return "feeder-lift"
    elif lift_name in upper_mountain_lifts:
        return "upper-mountain-lift"
    else:
        return ""

# ----------------------------
# Helper function to format a DataFrame for display as HTML with appropriate highlighting
def format_display_df(df):
    df_display = df.copy()
    
    # Format "10.60 TIME" column to show only the time if the value exists
    if "10.60 TIME" in df_display.columns:
        df_display["10.60 TIME"] = df_display["10.60 TIME"].apply(
            lambda x: x.strftime("%I:%M %p") if pd.notnull(x) else ""
        )
    
    # Create DataFrame HTML with row-based styling
    html = '<table border="1" class="dataframe">'
    
    # Add header
    html += '<thead><tr>'
    for col in df_display.columns:
        html += f'<th>{col}</th>'
    html += '</tr></thead>'
    
    # Add body with conditional styling
    html += '<tbody>'
    for _, row in df_display.iterrows():
        lift_name = row['Lift']
        category_class = get_lift_category(lift_name)
        html += f'<tr class="{category_class}">'
        for col in df_display.columns:
            html += f'<td>{row[col]}</td>'
        html += '</tr>'
    html += '</tbody></table>'
    
    return html

# Helper function to format NOAA wind forecast DataFrame as HTML
def format_noaa_df(df):
    return df.to_html(index=False)

# ----------------------------
# Set up the Streamlit dashboard

st.title("Lift Wind Status Dashboard")

# Auto-refresh every 30 seconds
st_autorefresh(interval=30 * 1000, key="data_refresh")

# Display debug messages if enabled
if show_debug and 'debug_messages' in st.session_state:
    with st.sidebar:
        st.subheader("Debug Messages")
        for msg in st.session_state.debug_messages:
            st.text(msg)

# Fetch lift data (now use all returned dataframes)
all_lifts_df, wind_hold_df, other_hold_df = get_lift_data()

# Add a "Village" column based on the lift name to all dataframes
all_lifts_df["Village"] = all_lifts_df["Lift"].apply(assign_village)
wind_hold_df["Village"] = wind_hold_df["Lift"].apply(assign_village)
other_hold_df["Village"] = other_hold_df["Lift"].apply(assign_village)

# Get lifts with reduced/adjusted speed only
reduced_speed_df = all_lifts_df[all_lifts_df["MEOW Category"] == "Reduced/Adjust Speed"]

# Split reduced speed lifts by Village
mv_reduced = reduced_speed_df[reduced_speed_df["Village"] == "Mountain Village"]
cv_reduced = reduced_speed_df[reduced_speed_df["Village"] == "Canyons Village"]

# Split wind holds by Village
mv_wind_hold = wind_hold_df[wind_hold_df["Village"] == "Mountain Village"]
cv_wind_hold = wind_hold_df[wind_hold_df["Village"] == "Canyons Village"]

# ----------------------------
# Display village lift information side by side using columns
col1, col2 = st.columns(2)

with col1:
    st.header("Mountain Village Lifts")
    st.subheader("Reduced/Adjust Speed")
    if not mv_reduced.empty:
        st.markdown(format_display_df(mv_reduced[["Lift", "10.60 TIME", "Duration", "Fault"]]), unsafe_allow_html=True)
    else:
        st.write("No Mountain Village lifts on reduced/adjust speed currently.")
    
    st.subheader("Hold - Wind Related")
    if not mv_wind_hold.empty:
        st.markdown(format_display_df(mv_wind_hold[["Lift", "10.60 TIME", "Duration", "Fault"]]), unsafe_allow_html=True)
    else:
        st.write("No Mountain Village lifts on wind-related hold currently.")

with col2:
    st.header("Canyons Village Lifts")
    st.subheader("Reduced/Adjust Speed")
    if not cv_reduced.empty:
        st.markdown(format_display_df(cv_reduced[["Lift", "10.60 TIME", "Duration", "Fault"]]), unsafe_allow_html=True)
    else:
        st.write("No Canyons Village lifts on reduced/adjust speed currently.")
    
    st.subheader("Hold - Wind Related")
    if not cv_wind_hold.empty:
        st.markdown(format_display_df(cv_wind_hold[["Lift", "10.60 TIME", "Duration", "Fault"]]), unsafe_allow_html=True)
    else:
        st.write("No Canyons Village lifts on wind-related hold currently.")

# ----------------------------
# Display NOAA wind forecasts
st.header("NOAA Wind Forecasts")
cols = st.columns(len(noaa_grid_points))
for idx, (name, url) in enumerate(noaa_grid_points.items()):
    with cols[idx]:
        st.subheader(name)
        wind_df, trend = get_noaa_hourly_wind(url)
        # Determine trend color based on the trend value
        if trend.lower() == "increasing":
            trend_color = "#FF0000"  # Red for increasing
        elif trend.lower() == "decreasing":
            trend_color = "#008000"  # Green for decreasing
        else:
            trend_color = "#333333"  # Default dark grey for constant or other
        
        # Display the label once, then the trend value in its corresponding color
        st.write(
            "<div style='text-align: center;'>"
            "<span style='color:#333333;'>Wind Speed Trend next 3 hours: </span> **<span style='color:" + trend_color + "'>" + trend + "</span>**",
            unsafe_allow_html=True
        )
        st.markdown(format_noaa_df(wind_df), unsafe_allow_html=True)

# ----------------------------
# Lifts on Hold - Other (Non-Wind Related)
st.header("Lifts on Hold - Other")
if not other_hold_df.empty:
    st.markdown(format_display_df(other_hold_df[["Lift", "Village", "10.60 TIME", "Duration", "Fault", "MEOW Reasoning"]]), unsafe_allow_html=True)
else:
    st.write("No lifts on hold for reasons other than wind currently.")