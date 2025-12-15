import streamlit as st
import json
import os
import time
from datetime import datetime
from streamlit_js_eval import get_geolocation, streamlit_js_eval
from math import radians, cos, sin, asin, sqrt

# ==========================================
# 1. SETUP UI: CLEAN & PROFESSIONAL
# ==========================================
st.set_page_config(page_title="Netflix Bio-Forensics", page_icon="🧬", layout="wide")
DB_FILE = 'netflix_bio_db.json'

st.markdown("""
<style>
    .stApp { background-color: #FFFFFF; color: #222; }
    h1, h2, h3 { color: #E50914 !important; font-weight: 800 !important; }
    
    /* Table Styling */
    .comp-table {
        width: 100%; border-collapse: collapse; margin: 20px 0; font-size: 16px;
        box-shadow: 0 0 20px rgba(0, 0, 0, 0.1);
    }
    .comp-table thead tr { background-color: #E50914; color: #ffffff; text-align: left; }
    .comp-table th, .comp-table td { padding: 12px 15px; border-bottom: 1px solid #dddddd; }
    .comp-table tbody tr:nth-of-type(even) { background-color: #f3f3f3; }
    
    /* Input Area Styling */
    .typing-area {
        border: 2px dashed #E50914; padding: 20px; border-radius: 10px; background-color: #fff0f0; text-align: center;
    }
    .big-code { font-size: 24px; font-weight: bold; font-family: monospace; color: #333; letter-spacing: 2px; }
    
    /* Status Badges */
    .badge-ok { background-color: #d4edda; color: #155724; padding: 5px 10px; border-radius: 4px; font-weight: bold; }
    .badge-err { background-color: #f8d7da; color: #721c24; padding: 5px 10px; border-radius: 4px; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. LOGIC ENGINE
# ==========================================

def get_client_ip(key_suffix):
    return streamlit_js_eval(js_expressions='fetch("https://api.ipify.org?format=json").then(r => r.json()).then(d => d.ip)', key=f'ip_{key_suffix}')

def get_screen_width(key_suffix):
    return streamlit_js_eval(js_expressions='screen.width', key=f'sw_{key_suffix}')

def haversine(lon1, lat1, lon2, lat2):
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    a = sin((lat2-lat1)/2)**2 + cos(lat1) * cos(lat2) * sin((lon2-lon1)/2)**2
    c = 2 * asin(sqrt(a))
    return c * 6371

def calculate_cpm(text, start_time, end_time):
    """Menghitung Characters Per Minute"""
    if not start_time or not end_time: return 0
    duration = end_time - start_time
    if duration <= 0: return 0
    chars = len(text)
    cpm = (chars / duration) * 60
    return int(cpm)

# DB Utils
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
st.title("🧬 Netflix Bio-Forensics")
st.markdown("Menggabungkan **GPS**, **Network**, dan **Keystroke Dynamics (Kecepatan Ketik)**.")

data = load_db()
has_host = data is not None

# Init Session State
if 'is_host' not in st.session_state: st.session_state['is_host'] = False
if 'host_start_time' not in st.session_state: st.session_state['host_start_time'] = None
if 'vis_start_time' not in st.session_state: st.session_state['vis_start_time'] = None

with st.sidebar:
    if has_host and st.button("🔄 Reset System"):
        reset_db()
        st.session_state['is_host'] = False
        st.rerun()

# ==========================================
# FASE 1: HOST REGISTRATION (ENROLLMENT)
# ==========================================
if not has_host or (has_host and st.session_state['is_host']):
    if not has_host:
        st.subheader("1. Household Biometric Enrollment")
        st.info("Sistem akan merekam 'Kecepatan Mengetik' Anda sebagai password biometrik.")
        
        # --- BIOMETRIC RECORDER ---
        st.markdown('<div class="typing-area">', unsafe_allow_html=True)
        st.write("Frase Keamanan:")
        st.markdown('<p class="big-code">netflix secure login</p>', unsafe_allow_html=True)
        
        # Logic Timer: User klik Start -> Ketik -> Klik Save
        col_btn1, col_btn2 = st.columns([1, 4])
        
        if col_btn1.button("⏱️ START RECORDING"):
            st.session_state['host_start_time'] = time.time()
            st.toast("Timer Started! Ketik sekarang!")
        
        host_text = col_btn2.text_input("Ketik frase di atas di sini:", key="h_input")
        
        if st.checkbox("📍 Save Profile (Stop Timer & GPS)"):
            if st.session_state['host_start_time'] is None:
                st.error("Klik START dulu!")
            else:
                end_time = time.time()
                # Hitung CPM
                host_cpm = calculate_cpm(host_text, st.session_state['host_start_time'], end_time)
                
                # Validasi Teks
                if host_text.lower() != "netflix secure login":
                    st.error("❌ Teks salah! Ketik: 'netflix secure login'")
                else:
                    st.success(f"✅ Biometrik Terekam! Kecepatan: {host_cpm} CPM")
                    
                    # Ambil Sensor Lain
                    ip = get_client_ip('host')
                    width = get_screen_width('host')
                    loc = get_geolocation(component_key='gps_host')
                    
                    if loc and ip:
                        db_data = {
                            'ip': ip,
                            'cpm': host_cpm, # SIMPAN KECEPATAN ASLI
                            'res_width': width,
                            'lat': loc['coords']['latitude'],
                            'lon': loc['coords']['longitude']
                        }
                        save_db(db_data)
                        st.session_state['is_host'] = True
                        time.sleep(1)
                        st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        
    else:
        st.success("✅ HOST ACTIVE")
        st.metric("Recorded Typing Speed", f"{data['cpm']} CPM")

# ==========================================
# FASE 2: VISITOR CHALLENGE & COMPARISON
# ==========================================
else:
    st.subheader("2. Visitor Biometric Challenge")
    
    st.markdown('<div class="typing-area">', unsafe_allow_html=True)
    st.write("Silakan ketik ulang frase ini untuk verifikasi identitas:")
    st.markdown('<p class="big-code">netflix secure login</p>', unsafe_allow_html=True)
    
    c1, c2 = st.columns([1, 4])
    if c1.button("⏱️ START TYPING"):
        st.session_state['vis_start_time'] = time.time()
        st.toast("Timer Berjalan...")
        
    vis_text = c2.text_input("Ketik di sini:", key="v_input")
    
    if st.checkbox("🚀 ANALYZE & COMPARE"):
        if st.session_state['vis_start_time'] is None:
            st.error("Klik tombol START TYPING sebelum mengetik!")
            st.stop()
            
        vis_end_time = time.time()
        vis_cpm = calculate_cpm(vis_text, st.session_state['vis_start_time'], vis_end_time)
        
        # Validasi
        if vis_text.lower() != "netflix secure login":
            st.error("Teks salah. Hasil analisis tidak valid.")
            st.stop()
            
        # Ambil Sensor Visitor
        vis_ip = get_client_ip('vis')
        vis_width = get_screen_width('vis')
        loc = get_geolocation(component_key='gps_vis')
        
        if loc and vis_ip:
            # === LOGIKA PERBANDINGAN ===
            
            # 1. Analisis Biometrik (CPM)
            # Toleransi +/- 40 CPM (Manusia tidak robot, ada variasi dikit)
            cpm_diff = abs(data['cpm'] - vis_cpm)
            is_bio_match = cpm_diff < 50 
            
            bio_verdict = "✅ MATCH" if is_bio_match else "⛔ MISMATCH"
            bio_class = "badge-ok" if is_bio_match else "badge-err"
            bio_detail = f"Diff: {cpm_diff} CPM"
            
            # 2. Analisis Lokasi
            dist = haversine(data['lon'], data['lat'], loc['coords']['latitude'], loc['coords']['longitude'])
            is_dist_ok = dist < 60
            dist_verdict = "✅ HOME" if is_dist_ok else f"⛔ AWAY ({int(dist)} KM)"
            dist_class = "badge-ok" if is_dist_ok else "badge-err"
            
            # 3. Analisis Network
            is_ip_ok = (vis_ip == data['ip'])
            ip_verdict = "✅ SAME WIFI" if is_ip_ok else "⚠️ DIFF NET"
            ip_class = "badge-ok" if is_ip_ok else "badge-warn"
            
            # 4. Propensity (Kekayaan)
            propensity = 50
            if vis_width > 1500: propensity += 30 # PC/High Res
            elif vis_width < 500: propensity -= 10 # HP Low Res
            
            # === TABEL FORENSIK (THE WOW FACTOR) ===
            st.write("### 📋 Forensic & Biometric Report")
            
            html_table = f"""
            <table class="comp-table">
                <thead>
                    <tr>
                        <th>PARAMETER</th>
                        <th>🏠 HOST DATA (BASELINE)</th>
                        <th>📱 VISITOR DATA (REAL-TIME)</th>
                        <th>VERDICT</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td><b>1. Keystroke Dynamics</b><br><small>(Typing Speed)</small></td>
                        <td><b>{data['cpm']}</b> CPM</td>
                        <td><b>{vis_cpm}</b> CPM</td>
                        <td><span class="{bio_class}">{bio_verdict}</span><br><small>{bio_detail}</small></td>
                    </tr>
                    <tr>
                        <td><b>2. Physical Location</b><br><small>(GPS Coordinate)</small></td>
                        <td>Lat: {data['lat']:.2f}...</td>
                        <td>Lat: {loc['coords']['latitude']:.2f}...</td>
                        <td><span class="{dist_class}">{dist_verdict}</span></td>
                    </tr>
                    <tr>
                        <td><b>3. Network Signature</b><br><small>(Public IP)</small></td>
                        <td>{data['ip']}</td>
                        <td>{vis_ip}</td>
                        <td><span class="{ip_class}">{ip_verdict}</span></td>
                    </tr>
                </tbody>
            </table>
            """
            st.markdown(html_table, unsafe_allow_html=True)
            
            st.divider()
            
            # === KEPUTUSAN FINAL ===
            st.subheader("🤖 AI Decision Engine")
            
            # Skenario 1: Jarak Jauh + Cara Ngetik Beda (FIX SHARING)
            if not is_dist_ok and not is_bio_match:
                st.error("⛔ BLOCKED: ACCOUNT SHARING DETECTED")
                st.write("**Reason:** Lokasi jauh DAN pola biometrik (kecepatan mengetik) sangat berbeda. Ini bukan pemilik akun.")
                
                # Monetization
                if propensity > 60:
                    st.button("💎 Subscribe Premium (High Value Device)")
                else:
                    st.button("📺 Subscribe Basic with Ads")
                    
            # Skenario 2: Jarak Jauh + Cara Ngetik Sama (TRAVELING)
            elif not is_dist_ok and is_bio_match:
                st.success("✅ TRAVEL MODE APPROVED")
                st.write(f"**Reason:** Lokasi jauh, tetapi pola ketik ({vis_cpm} CPM) sangat mirip dengan Host ({data['cpm']} CPM). Pemilik sedang liburan.")
                
            # Skenario 3: Jarak Dekat (HOUSEHOLD)
            else:
                st.success("✅ HOUSEHOLD ACCESS GRANTED")
                st.write("**Reason:** Perangkat berada di lokasi rumah yang valid.")

    st.markdown('</div>', unsafe_allow_html=True)
