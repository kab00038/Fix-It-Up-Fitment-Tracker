import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="Fitment Visualizer", page_icon="🏎️", layout="centered")
# 1. Load Data
@st.cache_data
def load_data():
    # Make sure your CSV filename matches exactly!
    df = pd.read_csv("fitment database.csv")
    
    # Clean up strings
    df['make'] = df['make'].astype(str).str.strip()
    df['model'] = df['model'].astype(str).str.strip()
    
    # Normalize position names (lowercase, underscores) to match logic
    # e.g. "Front Left" -> "front_left"
    df['position'] = df['position'].astype(str).str.lower().str.strip().str.replace(' ', '_')
    return df

try:
    df = load_data()
except FileNotFoundError:
    st.error("Database file not found. Ensure 'fitment database.xlsx - Sheet1.csv' is in the folder.")
    st.stop()

# 2. The Diagram Logic
def create_tpms_diagram(car_data, make, model):
    """
    Draws a top-down car view and maps data to the 4 corners.
    """
    
    # A dictionary to hold the text for each of the 4 corners
    # Default state is empty
    wheel_corners = {
        'FL': {'text': "N/A", 'x': -2.5, 'y': 2.8, 'color': '#adadad'},
        'FR': {'text': "N/A", 'x': 2.5,  'y': 2.8, 'color': '#adadad'},
        'RL': {'text': "N/A", 'x': -2.5, 'y': -2.8, 'color': '#adadad'},
        'RR': {'text': "N/A", 'x': 2.5,  'y': -2.8, 'color': '#adadad'}
    }

    # Helper to format the string
    def fmt(row):
        return f"<b>{row['width_mm']} / {row['aspect_ratio']} R{row['rim_diameter_in']}</b>"

    # Map the database rows to the visual corners
    for _, row in car_data.iterrows():
        pos = row['position']
        label = fmt(row)
        
        # Logic to apply "Front" data to both FL and FR, etc.
        if pos in ['front', 'front_axle']:
            wheel_corners['FL'].update({'text': label, 'color': '#333'})
            wheel_corners['FR'].update({'text': label, 'color': '#333'})
        elif pos in ['back', 'rear', 'rear_axle']:
            wheel_corners['RL'].update({'text': label, 'color': '#333'})
            wheel_corners['RR'].update({'text': label, 'color': '#333'})
        elif pos == 'all':
            for key in wheel_corners:
                wheel_corners[key].update({'text': label, 'color': '#333'})
        elif pos == 'front_left':
            wheel_corners['FL'].update({'text': label, 'color': '#333'})
        elif pos == 'front_right':
            wheel_corners['FR'].update({'text': label, 'color': '#333'})
        elif pos == 'back_left':
            wheel_corners['RL'].update({'text': label, 'color': '#333'})
        elif pos == 'back_right':
            wheel_corners['RR'].update({'text': label, 'color': '#333'})

    # --- DRAWING WITH PLOTLY ---
    fig = go.Figure()

    # 1. Draw Car Body (Simple Rounded Rectangle)
    fig.add_shape(type="rect", x0=-1.5, y0=-3.5, x1=1.5, y1=3.5,
        line=dict(color="#2c3e50", width=3), fillcolor="#ecf0f1", opacity=1)
    
    # 2. Draw Windshield (Visual cue for "Front")
    fig.add_shape(type="path", path="M -1.3,1 L 1.3,1 L 1.3,2.5 L -1.3,2.5 Z",
        fillcolor="#3498db", opacity=0.3, line_width=0)
    
    # 3. Draw 4 Wheels
    # Coords: [x_center, y_center]
    wheels = [(-1.6, 2.5), (1.6, 2.5), (-1.6, -2.5), (1.6, -2.5)]
    for wx, wy in wheels:
        fig.add_shape(type="rect", 
            x0=wx-0.3, y0=wy-0.6, x1=wx+0.3, y1=wy+0.6, # Dimensions of tire
            fillcolor="#1a1a1a", line_color="black"
        )

    # 4. Add the Text Annotations (The "TPMS" Readout)
    for key, data in wheel_corners.items():
        fig.add_annotation(
            x=data['x'], 
            y=data['y'],
            text=data['text'],
            showarrow=False,
            font=dict(size=18, color=data['color']),
            bgcolor="rgba(255,255,255,0.9)",
            bordercolor=data['color'],
            borderwidth=1,
            borderpad=5
        )

    # Layout Cleaning
    fig.update_xaxes(range=[-5, 5], visible=False, fixedrange=True)
    fig.update_yaxes(range=[-5, 5], visible=False, fixedrange=True)
    fig.update_layout(
        title_text=f"{make} {model} Fitment",
        title_x=0.5,
        width=600,
        height=600,
        margin=dict(l=10, r=10, t=50, b=10),
        plot_bgcolor="white",
        hovermode=False # Disable hover interactions for cleaner feel
    )

    return fig

# 3. UI Layout

st.title("🏎️ Fitment Visualizer")
st.markdown("Select a vehicle to see the tire sizing configuration.")

col1, col2 = st.columns(2)

with col1:
    all_makes = sorted(df['make'].unique())
    selected_make = st.selectbox("Make", options=all_makes, index=None, placeholder="Select Make")

with col2:
    if selected_make:
        filtered_models = sorted(df[df['make'] == selected_make]['model'].unique())
        selected_model = st.selectbox("Model", options=filtered_models, index=None, placeholder="Select Model")
    else:
        st.selectbox("Model", options=[], disabled=True, placeholder="Waiting for Make...")

# 4. Display Logic
if selected_make and selected_model:
    st.divider()
    
    # Filter data for this car
    result = df[(df['make'] == selected_make) & (df['model'] == selected_model)]
    
    if not result.empty:
        # Draw the car
        fig = create_tpms_diagram(result, selected_make, selected_model)
        st.plotly_chart(fig, use_container_width=True)
        
        # Optional: Show the raw data below in an expander if they want details
        with st.expander("View Raw Data Table"):
            st.dataframe(result)
    else:
        st.warning("No data found for this specific configuration.")
else:
    # Start screen
    st.info("👆 Use the dropdowns above to load a car.")