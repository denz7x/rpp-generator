import streamlit as st
import google.generativeai as genai
import json
import io
from docx import Document
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH

# ==========================================
# 1. KONFIGURASI API KEY (WAJIB DIGANTI!)
# ==========================================
# Tempel API Key BARU Bapak di dalam tanda kutip di bawah ini:
MY_API_KEY = "AIzaSyBNML1Sxl73d2H8-AMsHKQm1RryGH1YRWc"

# Konfigurasi Awal
try:
    genai.configure(api_key=MY_API_KEY)
except Exception as e:
    st.error(f"Error Konfigurasi: {e}")

# ==========================================
# 2. PENGATURAN TAMPILAN (UI)
# ==========================================
st.set_page_config(page_title="Generator Modul Ajar Pro", page_icon="📝", layout="wide")

st.markdown("""
<style>
    .stButton>button { 
        width: 100%; border-radius: 8px; font-weight: bold; 
        background-color: #2e7d32; color: white; height: 3em;
    }
    .running-text {
        background-color: #e8f5e9; padding: 10px; 
        border: 1px solid #c8e6c9; margin-bottom: 20px; text-align: center;
    }
    .preview-box {
        border: 1px solid #ddd; padding: 20px; border-radius: 10px;
        background-color: #ffffff; margin-top: 20px;
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

# ==========================================
# 4. FUNGSI LOGIKA (BACKEND)
# ==========================================

# A. Cari Model AI Otomatis
def get_available_model():
    try:
        available_models = []
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                available_models.append(m.name)
        
        if not available_models: return None
        # Prioritas model
        if "models/gemini-1.5-flash" in available_models: return "models/gemini-1.5-flash"
        if "models/gemini-pro" in available_models: return "models/gemini-pro"
        return available_models[0]
    except:
        return "models/gemini-pro"

# B. Fungsi Generate Konten AI
def generate_rpp_content(model_name, mapel, topik, kelas, waktu, profil_list, pakai_lkpd):
    try:
        model = genai.GenerativeModel(model_name)
        profil_str = ", ".join(profil_list)
        
        # Instruksi Tambahan untuk LKPD
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
        
        response = model.generate_content(prompt)
        text = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(text)
    except Exception as e:
        st.error(f"Gagal Generate: {str(e)}")
        return None

# C. Fungsi Membuat Word (Rapi dengan Tabel)
def create_docx(data_input, ai_data, pakai_lkpd):
    doc = Document()
    
    # Judul Dokumen
    head = doc.add_heading('MODUL AJAR / RPP', 0)
    head.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph("")

    # --- TABEL IDENTITAS (Agar Rapi) ---
    table = doc.add_table(rows=5, cols=3)
    table.autofit = False
    # Atur lebar kolom: Label | Titik Dua | Isi
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
        # Set teks
        table.cell(i,0).text = label
        table.cell(i,1).text = ":"
        table.cell(i,2).text = val
        # Hapus spasi paragraf agar tabel rapat
        table.cell(i,0).paragraphs[0].paragraph_format.space_after = Pt(2)
        table.cell(i,2).paragraphs[0].paragraph_format.space_after = Pt(2)

    doc.add_paragraph("") # Spasi

    # --- ISI MODUL ---
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
    
    # Kegiatan Pembelajaran
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

    # --- TANDA TANGAN (TABEL) ---
    doc.add_paragraph("\n\n")
    sig_table = doc.add_table(rows=1, cols=2)
    sig_table.autofit = True
    
    c1 = sig_table.cell(0,0)
    c1.text = f"Mengetahui,\nKepala Sekolah\n\n\n\n{data_input['kepsek']}"
    c1.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    c2 = sig_table.cell(0,1)
    c2.text = f"Guru Mata Pelajaran\n\n\n\n{data_input['guru']}"
    c2.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER

    # --- LKPD (HALAMAN BARU) ---
    if pakai_lkpd == "Ya" and ai_data.get('lkpd'):
        doc.add_page_break()
        doc.add_heading('LAMPIRAN: LEMBAR KERJA PESERTA DIDIK (LKPD)', 0)
        doc.add_paragraph("")
        doc.add_paragraph(f"Nama Siswa : ...................................")
        doc.add_paragraph(f"Kelas      : {data_input['kelas']}")
        doc.add_paragraph("----------------------------------------------------------------------------------")
        doc.add_paragraph(ai_data.get('lkpd'))

    # Simpan ke memori
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

# ==========================================
# 5. HALAMAN UTAMA (FRONTEND)
# ==========================================
def page_generator():
    st.title("📚 Generator Modul Ajar & LKPD")
    st.markdown("""
        <div class="running-text">
            <b>Aplikasi ini dibuat oleh Ceng Ucu Muhammad, S.H - SMP IT Nurusy Syifa</b>
        </div>
    """, unsafe_allow_html=True)

    # Cek Model
    active_model = get_available_model()
    if not active_model:
        st.error("⚠️ API Key bermasalah atau kuota habis. Silakan buat API Key baru.")
        st.stop()

    # --- FORM INPUT ---
    with st.form("main_form"):
        st.subheader("1. Identitas")
        c1, c2, c3 = st.columns(3)
        nama_guru = c1.text_input("Nama Guru")
        nama_sekolah = c2.text_input("Nama Sekolah")
        nama_kepsek = c3.text_input("Nama Kepala Sekolah")
        
        st.subheader("2. Materi & Pilihan")
        c4, c5 = st.columns(2)
        with c4:
            mapel = st.text_input("Mata Pelajaran", "IPA")
            kelas = st.selectbox("Kelas", ["VII", "VIII", "IX", "X", "XI", "XII"])
            profil = st.multiselect("Profil Pancasila", st.session_state['profil_db'], default=st.session_state['profil_db'][:2])
        with c5:
            waktu = st.text_input("Alokasi Waktu", "2 JP (2x40 Menit)")
            topik = st.text_input("Topik Materi (Wajib)", "Sistem Pencernaan")
            # PILIHAN LKPD
            pilihan_lkpd = st.radio("Sertakan Lembar Kerja (LKPD)?", ["Tidak", "Ya"], horizontal=True)

        st.markdown("---")
        submitted = st.form_submit_button("🚀 PROSES DATA (KLIK SEKALI)")

    # --- LOGIKA SETELAH TOMBOL DITEKAN ---
    if submitted:
        if not topik:
            st.warning("⚠️ Topik materi wajib diisi agar AI bisa bekerja.")
        else:
            with st.spinner("🤖 AI sedang menyusun Modul Ajar & LKPD..."):
                # 1. Generate Konten
                res = generate_rpp_content(active_model, mapel, topik, kelas, waktu, profil, pilihan_lkpd)
                
                if res:
                    # 2. Siapkan Data
                    data_input = {
                        'guru': nama_guru, 'sekolah': nama_sekolah, 'kepsek': nama_kepsek,
                        'mapel': mapel, 'kelas': kelas, 'waktu': waktu, 'profil': profil
                    }
                    
                    # 3. Tampilkan Preview (FITUR BARU)
                    st.success("✅ Selesai! Silakan cek preview di bawah sebelum download.")
                    
                    with st.expander("👁️ PREVIEW HASIL (Klik untuk menutup/buka)", expanded=True):
                        st.markdown(f"### Tujuan Pembelajaran")
                        st.write(res.get('tujuan'))
                        
                        c_prev1, c_prev2 = st.columns(2)
                        with c_prev1:
                            st.markdown("### Kegiatan Inti")
                            st.write(res.get('inti'))
                        with c_prev2:
                            st.markdown("### Asesmen")
                            st.write(res.get('asesmen'))
                        
                        if pilihan_lkpd == "Ya":
                            st.markdown("---")
                            st.markdown("### 📝 Preview LKPD")
                            st.info(res.get('lkpd'))

                    # 4. Buat Word
                    docx_file = create_docx(data_input, res, pilihan_lkpd)
                    
                    # 5. Tombol Download
                    st.download_button(
                        label="📥 DOWNLOAD FORMAT WORD (.DOCX)",
                        data=docx_file,
                        file_name=f"Modul_Ajar_{mapel}_{kelas}.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        type="primary"
                    )

# ==========================================
# 6. HALAMAN DATABASE PROFIL
# ==========================================
def page_profil():
    st.title("🎓 Database Profil")
    baru = st.text_input("Tambah Profil Baru")
    if st.button("Simpan") and baru:
        st.session_state['profil_db'].append(baru)
        st.rerun()
    
    st.write("Daftar Profil Saat Ini:")
    for i, p in enumerate(st.session_state['profil_db']):
        cols = st.columns([0.8, 0.2])
        cols[0].info(p)
        if cols[1].button("Hapus", key=f"del_{i}"):
            st.session_state['profil_db'].pop(i)
            st.rerun()

# ==========================================
# 7. NAVIGASI UTAMA
# ==========================================
with st.sidebar:
    st.title("Menu Navigasi")
    menu = st.radio("Pilih:", ["📝 Buat Modul Ajar", "🎓 Database Profil", "ℹ️ Tentang"])

if menu == "📝 Buat Modul Ajar":
    page_generator()
elif menu == "🎓 Database Profil":
    page_profil()
elif menu == "ℹ️ Tentang":
    st.title("Tentang Aplikasi")
    st.write("Generator Modul Ajar & LKPD (Support Word Table)")
    st.caption("Dikembangkan oleh: Ceng Ucu Muhammad, S.H - SMP IT Nurusy Syifa")
