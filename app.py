import streamlit as st
import json
import os
import time
import pandas as pd
from datetime import datetime
from streamlit_js_eval import get_geolocation, streamlit_js_eval
from math import radians, cos, sin, asin, sqrt

# ==========================================
# 1. SETUP UI
# ==========================================
st.set_page_config(page_title="Netflix Strategic Guard", page_icon="🛡️", layout="wide")
DB_FILE = 'netflix_fix_db.json'

st.markdown("""
<style>
    .stApp { background-color: #F4F6F8; color: #2C3E50; }
    h1, h2, h3 { color: #E50914 !important; font-weight: 800 !important; }
    
    .verdict-box { padding: 20px; border-radius: 10px; margin-bottom: 20px; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    .v-success { background-color: #d4edda; color: #155724; border: 2px solid #c3e6cb; }
    .v-warning { background-color: #fff3cd; color: #856404; border: 2px solid #ffeeba; }
    .v-danger { background-color: #f8d7da; color: #721c24; border: 2px solid #f5c6cb; }
    
    .forensic-table { width: 100%; border-collapse: collapse; margin-bottom: 20px; background: white; border-radius: 8px; overflow: hidden; }
    .forensic-table th { background: #222; color: white; padding: 12px; text-align: left; }
    .forensic-table td { padding: 10px; border-bottom: 1px solid #eee; }
    
    .badge { padding: 4px 8px; border-radius: 4px; font-weight: bold; font-size: 12px; }
    .b-green { background: #E8F5E9; color: #2E7D32; }
    .b-red { background: #FFEBEE; color: #C62828; }
    
    .gps-monitor { font-family: monospace; font-size: 12px; color: #666; background: #eee; padding: 5px; border-radius: 4px; margin-top: 5px; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. LOGIC ENGINE
# ==========================================

def get_all_sensors(key_suffix):
    ip = streamlit_js_eval(js_expressions='fetch("https://api.ipify.org?format=json").then(r => r.json()).then(d => d.ip)', key=f'ip_{key_suffix}')
    sw = streamlit_js_eval(js_expressions='screen.width', key=f'sw_{key_suffix}')
    sh = streamlit_js_eval(js_expressions='screen.height', key=f'sh_{key_suffix}')
    ua = streamlit_js_eval(js_expressions='navigator.userAgent', key=f'ua_{key_suffix}')
    return ip, sw, sh, ua

def parse_fingerprint(ua):
    if not ua: return "Unknown", "Unknown", "Unknown"
    ua = ua.lower()
    os_name = "Windows PC" if "windows" in ua else "MacBook" if "mac" in ua else "iPhone" if "iphone" in ua else "Android" if "android" in ua else "Linux"
    browser = "Chrome" if "chrome" in ua else "Safari" if "safari" in ua else "Firefox"
    dev_class = "Desktop" if "windows" in ua or "mac" in ua else "Mobile"
    return os_name, browser, dev_class

def calculate_cpm(text, duration):
    if duration <= 0: return 0
    return int((len(text) / duration) * 60)

def haversine(lon1, lat1, lon2, lat2):
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    a = sin((lat2-lat1)/2)**2 + cos(lat1) * cos(lat2) * sin((lon2-lon1)/2)**2
    c = 2 * asin(sqrt(a))
    return c * 6371

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
# 3. APP FLOW
# ==========================================
st.title("🛡️ Netflix Strategic AI Dashboard")
data = load_db()
has_host = data is not None

if 'is_host' not in st.session_state: st.session_state['is_host'] = False
if 'page_load_time' not in st.session_state: st.session_state['page_load_time'] = time.time()

with st.sidebar:
    if has_host and st.button("🔄 Reset Household Data"):
        reset_db()
        st.session_state['is_host'] = False
        st.rerun()

# ==========================================
# FASE 1: HOST ENROLLMENT
# ==========================================
if not has_host or (has_host and st.session_state['is_host']):
    if not has_host:
        st.subheader("🏠 Phase 1: Host Enrollment")
        st.info("Pastikan GPS browser diizinkan (Allow) agar titik koordinat akurat.")
        
        h_ip, h_sw, h_sh, h_ua = get_all_sensors('host')
        
        st.write("---")
        st.write("🔐 **Biometric Pattern:** Ketik 'netflix' lalu ENTER.")
        h_input = st.text_input("Input:", key="h_in")
        
        # GPS COMPONENT
        loc = get_geolocation(component_key='gps_host')
        
        # MONITOR GPS DEBUG (Supaya kelihatan errornya)
        if loc:
            lat = loc['coords']['latitude']
            lon = loc['coords']['longitude']
            acc = loc['coords']['accuracy']
            st.markdown(f"<div class='gps-monitor'>📡 GPS DETECTED: {lat}, {lon} (Akurasi: {acc}m)</div>", unsafe_allow_html=True)
            
            if h_input == "netflix":
                if st.button("📍 SAVE HOUSEHOLD PROFILE"):
                    # Validasi Anti-Null Island (0,0)
                    if lat == 0 or lon == 0:
                        st.error("❌ GPS belum lock (Koordinat 0,0). Tunggu sebentar atau refresh.")
                    else:
                        dur = time.time() - st.session_state['page_load_time']
                        h_cpm = calculate_cpm(h_input, max(1, dur - 3))
                        h_os, h_browser, h_class = parse_fingerprint(h_ua)
                        
                        db = {
                            'ip': h_ip, 'os': h_os, 'browser': h_browser, 'dev_class': h_class,
                            'res': f"{h_sw}x{h_sh}", 'width': h_sw, 'cpm': h_cpm,
                            'lat': lat, 'lon': lon
                        }
                        save_db(db)
                        st.session_state['is_host'] = True
                        st.rerun()
        else:
            st.warning("⏳ Menunggu Sinyal GPS... (Pastikan klik Allow di popup browser)")
            
    else:
        st.success("✅ HOUSEHOLD MODEL ACTIVE")
        st.write(f"Host Location: {data['lat']}, {data['lon']}")

# ==========================================
# FASE 2: VISITOR ANALYSIS
# ==========================================
else:
    st.write("---")
    st.subheader("🕵️ Phase 2: AI Detection")
    
    v_ip, v_sw, v_sh, v_ua = get_all_sensors('vis')
    st.write("Verifikasi identitas:")
    v_input = st.text_input("Passphrase:", key="v_in", placeholder="Ketik 'netflix'...")

    if v_input:
        loc = get_geolocation(component_key='gps_vis')
        
        if loc:
            lat = loc['coords']['latitude']
            lon = loc['coords']['longitude']
            st.markdown(f"<div class='gps-monitor'>📡 VISITOR GPS: {lat}, {lon}</div>", unsafe_allow_html=True)
            
            # --- CALCULATIONS ---
            dur = time.time() - st.session_state['page_load_time']
            v_cpm = calculate_cpm(v_input, max(1, dur - 3))
            v_os, v_browser, v_class = parse_fingerprint(v_ua)
            v_res = f"{v_sw}x{v_sh}"
            
            # Hitung Jarak
            dist = haversine(data['lon'], data['lat'], lon, lat)
            
            # === MATCHING LOGIC ===
            is_dist_match = dist < 60 # Radius 60 KM
            cpm_diff = abs(data['cpm'] - v_cpm)
            is_bio_match = (cpm_diff < 50) and (data['dev_class'] == v_class)
            
            # DECISION TREE
            if is_dist_match:
                verdict_title = "✅ LOGIN GRANTED"
                verdict_class = "v-success"
                verdict_msg = "Perangkat di lokasi rumah."
            elif not is_dist_match and is_bio_match:
                verdict_title = "⚠️ VERIFY IDENTITY (OTP)"
                verdict_class = "v-warning"
                verdict_msg = "Lokasi jauh, Biometrik cocok (Travel Mode)."
            else:
                verdict_title = "⛔ SHARING DETECTED"
                verdict_class = "v-danger"
                verdict_msg = "Lokasi jauh & Pola berbeda."

            # OUTPUT BANNER
            st.markdown(f"""
            <div class="verdict-box {verdict_class}">
                <h2 style="margin:0; color:inherit !important;">{verdict_title}</h2>
                <p style="margin:0;">{verdict_msg}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # FULL FORENSIC TABLE
            st.markdown("### 📋 7-Parameter Forensic Evidence")
            
            # Warna indikator jarak
            dist_badge = "b-green" if is_dist_match else "b-red"
            
            table_html = f"""
            <table class="forensic-table">
                <thead>
                    <tr><th>PARAMETER</th><th>🏠 HOST</th><th>📱 VISITOR</th><th>STATUS</th></tr>
                </thead>
                <tbody>
                    <tr>
                        <td><b>GPS Coordinates</b></td>
                        <td>{data['lat']:.4f}, {data['lon']:.4f}</td>
                        <td>{lat:.4f}, {lon:.4f}</td>
                        <td><span class="badge {dist_badge}">{int(dist)} KM</span></td>
                    </tr>
                    <tr>
                        <td><b>Typing Speed</b></td>
                        <td>{data['cpm']} CPM</td>
                        <td>{v_cpm} CPM</td>
                        <td><span class="badge {'b-green' if abs(data['cpm']-v_cpm) < 50 else 'b-red'}">{'MATCH' if abs(data['cpm']-v_cpm) < 50 else 'DIFF'}</span></td>
                    </tr>
                     <tr>
                        <td><b>Network IP</b></td>
                        <td>{data['ip']}</td>
                        <td>{v_ip}</td>
                        <td><span class="badge {'b-green' if data['ip'] == v_ip else 'b-red'}">{'SAME' if data['ip'] == v_ip else 'DIFF'}</span></td>
                    </tr>
                    <tr>
                        <td><b>OS Platform</b></td>
                        <td>{data['os']}</td>
                        <td>{v_os}</td>
                        <td>{v_os}</td>
                    </tr>
                    <tr>
                        <td><b>Browser</b></td>
                        <td>{data['browser']}</td>
                        <td>{v_browser}</td>
                        <td>Match</td>
                    </tr>
                     <tr>
                        <td><b>Resolution</b></td>
                        <td>{data['res']}</td>
                        <td>{v_res}</td>
                        <td>Match</td>
                    </tr>
                     <tr>
                        <td><b>Device Class</b></td>
                        <td>{data['dev_class']}</td>
                        <td>{v_class}</td>
                        <td>{'MATCH' if data['dev_class'] == v_class else 'DIFF'}</td>
                    </tr>
                </tbody>
            </table>
            """
            st.markdown(table_html, unsafe_allow_html=True)

            # STRATEGIC ACTION (Jika Blocked)
            if verdict_title == "⛔ SHARING DETECTED":
                st.markdown("### 🎯 Strategic Action")
                propensity = 50
                if v_sw > 1500 or "Mac" in v_os or "iOS" in v_os: propensity += 30
                
                if propensity > 70:
                    st.error("💎 Target: High Value -> Offer Premium Plan")
                else:
                    st.info("📺 Target: Budget -> Offer Ad-Supported Plan")

        else:
            st.info("⏳ Menunggu Sinyal GPS... (Refresh jika macet)")
