import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests
import pandas as pd
from datetime import datetime
import os
import json
import streamlit as st

# Debug logging to help troubleshoot Google Sheets connection issues
def debug_log(message):
    """Print a debug message to console and also to Streamlit"""
    print(f"DEBUG: {message}")
    if 'debug_messages' not in st.session_state:
        st.session_state.debug_messages = []
    st.session_state.debug_messages.append(message)

# Google Sheets API setup with Streamlit secrets
def get_google_credentials():
    """
    Get Google API credentials from Streamlit secrets
    Returns credentials object or None if failed
    """
    debug_log("Starting credentials setup...")
    
    # Check if Streamlit secrets are available
    if hasattr(st, 'secrets'):
        debug_log("Streamlit secrets are available")
        
        # DEBUG: Print all available secrets (without sensitive content)
        debug_log(f"Available secret keys: {list(st.secrets.keys())}")
        
        # Check for Google credentials in secrets
        if 'GOOGLE_CREDENTIALS' in st.secrets:
            debug_log("Found GOOGLE_CREDENTIALS in secrets")
            try:
                # Get credentials dict
                credentials_dict = st.secrets['GOOGLE_CREDENTIALS']
                
                # Log some basic info about the credentials (without sensitive parts)
                if isinstance(credentials_dict, dict):
                    debug_log(f"Credentials format: dictionary")
                    if 'client_email' in credentials_dict:
                        debug_log(f"Service account email: {credentials_dict['client_email']}")
                    if 'project_id' in credentials_dict:
                        debug_log(f"Project ID: {credentials_dict['project_id']}")
                else:
                    debug_log(f"Credentials format is not a dictionary: {type(credentials_dict)}")
                    # Try to parse as string if it's not already a dict
                    try:
                        debug_log(f"Credentials value preview: {str(credentials_dict)[:30]}...")
                        credentials_dict = json.loads(credentials_dict)
                        debug_log("Successfully parsed credentials string as JSON")
                    except Exception as parse_error:
                        debug_log(f"Failed to parse credentials as JSON: {str(parse_error)}")
                
                # Create credentials object
                debug_log("Creating ServiceAccountCredentials...")
                return ServiceAccountCredentials.from_json_keyfile_dict(
                    credentials_dict, 
                    ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
                )
            except Exception as e:
                debug_log(f"Error processing credentials: {str(e)}")
        else:
            debug_log("GOOGLE_CREDENTIALS not found in Streamlit secrets")
            debug_log("Looking for google.credentials instead...")
            
            # Try alternative format (google.credentials)
            if 'google' in st.secrets and 'credentials' in st.secrets.google:
                debug_log("Found google.credentials in secrets")
                try:
                    credentials_str = st.secrets.google.credentials
                    debug_log(f"Credentials string preview: {credentials_str[:30]}...")
                    
                    credentials_dict = json.loads(credentials_str)
                    debug_log("Successfully parsed credentials from google.credentials")
                    
                    # Create credentials object
                    return ServiceAccountCredentials.from_json_keyfile_dict(
                        credentials_dict,
                        ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
                    )
                except Exception as e:
                    debug_log(f"Error processing google.credentials: {str(e)}")
    else:
        debug_log("No Streamlit secrets available")
    
    debug_log("Falling back to dummy data mode")
    return None

# Try to get the Google Sheet name
def get_sheet_name():
    """Get sheet name from Streamlit secrets or use default"""
    if hasattr(st, 'secrets'):
        if 'GOOGLE_SHEET_NAME' in st.secrets:
            sheet_name = st.secrets['GOOGLE_SHEET_NAME']
            debug_log(f"Using GOOGLE_SHEET_NAME from secrets: {sheet_name}")
            return sheet_name
        elif 'google' in st.secrets and 'sheet_name' in st.secrets.google:
            sheet_name = st.secrets.google.sheet_name
            debug_log(f"Using google.sheet_name from secrets: {sheet_name}")
            return sheet_name
    
    # Default sheet name
    default_name = 'ARM_1060_copy'
    debug_log(f"No sheet name in secrets, using default: {default_name}")
    return default_name

# Attempt to get Google API credentials
debug_log("INITIALIZING: Starting Google Sheets connection process")
creds = get_google_credentials()

# Try to authorize with gspread if we have credentials
if creds:
    try:
        debug_log("Authorizing with gspread...")
        client = gspread.authorize(creds)
        debug_log("gspread authorization successful")
        
        # Get the sheet name
        SHEET_NAME = get_sheet_name()
        
        # Try to open the Google Sheet
        debug_log(f"Attempting to open Google Sheet: {SHEET_NAME}")
        try:
            spreadsheet = client.open(SHEET_NAME)
            debug_log(f"Successfully opened sheet: {SHEET_NAME}")
            
            # List available worksheets
            worksheet_list = spreadsheet.worksheets()
            debug_log(f"Available worksheets: {', '.join([ws.title for ws in worksheet_list])}")
            
            # Use the first sheet
            sheet = spreadsheet.sheet1
            debug_log(f"Using first worksheet: {sheet.title}")
            
            # Verify we can read data
            try:
                cell_value = sheet.acell('A1').value
                debug_log(f"Successfully read cell A1: {cell_value}")
            except Exception as read_error:
                debug_log(f"Error reading cell A1: {str(read_error)}")
                sheet = None
        except gspread.exceptions.SpreadsheetNotFound:
            debug_log(f"Spreadsheet '{SHEET_NAME}' not found. Check the sheet name and sharing permissions.")
            sheet = None
        except Exception as sheet_error:
            debug_log(f"Error opening spreadsheet: {str(sheet_error)}")
            sheet = None
            
    except Exception as auth_error:
        debug_log(f"Error during gspread authorization: {str(auth_error)}")
        sheet = None
        client = None
else:
    debug_log("No valid credentials, cannot authorize with gspread")
    client = None
    sheet = None

# Setup dummy sheet data for when we can't connect to the actual sheet
class DummySheet:
    def get_all_records(self):
        debug_log("Using dummy sheet data")
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

# If we couldn't connect to the sheet, use the dummy data
if sheet is None:
    debug_log("Sheet connection failed or not initialized, using DummySheet")
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
        debug_log(f"Error fetching NOAA data: {str(e)}")
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
    try:
        debug_log("Fetching data from sheet...")
        data = sheet.get_all_records()
        debug_log(f"Got {len(data)} records from sheet")
        
        if len(data) == 0:
            debug_log("WARNING: Sheet returned 0 records")
        
        df = pd.DataFrame(data)
        debug_log(f"DataFrame created with columns: {', '.join(df.columns)}")

        # Convert the "10.60 TIME" column to datetime
        df["10.60 TIME"] = pd.to_datetime(df["10.60 TIME"], errors="coerce")

        # Filter for today's records, where MEOW Category is either "Reduced/Adjust Speed" or "Hold"
        # and where "10.63" is blank (meaning they haven't been resolved yet).
        today = datetime.today().strftime("%Y-%m-%d")
        debug_log(f"Filtering for today's date: {today}")
        
        filtered_df = df[
            (df["10.60 TIME"].dt.strftime("%Y-%m-%d") == today) &
            (df["MEOW Category"].isin(["Reduced/Adjust Speed", "Hold"])) &
            ((df["10.63"].isna()) | (df["10.63"] == ""))
        ].copy()
        
        debug_log(f"After filtering: {len(filtered_df)} records")

        # Calculate the "Duration" (in hours, rounded to 2 decimal places) since the "10.60 TIME"
        now = pd.Timestamp.now()
        filtered_df["Duration"] = ((now - filtered_df["10.60 TIME"]).dt.total_seconds() / 3600).round(2)

        # Get only the lifts on hold (i.e. where MEOW Category is "Hold")
        holds_all = filtered_df[filtered_df["MEOW Category"] == "Hold"]
        debug_log(f"Lifts on hold: {len(holds_all)}")

        # From the holds, get those where the MEOW Reasoning mentions "wind"
        wind_hold = holds_all[holds_all["MEOW Reasoning"].str.contains("wind", case=False, na=False)]
        debug_log(f"Lifts on wind hold: {len(wind_hold)}")

        # The "other" holds are those lifts on hold that are not wind-related
        other_hold = holds_all[~holds_all.index.isin(wind_hold.index)]
        debug_log(f"Lifts on other hold: {len(other_hold)}")

        return filtered_df, wind_hold, other_hold
    
    except Exception as e:
        debug_log(f"Error processing lift data: {str(e)}")
        # Return empty DataFrames in case of error
        empty_df = pd.DataFrame(columns=["Lift", "MEOW Category", "MEOW Reasoning", 
                                         "10.60 TIME", "10.63", "Fault", "Duration"])
        return empty_df, empty_df, empty_df

# For testing purposes:
if __name__ == "__main__":
    all_lifts, wind_hold, other_hold = get_lift_data()
    print(f"All Lifts: {len(all_lifts)}")
    print(f"Wind Hold: {len(wind_hold)}")
    print(f"Other Hold: {len(other_hold)}")
    print("\nNOAA Forecast:")
    print(get_noaa_hourly_wind())