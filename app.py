import streamlit as st
import google.generativeai as genai
import json
import io
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH

# --- 1. KONFIGURASI HALAMAN & CSS ---
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
    h1, h2, h3 { color: #2c3e50; }
    .stTextInput>div>div>input { border-radius: 8px; }
</style>
""", unsafe_allow_html=True)

# --- 2. DATABASE SEMENTARA (SESSION STATE) ---
# Menyimpan Profil Lulusan agar bisa diedit
if 'profil_db' not in st.session_state:
    st.session_state['profil_db'] = [
        "Beriman, Bertakwa kepada Tuhan YME, dan Berakhlak Mulia",
        "Berkebinekaan Global",
        "Bergotong Royong",
        "Mandiri",
        "Bernalar Kritis",
        "Kreatif"
    ]

# --- 3. FUNGSI AI GENERATOR (GEMINI) ---
def generate_rpp_content(api_key, model_name, mapel, topik, kelas, waktu, profil_list):
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_name)
    
    profil_str = ", ".join(profil_list)
    
    # Prompt khusus agar AI mengeluarkan data JSON
    prompt = f"""
    Bertindaklah sebagai Guru Profesional. Buatkan konten Modul Ajar/RPP lengkap.
    
    Informasi:
    - Mapel: {mapel}
    - Kelas: {kelas}
    - Topik: {topik}
    - Waktu: {waktu}
    - Profil Lulusan: {profil_str}

    Instruksi Penting:
    Berikan output HANYA dalam format JSON valid (tanpa markdown ```json).
    Struktur JSON harus seperti ini:
    {{
        "tujuan": "Tuliskan 2 tujuan pembelajaran spesifik.",
        "pemahaman": "Pertanyaan pemantik atau pemahaman bermakna.",
        "pendahuluan": "Langkah kegiatan pendahuluan (poin-poin).",
        "inti": "Langkah kegiatan inti detail sesuai model pembelajaran aktif.",
        "penutup": "Kegiatan penutup dan refleksi.",
        "asesmen": "Teknik penilaian (Sikap, Pengetahuan, Keterampilan)."
    }}
    Pastikan bahasa Indonesia formal pendidikan.
    """
    
    try:
        response = model.generate_content(prompt)
        # Membersihkan hasil jika AI menyertakan backticks markdown
        clean_text = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(clean_text)
    except Exception as e:
        return None

# --- 4. FUNGSI PEMBUAT DOCX (WORD) ---
def create_docx(data_input, ai_data):
    doc = Document()
    
    # Gaya Judul
    heading = doc.add_heading('MODUL AJAR / RPP', 0)
    heading.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph("")

    # Tabel Identitas (Agar Rapi)
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
            doc.add_paragraph(f"- {p}")
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
    c1.text = f"Mengetahui,\nKepala Sekolah\n\n\n\n{data_input['kepsek']}"
    c1.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    c2 = sig_table.cell(0, 1)
    c2.text = f"Guru Mata Pelajaran\n\n\n\n{data_input['guru']}"
    c2.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER

    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

# --- 5. HALAMAN: UTAMA (GENERATOR) ---
def page_generator():
    st.title("📚 Generator Modul Ajar Otomatis")
    
    # RUNNING TEXT (FITUR PERMINTAAN)
    st.markdown("""
        <div style='background-color: #ffe6e6; padding: 10px; border-radius: 5px;'>
            <marquee direction="left" scrollamount="8" style="color: red; font-weight: bold; font-size: 16px;">
            Aplikasi ini dibuat oleh Ceng Ucu Muhammad, S.H - SMP IT Nurusy Syifa
            </marquee>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Ambil API Key dari Sidebar
    api_key = st.session_state.get('api_key', '')
    model_choice = st.session_state.get('model_choice', 'gemini-1.5-flash')

    if not api_key:
        st.warning("⚠️ Silakan masukkan API Key di menu sebelah kiri (Sidebar) terlebih dahulu.")
        return

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
            topik = st.text_input("Topik Materi (Wajib)", placeholder="Contoh: Pencemaran Lingkungan")

        st.subheader("3. Profil Lulusan")
        profil_pilihan = st.multiselect(
            "Pilih Profil yang ingin dikuatkan:", 
            options=st.session_state['profil_db'],
            default=st.session_state['profil_db'][:2] # Default pilih 2 pertama
        )
        
        st.markdown("---")
        submitted = st.form_submit_button("🚀 Generate Modul Ajar (AI)")

    # LOGIKA SETELAH TOMBOL DITEKAN
    if submitted:
        if not topik or not mapel:
            st.error("❌ Mata Pelajaran dan Topik wajib diisi!")
        else:
            with st.spinner("🤖 AI sedang berpikir dan menyusun dokumen..."):
                # 1. Panggil AI
                ai_result = generate_rpp_content(api_key, model_choice, mapel, topik, kelas, waktu, profil_pilihan)
                
                if ai_result:
                    # 2. Siapkan Data untuk Word
                    data_input = {
                        'guru': nama_guru, 'sekolah': nama_sekolah, 'kepsek': nama_kepsek,
                        'mapel': mapel, 'kelas': kelas, 'waktu': waktu,
                        'profil': profil_pilihan
                    }
                    
                    # 3. Buat File Word
                    docx_file = create_docx(data_input, ai_result)
                    
                    st.success("✅ Berhasil! Silakan download dokumen di bawah ini.")
                    
                    # 4. Tombol Download
                    st.download_button(
                        label="📥 Download Modul Ajar (.docx)",
                        data=docx_file,
                        file_name=f"Modul_Ajar_{mapel}_{kelas}.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    )
                    
                    # 5. Preview Singkat
                    with st.expander("👁️ Lihat Preview Konten AI"):
                        st.json(ai_result)
                else:
                    st.error("Gagal mendapatkan respons dari AI. Cek API Key atau koneksi internet.")

# --- 6. HALAMAN: DATABASE PROFIL ---
def page_profil():
    st.title("🎓 Database Profil Lulusan")
    st.info("Di sini Anda bisa menambah atau menghapus opsi Profil Lulusan yang muncul di halaman utama.")
    
    col_in, col_btn = st.columns([3, 1])
    with col_in:
        new_item = st.text_input("Tambah Profil Baru")
    with col_btn:
        st.write("")
        st.write("") # Spasi layout
        if st.button("➕ Tambah"):
            if new_item and new_item not in st.session_state['profil_db']:
                st.session_state['profil_db'].append(new_item)
                st.success("Ditambahkan!")
    
    st.markdown("### Daftar Profil Saat Ini:")
    for i, item in enumerate(st.session_state['profil_db']):
        c1, c2 = st.columns([4, 1])
        c1.markdown(f"**{i+1}. {item}**")
        if c2.button("Hapus", key=f"del_{i}"):
            st.session_state['profil_db'].pop(i)
            st.rerun()

# --- 7. NAVIGASI SIDEBAR ---
with st.sidebar:
    st.title("Navigasi")
    
    # Input API Key (Supaya Aman & Fleksibel)
    st.markdown("### 🔑 Konfigurasi AI")
    # Default key bisa dimasukkan di value="" jika untuk penggunaan pribadi sendiri
    # Namun disarankan dikosongkan agar user input sendiri
    api_key_input = st.text_input("Google API Key", type="password", help="Dapatkan di aistudio.google.com")
    if api_key_input:
        st.session_state['api_key'] = api_key_input
    
    # Pilihan Model
    model_opts = ["gemini-1.5-flash", "gemini-pro"]
    st.session_state['model_choice'] = st.selectbox("Model AI", model_opts)

    st.markdown("---")
    menu = st.radio("Pilih Menu:", ["📝 Buat Modul Ajar", "🎓 Database Profil", "ℹ️ Tentang"])

# --- 8. ROUTING ---
if menu == "📝 Buat Modul Ajar":
    page_generator()
elif menu == "🎓 Database Profil":
    page_profil()
elif menu == "ℹ️ Tentang":
    st.title("Tentang Aplikasi")
    st.write("Aplikasi Generator Modul Ajar ini dikembangkan untuk membantu guru menyusun administrasi dengan cepat menggunakan kecerdasan buatan (AI).")
    st.markdown("**Developer:** Ceng Ucu Muhammad, S.H")
    st.markdown("**Instansi:** SMP IT Nurusy Syifa")
