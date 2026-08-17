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
        "Settings → Secrets (Streamlit Cloud), atau di file "
        ".streamlit/secrets.toml (kalau dijalankan lokal)."
    )
    st.stop()

# Konfigurasi Awal
try:
    genai.configure(api_key=MY_API_KEY)
except Exception as e:
    st.error(f"Error Konfigurasi: {e}")
    st.stop()

# ==========================================
# 2. PENGATURAN TAMPILAN (UI) MODERN
# ==========================================
st.set_page_config(
    page_title="Generator RPP & MODUL AJAR",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS untuk tampilan modern
st.markdown("""
<style>
    .main {
        padding: 1rem 2rem;
    }
    .header-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        color: white;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .stCard {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        margin-bottom: 1rem;
        border-left: 4px solid #667eea;
    }
    .stButton>button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.75rem 2rem;
        border-radius: 8px;
        font-weight: 600;
        font-size: 1rem;
        transition: all 0.3s ease;
        width: 100%;
        margin-top: 1rem;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
    }
    .success-message {
        background: linear-gradient(135deg, #4CAF50 0%, #2E7D32 100%);
        color: white;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
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
# 4. FUNGSI LOGIKA (BACKEND)
# ==========================================
def get_available_model():
    try:
        available_models = []
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                available_models.append(m.name)
        
        if not available_models: return None
        prioritas = [
            "models/gemini-2.5-flash",
            "models/gemini-1.5-flash",
        ]
        for nama in prioritas:
            if nama in available_models:
                return nama
        return available_models[0]
    except Exception as e:
        st.error(f"Gagal mengambil daftar model dari Google: {e}")
        return None

def generate_rpp_content(model_name, mapel, topik, kelas, waktu, profil_list, pakai_lkpd):
    try:
        model = genai.GenerativeModel(model_name)
        profil_str = ", ".join(profil_list)
        
        instruksi_lkpd = ""
        json_structure_lkpd = ""
        if pakai_lkpd == "Ya":
            instruksi_lkpd = "Sertakan juga materi untuk Lembar Kerja Peserta Didik (LKPD) berisi 3-5 soal atau aktivitas."
            json_structure_lkpd = ', "lkpd": "Isi detail LKPD (Soal/Aktivitas)."'

        prompt = f"""
        Buatkan Modul Ajar Kurikulum Merdeka dalam format JSON.
        Data: Mapel {mapel}, Kelas {kelas}, Topik {topik}, Waktu {waktu}, Profil {profil_str}.
        {instruksi_lkpd}
        
        Output WAJIB JSON MURNI (tanpa format markdown):
        {{
            "tujuan": "Tujuan pembelajaran (poin-poin).",
            "pemahaman": "Pertanyaan pemantik.",
            "pendahuluan": "Kegiatan awal (poin-poin).",
            "inti": "Kegiatan inti detail (poin-poin).",
            "penutup": "Kegiatan penutup (poin-poin).",
            "asesmen": "Teknik penilaian."
            {json_structure_lkpd}
        }}
        Gunakan Bahasa Indonesia formal pendidikan.
        """
        
        response = model.generate_content(
            prompt,
            request_options={"timeout": 60},
        )
        text = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(text)
    except json.JSONDecodeError:
        st.error("⚠️ AI mengembalikan format yang tidak sesuai. Coba klik tombol Generate sekali lagi.")
        return None
    except Exception as e:
        st.error(f"Gagal Generate: {str(e)}")
        return None

def create_docx(data_input, ai_data, pakai_lkpd):
    doc = Document()
    
    head = doc.add_heading('MODUL AJAR / RPP', 0)
    head.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph("")

    table = doc.add_table(rows=5, cols=3)
    table.autofit = False
    table.columns[0].width = Inches(1.8)
    table.columns[1].width = Inches(0.2)
    table.columns[2].width = Inches(4.5)
    
    infos = [
        ("Nama Sekolah", data_input['sekolah']),
        ("Nama Guru", data_input['guru']),
        ("Mata Pelajaran", data_input['mapel']),
        ("Kelas / Semester", data_input['kelas']),
        ("Alokasi Waktu", data_input['waktu'])
    ]
    
    for i, (label, val) in enumerate(infos):
        table.cell(i,0).text = label
        table.cell(i,1).text = ":"
        table.cell(i,2).text = val
        table.cell(i,0).paragraphs[0].paragraph_format.space_after = Pt(2)
        table.cell(i,2).paragraphs[0].paragraph_format.space_after = Pt(2)

    doc.add_paragraph("")

    def add_section(title, content):
        doc.add_heading(title, level=1)
        if content:
            doc.add_paragraph(content)
        else:
            doc.add_paragraph("-")

    add_section('A. Tujuan Pembelajaran', ai_data.get('tujuan'))
    
    doc.add_heading('B. Profil Pelajar Pancasila', level=1)
    for p in data_input['profil']:
        doc.add_paragraph(f"- {p}", style='List Bullet')

    add_section('C. Pemahaman Bermakna', ai_data.get('pemahaman'))
    
    doc.add_heading('D. Kegiatan Pembelajaran', level=1)
    
    p = doc.add_paragraph()
    p.add_run("1. Kegiatan Pendahuluan").bold = True
    doc.add_paragraph(ai_data.get('pendahuluan', '-'))
    
    p = doc.add_paragraph()
    p.add_run("2. Kegiatan Inti").bold = True
    doc.add_paragraph(ai_data.get('inti', '-'))
    
    p = doc.add_paragraph()
    p.add_run("3. Kegiatan Penutup").bold = True
    doc.add_paragraph(ai_data.get('penutup', '-'))

    add_section('E. Asesmen / Penilaian', ai_data.get('asesmen'))

    doc.add_paragraph("\n\n")
    sig_table = doc.add_table(rows=1, cols=2)
    sig_table.autofit = True
    
    c1 = sig_table.cell(0,0)
    c1.text = f"Mengetahui,\nKepala Sekolah\n\n\n\n{data_input['kepsek']}"
    c1.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    c2 = sig_table.cell(0,1)
    c2.text = f"Guru Mata Pelajaran\n\n\n\n{data_input['guru']}"
    c2.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER

    if pakai_lkpd == "Ya" and ai_data.get('lkpd'):
        doc.add_page_break()
        doc.add_heading('LAMPIRAN: LEMBAR KERJA PESERTA DIDIK (LKPD)', 0)
        doc.add_paragraph("")
        doc.add_paragraph("Nama Siswa : ...................................")
        doc.add_paragraph(f"Kelas      : {data_input['kelas']}")
        doc.add_paragraph("----------------------------------------------------------------------------------")
        doc.add_paragraph(ai_data.get('lkpd'))

    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

# ==========================================
# 5. HALAMAN UTAMA MODERN
# ==========================================
def page_generator():
    st.markdown("""
    <div class="header-container">
        <h1 style="margin: 0; font-size: 2.5rem;">📚 Generator Modul Ajar & LKPD</h1>
        <p style="margin: 0.5rem 0 0 0; font-size: 1.1rem; opacity: 0.9;">
            Aplikasi ini dibuat oleh Ceng Ucu Muhammad, S.H - SMP IT Nurusy Syifa
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    active_model = get_available_model()
    if not active_model:
        st.error("⚠️ API Key bermasalah atau kuota habis.")
        st.stop()

    tab1, tab2, tab3 = st.tabs(["📝 Input Data", "👁️ Preview", "⚙️ Settings"])
    
    with tab1:
        st.markdown("### Form Input Data Modul Ajar")
        
        with st.container():
            st.markdown('<div class="stCard">', unsafe_allow_html=True)
            st.subheader("1. Identitas Sekolah & Guru")
            col1, col2, col3 = st.columns(3)
            with col1:
                nama_guru = st.text_input("Nama Guru", placeholder="Masukkan nama guru...")
            with col2:
                nama_sekolah = st.text_input("Nama Sekolah", value="SMP IT Nurusy Syifa", placeholder="Masukkan nama sekolah...")
            with col3:
                nama_kepsek = st.text_input("Nama Kepala Sekolah", placeholder="Masukkan nama kepala sekolah...")
            st.markdown('</div>', unsafe_allow_html=True)
        
        with st.container():
            st.markdown('<div class="stCard">', unsafe_allow_html=True)
            st.subheader("2. Materi Pembelajaran")
            col4, col5, col6 = st.columns(3)
            with col4:
                mapel = st.text_input("Mata Pelajaran", value="IPA", placeholder="Contoh: IPA")
                kelas = st.selectbox("Kelas", ["VII", "VIII", "IX", "X", "XI", "XII"], index=0)
            with col5:
                waktu = st.text_input("Alokasi Waktu", value="2 JP (2x40 Menit)", placeholder="Contoh: 2 JP")
                topik = st.text_input("Topik Materi*", value="Sistem Pencernaan", placeholder="Wajib diisi")
            with col6:
                profil = st.multiselect(
                    "Profil Pelajar Pancasila",
                    st.session_state['profil_db'],
                    default=st.session_state['profil_db'][:2]
                )
            
            st.subheader("3. Opsi Tambahan")
            pilihan_lkpd = st.radio(
                "Sertakan Lembar Kerja (LKPD)?",
                ["Tidak", "Ya"],
                horizontal=True
            )
            st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown("---")
        col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
        with col_btn2:
            submitted = st.button("🚀 GENERATE MODUL AJAR", use_container_width=True, type="primary")
    
    with tab2:
        st.markdown("### Preview Hasil")
        if st.session_state.ai_result:
            st.markdown('<div class="success-message">✅ Modul Ajar berhasil digenerate!</div>', unsafe_allow_html=True)
            with st.expander("📋 Tujuan Pembelajaran", expanded=True):
                st.write(st.session_state.ai_result.get('tujuan', 'Tidak tersedia'))
            
            col_preview1, col_preview2 = st.columns(2)
            with col_preview1:
                with st.expander("🎯 Kegiatan Inti", expanded=True):
                    st.write(st.session_state.ai_result.get('inti', 'Tidak tersedia'))
            with col_preview2:
                with st.expander("📊 Asesmen", expanded=True):
                    st.write(st.session_state.ai_result.get('asesmen', 'Tidak tersedia'))
            
            if 'lkpd' in st.session_state.ai_result:
                with st.expander("📝 Lembar Kerja (LKPD)", expanded=True):
                    st.info(st.session_state.ai_result.get('lkpd'))
        else:
            st.info("ℹ️ Silakan generate modul ajar terlebih dahulu di tab 'Input Data'")
    
    with tab3:
        st.markdown("### Pengaturan Aplikasi")
        with st.container():
            st.markdown('<div class="stCard">', unsafe_allow_html=True)
            st.subheader("Model AI")
            st.info(f"Model yang aktif: **{active_model.split('/')[-1]}**")
            st.subheader("Informasi Pengembang")
            st.markdown("""
            **Nama:** Ceng Ucu Muhammad, S.H  
            **Sekolah:** SMP IT Nurusy Syifa  
            **Versi Aplikasi:** 2.0  
            """)
            st.markdown('</div>', unsafe_allow_html=True)
    
    if 'submitted' in locals() and submitted:
        if not topik:
            st.error("⚠️ Topik materi wajib diisi!")
        elif not nama_guru or not nama_sekolah:
            st.error("⚠️ Nama guru dan sekolah wajib diisi!")
        else:
            with st.spinner("🤖 AI sedang menyusun Modul Ajar & LKPD..."):
                res = generate_rpp_content(active_model, mapel, topik, kelas, waktu, profil, pilihan_lkpd)
                if res:
                    st.session_state.ai_result = res
                    st.session_state.data_input = {
                        'guru': nama_guru, 'sekolah': nama_sekolah, 'kepsek': nama_kepsek,
                        'mapel': mapel, 'kelas': kelas, 'waktu': waktu, 'profil': profil,
                        'pilihan_lkpd': pilihan_lkpd
                    }
                    st.success("✅ Selesai! Lihat hasil di tab 'Preview'")
                    st.rerun()

    if st.session_state.ai_result and st.session_state.get('data_input'):
        st.markdown("---")
        st.markdown("### 📥 Download Hasil")
        col_dl1, col_dl2, col_dl3 = st.columns([1, 2, 1])
        with col_dl2:
            docx_file = create_docx(
                st.session_state.data_input, 
                st.session_state.ai_result, 
                st.session_state.data_input['pilihan_lkpd']
            )
            st.download_button(
                label="💾 DOWNLOAD MODUL (.DOCX)",
                data=docx_file,
                file_name=f"Modul_Ajar_{st.session_state.data_input['mapel']}_{st.session_state.data_input['kelas']}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                type="primary",
                use_container_width=True
            )

# ==========================================
# 6. HALAMAN DATABASE PROFIL
# ==========================================
def page_profil():
    st.title("🎓 Database Profil Pelajar Pancasila")
    with st.container():
        st.markdown('<div class="stCard">', unsafe_allow_html=True)
        st.subheader("Tambah Profil Baru")
        col_add1, col_add2 = st.columns([3, 1])
        with col_add1:
            baru = st.text_input("Nama profil baru", placeholder="Masukkan nama profil...")
        with col_add2:
            st.write("") 
            st.write("")
            if st.button("➕ Tambah", use_container_width=True) and baru:
                if baru not in st.session_state['profil_db']:
                    st.session_state['profil_db'].append(baru)
                    st.success(f"Profil '{baru}' berhasil ditambahkan!")
                    st.rerun()
                else:
                    st.warning("Profil sudah ada dalam database")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with st.container():
        st.markdown('<div class="stCard">', unsafe_allow_html=True)
        st.subheader("Daftar Profil Saat Ini")
        for i, p in enumerate(st.session_state['profil_db']):
            col_prof1, col_prof2 = st.columns([4, 1])
            with col_prof1:
                st.markdown(f"**{i+1}. {p}**")
            with col_prof2:
                if st.button("🗑️ Hapus", key=f"del_{i}", use_container_width=True):
                    st.session_state['profil_db'].pop(i)
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# 7. HALAMAN TENTANG
# ==========================================
def page_tentang():
    st.title("ℹ️ Tentang Aplikasi")
    with st.container():
        st.markdown('<div class="stCard">', unsafe_allow_html=True)
        st.markdown("""
        ### 📚 Generator Modul Ajar & LKPD Pro
        **Pengembang:** Ceng Ucu Muhammad, S.H  
        **Instansi:** SMP IT Nurusy Syifa  
        **Versi:** 2.0.0  
        """)
        st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# 8. NAVIGASI UTAMA
# ==========================================
with st.sidebar:
    st.markdown("""
    <div style="text-align: center; padding: 1rem 0;">
        <h2 style="color: #667eea; margin: 0;">📚 EduGen</h2>
        <p style="color: #666; font-size: 0.9rem; margin: 0;">SMP IT Nurusy Syifa</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    menu_options = {
        "📝 Buat Modul Ajar": page_generator,
        "🎓 Kelola Profil": page_profil,
        "ℹ️ Tentang": page_tentang
    }
    
    menu_selection = st.radio(
        "Pilih menu:",
        list(menu_options.keys()),
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    if st.button("🔄 Reset Aplikasi", use_container_width=True):
        for key in list(st.session_state.keys()):
            if key != 'profil_db':
                del st.session_state[key]
        st.rerun()

menu_options[menu_selection]()
