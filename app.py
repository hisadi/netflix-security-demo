import streamlit as st
import json
import os
import time
from datetime import datetime
from streamlit_js_eval import get_geolocation, streamlit_js_eval
from math import radians, cos, sin, asin, sqrt

# ==========================================
# 1. SETUP UI: LIGHT MODE MODERN
# ==========================================
st.set_page_config(page_title="Netflix Neuro-ID", page_icon="🧠", layout="wide")
DB_FILE = 'netflix_neuro_db.json'

# CSS Custom: Light Mode + Netflix Red Accent
st.markdown("""
<style>
    /* Background Putih Bersih */
    .stApp {
        background-color: #FFFFFF !important;
        color: #333333 !important;
    }
    
    /* Header Styles */
    h1, h2 { color: #E50914 !important; font-weight: 800 !important; }
    h3, h4 { color: #222222 !important; font-weight: 600 !important; }
    
    /* Metrics Card Style */
    .metric-container {
        background-color: #F8F9FA;
        border: 1px solid #E0E0E0;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        margin-bottom: 15px;
    }
    
    /* Custom Input Fields */
    .stTextInput > div > div > input {
        background-color: #ffffff;
        color: #333;
        border: 1px solid #ccc;
    }
    
    /* Buttons */
    .stButton > button {
        background-color: #E50914 !important;
        color: white !important;
        border-radius: 5px !important;
        border: none !important;
        padding: 0.5rem 1rem !important;
    }
    
    /* Alert Boxes Custom */
    .success-box { background-color: #d1e7dd; color: #0f5132; padding: 15px; border-radius: 8px; border: 1px solid #badbcc; }
    .warning-box { background-color: #fff3cd; color: #664d03; padding: 15px; border-radius: 8px; border: 1px solid #ffecb5; }
    .error-box { background-color: #f8d7da; color: #842029; padding: 15px; border-radius: 8px; border: 1px solid #f5c2c7; }

</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. LOGIC ENGINE (SENSORS & BIOMETRICS)
# ==========================================

def get_device_sensors(key_suffix):
    # Mengambil Sensor Hardware & Network
    ip = streamlit_js_eval(js_expressions='fetch("https://api.ipify.org?format=json").then(r => r.json()).then(d => d.ip)', key=f'ip_{key_suffix}')
    sw = streamlit_js_eval(js_expressions='screen.width', key=f'sw_{key_suffix}')
    ua = streamlit_js_eval(js_expressions='navigator.userAgent', key=f'ua_{key_suffix}')
    return ip, sw, ua

def parse_ua(ua):
    if not ua: return "Unknown", "Unknown"
    ua = ua.lower()
    os_name = "Windows" if "windows" in ua else "Mac/iOS" if "mac" in ua or "iphone" in ua else "Android" if "android" in ua else "Linux/Other"
    browser = "Chrome" if "chrome" in ua else "Safari" if "safari" in ua else "Firefox" if "firefox" in ua else "Edge"
    return os_name, browser

def haversine(lon1, lat1, lon2, lat2):
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    a = sin((lat2-lat1)/2)**2 + cos(lat1) * cos(lat2) * sin((lon2-lon1)/2)**2
    c = 2 * asin(sqrt(a))
    return c * 6371

def calculate_propensity(os_name, width):
    """Menilai Kekayaan User berdasarkan Hardware"""
    score = 50
    if "Mac" in os_name: score += 30
    elif "Windows" in os_name: score += 10
    elif "Android" in os_name: score -= 10
    
    if width and width > 1500: score += 20 # High Res Screen
    return max(0, min(100, score))

# DATABASE UTILS
def load_db():
    # Cek dulu apakah file ada
    if not os.path.exists(DB_FILE): 
        return None
    
    # Coba buka file
    try:
        with open(DB_FILE, 'r') as f:
            return json.load(f)
    except:
        # Jika file rusak atau error, kembalikan None
        return None

def save_db(data):
    with open(DB_FILE, 'w') as f: json.dump(data, f)

def reset_db():
    if os.path.exists(DB_FILE): os.remove(DB_FILE)

# ==========================================
# 3. UI UTAMA
# ==========================================
st.title("🧠 Netflix Neuro-ID")
st.markdown("##### Multi-Factor Detection: Forensics (Device/GPS) + Behavioral (Typing Biometrics)")

data = load_db()
has_host = data is not None

if 'is_host' not in st.session_state: st.session_state['is_host'] = False

# Sidebar
with st.sidebar:
    st.header("Control Panel")
    if has_host:
        if st.button("🔄 Reset System"):
            reset_db()
            st.session_state['is_host'] = False
            st.rerun()

# ==========================================
# FASE 1: HOST REGISTRATION (ANCHORING)
# ==========================================
if not has_host or (has_host and st.session_state['is_host']):
    if not has_host:
        st.subheader("1. Household Registration")
        st.info("Daftarkan perangkat utama. Sistem juga akan merekam **Gaya Mengetik** Anda sebagai biometrik.")
    else:
        st.success("✅ HOST DASHBOARD (Monitoring Mode)")
        st.json(data)
    
    # --- SENSOR 1: Hardware ---
    h_ip, h_sw, h_ua = get_device_sensors('host')
    
    if not has_host:
        st.write("---")
        st.markdown("#### ⌨️ Behavioral Calibration")
        st.write("Ketik frase berikut secepat mungkin. Sistem menghitung ritme ketikan Anda.")
        st.code("netflix and chill", language="text")
        
        # LOGIKA TYPING SPEED (BIOMETRIK SEDERHANA)
        # Kita pakai text_input biasa, tapi kita minta user klik tombol start/stop secara implisit via submit
        
        start_time = st.number_input("Timestamp Start (System)", value=time.time(), disabled=True, label_visibility="collapsed")
        typing_input = st.text_input("Ketik di sini:", placeholder="netflix and chill")
        end_time = time.time()
        
        # Hitung durasi kasar (ini demo, jadi pakai selisih render streamlt cukup oke)
        # Note: Untuk akurasi tinggi butuh JS custom, tapi untuk demo konsep ini cukup.
        
        if h_ip:
            h_os, h_browser = parse_ua(h_ua)
            st.caption(f"Device Fingerprint: {h_os} | {h_browser} | Screen: {h_sw}px")
            
            if st.checkbox("📍 Lock GPS & Save Biometrics"):
                loc = get_geolocation(component_key='gps_host')
                
                if loc:
                    # Simpan Durasi Mengetik sebagai 'Baseline Biometrik'
                    # Kita asumsi panjang string / waktu
                    if len(typing_input) > 5:
                        # Simulasi baseline (Host biasanya cepat)
                        # Di real world kita simpan keystroke flight time
                        typing_baseline = 50 # millisecond per key (contoh)
                    else:
                        typing_baseline = 0 # Invalid
                    
                    db_data = {
                        'ip': h_ip,
                        'os': h_os,
                        'browser': h_browser,
                        'res': h_sw,
                        'lat': loc['coords']['latitude'],
                        'lon': loc['coords']['longitude'],
                        'bio_pattern': "Fast_Desktop" if "Windows" in h_os or "Mac" in h_os else "Thumb_Mobile",
                        'timestamp': datetime.now().timestamp()
                    }
                    save_db(db_data)
                    st.session_state['is_host'] = True
                    st.rerun()
                else:
                    st.warning("⏳ Menunggu GPS...")
        else:
            st.info("Scanning sensors...")

# ==========================================
# FASE 2: VISITOR ANALYSIS (FULL ENGINE)
# ==========================================
else:
    st.subheader("2. Visitor Login & Analysis")
    st.write("Analisis gabungan: **Lokasi** + **Device** + **Perilaku Mengetik**.")
    
    v_ip, v_sw, v_ua = get_device_sensors('vis')
    
    st.markdown("""
    <div class="metric-container">
        <h4>⌨️ Active Biometric Challenge</h4>
        <p>Untuk memverifikasi bahwa Anda adalah pemilik akun, silakan ketik frase keamanan:</p>
        <code style="font-size:1.2em; font-weight:bold;">netflix and chill</code>
    </div>
    """, unsafe_allow_html=True)
    
    vis_input = st.text_input("Ketik frase di atas:", key="vis_typing")
    
    if st.checkbox("🚀 Verify Identity"):
        if not v_ip:
            st.warning("Scanning network...")
            st.stop()
            
        loc = get_geolocation(component_key='gps_vis')
        
        if loc and vis_input.lower() == "netflix and chill":
            # === ENGINE ANALISIS ===
            
            # 1. Parsing Data
            v_os, v_browser = parse_ua(v_ua)
            v_lat = loc['coords']['latitude']
            v_lon = loc['coords']['longitude']
            
            # 2. BEHAVIORAL BIOMETRICS MATCHING (Simulasi Logic)
            # Logika: Jika Host pakai PC (Keyboard fisik) dan Visitor pakai HP (Layar sentuh),
            # Pola ketikan pasti beda drastis.
            
            host_device_type = "Desktop" if "Windows" in data['os'] or "Mac" in data['os'] else "Mobile"
            vis_device_type = "Desktop" if "Windows" in v_os or "Mac" in v_os else "Mobile"
            
            # Skor Biometrik
            if host_device_type == vis_device_type:
                bio_score = 90 # Match tinggi (Sama-sama PC atau sama-sama HP)
                bio_status = "✅ MATCH"
            else:
                bio_score = 40 # Mismatch (Host PC vs Visitor HP)
                bio_status = "⚠️ MISMATCH"
                
            # 3. FORENSIC MATCHING
            dist = haversine(data['lon'], data['lat'], v_lon, v_lat)
            ip_match = (v_ip == data['ip'])
            
            # 4. PROPENSITY SCORING
            propensity = calculate_propensity(v_os, v_sw)
            
            # === TAMPILAN DASHBOARD HASIL ===
            st.divider()
            st.markdown("### 🔍 Forensic & Biometric Report")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("**1. Physical Layer**")
                st.metric("Distance", f"{dist:.1f} KM", delta="Risk" if dist > 60 else "Safe", delta_color="inverse")
                st.caption(f"IP Match: {'Yes' if ip_match else 'No'}")
                
            with col2:
                st.markdown("**2. Behavioral Layer**")
                st.metric("Biometric Score", f"{bio_score}/100", delta=bio_status)
                st.caption(f"Input Pattern: {vis_device_type} Typing")
                
            with col3:
                st.markdown("**3. Value Layer**")
                st.metric("Propensity Score", f"{propensity}/100")
                st.caption(f"Device: {v_os} ({'High End' if propensity>60 else 'Standard'})")
            
            st.write("---")
            
            # === DECISION MATRIX (FINAL LOGIC) ===
            
            # A. HARD BLOCK (Jarak Jauh + Biometrik Salah)
            if dist > 60 and bio_score < 50:
                st.markdown("""<div class="error-box">
                    <h3>⛔ BLOCKED: ACCOUNT SHARING DETECTED</h3>
                    <p>Lokasi jauh dan pola biometrik (cara mengetik) tidak sesuai dengan pemilik akun.</p>
                </div>""", unsafe_allow_html=True)
                
                # MONETIZATION OFFER
                st.write("")
                st.subheader("💡 AI Recommendation (Monetization)")
                if propensity > 70:
                    st.button("💎 Subscribe Premium (Full Price)")
                    st.caption("User mampu membayar (High Value Device).")
                else:
                    st.button("📺 Subscribe Basic (Ad-Supported)")
                    st.caption("User budget sensitive. Tawarkan paket Iklan.")
                    
            # B. SOFT CHALLENGE (Jarak Jauh TAPI Biometrik Cocok - Travel Mode)
            elif dist > 60 and bio_score >= 80:
                st.markdown("""<div class="success-box">
                    <h3>✅ TRAVEL MODE APPROVED</h3>
                    <p>Lokasi jauh, TAPI pola biometrik cocok. User diverifikasi sebagai pemilik akun yang sedang bepergian.</p>
                </div>""", unsafe_allow_html=True)
                
            # C. HOUSEHOLD MATCH (Jarak Dekat)
            else:
                st.markdown("""<div class="success-box">
                    <h3>✅ HOUSEHOLD ACCESS GRANTED</h3>
                    <p>Perangkat berada di lokasi rumah yang valid.</p>
                </div>""", unsafe_allow_html=True)
                
        elif vis_input.lower() != "netflix and chill":
            st.error("❌ Frase salah. Ketikan tidak dapat dianalisis.")
        else:
            st.warning("⏳ Waiting for GPS...")

