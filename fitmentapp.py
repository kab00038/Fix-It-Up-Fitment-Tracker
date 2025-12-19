import streamlit as st
import pandas as pd

# 1. Load Data
@st.cache_data
def load_data():
    # Load the CSV
    df = pd.read_csv("fitment database.csv")
    
    # Clean text for better display
    df['make'] = df['make'].astype(str).str.strip()
    df['model'] = df['model'].astype(str).str.strip()
    df['position'] = df['position'].astype(str).str.strip().str.replace('_', ' ').str.title()
    
    return df

try:
    df = load_data()
except FileNotFoundError:
    st.error("Database file not found. Please ensure the CSV is in the directory.")
    st.stop()

# 2. UI Layout
st.set_page_config(page_title="Fitment Database", page_icon="🚗")

st.title("🚗 Fitment Check")
st.markdown("Search for a vehicle below to view wheel specs.")

# 3. Search Bars (Cascading Filters)
col1, col2 = st.columns(2)

with col1:
    # Get unique makes
    all_makes = sorted(df['make'].unique())
    # Index=None ensures it starts empty/blank
    selected_make = st.selectbox(
        "Make", 
        options=all_makes, 
        index=None, 
        placeholder="Type to search make..."
    )

with col2:
    # Only show models if a make is selected
    if selected_make:
        filtered_models = sorted(df[df['make'] == selected_make]['model'].unique())
        selected_model = st.selectbox(
            "Model", 
            options=filtered_models, 
            index=None, 
            placeholder="Type to search model..."
        )
    else:
        # Disabled empty box if no make selected
        st.selectbox("Model", options=[], disabled=True, placeholder="Select Make first")

# 4. Results Display (Logic: Show nothing until both are selected)
if selected_make and selected_model:
    st.divider()
    
    # Filter the data
    result = df[(df['make'] == selected_make) & (df['model'] == selected_model)]
    
    if not result.empty:
        st.subheader(f"Specs for {selected_make} {selected_model}")
        
        # Display setup type (e.g., Staggered, Symmetric) from the first row found
        setup_type = result.iloc[0]['setup_type'].title()
        st.caption(f"Setup Type: {setup_type}")

        # Iterate through the rows and create "Cards"
        # We use a grid layout for better readability
        for index, row in result.iterrows():
            # Create a visual card for each wheel
            with st.container():
                st.markdown(f"#### 📍 {row['position']}")
                
                # Use columns for the metrics to make them stand out
                c1, c2, c3 = st.columns(3)
                
                with c1:
                    st.metric(label="Width", value=f"{row['width_mm']} mm")
                with c2:
                    st.metric(label="Aspect Ratio", value=row['aspect_ratio'])
                with c3:
                    st.metric(label="Rim Size", value=f"{row['rim_diameter_in']}\"")
                
                st.markdown("---") # Separator line
    else:
        st.warning("No specific data found for this configuration.")

# 5. Empty State (Friendly message when nothing is selected)
else:
    st.info("👆 Use the search bars above to find your car.")