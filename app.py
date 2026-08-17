import streamlit as st
import google.generativeai as genai
import json
import io
from docx import Document
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH

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
# 2. PENGATURAN TAMPILAN FULLSCREEN & ESTETIK
# ==========================================
st.set_page_config(
    page_title="EduGen Pro",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="collapsed" # Sengaja disembunyikan di awal agar layar HP lega
)

# CSS KHUSUS UNTUK MEMBUNUH FRAME STREAMLIT & MENGUBAH TEMA
st.markdown("""
<style>
    /* 1. MENGHILANGKAN FRAME, HEADER, FOOTER BAWAAN STREAMLIT (FULLSCREEN MODE) */
    header[data-testid="stHeader"] { display: none !important; }
    footer { display: none !important; }
    .stAppBottomBlockContainer { display: none !important; }
    .viewerBadge_container__1QSob { display: none !important; }
    #MainMenu { display: none !important; }
    
    /* 2. MENGHAPUS JARAK KOSONG DI ATAS DAN KIRI KANAN PADA HP */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 0rem !important;
        padding-left: 0.5rem !important;
        padding-right: 0.5rem !important;
        max-width: 100% !important;
    }

    /* 3. TEMA BACKGROUND GLOBAL */
    .stApp {
        background-color: #f0f4f8;
    }

    /* 4. HEADER UTAMA (Lebih kecil dan rapi di HP) */
    .header-container {
        background: linear-gradient(135deg, #4338ca 0%, #3b82f6 50%, #06b6d4 100%);
        padding: 1.2rem 1rem;
        border-radius: 16px;
        margin-bottom: 1rem;
        color: white;
        text-align: center;
        box-shadow: 0 4px 15px rgba(59, 130, 246, 0.3);
    }
    
    /* 5. KARTU (CARDS) COLORFUL UNTUK SETIAP BAGIAN */
    .stCard {
        padding: 1.2rem;
        border-radius: 16px;
        margin-bottom: 1rem;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05);
        border: 1px solid rgba(255,255,255,0.6);
    }
    /* Warna Kotak Identitas (Biru Muda Pastel) */
    .card-biru { background: linear-gradient(135deg, #e0f2fe 0%, #bae6fd 100%); border-left: 5px solid #0ea5e9; }
    /* Warna Kotak Parameter (Ungu Muda Pastel) */
    .card-ungu { background: linear-gradient(135deg, #f3e8ff 0%, #e9d5ff 100%); border-left: 5px solid #a855f7; }
    /* Warna Kotak Informasi (Hijau/Cyan Muda Pastel) */
    .card-cyan { background: linear-gradient(135deg, #ccfbf1 0%, #99f6e4 100%); border-left: 5px solid #14b8a6; }

    /* 6. TOMBOL GENERATE (Tegas & Menonjol) */
    button[kind="primary"] {
        background: linear-gradient(135deg, #4f46e5 0%, #2563eb 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 50px !important;
        padding: 0.6rem 2rem !important;
        font-weight: bold !important;
        box-shadow: 0 8px 15px rgba(37, 99, 235, 0.3) !important;
        transition: transform 0.2s ease !important;
    }
    button[kind="primary"]:active {
        transform: scale(0.95) !important;
    }

    /* 7. KOTAK INPUT (Biar nyatu dengan kotak warna-warni) */
    .stTextInput>div>div>input, .stSelectbox>div>div>select, .stMultiSelect>div>div>div {
        background-color: rgba(255, 255, 255, 0.9) !important;
        border-radius: 10px !important;
        border: 1px solid rgba(0,0,0,0.1) !important;
        padding: 0.5rem !important;
    }

    /* 8. TABS (Menu Atas) */
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

if 'ai_result' not in st.session_state:
    st.session_state.ai_result = None

# ==========================================
# 4. FUNGSI LOGIKA (BACKEND AI & WORD)
# ==========================================
def get_available_model():
    try:
        available_models = []
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                available_models.append(m.name)
        
        if not available_models: return None
        prioritas = ["models/gemini-2.5-flash", "models/gemini-1.5-flash"]
        for nama in prioritas:
            if nama in available_models: return nama
        return available_models[0]
    except Exception as e:
        st.error("Gagal memuat AI.")
        return None

def generate_rpp_content(model_name, mapel, topik, kelas, waktu, profil_list, pakai_lkpd):
    try:
        model = genai.GenerativeModel(model_name)
        profil_str = ", ".join(profil_list)
        
        instruksi_lkpd = "Sertakan materi untuk LKPD (3-5 soal/aktivitas)." if pakai_lkpd == "Ya" else ""
        json_structure_lkpd = ', "lkpd": "Isi detail LKPD (Soal/Aktivitas)."' if pakai_lkpd == "Ya" else ""

        prompt = f"""
        Buatkan Modul Ajar Kurikulum Merdeka format JSON.
        Mapel {mapel}, Kelas {kelas}, Topik {topik}, Waktu {waktu}, Profil {profil_str}.
        {instruksi_lkpd}
        Output JSON MURNI:
        {{
            "tujuan": "Tujuan (poin-poin).",
            "pemahaman": "Pertanyaan pemantik.",
            "pendahuluan": "Awal (poin-poin).",
            "inti": "Inti (poin-poin).",
            "penutup": "Penutup (poin-poin).",
            "asesmen": "Penilaian."
            {json_structure_lkpd}
        }}
        """
        response = model.generate_content(prompt, request_options={"timeout": 60})
        text = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(text)
    except Exception as e:
        return None

def create_docx(data_input, ai_data, pakai_lkpd):
    doc = Document()
    head = doc.add_heading('MODUL AJAR / RPP', 0)
    head.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph("")

    table = doc.add_table(rows=5, cols=3)
    table.columns[0].width = Inches(1.5)
    table.columns[1].width = Inches(0.2)
    table.columns[2].width = Inches(4.5)
    
    infos = [
        ("Nama Sekolah", data_input['sekolah']),
        ("Nama Guru", data_input['guru']),
        ("Mata Pelajaran", data_input['mapel']),
        ("Kelas/Semester", data_input['kelas']),
        ("Alokasi Waktu", data_input['waktu'])
    ]
    
    for i, (label, val) in enumerate(infos):
        table.cell(i,0).text = label
        table.cell(i,1).text = ":"
        table.cell(i,2).text = val

    def add_section(title, content):
        doc.add_heading(title, level=1)
        doc.add_paragraph(content if content else "-")

    add_section('A. Tujuan Pembelajaran', ai_data.get('tujuan'))
    doc.add_heading('B. Profil Pelajar Pancasila', level=1)
    for p in data_input['profil']: doc.add_paragraph(f"- {p}", style='List Bullet')
    add_section('C. Pemahaman Bermakna', ai_data.get('pemahaman'))
    
    doc.add_heading('D. Kegiatan Pembelajaran', level=1)
    doc.add_paragraph("1. Pendahuluan").bold = True
    doc.add_paragraph(ai_data.get('pendahuluan', '-'))
    doc.add_paragraph("2. Kegiatan Inti").bold = True
    doc.add_paragraph(ai_data.get('inti', '-'))
    doc.add_paragraph("3. Kegiatan Penutup").bold = True
    doc.add_paragraph(ai_data.get('penutup', '-'))
    add_section('E. Asesmen / Penilaian', ai_data.get('asesmen'))

    doc.add_paragraph("\n\n")
    sig_table = doc.add_table(rows=1, cols=2)
    sig_table.cell(0,0).text = f"Mengetahui,\nKepala Sekolah\n\n\n\n{data_input['kepsek']}"
    sig_table.cell(0,0).paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
    sig_table.cell(0,1).text = f"Guru Mata Pelajaran\n\n\n\n{data_input['guru']}"
    sig_table.cell(0,1).paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER

    if pakai_lkpd == "Ya" and ai_data.get('lkpd'):
        doc.add_page_break()
        doc.add_heading('LAMPIRAN: LKPD', 0)
        doc.add_paragraph(ai_data.get('lkpd'))

    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

# ==========================================
# 5. ANTARMUKA UTAMA (UI)
# ==========================================
# Bagian Judul (Ukurannya pas untuk HP)
st.markdown("""
<div class="header-container">
    <h1 style="margin: 0; font-size: 1.6rem; font-weight: 800; text-shadow: 1px 1px 2px rgba(0,0,0,0.2);">🚀 EduGen Pro</h1>
    <p style="margin: 0.2rem 0 0 0; font-size: 0.85rem; font-weight: 500;">Penyusun Modul Ajar Cerdas</p>
    <div style="margin-top: 8px; font-size: 0.75rem; background: rgba(0,0,0,0.15); padding: 4px 10px; border-radius: 20px; display: inline-block;">
        Ceng Ucu Muhammad, S.H - SMP IT Nurusy Syifa
    </div>
</div>
""", unsafe_allow_html=True)

active_model = get_available_model()

# Menu TABS
tab1, tab2, tab3 = st.tabs(["📝 Form RPP", "👁️ Hasil", "⚙️ DB Profil"])

# --- TAB 1: INPUT DATA ---
with tab1:
    # KOTAK 1: BIRU MUDA (Identitas)
    st.markdown('<div class="stCard card-biru"><h4 style="margin-top:0; color:#0369a1;">🧑‍🏫 Identitas Guru</h4>', unsafe_allow_html=True)
    nama_guru = st.text_input("Nama Guru", placeholder="Cth: Ceng Ucu, S.H")
    nama_sekolah = st.text_input("Sekolah", value="SMP IT Nurusy Syifa")
    nama_kepsek = st.text_input("Kepala Sekolah", placeholder="Cth: Ahmad, M.Pd")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # KOTAK 2: UNGU MUDA (Parameter)
    st.markdown('<div class="stCard card-ungu"><h4 style="margin-top:0; color:#7e22ce;">📚 Parameter Modul</h4>', unsafe_allow_html=True)
    mapel = st.text_input("Mata Pelajaran", value="Ilmu Pengetahuan Sosial (IPS)")
    kelas = st.selectbox("Kelas", ["VII (Fase D)", "VIII (Fase D)", "IX (Fase D)"], index=0)
    topik = st.text_input("Topik Materi*", placeholder="Wajib: Cth: Interaksi Sosial")
    waktu = st.text_input("Waktu", value="2 JP (2 x 40 Menit)")
    profil = st.multiselect("Profil Pelajar", st.session_state['profil_db'], default=st.session_state['profil_db'][:2])
    pilihan_lkpd = st.radio("Buat LKPD Otomatis?", ["Tidak", "Ya"], horizontal=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # TOMBOL GENERATE
    submitted = st.button("🚀 GENERATE SEKARANG", use_container_width=True, type="primary")

# --- TAB 2: PREVIEW HASIL ---
with tab2:
    if st.session_state.ai_result:
        st.markdown('<div style="background:#10b981; color:white; padding:10px; border-radius:10px; margin-bottom:15px; font-weight:bold; text-align:center;">✅ Selesai Disusun!</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="stCard card-cyan">', unsafe_allow_html=True)
        with st.expander("🎯 Tujuan Pembelajaran", expanded=True): st.write(st.session_state.ai_result.get('tujuan'))
        with st.expander("🔥 Kegiatan Inti", expanded=True): st.write(st.session_state.ai_result.get('inti'))
        with st.expander("📝 Penilaian (Asesmen)"): st.write(st.session_state.ai_result.get('asesmen'))
        if 'lkpd' in st.session_state.ai_result:
            with st.expander("📚 LKPD"): st.write(st.session_state.ai_result.get('lkpd'))
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("💡 Hasil modul ajar akan muncul di sini.")

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
        st.error("⚠️ Topik, Nama Guru, dan Sekolah wajib diisi!")
    else:
        with st.spinner("✨ Meracik RPP..."):
            res = generate_rpp_content(active_model, mapel, topik, kelas, waktu, profil, pilihan_lkpd)
            if res:
                st.session_state.ai_result = res
                st.session_state.data_input = {
                    'guru': nama_guru, 'sekolah': nama_sekolah, 'kepsek': nama_kepsek,
                    'mapel': mapel, 'kelas': kelas, 'waktu': waktu, 'profil': profil, 'pilihan_lkpd': pilihan_lkpd
                }
                st.rerun()

if st.session_state.ai_result and st.session_state.get('data_input'):
    st.markdown("<hr style='margin:10px 0;'>", unsafe_allow_html=True)
    docx_file = create_docx(st.session_state.data_input, st.session_state.ai_result, st.session_state.data_input['pilihan_lkpd'])
    st.download_button(
        label="📥 UNDUH FILE WORD (.DOCX)",
        data=docx_file,
        file_name=f"Modul_Ajar_{st.session_state.data_input['mapel']}.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        use_container_width=True,
        type="primary"
    )
