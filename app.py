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
st.set_page_config(page_title="Netflix AI Scoring Engine", page_icon="🧠", layout="wide")
DB_FILE = 'netflix_scoring_db.json'

st.markdown("""
<style>
    .stApp { background-color: #F8F9FA; color: #212529; }
    h1, h2, h3 { color: #E50914 !important; font-weight: 800 !important; }
    
    /* SCORE CARD */
    .score-card {
        padding: 20px; border-radius: 15px; text-align: center; color: white; margin-bottom: 20px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.2);
    }
    .sc-green { background: linear-gradient(135deg, #198754, #20c997); }
    .sc-yellow { background: linear-gradient(135deg, #ffc107, #fd7e14); color: #333; }
    .sc-red { background: linear-gradient(135deg, #dc3545, #E50914); }
    
    .big-score { font-size: 48px; font-weight: bold; margin: 0; }
    .score-label { font-size: 18px; text-transform: uppercase; letter-spacing: 1px; }
    
    /* TABLE */
    .forensic-table { width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden; }
    .forensic-table th { background: #333; color: white; padding: 10px; text-align: left; }
    .forensic-table td { padding: 10px; border-bottom: 1px solid #eee; }
    
    /* PROGRESS BAR CUSTOM */
    .stProgress > div > div > div > div { background-color: #E50914; }
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

# === ALGORITMA PEMBOBOTAN (WEIGHTED SCORING) ===
def calculate_trust_score(host_data, vis_data):
    score = 0
    breakdown = []
    
    # 1. GEOLOCATION (Bobot Max: 35)
    dist = haversine(host_data['lon'], host_data['lat'], vis_data['lon'], vis_data['lat'])
    if dist < 1: score += 35      # Sangat dekat (<1 KM)
    elif dist < 20: score += 30   # Satu Kota
    elif dist < 60: score += 20   # Commuter Range
    elif dist < 200: score += 10  # Intercity Travel
    else: score += 0              # Jauh sekali
    
    # 2. BIOMETRICS / CPM (Bobot Max: 30)
    cpm_diff = abs(host_data['cpm'] - vis_data['cpm'])
    if cpm_diff < 15: score += 30       # Sangat Identik
    elif cpm_diff < 40: score += 20     # Mirip
    elif cpm_diff < 80: score += 10     # Agak beda
    else: score += 0                    # Beda orang
    
    # 3. DEVICE CONSISTENCY (Bobot Max: 25)
    # Device Class (Desktop vs Mobile) - Penting!
    if host_data['dev_class'] == vis_data['dev_class']: score += 10
    # OS Matching
    if host_data['os'] == vis_data['os']: score += 10
    # Browser Matching
    if host_data['browser'] == vis_data['browser']: score += 5
    
    # 4. NETWORK (Bobot Max: 10)
    if host_data['ip'] == vis_data['ip']: score += 10
    
    return score, dist, cpm_diff

# DB UTILS
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
# 3. APP EXECUTION
# ==========================================
st.title("🛡️ Netflix AI Scoring Engine")
st.caption("Multivariate Analysis: Location + Biometrics + Device Fingerprint")

data = load_db()
has_host = data is not None

if 'is_host' not in st.session_state: st.session_state['is_host'] = False
if 'page_load_time' not in st.session_state: st.session_state['page_load_time'] = time.time()

with st.sidebar:
    st.header("Admin")
    if has_host and st.button("🔄 Reset Data"):
        reset_db()
        st.session_state['is_host'] = False
        st.rerun()

# FASE 1: HOST
if not has_host or (has_host and st.session_state['is_host']):
    if not has_host:
        st.subheader("🏠 Host Enrollment")
        st.info("Training Baseline Model...")
        h_ip, h_sw, h_sh, h_ua = get_all_sensors('host')
        
        st.write("Ketik frase biometrik: `netflix ai`")
        h_input = st.text_input("Input:", key="h_in")
        loc = get_geolocation(component_key='gps_host')
        
        if loc and h_input == "netflix ai":
            lat = loc['coords']['latitude']
            lon = loc['coords']['longitude']
            if lat != 0:
                dur = time.time() - st.session_state['page_load_time']
                h_cpm = calculate_cpm(h_input, max(1, dur - 3))
                h_os, h_browser, h_class = parse_fingerprint(h_ua)
                
                if st.button("📍 SAVE BASELINE"):
                    save_db({
                        'ip': h_ip, 'os': h_os, 'browser': h_browser, 'dev_class': h_class,
                        'res': f"{h_sw}x{h_sh}", 'width': h_sw, 'cpm': h_cpm, 'lat': lat, 'lon': lon
                    })
                    st.session_state['is_host'] = True
                    st.rerun()
    else:
        st.success("✅ HOST MODEL READY")
        st.write(f"Baseline: {data['cpm']} CPM | {data['os']}")

# FASE 2: VISITOR SCORING
else:
    st.write("---")
    st.subheader("🕵️ Visitor Scoring Analysis")
    
    v_ip, v_sw, v_sh, v_ua = get_all_sensors('vis')
    st.write("Challenge: Ketik `netflix ai`")
    v_input = st.text_input("Passphrase:", key="v_in")
    
    if v_input:
        loc = get_geolocation(component_key='gps_vis')
        if loc:
            lat = loc['coords']['latitude']
            lon = loc['coords']['longitude']
            
            if lat != 0:
                # 1. GATHER VISITOR DATA
                dur = time.time() - st.session_state['page_load_time']
                v_cpm = calculate_cpm(v_input, max(1, dur - 3))
                v_os, v_browser, v_class = parse_fingerprint(v_ua)
                v_data = {
                    'ip': v_ip, 'os': v_os, 'browser': v_browser, 'dev_class': v_class,
                    'lat': lat, 'lon': lon, 'cpm': v_cpm
                }
                
                # 2. RUN WEIGHTED ALGORITHM
                trust_score, dist, cpm_diff = calculate_trust_score(data, v_data)
                
                # 3. DETERMINE VERDICT
                if trust_score >= 75:
                    v_class = "sc-green"
                    v_label = "✅ TRUSTED HOUSEHOLD"
                    v_msg = "Strategy 1: Instant Access"
                elif trust_score >= 45:
                    v_class = "sc-yellow"
                    v_label = "⚠️ SUSPICIOUS / TRAVEL"
                    v_msg = "Strategy 1.5: Verify with OTP"
                else:
                    v_class = "sc-red"
                    v_label = "⛔ SHARING DETECTED"
                    v_msg = "Strategy 2: Shadow Monetization"
                
                # 4. DISPLAY SCORE CARD
                st.markdown(f"""
                <div class="score-card {v_class}">
                    <p class="score-label">AI TRUST SCORE</p>
                    <p class="big-score">{trust_score}/100</p>
                    <h3>{v_label}</h3>
                    <p>{v_msg}</p>
                </div>
                """, unsafe_allow_html=True)
                
                # 5. BREAKDOWN TABEL (HOLISTIK)
                st.write("### 📊 Scoring Breakdown (Holistic Calculation)")
                
                # Logic untuk label
                loc_pts = 35 if dist<1 else 30 if dist<20 else 20 if dist<60 else 10 if dist<200 else 0
                bio_pts = 30 if cpm_diff<15 else 20 if cpm_diff<40 else 10 if cpm_diff<80 else 0
                dev_pts = (10 if data['dev_class']==v_class else 0) + (10 if data['os']==v_os else 0) + (5 if data['browser']==v_browser else 0)
                net_pts = 10 if data['ip']==v_ip else 0
                
                html_table = f"""
                <table class="forensic-table">
                    <thead>
                        <tr><th>PARAMETER</th><th>HOST VALUE</th><th>VISITOR VALUE</th><th>DELTA</th><th>POINTS EARNED</th></tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td><b>📍 Geolocation</b> (Max 35)</td>
                            <td>Lat: {data['lat']:.2f}</td>
                            <td>Lat: {lat:.2f}</td>
                            <td>{int(dist)} KM</td>
                            <td><b>+{loc_pts}</b></td>
                        </tr>
                        <tr>
                            <td><b>🧬 Biometrics</b> (Max 30)</td>
                            <td>{data['cpm']} CPM</td>
                            <td>{v_cpm} CPM</td>
                            <td>Diff: {int(cpm_diff)}</td>
                            <td><b>+{bio_pts}</b></td>
                        </tr>
                        <tr>
                            <td><b>📱 Device DNA</b> (Max 25)</td>
                            <td>{data['os']}</td>
                            <td>{v_os}</td>
                            <td>Match: {data['os']==v_os}</td>
                            <td><b>+{dev_pts}</b></td>
                        </tr>
                        <tr>
                            <td><b>🌐 Network</b> (Max 10)</td>
                            <td>{data['ip']}</td>
                            <td>{v_ip}</td>
                            <td>Match: {data['ip']==v_ip}</td>
                            <td><b>+{net_pts}</b></td>
                        </tr>
                        <tr style="background:#eee; font-weight:bold;">
                            <td colspan="4" style="text-align:right;">TOTAL WEIGHTED SCORE:</td>
                            <td style="font-size:18px;">{trust_score}/100</td>
                        </tr>
                    </tbody>
                </table>
                """
                st.markdown(html_table, unsafe_allow_html=True)
                
                # 6. ACTION (Jika Score Rendah)
                if trust_score < 45:
                    st.error("📉 Score too low. Analyzing Propensity to Pay...")
                    propensity = 50
                    if v_sw > 1500 or "Mac" in v_os or "iOS" in v_os: propensity += 30
                    if "Android" in v_os: propensity -= 10
                    
                    c1, c2 = st.columns(2)
                    c1.metric("Device Wealth Score", f"{propensity}/100")
                    if propensity > 70: c2.button("💎 Offer Premium (High Value)")
                    else: c2.button("📺 Offer Ads Plan (Budget)")
                    
        else:
            st.warning("⏳ Menunggu GPS...")
