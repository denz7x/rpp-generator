import streamlit as st
import google.generativeai as genai
from docx import Document
import io

# --- 1. KONFIGURASI API KEY (Menggunakan Secrets) ---
try:
    # Mengambil API Key dari Secrets Streamlit Cloud
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=GOOGLE_API_KEY)
except Exception as e:
    st.error("⚠️ API Key belum diatur di Secrets Streamlit Cloud.")
    st.stop()

st.set_page_config(page_title="Generator Modul Ajar", page_icon="📚")

# --- 2. FUNGSI PEMBUAT WORD ---
def create_docx(text_content, mapel, topik):
    doc = Document()
    doc.add_heading(f'Modul Ajar - {mapel}', 0)
    doc.add_heading(f'Topik: {topik}', level=1)
    
    # Menambahkan isi dari AI ke dokumen
    # Catatan: Ini akan masuk sebagai teks biasa. 
    doc.add_paragraph(text_content)
    
    doc.add_paragraph('\n\nDicetak otomatis oleh Generator RPP AI.')
    
    # Simpan ke memori (buffer) agar bisa didownload
    bio = io.BytesIO()
    doc.save(bio)
    bio.seek(0)
    return bio

# --- 3. SISTEM PENCARI MODEL OTOMATIS ---
st.sidebar.header("⚙️ Pengaturan AI")
try:
    available_models = []
    # Mencari model yang mendukung generateContent
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            available_models.append(m.name)
            
    # Prioritaskan model flash jika ada (lebih cepat)
    default_index = 0
    for i, model_name in enumerate(available_models):
        if "flash" in model_name:
            default_index = i
            break

    if available_models:
        selected_model = st.sidebar.selectbox("Model AI:", available_models, index=default_index)
        model = genai.GenerativeModel(selected_model)
        st.sidebar.success(f"✅ Aktif: {selected_model}")
    else:
        st.sidebar.error("❌ Tidak ada model AI yang ditemukan.")
        st.stop()

except Exception as e:
    st.sidebar.warning(f"Gagal memuat daftar model otomatis. Menggunakan default. Error: {e}")
    model = genai.GenerativeModel('gemini-1.5-flash') # Fallback manual

# --- 4. TAMPILAN APLIKASI ---
st.title("📚 Generator Perencanaan Pembelajaran")
st.markdown("Buat Modul Ajar/RPP lalu download file Word-nya.")

# Form Input
st.header("1. Informasi Umum")
col1, col2 = st.columns(2)
with col1:
    mapel = st.text_input("Mata Pelajaran", placeholder="Contoh: IPA")
    jenjang = st.selectbox("Jenjang", ["PAUD", "SD/MI", "SMP/MTs", "SMA/MA", "SMK"])
with col2:
    kelas = st.text_input("Kelas", placeholder="Contoh: 7")
    semester = st.selectbox("Semester", ["Ganjil", "Genap"])

durasi = st.text_input("Durasi Waktu", placeholder="Contoh: 2 x 45 menit")

st.header("2. Detail Pembelajaran")
topik = st.text_input("Topik Materi (Wajib)", placeholder="Masukan topik materi...")
tp = st.text_area("Tujuan Pembelajaran (Opsional)", height=100)
metode = st.multiselect("Metode Pembelajaran", ["PBL", "PjBL", "Discovery Learning", "Diskusi", "Ceramah"])
lkpd = st.radio("Buatkan Lampiran LKPD?", ["Ya", "Tidak"])

# Tombol Eksekusi
if st.button("🚀 Buat Modul Ajar", type="primary"):
    if not mapel or not topik:
        st.warning("⚠️ Mohon lengkapi Mata Pelajaran dan Topik Materi!")
    else:
        with st.spinner("Sedang meracik Modul Ajar... (Tunggu ya)"):
            # Prompt disesuaikan agar outputnya lebih bersih untuk Word
            prompt = f"""
            Buatkan Modul Ajar lengkap (RPP) untuk:
            Mapel: {mapel}, Kelas: {kelas}, Topik: {topik}.
            Metode: {', '.join(metode)}.
            
            Kelengkapan:
            1. Informasi Umum (Identitas Sekolah, Profil Pelajar Pancasila)
            2. Komponen Inti (Tujuan, Pemahaman Bermakna, Pertanyaan Pemantik)
            3. Langkah Pembelajaran (Pendahuluan, Inti, Penutup)
            4. Asesmen
            5. {lkpd} buatkan lampiran soal LKPD.

            Tuliskan isinya secara terstruktur tanpa menggunakan terlalu banyak format Markdown (seperti bold/italic) agar rapi saat dicetak ke Word.
            """
            
            try:
                # Minta AI berpikir
                response = model.generate_content(prompt)
                rpp_text = response.text
                
                # Tampilkan di layar
                st.success("Selesai! Silakan baca di bawah atau download file-nya.")
                st.markdown("---")
                
                # --- FITUR DOWNLOAD TOMBOL ---
                # Panggil fungsi pembuat docx
                docx_file = create_docx(rpp_text, mapel, topik)
                
                st.download_button(
                    label="📄 Download File Word (.docx)",
                    data=docx_file,
                    file_name=f"Modul_Ajar_{mapel}_{topik}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )
                
                st.markdown("---")
                st.text_area("Preview Hasil:", value=rpp_text, height=400)
                
            except Exception as e:
                st.error(f"Terjadi kesalahan: {e}")
