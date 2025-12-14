import streamlit as st
import json
import os
import requests
from datetime import datetime
from streamlit_js_eval import get_geolocation, streamlit_js_eval
from math import radians, cos, sin, asin, sqrt

# ==========================================
# 1. ENGINE & UTILS (REAL SENSORS)
# ==========================================
st.set_page_config(page_title="Netflix True Detective", page_icon="🕵️", layout="centered")
DB_FILE = 'household_signature.json'

# Fungsi Cek IP Public Asli (Bukan IP Lokal)
def get_public_ip():
    try:
        response = requests.get('https://api64.ipify.org?format=json').json()
        return response['ip']
    except:
        return "Unknown IP"

# Fungsi Parsing User Agent (Browser/Device Info)
def get_device_info(ua_string):
    if not ua_string: return "Unknown Device"
    ua = ua_string.lower()
    if "iphone" in ua: return "Apple iPhone"
    if "android" in ua: return "Android Phone"
    if "macintosh" in ua: return "MacBook"
    if "windows" in ua: return "Windows PC"
    return "Other Device"

# Hitung Jarak Fisik
def haversine(lon1, lat1, lon2, lat2):
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    a = sin((lat2-lat1)/2)**2 + cos(lat1) * cos(lat2) * sin((lon2-lon1)/2)**2
    c = 2 * asin(sqrt(a))
    return c * 6371 # KM

# Database Handler
def save_household(data):
    with open(DB_FILE, 'w') as f: json.dump(data, f)

def load_household():
    if not os.path.exists(DB_FILE): return None
    try:
        with open(DB_FILE, 'r') as f: return json.load(f)
    except: return None

# ==========================================
# 2. UI UTAMA
# ==========================================
st.title("🕵️ Netflix: Real-Time Sensor Forensics")
st.markdown("Aplikasi ini mendeteksi **IP Public**, **GPS**, dan **Device Fingerprint** asli tanpa simulasi.")

role = st.radio("Peran Perangkat Ini:", 
    ["🏠 HOST (Laptop/TV Utama)", "📱 VISITOR (HP Juri/Tamu)"], 
    horizontal=True
)

st.divider()

# ==========================================
# 3. LOGIKA HOST (DEVICE 1)
# ==========================================
if "HOST" in role:
    st.subheader("🏠 Registrasi Household (Rumah)")
    st.info("Sistem sedang memindai identitas digital perangkat ini sebagai standar 'Rumah'.")

    # --- SENSOR 1: IP PUBLIC ---
    with st.spinner("Mendeteksi Jaringan Public..."):
        real_ip = get_public_ip()
    
    # --- SENSOR 2: DEVICE FINGERPRINT ---
    raw_ua = streamlit_js_eval(js_expressions='navigator.userAgent', key='ua_host')
    device_name = get_device_info(raw_ua)

    col1, col2 = st.columns(2)
    col1.metric("IP Public (Network)", real_ip)
    col2.metric("Device Type", device_name)

    # --- SENSOR 3: GPS ---
    st.write("Klik tombol di bawah untuk mengunci lokasi rumah:")
    if st.checkbox("📍 Kunci Lokasi GPS (Asli)"):
        loc = get_geolocation(component_key='gps_host')

        if loc:
            lat = loc['coords']['latitude']
            lon = loc['coords']['longitude']
            acc = loc['coords']['accuracy']

            st.success(f"✅ Lokasi Terkunci (Akurasi: {int(acc)} meter)")
            st.map({'lat': [lat], 'lon': [lon]}, zoom=15)

            # SIMPAN DATA ASLI KE SERVER
            household_data = {
                'ip': real_ip,
                'device': device_name,
                'lat': lat,
                'lon': lon,
                'timestamp': datetime.now().timestamp(),
                'status': 'active'
            }
            save_household(household_data)
            
            st.warning("👉 Data tersimpan. JANGAN TUTUP TAB INI.")
            st.markdown("""
            **Tips Demo:** 
            Agar terdeteksi 'Anomali' di HP Juri, minta Juri **matikan WiFi** dan gunakan **Data Seluler**.
            """)

# ==========================================
# 4. LOGIKA VISITOR (DEVICE 2)
# ==========================================
else:
    st.subheader("📱 Analisis Login Tamu")
    
    household = load_household()
    
    if not household:
        st.error("❌ Host belum aktif. Silakan setup Device 1 terlebih dahulu.")
    else:
        st.write(f"Household IP: **{household['ip']}** | Device: **{household['device']}**")
        
        # --- SENSOR 1 & 2: IP & DEVICE ---
        current_ip = get_public_ip()
        raw_ua_vis = streamlit_js_eval(js_expressions='navigator.userAgent', key='ua_vis')
        current_device = get_device_info(raw_ua_vis)
        
        st.write("---")
        st.write("Silakan Login untuk validasi keamanan:")
        
        # --- SENSOR 3: GPS & PROSES ---
        if st.checkbox("🚀 Login & Scan Sensors"):
            loc_vis = get_geolocation(component_key='gps_vis')
            
            if loc_vis:
                vis_lat = loc_vis['coords']['latitude']
                vis_lon = loc_vis['coords']['longitude']
                
                # ANALISIS REAL-TIME
                is_same_ip = (current_ip == household['ip'])
                dist_km = haversine(household['lon'], household['lat'], vis_lon, vis_lat)
                
                # TAMPILAN FORENSIK
                st.write("### 🔍 Hasil Forensik Digital")
                
                # 1. Cek Network (IP)
                if is_same_ip:
                    st.success(f"✅ **Jaringan:** Cocok (Satu WiFi Rumah)\n\nIP: {current_ip}")
                else:
                    st.error(f"❌ **Jaringan:** Berbeda (Bukan Household)\n\nHost: {household['ip']} vs Kamu: {current_ip}")
                
                # 2. Cek Fisik (Jarak)
                # Jika jarak < 0.1 KM (100 meter), dianggap satu lokasi
                if dist_km < 0.1:
                    st.success(f"✅ **Lokasi:** Cocok (Satu Gedung) - Jarak: {int(dist_km*1000)} meter")
                else:
                    st.warning(f"⚠️ **Lokasi:** Berbeda Jarak {dist_km:.2f} KM")

                # KEPUTUSAN FINAL (ALGORITMA NETFLIX ASLI)
                st.divider()
                st.subheader("KEPUTUSAN SISTEM:")
                
                if is_same_ip:
                    # Skenario: Juri pakai WiFi yang sama dengan Laptop
                    st.balloons()
                    st.success("✅ **LOGIN DIIZINKAN (HOUSEHOLD MATCH)**")
                    st.write("Perangkat terhubung ke jaringan internet rumah yang sama.")
                    
                elif not is_same_ip and dist_km < 1.0:
                    # Skenario: Juri pakai 4G (Beda IP), tapi duduk di sebelah Laptop
                    st.warning("⚠️ **VERIFIKASI KODE DIBUTUHKAN (Temporary Access)**")
                    st.write("""
                    Anda berada di lokasi 'Rumah', tapi menggunakan jaringan berbeda (Data Seluler).
                    Netflix akan meminta kode OTP ke email pemilik untuk konfirmasi 'Travel Mode'.
                    """)
                    
                else:
                    # Skenario: Beda IP dan Jarak Jauh (Misal teman kamu buka di rumahnya sendiri)
                    st.error("⛔ **AKSES DIBLOKIR (SHARING DETECTED)**")
                    st.write("Terdeteksi penggunaan di luar Jaringan Rumah Tangga dan Lokasi berbeda.")
            
            else:
                st.warning("⏳ Menunggu GPS HP...")