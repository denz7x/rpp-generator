import streamlit as st
import google.generativeai as genai

# --- 1. KONFIGURASI API KEY ---
# GANTI TULISAN DI BAWAH INI DENGAN API KEY ANDA
GOOGLE_API_KEY = "AIzaSyDm4BXch5vuDdl5jodG4xUx78-4iqdX0r0"

# Setup Awal
try:
    genai.configure(api_key=GOOGLE_API_KEY)
except Exception as e:
    st.error(f"Terjadi kesalahan konfigurasi API Key: {e}")

st.set_page_config(page_title="Generator Modul Ajar", page_icon="📚")

# --- 2. SISTEM OTOMATIS PENCARI MODEL ---
# Bagian ini akan mencari model yang tersedia di akun Anda agar tidak error 404 lagi
st.sidebar.header("⚙️ Pengaturan AI")
try:
    available_models = []
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            available_models.append(m.name)
    
    # Jika model ditemukan, buat menu pilihan
    if available_models:
        selected_model_name = st.sidebar.selectbox("Pilih Model AI yang Tersedia:", available_models)
        model = genai.GenerativeModel(selected_model_name)
        st.sidebar.success(f"✅ Terhubung ke: {selected_model_name}")
    else:
        st.sidebar.error("❌ Tidak ada model AI yang ditemukan pada API Key ini.")
        st.stop()
        
except Exception as e:
    st.sidebar.error(f"Gagal memuat daftar model. Cek API Key Anda.\nError: {e}")
    st.stop()

# --- 3. TAMPILAN APLIKASI UTAMA ---
st.title("📚 Generator Perencanaan Pembelajaran Mendalam")
st.markdown("Alat bantu guru untuk membuat draft Modul Ajar / RPP secara instan.")
st.markdown("developed by : @denz7x")

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
topik = st.text_input("Topik Materi (Wajib diisi)", placeholder="Masukan topik materi...")
tp = st.text_area("Tujuan Pembelajaran (Opsional)", height=100)
metode = st.multiselect("Metode Pembelajaran", ["PBL", "PjBL", "Discovery Learning", "Diskusi", "Ceramah"])
lkpd = st.radio("Buatkan Lampiran LKPD?", ["Ya", "Tidak"])

# Tombol Eksekusi
if st.button("🚀 Buat Modul Ajar", type="primary"):
    if not mapel or not topik:
        st.warning("⚠️ Mohon lengkapi Mata Pelajaran dan Topik Materi!")
    else:
        with st.spinner("Sedang berpikir... (Mungkin butuh 10-30 detik)"):
            prompt = f"""
            Buatkan Modul Ajar lengkap untuk:
            Mapel: {mapel}, Kelas: {kelas}, Topik: {topik}, Model: {metode}.
            Kelengkapan: Informasi Umum, Komponen Inti, Langkah Pembelajaran, Asesmen, dan {lkpd} buatkan LKPD.
            """
            try:
                response = model.generate_content(prompt)
                st.success("Selesai!")
                st.markdown(response.text)
            except Exception as e:
                st.error(f"Terjadi kesalahan saat membuat konten: {e}")