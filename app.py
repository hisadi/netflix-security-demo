import streamlit as st
import json
import os
import time
import pandas as pd
from datetime import datetime
from streamlit_js_eval import get_geolocation, streamlit_js_eval
from math import radians, cos, sin, asin, sqrt

# ==========================================
# 1. UI CONFIGURATION
# ==========================================
st.set_page_config(page_title="Netflix Strategic AI", page_icon="🧠", layout="wide")
DB_FILE = 'netflix_full_db.json'

st.markdown("""
<style>
    /* Global Styles */
    .stApp { background-color: #F8F9FA; color: #212529; }
    h1, h2, h3 { color: #E50914 !important; font-weight: 800 !important; }
    
    /* Forensic Table */
    .forensic-table {
        width: 100%; border-collapse: collapse; margin-bottom: 20px;
        background: white; border-radius: 8px; overflow: hidden;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    .forensic-table th { background: #E50914; color: white; padding: 12px; text-align: left; }
    .forensic-table td { padding: 10px; border-bottom: 1px solid #dee2e6; color: #333; }
    .forensic-table tr:last-child td { border-bottom: none; }
    
    /* Status Labels */
    .status-match { background: #d1e7dd; color: #0f5132; padding: 4px 8px; border-radius: 4px; font-weight: bold; font-size: 0.9em; }
    .status-warn { background: #fff3cd; color: #664d03; padding: 4px 8px; border-radius: 4px; font-weight: bold; font-size: 0.9em; }
    .status-danger { background: #f8d7da; color: #842029; padding: 4px 8px; border-radius: 4px; font-weight: bold; font-size: 0.9em; }
    
    /* Input Box */
    .stTextInput input { border: 2px solid #ced4da; border-radius: 5px; padding: 10px; }
    .stTextInput input:focus { border-color: #E50914; box-shadow: 0 0 0 0.2rem rgba(229, 9, 20, 0.25); }
    
    /* Strategy Box */
    .strat-card { background: white; padding: 20px; border-radius: 10px; border-left: 5px solid #E50914; box-shadow: 0 2px 4px rgba(0,0,0,0.05); height: 100%; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. SENSOR & LOGIC ENGINE
# ==========================================

# --- A. SENSORS (Javascript) ---
def get_all_sensors(key_suffix):
    # Mengambil semua data fingerprint sekaligus
    ip = streamlit_js_eval(js_expressions='fetch("https://api.ipify.org?format=json").then(r => r.json()).then(d => d.ip)', key=f'ip_{key_suffix}')
    sw = streamlit_js_eval(js_expressions='screen.width', key=f'sw_{key_suffix}')
    sh = streamlit_js_eval(js_expressions='screen.height', key=f'sh_{key_suffix}')
    ua = streamlit_js_eval(js_expressions='navigator.userAgent', key=f'ua_{key_suffix}')
    return ip, sw, sh, ua

# --- B. PARSING & SCORING ---
def parse_fingerprint(ua):
    if not ua: return "Unknown", "Unknown"
    ua = ua.lower()
    
    # OS
    os_name = "Linux/Other"
    if "windows" in ua: os_name = "Windows PC"
    elif "mac" in ua: os_name = "MacBook/iMac"
    elif "iphone" in ua: os_name = "iPhone iOS"
    elif "android" in ua: os_name = "Android Mobile"
    
    # Browser
    browser = "Other"
    if "edg" in ua: browser = "Edge"
    elif "chrome" in ua: browser = "Chrome"
    elif "safari" in ua: browser = "Safari"
    elif "firefox" in ua: browser = "Firefox"
    
    return os_name, browser

def calculate_cpm(text, duration):
    """Menghitung Characters Per Minute"""
    if duration <= 0: return 0
    # CPM = (Jumlah Karakter / Detik) * 60
    return int((len(text) / duration) * 60)

def haversine(lon1, lat1, lon2, lat2):
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    a = sin((lat2-lat1)/2)**2 + cos(lat1) * cos(lat2) * sin((lon2-lon1)/2)**2
    c = 2 * asin(sqrt(a))
    return c * 6371

# --- C. DB UTILS ---
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
# 3. APP LOGIC
# ==========================================
st.title("🛡️ Netflix Strategic AI Dashboard")
st.markdown("Implementation of **Advanced AI Detection** & **Shadow Monetization**.")

data = load_db()
has_host = data is not None

# Init Session for Timers
if 'is_host' not in st.session_state: st.session_state['is_host'] = False
if 'page_load_time' not in st.session_state: st.session_state['page_load_time'] = time.time()

with st.sidebar:
    st.header("Admin Controls")
    if has_host and st.button("🔴 Reset Household Data"):
        reset_db()
        st.session_state['is_host'] = False
        st.rerun()

# ==========================================
# FASE 1: HOUSEHOLD ENRICHMENT (HOST)
# ==========================================
if not has_host or (has_host and st.session_state['is_host']):
    if not has_host:
        st.subheader("🏠 Phase 1: Host Data Enrichment")
        st.info("Training Model dengan Data Lengkap Host (Biometrik + Forensik).")
        
        # 1. SENSORS GATHERING
        h_ip, h_sw, h_sh, h_ua = get_all_sensors('host')
        
        # 2. AUTO-TIMER INPUT
        st.write("---")
        st.markdown("**🔐 Biometric Enrollment:** Ketik frase di bawah lalu tekan ENTER.")
        st.code("netflix secure access")
        
        # Reset timer saat user mulai mengetik (Callback trick tidak bisa di text_input standar, 
        # jadi kita pakai waktu selisih load vs submit sebagai 'reaction + typing time')
        # Ini metode paling seamless tanpa tombol start.
        
        h_input = st.text_input("Input:", key="h_in", placeholder="Ketik lalu Enter...")
        
        if h_input:
            if h_input.lower() == "netflix secure access":
                # Hitung CPM otomatis (Waktu sekarang - Waktu halaman dimuat)
                duration = time.time() - st.session_state['page_load_time']
                # Kita kurangi sedikit buffer (misal 2 detik untuk baca) agar CPM realistis
                adjusted_duration = max(1, duration - 2) 
                h_cpm = calculate_cpm(h_input, adjusted_duration)
                
                # Parsing Fingerprint
                h_os, h_browser = parse_fingerprint(h_ua)
                h_res = f"{h_sw}x{h_sh}"
                
                st.write(f"🔍 Detected: {h_os} | {h_cpm} CPM | {h_ip}")
                
                if st.checkbox("📍 Lock GPS & Train Model"):
                    loc = get_geolocation(component_key='gps_host')
                    if loc:
                        # SIMPAN SEMUA DATA LENGKAP
                        db_data = {
                            'ip': h_ip,
                            'os': h_os,
                            'browser': h_browser,
                            'res': h_res,
                            'width': h_sw, # untuk propensity
                            'cpm': h_cpm,  # biometrik
                            'lat': loc['coords']['latitude'],
                            'lon': loc['coords']['longitude'],
                            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }
                        save_db(db_data)
                        st.session_state['is_host'] = True
                        st.rerun()
                    else:
                        st.warning("⏳ Waiting for GPS...")
            else:
                st.error("❌ Teks salah! Ketik: 'netflix secure access'")
    else:
        st.success("✅ HOUSEHOLD MODEL TRAINED")
        st.write(f"Host Profile Active: {data['os']} at {data['ip']}")

# ==========================================
# FASE 2: VISITOR ANALYSIS (REAL-TIME)
# ==========================================
else:
    st.write("---")
    st.subheader("🕵️ Phase 2: AI Detection & Strategy Execution")
    
    # 1. INVISIBLE SENSORING
    v_ip, v_sw, v_sh, v_ua = get_all_sensors('vis')
    
    col_left, col_right = st.columns([1, 1.5])
    
    # --- KOLOM KIRI: INPUT CHALLENGE ---
    with col_left:
        st.markdown('<div class="strat-card">', unsafe_allow_html=True)
        st.markdown("#### 🔑 Security Challenge")
        st.write("Verifikasi identitas Anda:")
        st.code("netflix secure access")
        
        # AUTO TIMER LOGIC
        v_input = st.text_input("Passphrase:", key="v_in", placeholder="Langsung ketik & Enter...")
        
        run_analysis = False
        if v_input:
            run_analysis = True
        
        st.markdown("</div>", unsafe_allow_html=True)

    # --- KOLOM KANAN: DASHBOARD STRATEGI ---
    with col_right:
        if run_analysis:
            if not v_ip:
                st.warning("Scanning Sensors...")
                st.stop()
            
            loc = get_geolocation(component_key='gps_vis')
            
            if loc:
                # === A. DATA PROCESSING ===
                # 1. Biometrics (CPM)
                duration = time.time() - st.session_state['page_load_time']
                adj_duration = max(1, duration - 2)
                v_cpm = calculate_cpm(v_input, adj_duration)
                
                # 2. Forensics
                v_os, v_browser = parse_fingerprint(v_ua)
                v_res = f"{v_sw}x{v_sh}"
                dist = haversine(data['lon'], data['lat'], loc['coords']['latitude'], loc['coords']['longitude'])
                
                # 3. Validasi
                is_bio_match = abs(data['cpm'] - v_cpm) < 50 # Toleransi 50 CPM
                is_dist_match = dist < 60
                is_ip_match = (v_ip == data['ip'])
                is_os_match = (v_os == data['os'])
                
                # 4. Scoring (AI Models)
                trust_score = 0
                if is_dist_match: trust_score += 40
                if is_bio_match: trust_score += 30
                if is_ip_match: trust_score += 20
                if is_os_match: trust_score += 10
                
                propensity_score = 50
                if v_sw > 1500 or "Mac" in v_os or "iOS" in v_os: propensity_score += 30
                if "Android" in v_os: propensity_score -= 10
                
                # === B. TABEL FORENSIK LENGKAP (REQUEST ANDA) ===
                st.markdown("### 📡 Advanced AI Detection Layer")
                
                # Membangun Tabel HTML Dinamis
                table_html = f"""
                <table class="forensic-table">
                    <thead>
                        <tr>
                            <th>PARAMETER</th>
                            <th>🏠 HOST (BASELINE)</th>
                            <th>📱 VISITOR (REAL-TIME)</th>
                            <th>STATUS</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td><b>Behavioral Biometrics</b><br><small>Keystroke Dynamics (CPM)</small></td>
                            <td>{data['cpm']} CPM</td>
                            <td>{v_cpm} CPM</td>
                            <td><span class="{'status-match' if is_bio_match else 'status-danger'}">{'MATCH' if is_bio_match else 'ANOMALY'}</span></td>
                        </tr>
                        <tr>
                            <td><b>Geolocation</b><br><small>GPS Coordinates</small></td>
                            <td>Lat: {data['lat']:.2f}...</td>
                            <td>Lat: {loc['coords']['latitude']:.2f}...</td>
                            <td><span class="{'status-match' if is_dist_match else 'status-danger'}">{'HOME' if is_dist_match else f'AWAY ({int(dist)} KM)'}</span></td>
                        </tr>
                        <tr>
                            <td><b>Network Signature</b><br><small>Public IP Address</small></td>
                            <td>{data['ip']}</td>
                            <td>{v_ip}</td>
                            <td><span class="{'status-match' if is_ip_match else 'status-warn'}">{'SAME' if is_ip_match else 'DIFF'}</span></td>
                        </tr>
                        <tr>
                            <td><b>Device OS</b><br><small>Operating System</small></td>
                            <td>{data['os']}</td>
                            <td>{v_os}</td>
                            <td><span class="{'status-match' if is_os_match else 'status-warn'}">{'SAME' if is_os_match else 'DIFF'}</span></td>
                        </tr>
                        <tr>
                            <td><b>Browser Engine</b><br><small>Software Agent</small></td>
                            <td>{data['browser']}</td>
                            <td>{v_browser}</td>
                            <td>{'MATCH' if data['browser'] == v_browser else 'DIFF'}</td>
                        </tr>
                         <tr>
                            <td><b>Screen Resolution</b><br><small>Hardware Fingerprint</small></td>
                            <td>{data['res']}</td>
                            <td>{v_res}</td>
                            <td>{'MATCH' if data['res'] == v_res else 'DIFF'}</td>
                        </tr>
                    </tbody>
                </table>
                """
                st.markdown(table_html, unsafe_allow_html=True)
                
                # === C. STRATEGIC ACTION ===
                st.markdown("### 🎯 Strategic Decision Engine")
                
                c1, c2 = st.columns(2)
                
                # Metric AI Score
                c1.metric("AI Trust Score", f"{trust_score}%", delta="Safe" if trust_score > 70 else "Risk", delta_color="normal" if trust_score > 70 else "inverse")
                
                # Logic Strategy
                if trust_score > 70:
                    c2.success("✅ **Strategy 1: Low Friction**")
                    c2.write("User Verified. Instant Access.")
                else:
                    c2.error("⛔ **Strategy 2: Monetize**")
                    c2.write(f"Propensity: {propensity_score}/100")
                    if propensity_score > 70:
                        c2.button("💎 Premium Upsell")
                    else:
                        c2.button("📺 Ad-Supported Plan")

            else:
                st.info("⏳ Waiting for GPS...")
        else:
            st.info("👋 Silakan ketik passphrase untuk memulai analisis.")
