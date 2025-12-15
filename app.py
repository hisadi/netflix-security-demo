import streamlit as st
import json
import os
import time
import pandas as pd
from datetime import datetime
from streamlit_js_eval import get_geolocation, streamlit_js_eval
from math import radians, cos, sin, asin, sqrt

# ==========================================
# 1. SETUP UI: SESUAI INFOGRAFIS PPT
# ==========================================
st.set_page_config(page_title="Strategic AI Monetization", page_icon="📊", layout="wide")
DB_FILE = 'netflix_ppt_db.json'

# Styling agar mirip Dashboard Analytics profesional
st.markdown("""
<style>
    .stApp { background-color: #F5F7F8; color: #333; }
    h1, h2, h3 { color: #E50914 !important; font-weight: 800 !important; }
    
    /* Box Strategi */
    .strat-box {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 20px;
        border-left: 5px solid #E50914;
    }
    
    /* Tabel Parameter */
    .param-table {
        width: 100%; border-collapse: collapse; font-size: 14px;
    }
    .param-table td { padding: 8px; border-bottom: 1px solid #eee; }
    .param-label { font-weight: bold; color: #555; }
    
    /* Badges */
    .risk-high { color: white; background: #dc3545; padding: 2px 8px; border-radius: 4px; font-size: 12px; }
    .risk-low { color: white; background: #28a745; padding: 2px 8px; border-radius: 4px; font-size: 12px; }
    
    /* Input Area */
    .input-hidden { opacity: 0; position: absolute; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. LOGIC ENGINE (ALL PARAMETERS)
# ==========================================

# --- A. SENSORS (JS) ---
def get_sensors(key_suffix):
    ip = streamlit_js_eval(js_expressions='fetch("https://api.ipify.org?format=json").then(r => r.json()).then(d => d.ip)', key=f'ip_{key_suffix}')
    sw = streamlit_js_eval(js_expressions='screen.width', key=f'sw_{key_suffix}')
    ua = streamlit_js_eval(js_expressions='navigator.userAgent', key=f'ua_{key_suffix}')
    return ip, sw, ua

# --- B. FINGERPRINT PARSER ---
def parse_device(ua):
    if not ua: return "Unknown", "Unknown"
    ua = ua.lower()
    os_name = "Windows" if "windows" in ua else "Mac/iOS" if "mac" in ua or "iphone" in ua else "Android" if "android" in ua else "Linux"
    browser = "Chrome" if "chrome" in ua else "Safari" if "safari" in ua else "Firefox"
    return os_name, browser

# --- C. SCORING MODELS (SESUAI PPT) ---

def calculate_trust_score(dist, ip_match, bio_match, os_match):
    """
    STRATEGY 1: ADAPTIVE TRUST MODEL
    Menghitung seberapa percaya kita bahwa ini adalah User Asli.
    """
    score = 0
    # 1. Lokasi (Bobot 40%)
    if dist < 50: score += 40
    # 2. Network (Bobot 20%)
    if ip_match: score += 20
    # 3. Biometrik/Perilaku (Bobot 25%) - CPM Match
    if bio_match: score += 25
    # 4. Device Consistency (Bobot 15%)
    if os_match: score += 15
    
    return score

def calculate_propensity_score(os_name, width):
    """
    STRATEGY 2: PROPENSITY TO PAY MODEL
    Menghitung kekayaan user berdasarkan device (Shadow Monetization).
    """
    score = 50 # Baseline
    # Hardware Premium Indicators
    if "Mac" in os_name or "iOS" in os_name: score += 30
    if width and width > 1600: score += 20
    # Budget Indicators
    if "Android" in os_name: score -= 10
    
    return max(0, min(100, score))

def haversine(lon1, lat1, lon2, lat2):
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    a = sin((lat2-lat1)/2)**2 + cos(lat1) * cos(lat2) * sin((lon2-lon1)/2)**2
    c = 2 * asin(sqrt(a))
    return c * 6371

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
# 3. UI DASHBOARD
# ==========================================
st.title("📊 Strategic AI Solution: Monetizing Credential")
st.markdown("Implementasi Real-Time dari strategi: **Detect (Advanced AI)** & **Convert (Shadow Monetization)**.")

data = load_db()
has_host = data is not None

if 'is_host' not in st.session_state: st.session_state['is_host'] = False
if 'start_timer' not in st.session_state: st.session_state['start_timer'] = 0

with st.sidebar:
    st.header("Admin Control")
    if has_host and st.button("🔄 Reset Household Data"):
        reset_db()
        st.session_state['is_host'] = False
        st.rerun()

# ==========================================
# FASE 1: HOUSEHOLD ANCHOR (HOST SETUP)
# ==========================================
if not has_host or (has_host and st.session_state['is_host']):
    if not has_host:
        st.subheader("🏠 Phase 1: Data Enrichment (Host Registration)")
        st.info("Sistem mengumpulkan Log, Merekayasa Fitur, dan Melatih Model (Baseline).")
        
        # SENSORS
        h_ip, h_sw, h_ua = get_sensors('host')
        
        st.write("---")
        st.write("**🔐 Behavioral Enrollment:** Ketik frase 'netflix ai' untuk merekam pola ketik.")
        
        c1, c2 = st.columns([1, 3])
        if c1.button("⏱️ Start"): st.session_state['start_timer'] = time.time()
        
        h_input = c2.text_input("Input:", label_visibility="collapsed")
        
        if st.checkbox("📍 Lock GPS & Train Model"):
            if st.session_state['start_timer'] == 0:
                st.error("Klik Start dulu!")
            else:
                # Hitung CPM (Biometrics)
                dur = time.time() - st.session_state['start_timer']
                h_cpm = (len(h_input) / dur) * 60
                
                h_os, h_browser = parse_device(h_ua)
                loc = get_geolocation(component_key='gps_host')
                
                if loc and h_ip:
                    db = {
                        'ip': h_ip, 'os': h_os, 'res': h_sw,
                        'cpm': h_cpm, # Biometric Baseline
                        'lat': loc['coords']['latitude'], 'lon': loc['coords']['longitude']
                    }
                    save_db(db)
                    st.session_state['is_host'] = True
                    st.rerun()
                else:
                    st.warning("Waiting for GPS...")
    else:
        st.success("✅ HOUSEHOLD ANCHOR ACTIVE")
        st.write("Model has been trained with Host Data.")

# ==========================================
# FASE 2: REAL-TIME INFERENCE (VISITOR)
# ==========================================
else:
    st.write("---")
    st.subheader("🕵️ Phase 2: AI Detection & Shadow Monetization")
    
    # 1. INVISIBLE SENSORS GATHERING
    v_ip, v_sw, v_ua = get_sensors('vis')
    
    # 2. CHALLENGE (Untuk Biometric Data)
    col_chal, col_dash = st.columns([1, 3])
    
    with col_chal:
        st.markdown('<div class="strat-box">', unsafe_allow_html=True)
        st.write("#### 🔐 Security Challenge")
        st.write("Verifikasi identitas dengan mengetik:")
        st.code("netflix ai")
        
        if st.button("⏱️ Start Typing"): st.session_state['start_timer'] = time.time()
        v_input = st.text_input("Passphrase:", key="v_in")
        
        run_ai = st.checkbox("🚀 RUN AI DIAGNOSTICS")
        st.markdown('</div>', unsafe_allow_html=True)

    # 3. DASHBOARD HASIL (Kanan)
    if run_ai:
        if not v_ip:
            st.warning("Scanning Sensors...")
            st.stop()
            
        loc = get_geolocation(component_key='gps_vis')
        
        if loc and v_input:
            # === FEATURE ENGINEERING (PENGOLAHAN DATA) ===
            
            # A. Biometric Calculation
            dur = time.time() - st.session_state['start_timer']
            v_cpm = (len(v_input) / dur) * 60
            bio_diff = abs(data['cpm'] - v_cpm)
            is_bio_match = bio_diff < 50 # Toleransi CPM
            
            # B. Forensic Params
            v_os, v_browser = parse_device(v_ua)
            dist = haversine(data['lon'], data['lat'], loc['coords']['latitude'], loc['coords']['longitude'])
            is_ip_match = (v_ip == data['ip'])
            
            # === AI MODEL SCORING (THE BRAIN) ===
            
            # 1. TRUST SCORE (Untuk Strategy 1)
            trust_score = calculate_trust_score(dist, is_ip_match, is_bio_match, (v_os == data['os']))
            
            # 2. PROPENSITY SCORE (Untuk Strategy 2)
            propensity_score = calculate_propensity_score(v_os, v_sw)

            # === DISPLAY DASHBOARD 3 PILAR ===
            with col_dash:
                c1, c2 = st.columns(2)
                
                # KOLOM 1: ADVANCED AI DETECTION (The 5 Parameters)
                with c1:
                    st.markdown("### 📡 1. Advanced AI Detection")
                    st.markdown(f"""
                    <table class="param-table">
                        <tr>
                            <td class="param-label">Geolocaltion (GPS)</td>
                            <td>{dist:.1f} KM</td>
                            <td><span class="{'risk-low' if dist < 50 else 'risk-high'}">{'HOME' if dist < 50 else 'AWAY'}</span></td>
                        </tr>
                        <tr>
                            <td class="param-label">Behavioral Biometrics</td>
                            <td>{int(v_cpm)} CPM (vs {int(data['cpm'])})</td>
                            <td><span class="{'risk-low' if is_bio_match else 'risk-high'}">{'MATCH' if is_bio_match else 'ANOMALY'}</span></td>
                        </tr>
                        <tr>
                            <td class="param-label">Network (IP)</td>
                            <td>{v_ip}</td>
                            <td><span class="{'risk-low' if is_ip_match else 'risk-high'}">{'SAME' if is_ip_match else 'DIFF'}</span></td>
                        </tr>
                        <tr>
                            <td class="param-label">Device Fingerprint</td>
                            <td>{v_os}</td>
                            <td><span class="{'risk-low' if v_os == data['os'] else 'risk-high'}">{'SAME' if v_os == data['os'] else 'DIFF'}</span></td>
                        </tr>
                    </table>
                    <br>
                    """, unsafe_allow_html=True)
                    
                    st.info(f"🤖 **AI Trust Score: {trust_score}%** (Threshold: 75%)")

                # KOLOM 2: STRATEGIC ACTION (Monetization)
                with c2:
                    st.markdown("### 🎯 2. Strategic Action")
                    
                    # LOGIKA STRATEGI SESUAI PPT
                    
                    # Strategy 1: Adaptive Trust (Low Friction)
                    if trust_score >= 75:
                        st.success("✅ **Strategy 1: Adaptive Trust**")
                        st.write("User Verified. **Instant Access Granted.**")
                        st.caption("Alasan: Trust Score Tinggi (Biometrik/Lokasi Valid).")
                        
                    # Jika Trust Rendah -> Masuk Strategy 2: Monetization
                    else:
                        st.error("⛔ **Sharing Detected**")
                        st.write("Executing **Strategy 2: Shadow Monetization**")
                        st.progress(propensity_score / 100)
                        st.caption(f"Propensity to Pay Score: {propensity_score}/100")
                        
                        # Waterfall Logic
                        if propensity_score > 70:
                            st.markdown("""
                            <div style="background:#f8d7da; padding:10px; border-radius:5px;">
                                <b>Offer: HARD PAYWALL</b><br>
                                Target: High Value User.<br>
                                <button>💎 Subscribe Full Price</button>
                            </div>
                            """, unsafe_allow_html=True)
                        elif propensity_score > 40:
                            st.markdown("""
                            <div style="background:#fff3cd; padding:10px; border-radius:5px;">
                                <b>Offer: UPSIZING</b><br>
                                Target: Mid Value User.<br>
                                <button>➕ Add Extra Member</button>
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.markdown("""
                            <div style="background:#e2e3e5; padding:10px; border-radius:5px;">
                                <b>Offer: DOWNGRADING</b><br>
                                Target: Low Value User.<br>
                                <button>📺 Switch to Basic Ads</button>
                            </div>
                            """, unsafe_allow_html=True)

            # Strategy 3: Social Graph (Footer)
            st.markdown("---")
            st.markdown("### 🔗 3. Social Graph Analysis (Churn Reduction)")
            st.info("💡 **Feature Enabled:** Jika user menolak tawaran di atas, aktifkan **'Profile Transfer'** untuk mengamankan history tontonan mereka ke akun baru.")

        else:
            st.warning("⏳ Menunggu GPS...")
