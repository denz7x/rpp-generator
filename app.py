import streamlit as st
import google.generativeai as genai
import json
import io
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH

# --- 1. KONFIGURASI API KEY (HARDCODED) ---
# API Key Anda sudah dimasukkan di sini
MY_API_KEY = "AIzaSyDm4BXch5vuDdl5jodG4xUx78-4iqdX0r0"

# --- 2. KONFIGURASI HALAMAN & CSS ---
st.set_page_config(
    page_title="AI Modul Ajar Generator",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS untuk tampilan profesional
st.markdown("""
<style>
    .main { background-color: #f8f9fa; }
    .stButton>button { 
        width: 100%; 
        border-radius: 8px; 
        font-weight: bold; 
        height: 3em;
        background-color: #4CAF50; 
        color: white;
    }
    .stButton>button:hover { background-color: #45a049; }
    h1, h2, h3 { color: #2c3e50; font-family: 'Segoe UI', sans-serif; }
    .stTextInput>div>div>input { border-radius: 8px; }
    
    /* Style untuk Running Text Container */
    .running-text-container {
        background-color: #ffe6e6; 
        padding: 10px; 
        border-radius: 5px;
        margin-bottom: 20px;
        border: 1px solid #ffcccc;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. DATABASE SEMENTARA (SESSION STATE) ---
if 'profil_db' not in st.session_state:
    st.session_state['profil_db'] = [
        "Beriman, Bertakwa kepada Tuhan YME, dan Berakhlak Mulia",
        "Berkebinekaan Global",
        "Bergotong Royong",
        "Mandiri",
        "Bernalar Kritis",
        "Kreatif"
    ]

# --- 4. FUNGSI AI GENERATOR (GEMINI) ---
def generate_rpp_content(model_name, mapel, topik, kelas, waktu, profil_list):
    # Konfigurasi API menggunakan Key yang sudah di-hardcode
    try:
        genai.configure(api_key=MY_API_KEY)
        model = genai.GenerativeModel(model_name)
        
        profil_str = ", ".join(profil_list)
        
        # Prompt Engineering (Instruksi ke AI)
        prompt = f"""
        Bertindaklah sebagai Guru Profesional Kurikulum Merdeka. 
        Buatkan konten Modul Ajar/RPP lengkap dalam format JSON.
        
        Data:
        - Mapel: {mapel}
        - Kelas: {kelas}
        - Topik: {topik}
        - Waktu: {waktu}
        - Profil: {profil_str}

        Output WAJIB JSON valid (tanpa markdown ```json):
        {{
            "tujuan": "2-3 tujuan pembelajaran spesifik & terukur.",
            "pemahaman": "Pertanyaan pemantik.",
            "pendahuluan": "Poin kegiatan pendahuluan (apersepsi).",
            "inti": "Langkah kegiatan inti detail (Model PBL/PjBL).",
            "penutup": "Refleksi dan penutup.",
            "asesmen": "Teknik penilaian (Sikap, Pengetahuan, Keterampilan)."
        }}
        Gunakan Bahasa Indonesia formal.
        """
        
        response = model.generate_content(prompt)
        text = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(text)
        
    except Exception as e:
        st.error(f"Error AI: {str(e)}")
        return None

# --- 5. FUNGSI PEMBUAT DOCX (WORD) ---
def create_docx(data_input, ai_data):
    doc = Document()
    
    # Judul
    heading = doc.add_heading('MODUL AJAR / RPP', 0)
    heading.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph("")

    # Tabel Identitas Rapi
    table = doc.add_table(rows=5, cols=3)
    table.autofit = False
    table.columns[0].width = Inches(1.5)
    table.columns[1].width = Inches(0.2)
    table.columns[2].width = Inches(4.5)

    def fill_row(idx, label, value):
        table.cell(idx, 0).text = label
        table.cell(idx, 1).text = ":"
        table.cell(idx, 2).text = value

    fill_row(0, "Nama Sekolah", data_input['sekolah'])
    fill_row(1, "Nama Guru", data_input['guru'])
    fill_row(2, "Mata Pelajaran", data_input['mapel'])
    fill_row(3, "Kelas / Semester", data_input['kelas'])
    fill_row(4, "Alokasi Waktu", data_input['waktu'])

    doc.add_paragraph("")
    
    # Isi dari AI
    doc.add_heading('A. Tujuan Pembelajaran', level=1)
    doc.add_paragraph(ai_data.get('tujuan', '-'))

    doc.add_heading('B. Profil Lulusan', level=1)
    if data_input['profil']:
        for p in data_input['profil']:
            doc.add_paragraph(f"- {p}", style='List Bullet')
    else:
        doc.add_paragraph("-")

    doc.add_heading('C. Pemahaman Bermakna', level=1)
    doc.add_paragraph(ai_data.get('pemahaman', '-'))

    doc.add_heading('D. Kegiatan Pembelajaran', level=1)
    
    p = doc.add_paragraph()
    p.add_run("1. Pendahuluan").bold = True
    doc.add_paragraph(ai_data.get('pendahuluan', '-'))
    
    p = doc.add_paragraph()
    p.add_run("2. Kegiatan Inti").bold = True
    doc.add_paragraph(ai_data.get('inti', '-'))
    
    p = doc.add_paragraph()
    p.add_run("3. Penutup").bold = True
    doc.add_paragraph(ai_data.get('penutup', '-'))

    doc.add_heading('E. Asesmen', level=1)
    doc.add_paragraph(ai_data.get('asesmen', '-'))

    # Tanda Tangan
    doc.add_paragraph("\n\n")
    sig_table = doc.add_table(rows=1, cols=2)
    sig_table.autofit = True
    
    c1 = sig_table.cell(0, 0)
    p1 = c1.paragraphs[0]
    p1.add_run(f"Mengetahui,\nKepala Sekolah\n\n\n\n{data_input['kepsek']}").bold = True
    p1.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    c2 = sig_table.cell(0, 1)
    p2 = c2.paragraphs[0]
    p2.add_run(f"Guru Mata Pelajaran\n\n\n\n{data_input['guru']}").bold = True
    p2.alignment = WD_ALIGN_PARAGRAPH.CENTER

    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

# --- 6. HALAMAN UTAMA ---
def page_generator():
    st.title("📚 Generator Modul Ajar Otomatis")
    
    # Running Text (Permintaan Khusus)
    st.markdown("""
        <div class="running-text-container">
            <marquee direction="left" scrollamount="8" style="color: red; font-weight: bold; font-size: 16px;">
            Aplikasi ini dibuat oleh Ceng Ucu Muhammad, S.H - SMP IT Nurusy Syifa
            </marquee>
        </div>
    """, unsafe_allow_html=True)
    
    # Model Choice (Hidden logic)
    model_choice = "gemini-1.5-flash" # Default model yang cepat

    # FORM INPUT
    with st.form("main_form"):
        st.subheader("1. Identitas Sekolah")
        c1, c2, c3 = st.columns(3)
        with c1:
            nama_guru = st.text_input("Nama Guru")
        with c2:
            nama_sekolah = st.text_input("Nama Sekolah")
        with c3:
            nama_kepsek = st.text_input("Nama Kepala Sekolah")

        st.subheader("2. Detail Pembelajaran")
        c4, c5 = st.columns(2)
        with c4:
            mapel = st.text_input("Mata Pelajaran", placeholder="Contoh: IPA")
            kelas = st.selectbox("Kelas", ["VII", "VIII", "IX", "X", "XI", "XII"])
        with c5:
            waktu = st.text_input("Alokasi Waktu", placeholder="2 JP x 40 Menit")
            topik = st.text_input("Topik Materi (Wajib)", placeholder="Contoh: Sistem Pencernaan")

        st.subheader("3. Profil Lulusan")
        profil_pilihan = st.multiselect(
            "Pilih Profil yang dikuatkan:", 
            options=st.session_state['profil_db'],
            default=st.session_state['profil_db'][:2] 
        )
        
        st.markdown("---")
        # Tombol Submit Form
        submitted = st.form_submit_button("🚀 Generate Modul Ajar (AI)")

    # LOGIKA PROSES (DI LUAR FORM AGAR TIDAK ERROR SAAT DOWNLOAD)
    if submitted:
        if not topik or not mapel:
            st.error("❌ Mohon isi Mata Pelajaran dan Topik Materi!")
        else:
            with st.spinner("🤖 AI sedang menyusun RPP... Mohon tunggu..."):
                # Panggil AI
                ai_result = generate_rpp_content(model_choice, mapel, topik, kelas, waktu, profil_pilihan)
                
                if ai_result:
                    # Siapkan Data Word
                    data_input = {
                        'guru': nama_guru, 'sekolah': nama_sekolah, 'kepsek': nama_kepsek,
                        'mapel': mapel, 'kelas': kelas, 'waktu': waktu,
                        'profil': profil_pilihan
                    }
                    
                    docx_file = create_docx(data_input, ai_result)
                    
                    st.success("✅ Berhasil! Dokumen siap diunduh.")
                    
                    # Tombol Download
                    st.download_button(
                        label="📥 Download Modul Ajar (.docx)",
                        data=docx_file,
                        file_name=f"Modul_Ajar_{mapel}_{kelas}.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    )
                    
                    # Preview
                    with st.expander("👁️ Lihat Preview Isi"):
                        st.write("**Tujuan:**", ai_result.get('tujuan'))
                        st.write("**Kegiatan Inti:**", ai_result.get('inti'))

# --- 7. HALAMAN DATABASE PROFIL ---
def page_profil():
    st.title("🎓 Database Profil Lulusan")
    
    c_in, c_btn = st.columns([3, 1])
    with c_in:
        new_item = st.text_input("Tambah Profil Baru")
    with c_btn:
        st.write("")
        st.write("")
        if st.button("➕ Tambah"):
            if new_item:
                st.session_state['profil_db'].append(new_item)
                st.success("OK")
    
    st.markdown("### Daftar Profil:")
    for i, item in enumerate(st.session_state['profil_db']):
        c1, c2 = st.columns([4, 1])
        c1.info(item)
        if c2.button("Hapus", key=f"del_{i}"):
            st.session_state['profil_db'].pop(i)
            st.rerun()

# --- 8. NAVIGASI SIDEBAR ---
with st.sidebar:
    st.image("[https://cdn-icons-png.flaticon.com/512/201/201612.png](https://cdn-icons-png.flaticon.com/512/201/201612.png)", width=80)
    st.title("Menu Navigasi")
    menu = st.radio("Pilih Halaman:", ["📝 Buat Modul Ajar", "🎓 Database Profil", "ℹ️ Tentang"])
    
    st.markdown("---")
    st.caption("Status AI: ✅ Terhubung")

# --- 9. ROUTING ---
if menu == "📝 Buat Modul Ajar":
    page_generator()
elif menu == "🎓 Database Profil":
    page_profil()
elif menu == "ℹ️ Tentang":
    st.title("Tentang Aplikasi")
    st.write("Generator Modul Ajar AI (Versi Auto-Key)")
    st.write("Developer: Ceng Ucu Muhammad, S.H")
    st.write("Instansi: SMP IT Nurusy Syifa")
