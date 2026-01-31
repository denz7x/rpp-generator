import streamlit as st
import google.generativeai as genai
import json
import io
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH

# --- 1. KONFIGURASI API KEY ---
# Kode ini sudah otomatis pakai API Key Anda
MY_API_KEY = "AIzaSyDm4BXch5vuDdl5jodG4xUx78-4iqdX0r0"

# --- 2. SETUP HALAMAN ---
st.set_page_config(
    page_title="AI Modul Ajar Generator",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS Agar Tampilan Bagus
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
    .running-text-container {
        background-color: #ffe6e6; 
        padding: 10px; 
        border-radius: 5px;
        margin-bottom: 20px;
        border: 1px solid #ffcccc;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. DATABASE PROFIL ---
if 'profil_db' not in st.session_state:
    st.session_state['profil_db'] = [
        "Beriman, Bertakwa kepada Tuhan YME, dan Berakhlak Mulia",
        "Berkebinekaan Global",
        "Bergotong Royong",
        "Mandiri",
        "Bernalar Kritis",
        "Kreatif"
    ]

# --- 4. FUNGSI AI ---
def generate_rpp_content(model_name, mapel, topik, kelas, waktu, profil_list):
    try:
        genai.configure(api_key=MY_API_KEY)
        model = genai.GenerativeModel(model_name)
        
        profil_str = ", ".join(profil_list)
        
        prompt = f"""
        Buatkan Modul Ajar/RPP Kurikulum Merdeka format JSON.
        
        Info:
        - Mapel: {mapel}
        - Kelas: {kelas}
        - Topik: {topik}
        - Waktu: {waktu}
        - Profil: {profil_str}

        Output WAJIB JSON MURNI (tanpa ```json):
        {{
            "tujuan": "Tujuan pembelajaran.",
            "pemahaman": "Pertanyaan pemantik.",
            "pendahuluan": "Kegiatan awal.",
            "inti": "Kegiatan inti detail.",
            "penutup": "Kegiatan penutup.",
            "asesmen": "Penilaian."
        }}
        Bahasa Indonesia formal.
        """
        
        response = model.generate_content(prompt)
        text = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(text)
        
    except Exception as e:
        st.error(f"Error pada AI: {str(e)}")
        return None

# --- 5. FUNGSI WORD (DOCX) ---
def create_docx(data_input, ai_data):
    doc = Document()
    
    heading = doc.add_heading('MODUL AJAR / RPP', 0)
    heading.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph("")

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
    
    doc.add_heading('A. Tujuan Pembelajaran', level=1)
    doc.add_paragraph(ai_data.get('tujuan', '-'))

    doc.add_heading('B. Profil Lulusan', level=1)
    if data_input['profil']:
        for p in data_input['profil']:
            doc.add_paragraph(f"- {p}", style='List Bullet')

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

# --- 6. HALAMAN GENERATOR ---
def page_generator():
    st.title("📚 Generator Modul Ajar Otomatis")
    
    # Running Text
    st.markdown("""
        <div class="running-text-container">
            <marquee direction="left" scrollamount="8" style="color: red; font-weight: bold; font-size: 16px;">
            Aplikasi ini dibuat oleh Ceng Ucu Muhammad, S.H - SMP IT Nurusy Syifa
            </marquee>
        </div>
    """, unsafe_allow_html=True)
    
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
            "Pilih Profil:", 
            options=st.session_state['profil_db'],
            default=st.session_state['profil_db'][:2] 
        )
        
        st.markdown("---")
        submitted = st.form_submit_button("🚀 Generate Modul Ajar")

    if submitted:
        if not topik or not mapel:
            st.error("❌ Mohon isi Mapel dan Topik!")
        else:
            with st.spinner("🤖 AI sedang bekerja..."):
                ai_result = generate_rpp_content("gemini-1.5-flash", mapel, topik, kelas, waktu, profil_pilihan)
                
                if ai_result:
                    data_input = {
                        'guru': nama_guru, 'sekolah': nama_sekolah, 'kepsek': nama_kepsek,
                        'mapel': mapel, 'kelas': kelas, 'waktu': waktu,
                        'profil': profil_pilihan
                    }
                    docx_file = create_docx(data_input, ai_result)
                    
                    st.success("✅ Selesai! Silakan download.")
                    st.download_button(
                        label="📥 Download (.docx)",
                        data=docx_file,
                        file_name=f"Modul_{mapel}.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    )
                    with st.expander("Lihat Hasil"):
                        st.write(ai_result)

# --- 7. HALAMAN PROFIL ---
def page_profil():
    st.title("🎓 Database Profil")
    new_item = st.text_input("Tambah Profil Baru")
    if st.button("Tambah"):
        if new_item:
            st.session_state['profil_db'].append(new_item)
            st.success("OK")
    
    for i, item in enumerate(st.session_state['profil_db']):
        c1, c2 = st.columns([4, 1])
        c1.text(item)
        if c2.button("Hapus", key=f"del_{i}"):
            st.session_state['profil_db'].pop(i)
            st.rerun()

# --- 8. NAVIGASI ---
with st.sidebar:
    st.title("Menu Aplikasi")
    # SAYA HAPUS GAMBARNYA SUPAYA TIDAK ERROR LAGI
    st.write("---")
    menu = st.radio("Pilih Halaman:", ["📝 Buat Modul Ajar", "🎓 Database Profil", "ℹ️ Tentang"])

if menu == "📝 Buat Modul Ajar":
    page_generator()
elif menu == "🎓 Database Profil":
    page_profil()
elif menu == "ℹ️ Tentang":
    st.title("Tentang")
    st.write("Dibuat oleh: Ceng Ucu Muhammad, S.H")
    st.write("SMP IT Nurusy Syifa")
