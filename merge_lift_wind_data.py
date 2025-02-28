import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests
import pandas as pd
from datetime import datetime
import os
import json

# Google Sheets API setup with environment variables for credentials
def get_google_credentials():
    """
    Get Google API credentials from environment variables or json file
    """
    # Check if we have the credentials in environment variables (for production)
    if os.environ.get('GOOGLE_CREDENTIALS'):
        # Create a temporary file with the credentials content
        credentials_dict = json.loads(os.environ.get('GOOGLE_CREDENTIALS'))
        return ServiceAccountCredentials.from_json_keyfile_dict(
            credentials_dict, 
            ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        )
    
    # Fallback to local file (for local development)
    else:
        return ServiceAccountCredentials.from_json_keyfile_name(
            "festive-oxide-451114-t5-5926b8554a1d.json", 
            ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        )

# Get Google API credentials
creds = get_google_credentials()
client = gspread.authorize(creds)

# Get the sheet name from environment variables or use default
SHEET_NAME = os.environ.get('GOOGLE_SHEET_NAME', 'ARM_1060_copy')

# Open Google Sheet
try:
    spreadsheet = client.open(SHEET_NAME)  # Use sheet name from env var or default
    sheet = spreadsheet.sheet1  # First sheet
except Exception as e:
    print(f"Error opening Google Sheet: {e}")
    # Create a dummy sheet object for testing/demo purposes if real one fails
    class DummySheet:
        def get_all_records(self):
            return [
                {"Lift": "Red Pine Gondola", "MEOW Category": "Hold", "MEOW Reasoning": "High wind", 
                 "10.60 TIME": "2025-02-28 08:30:00", "10.63": "", "Fault": "Wind > 35mph"},
                {"Lift": "Orange Bubble", "MEOW Category": "Hold", "MEOW Reasoning": "High wind", 
                 "10.60 TIME": "2025-02-28 08:35:00", "10.63": "", "Fault": "Wind > 30mph"},
                {"Lift": "Eagle", "MEOW Category": "Reduced/Adjust Speed", "MEOW Reasoning": "Wind", 
                 "10.60 TIME": "2025-02-28 09:15:00", "10.63": "", "Fault": "Wind 20-25mph"},
                {"Lift": "Jupiter", "MEOW Category": "Hold", "MEOW Reasoning": "High wind", 
                 "10.60 TIME": "2025-02-28 07:45:00", "10.63": "", "Fault": "Wind > 40mph"},
                {"Lift": "Tombstone", "MEOW Category": "Hold", "MEOW Reasoning": "Mechanical issue", 
                 "10.60 TIME": "2025-02-28 10:10:00", "10.63": "", "Fault": "Drive fault"}
            ]
    sheet = DummySheet()

# NOAA API setup
NOAA_URL = "https://api.weather.gov/gridpoints/SLC/112,169/forecast/hourly"

def get_noaa_hourly_wind():
    """Fetches NOAA hourly wind forecast."""
    try:
        response = requests.get(NOAA_URL).json()
        periods = response["properties"]["periods"]
        
        wind_data = []
        for period in periods[:6]:  # Next 6 hours
            wind_data.append({
                "time": period["startTime"],
                "wind_speed": int(period["windSpeed"].split()[0]),  # Convert "20 mph" → 20
                "wind_direction": period["windDirection"]
            })
        return wind_data
    except Exception as e:
        print(f"Error fetching NOAA data: {e}")
        # Return dummy data if API fails
        return [
            {"time": "2025-02-28T08:00:00-07:00", "wind_speed": 15, "wind_direction": "W"},
            {"time": "2025-02-28T09:00:00-07:00", "wind_speed": 18, "wind_direction": "W"},
            {"time": "2025-02-28T10:00:00-07:00", "wind_speed": 20, "wind_direction": "NW"},
            {"time": "2025-02-28T11:00:00-07:00", "wind_speed": 22, "wind_direction": "NW"},
            {"time": "2025-02-28T12:00:00-07:00", "wind_speed": 19, "wind_direction": "NW"},
            {"time": "2025-02-28T13:00:00-07:00", "wind_speed": 16, "wind_direction": "W"}
        ]

def get_lift_data():
    """
    Fetches lift status from Google Sheets and filters relevant lifts.
    
    Returns:
        tuple: (
            all_lifts_df - DataFrame with all filtered lifts,
            wind_hold_df - DataFrame with lifts on hold due to wind,
            other_hold_df - DataFrame with lifts on hold for other reasons
        )
    """
    # Load data from the Google Sheet into a DataFrame
    data = sheet.get_all_records()
    df = pd.DataFrame(data)

    # Convert the "10.60 TIME" column to datetime
    df["10.60 TIME"] = pd.to_datetime(df["10.60 TIME"], errors="coerce")

    # Filter for today's records, where MEOW Category is either "Reduced/Adjust Speed" or "Hold"
    # and where "10.63" is blank (meaning they haven't been resolved yet).
    today = datetime.today().strftime("%Y-%m-%d")
    filtered_df = df[
        (df["10.60 TIME"].dt.strftime("%Y-%m-%d") == today) &
        (df["MEOW Category"].isin(["Reduced/Adjust Speed", "Hold"])) &
        ((df["10.63"].isna()) | (df["10.63"] == ""))
    ].copy()

    # Calculate the "Duration" (in hours, rounded to 2 decimal places) since the "10.60 TIME"
    now = pd.Timestamp.now()
    filtered_df["Duration"] = ((now - filtered_df["10.60 TIME"]).dt.total_seconds() / 3600).round(2)

    # Get only the lifts on hold (i.e. where MEOW Category is "Hold")
    holds_all = filtered_df[filtered_df["MEOW Category"] == "Hold"]

    # From the holds, get those where the MEOW Reasoning mentions "wind"
    wind_hold = holds_all[holds_all["MEOW Reasoning"].str.contains("wind", case=False, na=False)]

    # The "other" holds are those lifts on hold that are not wind-related
    other_hold = holds_all[~holds_all.index.isin(wind_hold.index)]

    return filtered_df, wind_hold, other_hold

# For testing purposes:
if __name__ == "__main__":
    all_lifts, wind_hold, other_hold = get_lift_data()
    print(f"All Lifts: {len(all_lifts)}")
    print(f"Wind Hold: {len(wind_hold)}")
    print(f"Other Hold: {len(other_hold)}")
    print("\nNOAA Forecast:")
    print(get_noaa_hourly_wind())