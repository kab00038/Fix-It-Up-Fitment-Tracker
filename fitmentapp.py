import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="Car Tuner Pro", page_icon="🏎️", layout="centered")

# --- 1. Generic Load Data Function ---
@st.cache_data(ttl=0)
def load_data(gid):
    # Retrieve ID from secrets
    try:
        sheet_id = st.secrets["connections"]["gsheet_id"]
    except KeyError:
        st.error("Google Sheet ID not found in secrets. Please check secrets.toml.")
        st.stop()

    # Construct URL with specific GID
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"
    
    try:
        df = pd.read_csv(url)
    except Exception:
        st.error(f"Could not load data for GID {gid}. Check if the sheet exists and is public.")
        st.stop()
    
    # Standardize Column Names (lower case, strip spaces)
    df.columns = df.columns.str.lower().str.strip()
    
    # Standardize Make/Model (common to both sheets)
    if 'make' in df.columns:
        df['make'] = df['make'].astype(str).str.strip()
    if 'model' in df.columns:
        df['model'] = df['model'].astype(str).str.strip()
        
    return df

# --- 2. Load Datasets ---
try:
    # A. Load Fitment Data
    # Defaults to "0" if not specified in secrets
    fitment_gid = st.secrets["connections"].get("fitment_gid", "0")
    df_fitment = load_data(fitment_gid)
    
    # Fitment-specific cleanup: Normalize position names
    if 'position' in df_fitment.columns:
        df_fitment['position'] = df_fitment['position'].astype(str).str.lower().str.strip().str.replace(' ', '_')

    # B. Load Engine Data
    # Defaults to "0" if not specified, so make sure to add it to secrets!
    engine_gid = st.secrets["connections"].get("engine_gid", "0") 
    df_engine = load_data(engine_gid)

except Exception as e:
    st.error(f"Error loading databases: {e}")
    st.stop()

# --- 3. Diagram Logic (Your existing function) ---
def create_tpms_diagram(car_data, make, model):
    """
    Draws a top-down car view and maps data to the 4 corners.
    """
    wheel_corners = {
        'FL': {'text': "N/A", 'x': -2.9, 'y': 2.5,  'color': '#adadad'},
        'FR': {'text': "N/A", 'x': 2.9,  'y': 2.5,  'color': '#adadad'},
        'RL': {'text': "N/A", 'x': -2.9, 'y': -2.5, 'color': '#adadad'},
        'RR': {'text': "N/A", 'x': 2.9,  'y': -2.5, 'color': '#adadad'}
    }

    def fmt(row):
        return f"<b>{row['width_mm']} / {row['aspect_ratio']} R{row['rim_diameter_in']}</b>"

    for _, row in car_data.iterrows():
        pos = row['position']
        label = fmt(row)
        
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

    fig = go.Figure()

    # Car Body
    fig.add_shape(type="rect", x0=-1.5, y0=-3.5, x1=1.5, y1=3.5,
        line=dict(color="#2c3e50", width=3), fillcolor="#ecf0f1", opacity=1)
    # Windshield
    fig.add_shape(type="path", path="M -1.3,1 L 1.3,1 L 1.3,2.5 L -1.3,2.5 Z",
        fillcolor="#3498db", opacity=0.3, line_width=0)
    # Wheels
    wheels = [(-1.6, 2.5), (1.6, 2.5), (-1.6, -2.5), (1.6, -2.5)]
    for wx, wy in wheels:
        fig.add_shape(type="rect", 
            x0=wx-0.3, y0=wy-0.6, x1=wx+0.3, y1=wy+0.6, 
            fillcolor="#1a1a1a", line_color="black"
        )
    # Text
    for key, data in wheel_corners.items():
        fig.add_annotation(
            x=data['x'], y=data['y'], text=data['text'], showarrow=False,
            font=dict(size=18, color=data['color']), bgcolor="rgba(255,255,255,0.9)",
            bordercolor=data['color'], borderwidth=1, borderpad=5
        )

    fig.update_xaxes(range=[-5.5, 5.5], visible=False, fixedrange=True)
    fig.update_yaxes(range=[-5, 5], visible=False, fixedrange=True)
    fig.update_layout(
        title_text=f"{make} {model} Fitment", title_x=0.5,
        width=600, height=600, margin=dict(l=10, r=10, t=50, b=10),
        plot_bgcolor="white", hovermode=False
    )
    return fig

# --- 4. Main UI with Tabs ---

st.title("🏎️ Car Tuner Pro")
tab1, tab2 = st.tabs(["🛞 Wheel Fitment", "🔧 Engine Tuning"])

# === TAB 1: FITMENT ===
with tab1:
    st.header("Wheel Fitment")
    col1, col2 = st.columns(2)
    
    with col1:
        makes_fit = sorted(df_fitment['make'].unique())
        # Note the unique key="fit_make" to prevent conflict with the other tab
        sel_make_fit = st.selectbox("Make", options=makes_fit, index=None, key="fit_make", placeholder="Select Make")
    with col2:
        if sel_make_fit:
            models_fit = sorted(df_fitment[df_fitment['make'] == sel_make_fit]['model'].unique())
            sel_model_fit = st.selectbox("Model", options=models_fit, index=None, key="fit_model", placeholder="Select Model")
        else:
            st.selectbox("Model", options=[], disabled=True, key="fit_model_ph", placeholder="Waiting...")

    if sel_make_fit and sel_model_fit:
        st.divider()
        res_fit = df_fitment[(df_fitment['make'] == sel_make_fit) & (df_fitment['model'] == sel_model_fit)]
        if not res_fit.empty:
            fig = create_tpms_diagram(res_fit, sel_make_fit, sel_model_fit)
            st.plotly_chart(fig, use_container_width=True)
            with st.expander("Raw Fitment Data"):
                st.dataframe(res_fit)
        else:
            st.warning("No fitment data found.")
    elif not sel_make_fit:
        st.info("Select a car to view wheels.")

# === TAB 2: ENGINE TUNING ===
with tab2:
    st.header("Engine Specs")
    
    if df_engine.empty:
        st.warning("Engine database could not be loaded. Check your secrets.toml.")
    else:
        c1, c2 = st.columns(2)
        with c1:
            makes_eng = sorted(df_engine['make'].unique())
            sel_make_eng = st.selectbox("Make", options=makes_eng, index=None, key="eng_make", placeholder="Select Make")
        with c2:
            if sel_make_eng:
                models_eng = sorted(df_engine[df_engine['make'] == sel_make_eng]['model'].unique())
                sel_model_eng = st.selectbox("Model", options=models_eng, index=None, key="eng_model", placeholder="Select Model")
            else:
                st.selectbox("Model", options=[], disabled=True, key="eng_model_ph", placeholder="Waiting...")
        
        if sel_make_eng and sel_model_eng:
            st.divider()
            res_eng = df_engine[(df_engine['make'] == sel_make_eng) & (df_engine['model'] == sel_model_eng)]
            
            if not res_eng.empty:
                for idx, row in res_eng.iterrows():
                    st.subheader(f"⚙️ Tune Option #{idx+1}")
                    
                    # Dynamically get columns that aren't make/model
                    spec_cols = [c for c in res_eng.columns if c not in ['make', 'model']]
                    
                    # Display in a grid
                    cols = st.columns(3)
                    for i, col_name in enumerate(spec_cols):
                        val = row[col_name]
                        title = col_name.replace('_', ' ').title()
                        cols[i % 3].metric(title, str(val))
                    st.markdown("---")
            else:
                st.warning("No engine data found for this car.")
    
    if not sel_make_eng and not df_engine.empty:
         st.info("Select a car to view engine specs.")