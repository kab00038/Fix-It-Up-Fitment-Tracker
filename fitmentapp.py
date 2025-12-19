import streamlit as st
import pandas as pd

# 1. Load the Data
@st.cache_data
def load_data():
    # Load the CSV file
    df = pd.read_csv("fitment database.csv")
    
    # Ensure consistency in capitalization for display
    df['make'] = df['make'].str.title()
    df['model'] = df['model'].str.title()
    return df

try:
    df = load_data()
except FileNotFoundError:
    st.error("Could not find the database file. Make sure 'fitment database.xlsx - Sheet1.csv' is in the same folder.")
    st.stop()

# 2. App Title and Description
st.title("🚗 Roblox Car Fitment Tracker")
st.markdown("Use this tool to find the correct wheel specs for our cars.")

# 3. Sidebar Filters
st.sidebar.header("Filter Options")

# Make Filter
makes = sorted(df['make'].unique())
selected_make = st.sidebar.selectbox("Select Make", ["All"] + makes)

# Model Filter (Updates based on Make selection)
if selected_make != "All":
    filtered_models = sorted(df[df['make'] == selected_make]['model'].unique())
    selected_model = st.sidebar.selectbox("Select Model", ["All"] + filtered_models)
else:
    selected_model = st.sidebar.selectbox("Select Model", ["All"] + sorted(df['model'].unique()))

# 4. Filter the DataFrame based on selection
current_df = df.copy()

if selected_make != "All":
    current_df = current_df[current_df['make'] == selected_make]

if selected_model != "All":
    current_df = current_df[current_df['model'] == selected_model]

# 5. Display Results
if len(current_df) == 0:
    st.warning("No cars found with those filters.")
else:
    # If a specific car is selected, show details in a nice format
    if selected_make != "All" and selected_model != "All":
        st.success(f"Showing fitment for: **{selected_make} {selected_model}**")
        
        # Display cards for each wheel position
        for index, row in current_df.iterrows():
            with st.container():
                # Create a card-like look
                st.subheader(f"📍 {row['position'].title().replace('_', ' ')}")
                
                col1, col2, col3 = st.columns(3)
                col1.metric("Width", f"{row['width_mm']} mm")
                col2.metric("Aspect Ratio", row['aspect_ratio'])
                col3.metric("Rim Size", f"{row['rim_diameter_in']} in")
                
                st.caption(f"Setup Type: {row['setup_type']}")
                st.divider()
    else:
        # Show table view if looking at lists of cars
        st.dataframe(current_df, use_container_width=True)