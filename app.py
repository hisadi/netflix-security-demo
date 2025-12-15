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
# FASE 1: HOST DATA ENRICHMENT
# ==========================================
if not has_host or (has_host and st.session_state['is_host']):
    if not has_host:
        st.subheader("🏠 Phase 1: Host Enrollment")
        st.info("Training Model dengan Data Rumah Tangga (Biometrik + Forensik).")
        
        # SENSORS
        h_ip, h_sw, h_sh, h_ua = get_all_sensors('host')
        
        st.write("---")
        st.write("🔐 **Biometric Pattern:** Ketik frase berikut lalu tekan ENTER.")
        st.code("netflix secure access")
        
        h_input = st.text_input("Input:", key="h_in", placeholder="Ketik cepat...")
        
        if h_input:
            if h_input.lower() == "netflix secure access":
                # CPM Calculation
                dur = time.time() - st.session_state['page_load_time']
                h_cpm = calculate_cpm(h_input, max(1, dur - 3)) # Buffer reaction time
                
                h_os, h_browser, h_class = parse_fingerprint(h_ua)
                st.write(f"Detected: {h_os} | {h_cpm} CPM")
                
                if st.checkbox("📍 Lock GPS & Train Model"):
                    loc = get_geolocation(component_key='gps_host')
                    if loc:
                        db = {
                            'ip': h_ip, 'os': h_os, 'browser': h_browser, 'dev_class': h_class,
                            'res': f"{h_sw}x{h_sh}", 'width': h_sw, 'cpm': h_cpm,
                            'lat': loc['coords']['latitude'], 'lon': loc['coords']['longitude']
                        }
                        save_db(db)
                        st.session_state['is_host'] = True
                        st.rerun()
                    else:
                        st.warning("Waiting for GPS...")
    else:
        st.success("✅ HOUSEHOLD MODEL ACTIVE")
        st.write(f"Host Profile: {data['os']} ({data['cpm']} CPM) at {data['ip']}")

# ==========================================
# FASE 2: VISITOR ANALYSIS & VERDICT
# ==========================================
else:
    st.write("---")
    st.subheader("🕵️ Phase 2: AI Detection & Strategy")
    
    v_ip, v_sw, v_sh, v_ua = get_all_sensors('vis')
    
    col_input, col_result = st.columns([1, 2])
    
    with col_input:
        st.markdown('<div class="strat-card">', unsafe_allow_html=True)
        st.write("#### 🔑 Security Challenge")
        st.write("Verifikasi identitas:")
        st.code("netflix secure access")
        
        v_input = st.text_input("Passphrase:", key="v_in", placeholder="Ketik & Enter...")
        st.caption("AI akan menganalisis gaya mengetik Anda.")
        st.markdown('</div>', unsafe_allow_html=True)

    if v_input:
        if not v_ip:
            st.warning("Scanning Sensors...")
            st.stop()
        
        with col_result:
            loc = get_geolocation(component_key='gps_vis')
            
            if loc:
                # === A. DATA PROCESSING ===
                dur = time.time() - st.session_state['page_load_time']
                v_cpm = calculate_cpm(v_input, max(1, dur - 3))
                v_os, v_browser, v_class = parse_fingerprint(v_ua)
                v_res = f"{v_sw}x{v_sh}"
                dist = haversine(data['lon'], data['lat'], loc['coords']['latitude'], loc['coords']['longitude'])
                
                # === B. MATCHING LOGIC ===
                # 1. Biometric (CPM + Device Class)
                cpm_diff = abs(data['cpm'] - v_cpm)
                is_bio_match = (cpm_diff < 50) and (data['dev_class'] == v_class)
                
                # 2. Forensics
                is_dist_match = dist < 60
                is_ip_match = (v_ip == data['ip'])
                
                # 3. Propensity Score (Kekayaan)
                propensity = 50
                if v_sw > 1500 or "Mac" in v_os or "iOS" in v_os: propensity += 30
                if "Android" in v_os: propensity -= 10
                
                # === C. DECISION TREE (FINAL VERDICT) ===
                
                # CASE 1: HOUSEHOLD MATCH (Jarak Dekat)
                if is_dist_match:
                    verdict_title = "✅ LOGIN GRANTED"
                    verdict_msg = "Strategy 1: Adaptive Trust (Low Friction)"
                    verdict_desc = "Perangkat berada di lokasi rumah yang valid."
                    verdict_class = "v-success"
                    
                # CASE 2: TRAVEL MODE (Jarak Jauh TAPI Biometrik Cocok)
                elif not is_dist_match and is_bio_match:
                    verdict_title = "⚠️ VERIFY IDENTITY (OTP)"
                    verdict_msg = "Strategy 1.5: Travel Mode Protection"
                    verdict_desc = "Lokasi jauh, tapi Pola Biometrik cocok. Kirim OTP ke Email."
                    verdict_class = "v-warning"
                    
                # CASE 3: SHARING DETECTED (Jarak Jauh + Biometrik Beda)
                else:
                    verdict_title = "⛔ SHARING DETECTED"
                    verdict_msg = "Strategy 2: Shadow Monetization"
                    verdict_desc = "Lokasi jauh DAN Pola Biometrik tidak cocok. Akses diblokir."
                    verdict_class = "v-danger"

                # === D. DISPLAY DASHBOARD ===
                
                # 1. VERDICT BANNER (OUTPUT UTAMA)
                st.markdown(f"""
                <div class="verdict-box {verdict_class}">
                    <h2 style="margin:0; color:inherit !important;">{verdict_title}</h2>
                    <h4 style="margin:5px 0; color:inherit !important;">{verdict_msg}</h4>
                    <p style="margin:0; color:inherit !important;">{verdict_desc}</p>
                </div>
                """, unsafe_allow_html=True)
                
                # 2. FULL FORENSIC TABLE (BUKTI DATA)
                st.markdown("### 📋 7-Parameter Forensic Evidence")
                
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
                            <td><b>1. Typing Speed (CPM)</b></td>
                            <td>{data['cpm']} CPM</td>
                            <td>{v_cpm} CPM</td>
                            <td><span class="badge {'b-green' if abs(data['cpm']-v_cpm) < 50 else 'b-red'}">{'MATCH' if abs(data['cpm']-v_cpm) < 50 else 'ANOMALY'}</span></td>
                        </tr>
                        <tr>
                            <td><b>2. GPS Location</b></td>
                            <td>Lat: {data['lat']:.2f}...</td>
                            <td>Lat: {loc['coords']['latitude']:.2f}...</td>
                            <td><span class="badge {'b-green' if is_dist_match else 'b-red'}">{'HOME' if is_dist_match else f'AWAY ({int(dist)} KM)'}</span></td>
                        </tr>
                        <tr>
                            <td><b>3. Device Class</b></td>
                            <td>{data['dev_class']}</td>
                            <td>{v_class}</td>
                            <td><span class="badge {'b-green' if data['dev_class'] == v_class else 'b-red'}">{'MATCH' if data['dev_class'] == v_class else 'DIFF'}</span></td>
                        </tr>
                        <tr>
                            <td><b>4. OS Platform</b></td>
                            <td>{data['os']}</td>
                            <td>{v_os}</td>
                            <td><span class="badge {'b-green' if data['os'] == v_os else 'b-yellow'}">{'SAME' if data['os'] == v_os else 'DIFF'}</span></td>
                        </tr>
                        <tr>
                            <td><b>5. Browser Engine</b></td>
                            <td>{data['browser']}</td>
                            <td>{v_browser}</td>
                            <td>{'MATCH' if data['browser'] == v_browser else 'DIFF'}</td>
                        </tr>
                        <tr>
                            <td><b>6. Network IP</b></td>
                            <td>{data['ip']}</td>
                            <td>{v_ip}</td>
                            <td><span class="badge {'b-green' if is_ip_match else 'b-yellow'}">{'SAME' if is_ip_match else 'DIFF'}</span></td>
                        </tr>
                        <tr>
                            <td><b>7. Screen Res</b></td>
                            <td>{data['res']}</td>
                            <td>{v_res}</td>
                            <td>{'MATCH' if data['res'] == v_res else 'DIFF'}</td>
                        </tr>
                    </tbody>
                </table>
                """
                st.markdown(table_html, unsafe_allow_html=True)
                
                # 3. ACTIONABLE OFFER (JIKA DIBLOKIR)
                if verdict_title == "⛔ SHARING DETECTED":
                    st.markdown("### 🎯 Strategic Action (Conversion)")
                    
                    c_offer, c_churn = st.columns(2)
                    
                    with c_offer:
                        st.markdown(f'<div class="strat-card">', unsafe_allow_html=True)
                        st.write(f"**Propensity Score:** {propensity}/100")
                        
                        if propensity > 70:
                            st.error("💎 TARGET: HIGH VALUE USER")
                            st.write("Rekomendasi: **Hard Paywall (Premium)**")
                            st.button("Subscribe Premium Plan")
                        elif propensity > 40:
                            st.warning("➕ TARGET: MID VALUE USER")
                            st.write("Rekomendasi: **Add Extra Member**")
                            st.button("Add Member (+Rp20rb)")
                        else:
                            st.info("📺 TARGET: BUDGET USER")
                            st.write("Rekomendasi: **Ad-Supported Plan**")
                            st.button("Switch to Basic Ads")
                        st.markdown('</div>', unsafe_allow_html=True)

                    with c_churn:
                        st.markdown(f'<div class="strat-card">', unsafe_allow_html=True)
                        st.write("#### 🔗 Strategy 3: Social Graph")
                        st.write("Cegah pembatalan langganan dengan fitur transfer profil.")
                        st.button("📂 Transfer Profile (Save History)")
                        st.markdown('</div>', unsafe_allow_html=True)

            else:
                st.info("⏳ Waiting for GPS Signal...")
