import streamlit as st
import json
import os
import time
from datetime import datetime
from streamlit_js_eval import get_geolocation, streamlit_js_eval
from math import radians, cos, sin, asin, sqrt

# ==========================================
# 1. SETUP UI & TEMA (HIGH CONTRAST FIX)
# ==========================================
st.set_page_config(page_title="Netflix Strategic Guard", page_icon="🛡️", layout="wide")
DB_FILE = 'netflix_ultimate_db.json'

# CSS KETAT: Memaksa Background Hitam & Teks Putih agar tidak "Ga Jelas"
st.markdown("""
<style>
    /* Paksa Background Hitam Pekat */
    .stApp {
        background-color: #000000 !important;
        color: #ffffff !important;
    }
    
    /* Perbaikan Warna Input Box & Selectbox */
    .stTextInput > div > div > input, .stSelectbox > div > div > div {
        background-color: #333333 !important;
        color: white !important;
        border: 1px solid #555 !important;
    }
    
    /* Judul & Header */
    h1, h2, h3 { color: #E50914 !important; font-weight: 800 !important; }
    h4, h5, h6 { color: #ffffff !important; }
    p, label { color: #e0e0e0 !important; }
    
    /* Card Custom untuk Hasil */
    .metric-card {
        background-color: #141414;
        border: 1px solid #333;
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 10px;
    }
    .status-ok { color: #46d369; font-weight: bold; }
    .status-warn { color: #ffa00a; font-weight: bold; }
    .status-err { color: #E50914; font-weight: bold; }
    
    /* Tombol */
    .stButton > button {
        background-color: #E50914 !important;
        color: white !important;
        border: none !important;
        font-weight: bold !important;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. ENGINE: SENSORS & LOGIC
# ==========================================

# --- A. SENSOR CLIENT-SIDE (JS) ---
def get_client_full_details(key_suffix):
    # 1. IP Address
    ip = streamlit_js_eval(js_expressions='fetch("https://api.ipify.org?format=json").then(r => r.json()).then(d => d.ip)', key=f'ip_{key_suffix}')
    # 2. Screen Resolution (Hardware Fingerprint)
    sw = streamlit_js_eval(js_expressions='screen.width', key=f'sw_{key_suffix}')
    sh = streamlit_js_eval(js_expressions='screen.height', key=f'sh_{key_suffix}')
    # 3. User Agent (OS & Browser)
    ua = streamlit_js_eval(js_expressions='navigator.userAgent', key=f'ua_{key_suffix}')
    
    return ip, sw, sh, ua

def parse_fingerprint(ua):
    if not ua: return "Unknown", "Unknown"
    ua = ua.lower()
    
    # Deteksi OS
    os_name = "Other"
    if "windows" in ua: os_name = "Windows PC"
    elif "macintosh" in ua: os_name = "MacBook/iMac"
    elif "iphone" in ua: os_name = "iPhone iOS"
    elif "android" in ua: os_name = "Android Mobile"
    elif "linux" in ua: os_name = "Linux"
    
    # Deteksi Browser
    browser = "Other"
    if "edg" in ua: browser = "Edge"
    elif "chrome" in ua: browser = "Chrome"
    elif "safari" in ua: browser = "Safari"
    elif "firefox" in ua: browser = "Firefox"
    
    return os_name, browser

def calculate_propensity(os_name, width):
    """Menghitung Kekayaan Device (Willingness to Pay)"""
    score = 50 # Baseline
    # Hardware Premium
    if "Mac" in os_name or "iPhone" in os_name: score += 30
    if width and width > 1900: score += 15 # Layar Resolusi Tinggi
    # Hardware Entry Level
    if "Android" in os_name: score -= 10
    if width and width < 1300: score -= 5
    
    return max(0, min(100, score))

def haversine(lon1, lat1, lon2, lat2):
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    a = sin((lat2-lat1)/2)**2 + cos(lat1) * cos(lat2) * sin((lon2-lon1)/2)**2
    c = 2 * asin(sqrt(a))
    return c * 6371

# --- DATABASE ---
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
# 3. LOGIKA APLIKASI UTAMA
# ==========================================
st.title("🛡️ Netflix AI: Forensic & Monetization")
st.markdown("Integrasi **5-Parameter Forensik** dengan **AI Monetization Strategy**.")

data = load_db()
has_host = data is not None

# Session State
if 'is_host' not in st.session_state: st.session_state['is_host'] = False

# Sidebar Reset
with st.sidebar:
    st.header("⚙️ Admin Panel")
    if has_host:
        if st.button("🔴 RESET SYSTEM"):
            reset_db()
            st.session_state['is_host'] = False
            st.rerun()

st.write("---")

# ==========================================
# FASE 1: HOST REGISTRATION (ANCHOR)
# ==========================================
if not has_host or (has_host and st.session_state['is_host']):
    if not has_host:
        st.subheader("🏠 HOST REGISTRATION")
        st.info("Langkah 1: Daftarkan Perangkat Rumah Utama (Household Anchor).")
    else:
        st.success("✅ HOST ACTIVE (Household Master)")
        # Tampilkan Data Host dalam Card
        st.markdown(f"""
        <div class="metric-card">
            <h4>📡 Household DNA</h4>
            <p><b>IP:</b> {data['ip']}</p>
            <p><b>Device:</b> {data['os']} / {data['browser']}</p>
            <p><b>Resolution:</b> {data['res']}</p>
            <p><b>Location:</b> {data['lat']:.4f}, {data['lon']:.4f}</p>
        </div>
        """, unsafe_allow_html=True)

    # 1. SCAN SENSORS
    h_ip, h_sw, h_sh, h_ua = get_client_full_details('host')

    if not has_host:
        if h_ip:
            h_os, h_browser = parse_fingerprint(h_ua)
            st.write(f"Detected: **{h_os}** using **{h_browser}** on **{h_sw}x{h_sh}**")
            
            # 2. LOCK GPS
            if st.checkbox("📍 Lock GPS & Register Household"):
                loc = get_geolocation(component_key='gps_host')
                
                if loc:
                    # Simpan 5 Parameter Inti
                    db_data = {
                        'ip': h_ip,
                        'os': h_os,
                        'browser': h_browser,
                        'res': f"{h_sw}x{h_sh}",
                        'width': h_sw, # Simpan width angka untuk scoring nanti
                        'lat': loc['coords']['latitude'],
                        'lon': loc['coords']['longitude'],
                        'timestamp': datetime.now().timestamp()
                    }
                    save_db(db_data)
                    st.session_state['is_host'] = True
                    st.rerun()
                else:
                    st.warning("⏳ Waiting for GPS signal...")
        else:
            st.info("⏳ Scanning Host Fingerprint...")

# ==========================================
# FASE 2: VISITOR ANALYSIS (STRATEGI LENGKAP)
# ==========================================
else:
    st.subheader("🕵️ VISITOR LOGIN & ANALYSIS")
    st.write("Login tamu akan dianalisis menggunakan **5 Parameter Forensik** + **AI Propensity Model**.")
    
    # 1. SCAN SENSORS VISITOR
    v_ip, v_sw, v_sh, v_ua = get_client_full_details('vis')
    
    if st.checkbox("🚀 LOGIN & ANALYZE NOW"):
        if not v_ip:
            st.warning("⏳ Scanning Device... (Please wait)")
            st.stop()
            
        loc = get_geolocation(component_key='gps_vis')
        
        if loc:
            # === ENGINE ANALISIS ===
            
            # A. Parsing Data
            v_os, v_browser = parse_fingerprint(v_ua)
            v_res = f"{v_sw}x{v_sh}"
            v_lat = loc['coords']['latitude']
            v_lon = loc['coords']['longitude']
            
            # B. 5 PARAMETER FORENSIC CHECK
            risk_score = 0
            log_anomalies = []
            
            # 1. Jarak (Bobot 50 - Paling Fatal)
            dist = haversine(data['lon'], data['lat'], v_lon, v_lat)
            if dist > 60:
                risk_score += 50
                dist_status = "⛔ JAUH"
                log_anomalies.append("Lokasi di luar jangkauan rumah tangga")
            else:
                dist_status = "✅ DEKAT"

            # 2. IP Address (Bobot 20)
            if v_ip != data['ip']:
                risk_score += 20
                ip_status = "⚠️ BEDA"
                log_anomalies.append("Jaringan (IP) berbeda")
            else:
                ip_status = "✅ SAMA"
            
            # 3. OS Platform (Bobot 10)
            if v_os != data['os']:
                risk_score += 10
                os_status = "⚠️ BEDA"
            else:
                os_status = "✅ SAMA"

            # 4. Browser (Bobot 5)
            if v_browser != data['browser']:
                risk_score += 5
                br_status = "⚠️ BEDA"
            else:
                br_status = "✅ SAMA"

            # 5. Screen Res (Bobot 5)
            if v_res != data['res']:
                risk_score += 5
                res_status = "⚠️ BEDA"
            else:
                res_status = "✅ SAMA"

            # C. AI PROPENSITY SCORING (KEKAYAAN DEVICE)
            propensity_score = calculate_propensity(v_os, v_sw)
            
            # ==========================================
            # D. TAMPILAN HASIL (UI RAPI)
            # ==========================================
            st.divider()
            
            col_res1, col_res2 = st.columns(2)
            
            with col_res1:
                st.markdown("### 📊 5-Layer Forensic Match")
                st.markdown(f"""
                <div class="metric-card">
                    <p>1. <b>Distance:</b> {dist:.1f} KM ({dist_status})</p>
                    <p>2. <b>IP Addr:</b> {v_ip} ({ip_status})</p>
                    <p>3. <b>OS System:</b> {v_os} ({os_status})</p>
                    <p>4. <b>Browser:</b> {v_browser} ({br_status})</p>
                    <p>5. <b>Resolution:</b> {v_res} ({res_status})</p>
                    <hr style="border-color: #333;">
                    <h3 style="color: {'#E50914' if risk_score >= 50 else '#46d369'} !important;">
                        RISK SCORE: {risk_score}/100
                    </h3>
                </div>
                """, unsafe_allow_html=True)
                
            with col_res2:
                st.markdown("### 🧠 AI Propensity Insight")
                wealth_level = "High Value" if propensity_score > 70 else "Mid Value" if propensity_score > 40 else "Budget"
                st.markdown(f"""
                <div class="metric-card">
                    <p><b>Device Value:</b> {wealth_level}</p>
                    <p><b>Prediction:</b> {propensity_score}/100 (Willingness to Pay)</p>
                    <p><b>Behavior Match:</b> {'✅ High' if risk_score < 30 else '⚠️ Low'}</p>
                </div>
                """, unsafe_allow_html=True)

            # ==========================================
            # E. FINAL STRATEGIC DECISION
            # ==========================================
            st.subheader("🎯 FINAL SYSTEM ACTION")
            
            # SKENARIO 1: AMAN (Risk < 30)
            if risk_score < 30:
                st.markdown("""
                <div style="background-color: #155724; padding: 20px; border-radius: 10px;">
                    <h2 style="color: white !important; margin:0;">✅ ACCESS GRANTED</h2>
                    <p style="margin:0;">User valid. Tidak ada friksi yang diberikan.</p>
                </div>
                """, unsafe_allow_html=True)
                
            # SKENARIO 2: SOFT BLOCK (Risk 30-50) -> Minta OTP
            elif risk_score < 60:
                st.markdown("""
                <div style="background-color: #856404; padding: 20px; border-radius: 10px;">
                    <h2 style="color: white !important; margin:0;">⚠️ VERIFY DEVICE (2FA)</h2>
                    <p style="margin:0;">Terdeteksi device/jaringan baru di lokasi yang wajar. Kirim kode OTP.</p>
                </div>
                """, unsafe_allow_html=True)
                
            # SKENARIO 3: HARD BLOCK (Risk > 60) -> MONETISASI!
            else:
                st.markdown(f"""
                <div style="background-color: #721c24; padding: 20px; border-radius: 10px; margin-bottom: 20px;">
                    <h2 style="color: white !important; margin:0;">⛔ SHARING DETECTED</h2>
                    <p style="margin:0;">Aktivitas mencurigakan (Jarak Jauh + Device Beda).</p>
                </div>
                """, unsafe_allow_html=True)
                
                # WATERFALL OFFERING BERDASARKAN PROPENSITY
                st.write("🤖 **AI Recommendation Engine:**")
                
                if propensity_score > 70:
                    # ORANG KAYA -> Sikat Full Price
                    st.button("💎 OFFER: PREMIUM PLAN (Full Price)")
                    st.caption("Target: High Value Device (iPhone/Mac). Upsell to Premium.")
                    
                elif propensity_score > 40:
                    # KELAS MENENGAH -> Tawarkan Add Member
                    st.button("➕ OFFER: EXTRA MEMBER (Discounted)")
                    st.caption("Target: Mid Range Device. Cegah churn dengan harga teman.")
                    
                else:
                    # BUDGET -> Tawarkan Iklan
                    st.button("📺 OFFER: BASIC WITH ADS")
                    st.caption("Target: Budget Device. Monetisasi lewat Iklan.")
                    
        else:
            st.warning("⏳ Waiting for GPS...")
