import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="Car Tuner Pro", page_icon="🏎️", layout="centered")

# --- 1. Generic Load Data Function ---
@st.cache_data(ttl=0)
def load_data(gid):
    try:
        sheet_id = st.secrets["connections"]["gsheet_id"]
    except KeyError:
        st.error("Google Sheet ID not found in secrets.")
        st.stop()

    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"
    
    try:
        df = pd.read_csv(url)
    except Exception:
        return pd.DataFrame() # Return empty if sheet not found/loaded
    
    # Standardize Column Names
    df.columns = df.columns.str.lower().str.strip()
    
    # Clean string columns
    for col in df.columns:
        if df[col].dtype == 'object':
            df[col] = df[col].astype(str).str.strip()
            
    return df

# --- 2. Load All Datasets ---
try:
    # A. Fitment Data
    fitment_gid = st.secrets["connections"].get("fitment_gid", "0")
    df_fitment = load_data(fitment_gid)
    if 'position' in df_fitment.columns:
        df_fitment['position'] = df_fitment['position'].str.lower().str.replace(' ', '_')

    # B. Engine Data
    engine_gid = st.secrets["connections"].get("engine_gid", "0") 
    df_engine = load_data(engine_gid)
    
    # C. Value Data (New!)
    values_gid = st.secrets["connections"].get("values_gid", "0")
    df_values = load_data(values_gid)

except Exception as e:
    st.error(f"Error loading databases: {e}")
    st.stop()

# --- 3. Diagram Logic (Fitment) ---
def create_tpms_diagram(car_data, make, model):
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
    fig.add_shape(type="rect", x0=-1.5, y0=-3.5, x1=1.5, y1=3.5,
        line=dict(color="#2c3e50", width=3), fillcolor="#ecf0f1", opacity=1)
    fig.add_shape(type="path", path="M -1.3,1 L 1.3,1 L 1.3,2.5 L -1.3,2.5 Z",
        fillcolor="#3498db", opacity=0.3, line_width=0)
    wheels = [(-1.6, 2.5), (1.6, 2.5), (-1.6, -2.5), (1.6, -2.5)]
    for wx, wy in wheels:
        fig.add_shape(type="rect", x0=wx-0.3, y0=wy-0.6, x1=wx+0.3, y1=wy+0.6, 
            fillcolor="#1a1a1a", line_color="black")
    for key, data in wheel_corners.items():
        fig.add_annotation(x=data['x'], y=data['y'], text=data['text'], showarrow=False,
            font=dict(size=18, color=data['color']), bgcolor="rgba(255,255,255,0.9)",
            bordercolor=data['color'], borderwidth=1, borderpad=5)
    fig.update_xaxes(range=[-5.5, 5.5], visible=False, fixedrange=True)
    fig.update_yaxes(range=[-5, 5], visible=False, fixedrange=True)
    fig.update_layout(title_text=f"{make} {model} Fitment", title_x=0.5,
        width=600, height=600, margin=dict(l=10, r=10, t=50, b=10),
        plot_bgcolor="white", hovermode=False)
    return fig


# --- 4. Main UI ---
st.title("🏎️ Car Tuner Pro")
tab1, tab2, tab3 = st.tabs(["🛞 Wheel Fitment", "🔧 Engine Tuning", "💰 Car Values"])

# === TAB 1: FITMENT ===
with tab1:
    st.header("Wheel Fitment")
    c1, c2 = st.columns(2)
    with c1:
        makes_fit = sorted(df_fitment['make'].unique()) if 'make' in df_fitment.columns else []
        sel_make_fit = st.selectbox("Make", options=makes_fit, index=None, key="fit_make", placeholder="Select Make")
    with c2:
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
        else:
            st.warning("No fitment data found.")

# === TAB 2: ENGINE TUNING ===
with tab2:
    st.header("Engine Specs")
    if df_engine.empty:
        st.warning("Engine database empty or not loaded.")
    elif 'engine' in df_engine.columns:
        engines = sorted(df_engine['engine'].unique())
        sel_engine = st.selectbox("Choose Engine", options=engines, index=None, key="eng_select", placeholder="Select Engine...")
        
        if sel_engine:
            st.divider()
            row = df_engine[df_engine['engine'] == sel_engine].iloc[0]
            if 'hp' in row:
                st.metric("Target Horsepower", f"{row['hp']} HP")
            
            st.subheader("Tune Settings")
            st.markdown("Bars represent value out of 100")
            settings_cols = ['power_limit', 'boost', 'ignition', 'fuel_mix', 'valve_timing']
            grid_cols = st.columns(2)
            for i, col_name in enumerate(settings_cols):
                if col_name in row:
                    raw_val = row[col_name]
                    try:
                        val_int = int(raw_val)
                        display_val = max(0, min(100, val_int))
                    except ValueError:
                        val_int = raw_val
                        display_val = 0
                    
                    title = col_name.replace('_', ' ').title()
                    with grid_cols[i % 2]:
                        st.write(f"**{title}** ({val_int})")
                        if isinstance(val_int, int):
                            st.progress(display_val)

# === TAB 3: CAR VALUES (NEW) ===
with tab3:
    st.header("Market Values")
    
    if df_values.empty:
        st.warning("Value database not loaded. Check 'values_gid' in secrets.")
    elif 'car name' in df_values.columns:
        # Searchable Dropdown for Car Name
        all_cars = sorted(df_values['car name'].unique())
        sel_car_val = st.selectbox("Search Vehicle", options=all_cars, index=None, key="val_select", placeholder="Type to search car...")
        
        if sel_car_val:
            st.divider()
            # Get data row
            v_row = df_values[df_values['car name'] == sel_car_val].iloc[0]
            
            # Display Main Value huge
            st.metric("Market Value", f"${v_row['value']}")
            
            st.divider()
            
            # Display Rates
            c1, c2 = st.columns(2)
            with c1:
                st.metric("Junkyard Rate", v_row['junkyard rate'])
            with c2:
                st.metric("Auction Rate", v_row['auction rate'])
    else:
        st.error("Column 'Car Name' not found in values sheet.")