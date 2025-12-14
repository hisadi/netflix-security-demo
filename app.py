import streamlit as st
import json
import os
import requests
from datetime import datetime
from streamlit_js_eval import get_geolocation, streamlit_js_eval
from math import radians, cos, sin, asin, sqrt

# ==========================================
# 1. SETUP DATABASE & UTILS
# ==========================================
st.set_page_config(page_title="Netflix Security Guard", page_icon="🔐", layout="centered")
DB_FILE = 'netflix_secure_db.json'

def get_public_ip():
    try:
        response = requests.get('https://api64.ipify.org?format=json', timeout=3).json()
        return response['ip']
    except:
        return "Unknown IP"

def get_device_info(ua_string):
    if not ua_string: return "Unknown Device"
    ua = ua_string.lower()
    if "iphone" in ua: return "Apple iPhone"
    if "android" in ua: return "Android Phone"
    if "macintosh" in ua: return "MacBook"
    if "windows" in ua: return "Windows PC"
    return "Other Device"

def haversine(lon1, lat1, lon2, lat2):
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    a = sin((lat2-lat1)/2)**2 + cos(lat1) * cos(lat2) * sin((lon2-lon1)/2)**2
    c = 2 * asin(sqrt(a))
    return c * 6371

# === DATABASE MANAGER ===
def load_household():
    if not os.path.exists(DB_FILE): return None
    try:
        with open(DB_FILE, 'r') as f: return json.load(f)
    except: return None

def save_household(data):
    with open(DB_FILE, 'w') as f: json.dump(data, f)

def reset_system():
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)

# ==========================================
# 2. LOGIKA KONTROL AKSES (PENTING!)
# ==========================================
household_data = load_household()
host_exists = household_data is not None

# Cek Session State untuk mengetahui apakah browser INI adalah Host yang aktif
if 'is_host_session' not in st.session_state:
    st.session_state['is_host_session'] = False

st.title("🔐 Netflix Household Security")

# ==========================================
# 3. AREA SISTEM (LOGOUT / STATUS)
# ==========================================
if host_exists:
    st.info(f"🏠 **SYSTEM LOCKED:** Rumah Tangga aktif oleh perangkat **{household_data['device']}**.")
    
    # Tombol Logout Khusus Host (Atau Admin Demo)
    # Trik: Kita tampilkan tombol reset di sidebar agar Juri tidak sengaja klik, tapi Anda bisa klik.
    with st.sidebar:
        st.header("Admin / Host Controls")
        if st.button("⚠️ LOGOUT & RESET SYSTEM"):
            reset_system()
            st.session_state['is_host_session'] = False
            st.rerun()
else:
    st.success("🟢 **SYSTEM READY:** Belum ada Host. Silakan daftar.")

st.divider()

# ==========================================
# 4. PEMILIHAN PERAN (OTOMATIS)
# ==========================================

# Jika Host SUDAH ADA, dan saya BUKAN host sesi ini -> Paksa jadi VISITOR
if host_exists and not st.session_state['is_host_session']:
    role = "📱 VISITOR (Tamu/Juri)"
    st.write("👉 *Mode Host dikunci karena sudah ada Host aktif.*")

# Jika Host SUDAH ADA, dan saya ADALAH host sesi ini -> Tampilkan Panel Host
elif host_exists and st.session_state['is_host_session']:
    role = "🏠 HOST (Owner Dashboard)"

# Jika BELUM ADA Host -> Izinkan memilih
else:
    role = st.radio("Pilih Peran:", ["🏠 HOST (Daftar Rumah)", "📱 VISITOR (Tamu)"])

# ==========================================
# 5. LOGIKA HOST (PENDAFTARAN)
# ==========================================
if "HOST" in role:
    st.subheader("🏠 Dashboard Pemilik Rumah")
    
    # Jika sudah terdaftar, tampilkan data saja
    if host_exists:
        st.write(f"**IP Terdaftar:** {household_data['ip']}")
        st.write(f"**Lokasi Terdaftar:** {household_data['lat']}, {household_data['lon']}")
        st.success("✅ Sistem Keamanan Aktif. Menunggu tamu login...")
    
    # Jika belum terdaftar (Baru mau daftar)
    else:
        st.write("Sistem akan merekam jejak digital perangkat ini sebagai 'Master Household'.")
        
        # Sensor Data
        with st.spinner("Mendeteksi Jaringan..."):
            my_ip = get_public_ip()
        
        raw_ua = streamlit_js_eval(js_expressions='navigator.userAgent', key='ua_host')
        my_device = get_device_info(raw_ua)
        
        col1, col2 = st.columns(2)
        col1.metric("IP Public", my_ip)
        col2.metric("Device", my_device)
        
        # Tombol Kunci Lokasi
        if st.checkbox("📍 Kunci Lokasi GPS & Aktifkan Host"):
            loc = get_geolocation(component_key='gps_host')
            
            if loc:
                lat = loc['coords']['latitude']
                lon = loc['coords']['longitude']
                
                # SIMPAN DATA
                new_data = {
                    'ip': my_ip,
                    'device': my_device,
                    'lat': lat,
                    'lon': lon,
                    'created_at': datetime.now().strftime("%H:%M:%S")
                }
                save_household(new_data)
                
                # Tandai sesi browser ini sebagai Host
                st.session_state['is_host_session'] = True
                st.rerun() # Refresh agar UI terkunci
            else:
                st.warning("Menunggu GPS...")

# ==========================================
# 6. LOGIKA VISITOR (JURI)
# ==========================================
elif "VISITOR" in role:
    st.subheader("📱 Analisis Login Tamu")
    
    if not host_exists:
        st.warning("⚠️ Belum ada Host yang terdaftar. Harap setup Device 1 dahulu.")
    else:
        # Load data host untuk perbandingan
        host_data = load_household()
        
        st.markdown(f"""
        Menghubungkan ke Household:
        - **Host Device:** {host_data['device']}
        - **Sejak:** {host_data['created_at']}
        """)
        
        # --- DETEKSI DEVICE JURI ---
        my_ip = get_public_ip()
        raw_ua = streamlit_js_eval(js_expressions='navigator.userAgent', key='ua_vis')
        my_device = get_device_info(raw_ua)
        
        st.write("---")
        st.info("Silakan Login. Sistem akan memvalidasi posisi & jaringan Anda.")
        
        if st.button("🚀 LOGIN SEKARANG (Scan GPS & IP)"):
            loc = get_geolocation(component_key='gps_vis')
            
            # Note: get_geolocation butuh rerender kadang-kadang, 
            # untuk UX lebih baik pakai checkbox agar state tidak hilang saat rerender
            st.warning("⚠️ Klik sekali lagi checkbox di bawah untuk konfirmasi GPS 👇")
            
        if st.checkbox("✅ Konfirmasi Login & GPS"):
            loc = get_geolocation(component_key='gps_vis_confirm')
            
            if loc:
                lat = loc['coords']['latitude']
                lon = loc['coords']['longitude']
                
                # 1. Analisis Jarak
                dist = haversine(host_data['lon'], host_data['lat'], lon, lat)
                
                # 2. Analisis IP
                same_ip = (my_ip == host_data['ip'])
                
                # TAMPILAN HASIL
                st.divider()
                st.write("### 🕵️ Hasil Audit Keamanan")
                
                c1, c2 = st.columns(2)
                c1.metric("Status Jarak", f"{dist:.2f} KM", delta_color="inverse" if dist > 1 else "normal")
                c2.metric("Status IP", "Sama" if same_ip else "Beda", delta_color="normal" if same_ip else "inverse")
                
                # LOGIKA KEPUTUSAN FINAL
                if same_ip:
                    st.balloons()
                    st.success("✅ **LOGIN SUKSES (Household Valid)**\n\nBukan akses mencurigakan.")
                elif dist < 0.5: # Kurang dari 500 meter
                    st.warning("⚠️ **VERIFIKASI OTP (Soft Block)**\n\nLokasi cocok, tapi jaringan berbeda (Data Seluler).")
                else:
                    st.error("⛔ **BLOKIR: IMPOSSIBLE SHARING**\n\nLokasi jauh & Jaringan berbeda. Indikasi Sharing Ilegal.")
            else:
                st.write("⏳ Menunggu sinyal GPS...")

