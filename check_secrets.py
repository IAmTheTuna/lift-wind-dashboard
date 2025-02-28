import streamlit as st
import json

# Simple Streamlit app to check secrets
st.title("Streamlit Secrets Diagnostic")

# Check if secrets are available
if hasattr(st, 'secrets'):
    st.success("✅ Streamlit secrets are available")
    
    # List all secret keys (without showing values)
    st.subheader("Available Secret Keys")
    for key in st.secrets.keys():
        st.write(f"- {key}")
    
    # Check for specific Google credentials keys
    st.subheader("Google Credentials Check")
    
    if 'GOOGLE_CREDENTIALS' in st.secrets:
        st.success("✅ Found 'GOOGLE_CREDENTIALS' in secrets")
        
        # Check the type and content structure (without showing private data)
        creds = st.secrets['GOOGLE_CREDENTIALS']
        st.write(f"Type: {type(creds)}")
        
        if isinstance(creds, dict):
            # It's already a dictionary, check for required fields
            st.write("Format: JSON dictionary (correct)")
            
            required_fields = ['type', 'project_id', 'private_key_id', 'private_key', 
                               'client_email', 'client_id', 'auth_uri', 'token_uri']
            
            missing_fields = [field for field in required_fields if field not in creds]
            
            if missing_fields:
                st.error(f"❌ Missing required fields: {', '.join(missing_fields)}")
            else:
                st.success("✅ All required credential fields are present")
                
                # Show some non-sensitive fields
                st.write(f"Service Account Email: {creds.get('client_email')}")
                st.write(f"Project ID: {creds.get('project_id')}")
        else:
            # It's a string, check if it can be parsed as JSON
            st.write(f"Format: String (needs to be parsed as JSON)")
            try:
                # Try to parse as JSON, just as a test
                parsed = json.loads(str(creds))
                st.success("✅ Successfully parsed as JSON")
                
                # Check for required fields
                required_fields = ['type', 'project_id', 'private_key_id', 'private_key', 
                                  'client_email', 'client_id', 'auth_uri', 'token_uri']
                
                missing_fields = [field for field in required_fields if field not in parsed]
                
                if missing_fields:
                    st.error(f"❌ Missing required fields: {', '.join(missing_fields)}")
                else:
                    st.success("✅ All required credential fields are present")
            except json.JSONDecodeError as e:
                st.error(f"❌ Failed to parse as JSON: {str(e)}")
    else:
        st.error("❌ 'GOOGLE_CREDENTIALS' not found in secrets")
        
        # Check if it's in the nested format
        if 'google' in st.secrets and 'credentials' in st.secrets.google:
            st.success("✅ Found 'google.credentials' instead")
            # We could do the same validation here
        else:
            st.error("❌ No Google credentials found in any format")
    
    # Check for sheet name
    st.subheader("Google Sheet Name Check")
    if 'GOOGLE_SHEET_NAME' in st.secrets:
        sheet_name = st.secrets['GOOGLE_SHEET_NAME']
        st.success(f"✅ Found GOOGLE_SHEET_NAME: '{sheet_name}'")
    elif 'google' in st.secrets and 'sheet_name' in st.secrets.google:
        sheet_name = st.secrets.google.sheet_name
        st.success(f"✅ Found google.sheet_name: '{sheet_name}'")
    else:
        st.error("❌ No Google Sheet name found in secrets")
        
else:
    st.error("❌ No Streamlit secrets available")
    st.info("Make sure you've set up secrets in the Streamlit Cloud dashboard")