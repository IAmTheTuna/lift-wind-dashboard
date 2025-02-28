import streamlit as st

st.title("Simple Secrets Checker")

# Check if we have any secrets
if hasattr(st, 'secrets'):
    st.success("Secrets are available")
    
    # Print out all top-level keys
    st.write("Top-level keys in st.secrets:")
    for key in st.secrets.keys():
        st.write(f"- {key}")
    
    # If 'google' exists, look at its keys
    if 'google' in st.secrets:
        st.write("Keys inside st.secrets.google:")
        for key in st.secrets.google.keys():
            st.write(f"- {key}")
        
        # Check if credentials exist
        if 'credentials' in st.secrets.google:
            st.success("Found st.secrets.google.credentials")
            # Show a tiny preview without revealing sensitive data
            cred_preview = str(st.secrets.google.credentials)[:20] + "..." if st.secrets.google.credentials else "Empty"
            st.write(f"Preview: {cred_preview}")
        else:
            st.error("st.secrets.google.credentials is missing")
        
        # Check if sheet_name exists
        if 'sheet_name' in st.secrets.google:
            st.success(f"Found sheet_name: {st.secrets.google.sheet_name}")
        else:
            st.error("st.secrets.google.sheet_name is missing")
    else:
        st.error("'google' section is missing in secrets")
        
    # Also check for the flat format
    if 'GOOGLE_CREDENTIALS' in st.secrets:
        st.success("Found GOOGLE_CREDENTIALS")
    if 'GOOGLE_SHEET_NAME' in st.secrets:
        st.success(f"Found GOOGLE_SHEET_NAME: {st.secrets.GOOGLE_SHEET_NAME}")
        
else:
    st.error("No secrets available")
    
st.write("---")
st.write("If you don't see your secrets, make sure:")
st.write("1. You've added them correctly in the Streamlit Cloud settings")
st.write("2. You've saved the changes")
st.write("3. You've rebooted the app after saving secrets")