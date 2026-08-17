import streamlit as st
import google.generativeai as genai

from rpp_backend import generate_bagian_umum, generate_asesmen_lampiran, create_docx

# ==========================================
# 1. KONFIGURASI API KEY
# ==========================================
try:
    MY_API_KEY = st.secrets["GOOGLE_API_KEY"]
except Exception:
    MY_API_KEY = None
    st.error(
        "⚠️ API Key belum diatur. Tambahkan GOOGLE_API_KEY di menu "
        "Settings → Secrets (Streamlit Cloud)."
    )
    st.stop()

try:
    genai.configure(api_key=MY_API_KEY)
except Exception as e:
    st.error(f"Error Konfigurasi: {e}")
    st.stop()

# ==========================================
# 2. PENGATURAN TAMPILAN
# ==========================================
st.set_page_config(
    page_title="MODUL AJAR GENERATOR",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    [data-testid="stHeader"] { display: none !important; }
    [data-testid="stToolbar"] { display: none !important; }
    [data-testid="stDecoration"] { display: none !important; }
    [data-testid="stStatusWidget"] { display: none !important; }
    #MainMenu { display: none !important; }
    footer { display: none !important; }

    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 1rem !important;
        padding-left: 0.5rem !important;
        padding-right: 0.5rem !important;
        max-width: 100% !important;
    }

    .stApp { background-color: #f0f4f8; }

    .header-container {
        background: linear-gradient(135deg, #4338ca 0%, #3b82f6 50%, #06b6d4 100%);
        padding: 1.2rem 1rem;
        border-radius: 16px;
        margin-bottom: 1rem;
        color: white;
        text-align: center;
        box-shadow: 0 4px 15px rgba(59, 130, 246, 0.3);
    }

    .stCard {
        padding: 1.2rem;
        border-radius: 16px;
        margin-bottom: 1rem;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05);
        border: 1px solid rgba(255,255,255,0.6);
    }
    .card-biru { background: linear-gradient(135deg, #e0f2fe 0%, #bae6fd 100%); border-left: 5px solid #0ea5e9; }
    .card-ungu { background: linear-gradient(135deg, #f3e8ff 0%, #e9d5ff 100%); border-left: 5px solid #a855f7; }
    .card-cyan { background: linear-gradient(135deg, #ccfbf1 0%, #99f6e4 100%); border-left: 5px solid #14b8a6; }

    button[kind="primary"] {
        background: linear-gradient(135deg, #4f46e5 0%, #2563eb 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 50px !important;
        padding: 0.6rem 2rem !important;
        font-weight: bold !important;
        box-shadow: 0 8px 15px rgba(37, 99, 235, 0.3) !important;
    }

    .stTextInput>div>div>input, .stSelectbox>div>div>select, .stMultiSelect>div>div>div {
        background-color: rgba(255, 255, 255, 0.9) !important;
        border-radius: 10px !important;
        border: 1px solid rgba(0,0,0,0.1) !important;
    }

    .stTabs [data-baseweb="tab-list"] {
        background-color: white;
        border-radius: 12px;
        padding: 0.3rem;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        margin-bottom: 1rem;
        gap: 5px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: transparent;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        color: #64748b;
        font-weight: 600;
        font-size: 0.9rem;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #3b82f6 0%, #06b6d4 100%) !important;
        color: white !important;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. DATABASE (SESSION STATE)
# ==========================================
if 'profil_db' not in st.session_state:
    st.session_state['profil_db'] = [
        "Beriman, Bertakwa kepada Tuhan YME, dan Berakhlak Mulia",
        "Berkebinekaan Global",
        "Bergotong Royong",
        "Mandiri",
        "Bernalar Kritis",
        "Kreatif"
    ]

if 'ai_umum' not in st.session_state:
    st.session_state.ai_umum = None
if 'ai_asesmen' not in st.session_state:
    st.session_state.ai_asesmen = None


# ==========================================
# 4. MODEL AI
# ==========================================
def get_available_model():
    try:
        available_models = []
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                available_models.append(m.name)
        if not available_models:
            return None
        prioritas = ["models/gemini-1.5-flash", "models/gemini-2.5-flash"]
        for nama in prioritas:
            if nama in available_models:
                return nama
        return available_models[0]
    except Exception:
        st.error("Gagal memuat AI.")
        return None


active_model = get_available_model()

# ==========================================
# 5. ANTARMUKA UTAMA (UI)
# ==========================================
st.markdown("""
<div class="header-container">
    <h1 style="margin: 0; font-size: 1.6rem; font-weight: 600; text-shadow: 1px 1px 2px rgba(0,0,0,0.2);">🚀 GENERATOR MODUL AJAR</h1>
    <p style="margin: 0.2rem 0 0 0; font-size: 0.85rem; font-weight: 500;">Penyusun Modul Ajar & LKPD Cerdas Kurikulum Merdeka</p>
    <div style="margin-top: 8px; font-size: 0.75rem; background: rgba(0,0,0,0.15); padding: 4px 10px; border-radius: 20px; display: inline-block;">
        dibuat oleh : 
        Ceng Ucu Muhammad, S.H - ( Kepala Sekolah SMP IT Nurusy Syifa )
    </div>
</div>
""", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["📝 Form Modul", "👁️ Hasil", "⚙️ DB Profil"])

# --- TAB 1: INPUT DATA ---
with tab1:
    st.markdown('<div class="stCard card-biru"><h4 style="margin-top:0; color:#0369a1;">🧑‍🏫 Identitas Penyusun</h4>', unsafe_allow_html=True)
    nama_guru = st.text_input("Nama Guru / Penyusun", placeholder="Cth: Ust. Ahmad Fauzi, S.Pd")
    nik_guru = st.text_input("NIK / NIP (opsional)", placeholder="Cth: 198501012010011001")
    nama_sekolah = st.text_input("Nama Instansi / Sekolah", value="SMP IT Nurusy Syifa")
    nama_kepsek = st.text_input("Nama Kepala Sekolah / Pengasuh", placeholder="Cth: KH. Ahmad, M.Pd")
    tahun_penyusunan = st.text_input("Tahun Penyusunan", value="Tahun 2026")
    jenjang_sekolah = st.selectbox("Jenjang Sekolah", ["SMP/MTs", "SMA/MA", "SD/MI"], index=0)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="stCard card-ungu"><h4 style="margin-top:0; color:#7e22ce;">📚 Parameter Modul</h4>', unsafe_allow_html=True)
    mapel = st.text_input("Mata Pelajaran", value="Ilmu Pengetahuan Sosial (IPS)")
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        fase = st.selectbox("Fase", ["A", "B", "C", "D", "E", "F"], index=3)
    with col_b:
        kelas = st.selectbox("Kelas", ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII"], index=6)
    with col_c:
        semester = st.selectbox("Semester", ["Ganjil", "Genap"], index=0)
    tema = st.text_input("Tema / Bab", placeholder="Cth: Keluarga Awal Kehidupan")
    topik = st.text_input("Materi / Topik*", placeholder="Wajib diisi: Cth: Sejarah Keluarga")
    waktu = st.text_input("Alokasi Waktu", value="2 JP (2 x 40 Menit)")
    model_pembelajaran = st.selectbox(
        "Model Pembelajaran",
        ["Tatap Muka", "Resitasi", "Discovery Learning", "Problem Based Learning",
         "Project Based Learning", "Cooperative Learning"], index=0
    )
    profil = st.multiselect("Profil Pelajar Pancasila", st.session_state['profil_db'],
                             default=st.session_state['profil_db'][:2])
    pilihan_lkpd = st.radio("Sertakan Lampiran (LKPD, Bahan Bacaan, Glosarium, Daftar Pustaka)?",
                             ["Ya", "Tidak"], horizontal=True)
    st.markdown('</div>', unsafe_allow_html=True)

    submitted = st.button("🚀 GENERATE SEKARANG", use_container_width=True, type="primary")

# --- TAB 2: PREVIEW HASIL ---
with tab2:
    if st.session_state.ai_umum:
        st.markdown('<div style="background:#10b981; color:white; padding:10px; border-radius:10px; margin-bottom:15px; font-weight:bold; text-align:center;">✅ Modul Ajar Lengkap Selesai Disusun!</div>', unsafe_allow_html=True)

        st.markdown('<div class="stCard card-cyan">', unsafe_allow_html=True)
        with st.expander("🎯 Tujuan Pembelajaran", expanded=True):
            st.write(st.session_state.ai_umum.get('tujuan_pembelajaran'))
        with st.expander("🔥 Kegiatan Inti", expanded=True):
            st.write(st.session_state.ai_umum.get('kegiatan_inti'))
        if st.session_state.ai_asesmen:
            with st.expander("📝 Asesmen (Butir Soal)"):
                st.write(st.session_state.ai_asesmen.get('butir_soal'))
            with st.expander("📚 LKPD"):
                st.write(st.session_state.ai_asesmen.get('lkpd_soal'))
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("💡 Hasil modul ajar akan muncul di sini setelah kamu klik Generate.")

# --- TAB 3: PENGATURAN / PROFIL ---
with tab3:
    st.markdown('<div class="stCard card-biru"><h4 style="margin-top:0; color:#0369a1;">➕ Tambah Profil</h4>', unsafe_allow_html=True)
    baru = st.text_input("Nama Profil Baru", label_visibility="collapsed")
    if st.button("Simpan Profil", use_container_width=True) and baru:
        if baru not in st.session_state['profil_db']:
            st.session_state['profil_db'].append(baru)
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="stCard card-ungu"><h4 style="margin-top:0; color:#7e22ce;">📋 Daftar Profil</h4>', unsafe_allow_html=True)
    for i, p in enumerate(st.session_state['profil_db']):
        c1, c2 = st.columns([4, 1])
        c1.write(f"{i+1}. {p}")
        if c2.button("X", key=f"del_{i}"):
            st.session_state['profil_db'].pop(i)
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# 6. LOGIKA EKSEKUSI
# ==========================================
if 'submitted' in locals() and submitted:
    if not topik or not nama_guru or not nama_sekolah:
        st.error("⚠️ Materi/Topik, Nama Guru, dan Sekolah wajib diisi!")
    else:
        ctx = {
            'mapel': mapel, 'jenjang': jenjang_sekolah, 'fase': fase, 'kelas': kelas,
            'semester': semester, 'tema': tema or topik, 'materi': topik, 'waktu': waktu,
            'model_pembelajaran': model_pembelajaran, 'profil': profil,
        }
        with st.spinner("✨ Menyusun Informasi Umum & Komponen Inti..."):
            ai_umum = generate_bagian_umum(active_model, ctx)
        with st.spinner("✨ Menyusun Asesmen Lengkap & Lampiran..."):
            ai_asesmen = generate_asesmen_lampiran(active_model, ctx)

        if ai_umum is None or ai_asesmen is None:
            st.error("⚠️ Gagal menghasilkan konten dari AI. Silakan coba lagi.")
        else:
            st.session_state.ai_umum = ai_umum
            st.session_state.ai_asesmen = ai_asesmen
            st.session_state.data_input = {
                'guru': nama_guru, 'sekolah': nama_sekolah, 'kepsek': nama_kepsek,
                'nik': nik_guru, 'tahun': tahun_penyusunan, 'jenjang': jenjang_sekolah,
                'mapel': mapel, 'fase': fase, 'kelas': kelas, 'semester': semester,
                'tema': tema or topik, 'materi': topik, 'waktu': waktu,
                'model_pembelajaran': model_pembelajaran, 'profil': profil,
                'pakai_lkpd': pilihan_lkpd,
            }
            st.rerun()

if st.session_state.ai_umum and st.session_state.get('data_input'):
    st.markdown("<hr style='margin:10px 0;'>", unsafe_allow_html=True)
    docx_file = create_docx(
        st.session_state.data_input,
        st.session_state.ai_umum,
        st.session_state.ai_asesmen,
    )
    st.download_button(
        label="📥 UNDUH FILE WORD (.DOCX)",
        data=docx_file,
        file_name=f"Modul_Ajar_{st.session_state.data_input['mapel']}.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        use_container_width=True,
        type="primary"
    )
