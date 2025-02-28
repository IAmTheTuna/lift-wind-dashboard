import streamlit as st
import pandas as pd
import requests
import yaml
import streamlit_authenticator as authenticator
from merge_lift_wind_data import get_lift_data
from streamlit_autorefresh import st_autorefresh

# Load authentication configuration
with open('config.yaml') as file:
    config = yaml.load(file, Loader=yaml.SafeLoader)

# Create an authentication object
auth = authenticator.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days'],
    config['preauthorized']
)

# Create a login widget
name, authentication_status, username = auth.login('Login', 'main')

# If not authenticated, stop execution
if authentication_status == False:
    st.error('Username/password is incorrect')
    st.stop()
elif authentication_status == None:
    st.warning('Please enter your username and password')
    st.stop()

# If authenticated, continue with the app
if authentication_status:
    # Set the page layout to wide (must be the first Streamlit command)
    st.set_page_config(page_title="Lift Status Dashboard", layout="wide")
    
    # Show logout button
    auth.logout('Logout', 'sidebar')
    
    # Rest of your app code goes here
    st.title(f"Welcome {name} to the Lift Wind Status Dashboard")
    
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
    
    # Rest of your dashboard code from dashboard.py goes here...
    # (Copy the remaining functions and implementation from dashboard.py)