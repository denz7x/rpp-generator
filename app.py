import streamlit as st
from datetime import datetime
import io
# Pastikan library python-docx sudah terinstall
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH

# --- KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="Generator RPP Deep Learning",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM CSS ---
def local_css():
    st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

local_css()

# --- DATABASE SEMENTARA ---
if 'profil_lulusan_db' not in st.session_state:
    st.session_state['profil_lulusan_db'] = [
        "Beriman, Bertakwa kepada Tuhan YME, dan Berakhlak Mulia",
        "Berkebinekaan Global",
        "Bergotong Royong",
        "Mandiri",
        "Bernalar Kritis",
        "Kreatif"
    ]

# --- FUNGSI GENERATE WORD (DOCX) ---
def generate_rpp_docx(data):
    doc = Document()
    
    # Judul
    heading = doc.add_heading('RENCANA PELAKSANAAN PEMBELAJARAN (RPP)', 0)
    heading.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    doc.add_paragraph("") # Spasi

    # Tabel Identitas
    table = doc.add_table(rows=4, cols=3)
    table.autofit = False
    table.columns[0].width = Inches(1.5) 
    table.columns[1].width = Inches(0.2) 
    table.columns[2].width = Inches(4.0) 

    def fill_row(row_idx, label, value):
        table.cell(row_idx, 0).text = label
        table.cell(row_idx, 1).text = ":"
        table.cell(row_idx, 2).text = value

    fill_row(0, "Nama Sekolah", data['sekolah'])
    fill_row(1, "Mata Pelajaran", data['mapel'])
    fill_row(2, "Kelas / Semester", data['kelas'])
    fill_row(3, "Alokasi Waktu", data['waktu'])
    
    doc.add_paragraph("") 

    # A. Tujuan
    doc.add_heading('A. Tujuan Pembelajaran', level=1)
    doc.add_paragraph(data['tujuan'])

    # B. Profil Lulusan
    doc.add_heading('B. Profil Lulusan / Profil Pelajar Pancasila', level=1)
    if data['profil']:
        for item in data['profil']:
            p = doc.add_paragraph(item, style='List Bullet')
    else:
        doc.add_paragraph("-")

    # C. Materi
    doc.add_heading('C. Materi Pokok', level=1)
    doc.add_paragraph(data['materi'])

    # D. Kegiatan
    doc.add_heading('D. Kegiatan Pembelajaran', level=1)
    
    p_pend = doc.add_paragraph()
    p_pend.add_run("1. Pendahuluan").bold = True
    doc.add_paragraph(data['pendahuluan'])
    
    p_inti = doc.add_paragraph()
    p_inti.add_run("2. Kegiatan Inti").bold = True
    doc.add_paragraph(data['inti'])
    
    p_penutup = doc.add_paragraph()
    p_penutup.add_run("3. Penutup").bold = True
    doc.add_paragraph(data['penutup'])

    # E. Penilaian
    doc.add_heading('E. Penilaian', level=1)
    doc.add_paragraph(f"Sikap: {data['sikap']}")
    doc.add_paragraph(f"Pengetahuan: {data['pengetahuan']}")
    doc.add_paragraph(f"Keterampilan: {data['keterampilan']}")

    doc.add_paragraph("")
    doc.add_paragraph("")

    # Tanda Tangan
    sig_table = doc.add_table(rows=1, cols=2)
    sig_table.autofit = True
    
    cell_kepsek = sig_table.cell(0, 0)
    p_kepsek = cell_kepsek.paragraphs[0]
    p_kepsek.add_run(f"Mengetahui,\nKepala Sekolah\n\n\n\n\n{data['kepsek']}").bold = True
    p_kepsek.alignment = WD_ALIGN_PARAGRAPH.CENTER

    cell_guru = sig_table.cell(0, 1)
    p_guru = cell_guru.paragraphs[0]
    p_guru.add_run(f"Guru Mata Pelajaran\n\n\n\n\n\n{data['guru']}").bold = True
    p_guru.alignment = WD_ALIGN_PARAGRAPH.CENTER

    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

# --- FUNGSI HALAMAN UTAMA ---
def show_home():
    st.title("📚 Generator RPP Terintegrasi")
    
    # === [UPDATE] RUNNING TEXT DITAMBAHKAN DI SINI ===
    st.markdown("""
        <marquee direction="left" scrollamount="8" style="color: red; font-weight: bold; font-size: 16px;">
        Aplikasi ini dibuat oleh Ceng Ucu Muhammad, S.H - SMP IT Nurusy Syifa
        </marquee>
    """, unsafe_allow_html=True)
    # ==================================================

    st.markdown("---")
    
    # --- FORMULIR ---
    with st.form("rpp_form"):
        st.subheader("1. Identitas")
        c1, c2 = st.columns(2)
        with c1:
            nama_guru = st.text_input("Nama Guru")
            nama_sekolah = st.text_input("Nama Sekolah")
            kepala_sekolah = st.text_input("Nama Kepala Sekolah")
        with c2:
            mata_pelajaran = st.text_input("Mata Pelajaran")
            kelas_semester = st.selectbox("Kelas / Semester", ["VII / Ganjil", "VII / Genap", "VIII / Ganjil", "VIII / Genap", "IX / Ganjil", "IX / Genap", "X / Ganjil", "X / Genap", "XI / Ganjil", "XI / Genap", "XII / Ganjil", "XII / Genap"])
            alokasi_waktu = st.text_input("Alokasi Waktu (Misal: 2 JP)")

        st.subheader("2. Komponen Inti")
        st.markdown("##### 🌱 Profil Lulusan")
        profil_terpilih = st.multiselect("Pilih Profil:", options=st.session_state['profil_lulusan_db'])
        
        c3, c4 = st.columns(2)
        with c3:
            tujuan = st.text_area("Tujuan Pembelajaran", height=100)
        with c4:
            materi = st.text_area("Materi Pokok", height=100)

        with st.expander("📝 Kegiatan Pembelajaran"):
            pendahuluan = st.text_area("Pendahuluan")
            inti = st.text_area("Inti")
            penutup = st.text_area("Penutup")

        with st.expander("📊 Penilaian"):
            sikap = st.text_input("Penilaian Sikap")
            pengetahuan = st.text_input("Penilaian Pengetahuan")
            keterampilan = st.text_input("Penilaian Keterampilan")

        # Tombol Submit Form
        submitted = st.form_submit_button("🚀 Generate RPP")

    # --- LOGIKA DI LUAR FORM (AGAR TIDAK ERROR) ---
    if submitted:
        data_rpp = {
            'guru': nama_guru, 'sekolah': nama_sekolah, 'kepsek': kepala_sekolah,
            'mapel': mata_pelajaran, 'kelas': kelas_semester, 'waktu': alokasi_waktu,
            'profil': profil_terpilih, 'tujuan': tujuan, 'materi': materi,
            'pendahuluan': pendahuluan, 'inti': inti, 'penutup': penutup,
            'sikap': sikap, 'pengetahuan': pengetahuan, 'keterampilan': keterampilan
        }
        
        st.success("RPP Berhasil Dibuat! Silakan download di bawah ini.")
        
        # Buat file Word
        docx_file = generate_rpp_docx(data_rpp)
        
        # Tombol Download
        st.download_button(
            label="📥 Download RPP (.docx)",
            data=docx_file,
            file_name=f"RPP_{mata_pelajaran}_{kelas_semester}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        
        st.markdown("---")
        st.markdown("### Preview Hasil")
        st.write(f"**Tujuan:** {tujuan}")
        st.write(f"**Profil:** {', '.join(profil_terpilih)}")

def show_profil_lulusan():
    st.title("🎓 Kelola Profil Lulusan")
    col_input, col_btn = st.columns([3, 1])
    with col_input:
        new_profil = st.text_input("Tambah Profil Baru")
    with col_btn:
        st.write("")
        st.write("")
        if st.button("Tambah"):
            if new_profil:
                st.session_state['profil_lulusan_db'].append(new_profil)
                st.success("Ditambahkan.")
    
    for i, profil in enumerate(st.session_state['profil_lulusan_db']):
        c_txt, c_del = st.columns([4, 1])
        with c_txt: st.info(profil)
        with c_del: 
            if st.button("Hapus", key=f"del_{i}"):
                st.session_state['profil_lulusan_db'].pop(i)
                st.rerun()

# --- NAVIGASI ---
with st.sidebar:
    st.title("Navigasi")
    menu = st.radio("Menu", ["📝 Buat RPP", "🎓 Database Profil", "ℹ️ Tentang"])

if menu == "📝 Buat RPP": show_home()
elif menu == "🎓 Database Profil": show_profil_lulusan()
elif menu == "ℹ️ Tentang":
    st.title("Tentang")
    # Teks credit juga bisa ditaruh di sini jika mau
    st.write("Aplikasi Generator RPP v4.0")
    st.write("Dibuat oleh Ceng Ucu Muhammad, S.H - SMP IT Nurusy Syifa")
