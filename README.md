# Lift Wind Status Dashboard

A Streamlit dashboard to monitor lift statuses and wind conditions at a ski resort.

## Features

- Real-time monitoring of lift statuses categorized by village
- Separate views for lifts on reduced speed and lifts on hold
- NOAA wind forecasts with trend indicators
- Automatic highlighting of important lift categories:
  - Feeder lifts (highlighted in light red)
  - Upper mountain lifts (highlighted in light blue)
- Auto-refresh every 30 seconds

## Data Sources

- Lift status data from Google Sheets
- Wind forecast data from NOAA API

## Local Development

1. Install requirements:
```
pip install -r requirements.txt
```

2. Run the app:
```
streamlit run dashboard.py
```

## Deployment

This app is configured to be deployed on Streamlit Community Cloud. See the deployment guide for details.