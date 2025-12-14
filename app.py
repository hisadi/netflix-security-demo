import streamlit as st
import json
import os
import time
from datetime import datetime
from streamlit_js_eval import get_geolocation, streamlit_js_eval
from math import radians, cos, sin, asin, sqrt

# ==========================================
# 1. SETUP & ALGORITMA SKORING
# ==========================================
st.set_page_config(page_title="Netflix Forensic Core", page_icon="🕵️", layout="wide")
DB_FILE = 'netflix_fingerprint_db.json'

# --- Client-Side Javascript Injector ---
def get_client_details(key_suffix):
    # Mengambil IP
    ip = streamlit_js_eval(js_expressions='fetch("https://api.ipify.org?format=json").then(r => r.json()).then(d => d.ip)', key=f'ip_{key_suffix}')
    # Mengambil Resolusi Layar (Fingerprint Hardware)
    screen_w = streamlit_js_eval(js_expressions='screen.width', key=f'sw_{key_suffix}')
    screen_h = streamlit_js_eval(js_expressions='screen.height', key=f'sh_{key_suffix}')
    # Mengambil User Agent (OS & Browser)
    ua = streamlit_js_eval(js_expressions='navigator.userAgent', key=f'ua_{key_suffix}')
    return ip, screen_w, screen_h, ua

def parse_ua(ua):
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
    if "chrome" in ua and "edg" not in ua: browser = "Google Chrome"
    elif "safari" in ua and "chrome" not in ua: browser = "Safari"
    elif "firefox" in ua: browser = "Firefox"
    elif "edg" in ua: browser = "Microsoft Edge"
    
    return os_name, browser

def haversine(lon1, lat1, lon2, lat2):
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    a = sin((lat2-lat1)/2)**2 + cos(lat1) * cos(lat2) * sin((lon2-lon1)/2)**2
    c = 2 * asin(sqrt(a))
    return c * 6371

# Database Utils
def load_db():
    if not os.path.exists(DB_FILE): return None
    try:
        with open(DB_FILE, 'r') as f: return json.load(f)
    except: return None

def save_db(data):
    with open(DB_FILE, 'w') as f: json.dump(data, f)

def reset_db():
    if os.path.exists(DB_FILE): os.remove(DB_FILE)

# ==========================================
# 2. HEADER & CONTROL PANEL
# ==========================================
st.title("🕵️ Netflix: 5-Layer Forensic Detection")
st.markdown("**Parameters:** 1. GPS Distance | 2. IP Network | 3. OS Platform | 4. Browser | 5. Screen Res")

data = load_db()
has_host = data is not None

# Session Host Check
if 'is_host' not in st.session_state: st.session_state['is_host'] = False

# Sidebar Reset
if has_host:
    with st.sidebar:
        st.error("Admin Zone")
        if st.button("☢️ RESET SYSTEM"):
            reset_db()
            st.session_state['is_host'] = False
            st.rerun()

st.divider()

# ==========================================
# 3. LOGIKA HOST (REGISTRASI FINGERPRINT)
# ==========================================
if not has_host or (has_host and st.session_state['is_host']):
    if not has_host:
        st.subheader("🏠 HOST REGISTRATION (Household Master)")
        st.info("Sistem akan merekam 'Digital Fingerprint' perangkat ini sebagai standar rumah.")
    else:
        st.success("🏠 HOST DASHBOARD (Active)")
        st.json(data) # Tampilkan data mentah untuk bukti ke juri

    # --- PENGAMBILAN DATA SENSOR HOST ---
    # Kita butuh mengambil data browser host secara real-time
    h_ip, h_sw, h_sh, h_ua = get_client_details('host')
    
    if not has_host:
        # Tampilkan Preview Data sebelum simpan
        if h_ip and h_ua:
            h_os, h_browser = parse_ua(h_ua)
            
            c1, c2, c3 = st.columns(3)
            c1.metric("Network IP", h_ip)
            c2.metric("OS Platform", h_os)
            c3.metric("Screen Res", f"{h_sw} x {h_sh}")
            
            if st.checkbox("📍 LOCK GPS & REGISTER FINGERPRINT"):
                loc = get_geolocation(component_key='gps_host')
                if loc:
                    db_data = {
                        'ip': h_ip,
                        'os': h_os,
                        'browser': h_browser,
                        'res': f"{h_sw}x{h_sh}",
                        'lat': loc['coords']['latitude'],
                        'lon': loc['coords']['longitude'],
                        'timestamp': datetime.now().timestamp()
                    }
                    save_db(db_data)
                    st.session_state['is_host'] = True
                    st.rerun()
                else:
                    st.warning("Menunggu GPS...")
        else:
            st.write("⏳ Scanning Device Fingerprint...")

# ==========================================
# 4. LOGIKA VISITOR (JURI / LOGIN BARU)
# ==========================================
else:
    st.subheader("📱 VISITOR LOGIN (Forensic Analysis)")
    st.write("Sistem akan membandingkan 5 Parameter perangkat Anda dengan Host.")
    
    # --- PENGAMBILAN DATA SENSOR VISITOR ---
    v_ip, v_sw, v_sh, v_ua = get_client_details('vis')
    
    if st.checkbox("🚀 LOGIN & START SCANNING"):
        if not v_ip:
            st.warning("⏳ Mengambil data device (IP/Screen/OS)...")
            st.stop()
            
        loc = get_geolocation(component_key='gps_vis')
        
        if loc:
            # 1. Parsing Data Visitor
            v_os, v_browser = parse_ua(v_ua)
            v_res = f"{v_sw}x{v_sh}"
            v_lat = loc['coords']['latitude']
            v_lon = loc['coords']['longitude']
            
            # 2. KOMPARASI & SCORING (ALGORITMA UTAMA)
            score = 0
            log = []
            
            # Param 1: JARAK (Bobot Terbesar: 50)
            dist = haversine(data['lon'], data['lat'], v_lon, v_lat)
            if dist > 60:
                score += 50
                dist_status = "⛔ JAUH"
                log.append(f"CRITICAL: Jarak {dist:.0f} KM (Luar Rumah)")
            else:
                dist_status = "✅ DEKAT"
            
            # Param 2: IP (Bobot: 20)
            if v_ip != data['ip']:
                score += 20
                ip_status = "⚠️ BEDA"
                log.append("WARN: IP Network Berbeda")
            else:
                ip_status = "✅ SAMA"
                
            # Param 3: OS (Bobot: 15)
            if v_os != data['os']:
                score += 15
                os_status = "⚠️ BEDA"
                log.append(f"INFO: OS Berbeda ({data['os']} vs {v_os})")
            else:
                os_status = "✅ SAMA"
                
            # Param 4: Browser (Bobot: 10)
            if v_browser != data['browser']:
                score += 10
                br_status = "⚠️ BEDA"
            else:
                br_status = "✅ SAMA"
                
            # Param 5: Resolusi Layar (Bobot: 5)
            if v_res != data['res']:
                score += 5
                res_status = "⚠️ BEDA"
            else:
                res_status = "✅ SAMA"
            
            # --- TAMPILAN DASHBOARD ---
            st.divider()
            st.write("### 📊 Laporan Forensik Real-Time")
            
            # Tabel Perbandingan
            col_h, col_v = st.columns(2)
            with col_h:
                st.info("🏠 DATA HOST (RUMAH)")
                st.write(f"**IP:** {data['ip']}")
                st.write(f"**OS:** {data['os']}")
                st.write(f"**Layar:** {data['res']}")
                st.write(f"**Lokasi:** {data['lat']:.4f}, {data['lon']:.4f}")
            
            with col_v:
                st.warning("📱 DATA ANDA (VISITOR)")
                st.write(f"**IP:** {v_ip} ({ip_status})")
                st.write(f"**OS:** {v_os} ({os_status})")
                st.write(f"**Layar:** {v_res} ({res_status})")
                st.write(f"**Jarak:** {dist:.1f} KM ({dist_status})")
            
            st.divider()
            
            # --- HASIL KEPUTUSAN BERDASARKAN SKOR ---
            st.metric("TOTAL RISK SCORE", f"{score} / 100")
            
            if score >= 50:
                st.error("⛔ **AKSES DIBLOKIR (SHARING DETECTED)**")
                st.write("**Analisis:** Skor risiko terlalu tinggi. Indikasi kuat perangkat asing di lokasi berbeda.")
                with st.expander("Lihat Detail Pelanggaran"):
                    for l in log: st.write(f"- {l}")
                    
            elif score >= 20:
                st.warning("⚠️ **VERIFIKASI OTP (Device/Network Baru)**")
                st.write("**Analisis:** Lokasi aman, tetapi menggunakan Device atau Network baru. Perlu verifikasi kepemilikan.")
                
            else:
                st.balloons()
                st.success("✅ **LOGIN SUKSES (Household Verified)**")
                st.write("**Analisis:** Profil perangkat dan lokasi sangat identik dengan pemilik rumah.")
                
        else:
            st.warning("Menunggu GPS...")
