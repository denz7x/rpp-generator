import streamlit as st
import google.generativeai as genai
import json
import io
from docx import Document
from docx.shared import Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH

# --- 1. KONFIGURASI API KEY (WAJIB DIGANTI) ---
# Hapus tulisan PASTE_KEY_BARU_DISINI dan tempel API Key baru Anda di antara tanda kutip
MY_API_KEY = "AIzaSyBNML1Sxl73d2H8-AMsHKQm1RryGH1YRWc"

# Konfigurasi Awal
try:
    genai.configure(api_key=MY_API_KEY)
except Exception as e:
    st.error(f"Error Konfigurasi: {e}")

# --- 2. SETUP HALAMAN ---
st.set_page_config(
    page_title="AI Modul Ajar Generator",
    page_icon="🎓",
    layout="wide"
)

# CSS Tampilan
st.markdown("""
<style>
    .stButton>button { 
        width: 100%; border-radius: 8px; font-weight: bold; 
        background-color: #4CAF50; color: white; height: 3em;
    }
    .running-text {
        background-color: #ffe6e6; padding: 10px; 
        border: 1px solid #ffcccc; margin-bottom: 20px;
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

# --- 4. FUNGSI OTOMATIS CARI MODEL ---
def get_available_model():
    try:
        available_models = []
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                available_models.append(m.name)
        
        if not available_models:
            return None
        
        # Prioritas: Flash -> Pro -> Apa saja
        if "models/gemini-1.5-flash" in available_models:
            return "models/gemini-1.5-flash"
        if "models/gemini-pro" in available_models:
            return "models/gemini-pro"
            
        return available_models[0]
    except:
        return "models/gemini-pro" 

# --- 5. FUNGSI AI ---
def generate_rpp_content(model_name, mapel, topik, kelas, waktu, profil_list):
    try:
        model = genai.GenerativeModel(model_name)
        profil_str = ", ".join(profil_list)
        
        prompt = f"""
        Buatkan Modul Ajar Kurikulum Merdeka (JSON Format).
        Mapel: {mapel}, Kelas: {kelas}, Topik: {topik}, Waktu: {waktu}, Profil: {profil_str}.
        
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
        st.error(f"Gagal Generate (Cek API Key): {str(e)}")
        return None

# --- 6. FUNGSI WORD ---
def create_docx(data_input, ai_data):
    doc = Document()
    head = doc.add_heading('MODUL AJAR / RPP', 0)
    head.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # Tabel Identitas
    table = doc.add_table(rows=5, cols=3)
    table.autofit = False
    table.columns[0].width = Inches(1.5)
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

    doc.add_paragraph("")
    doc.add_heading('A. Tujuan Pembelajaran', 1)
    doc.add_paragraph(ai_data.get('tujuan', '-'))
    
    doc.add_heading('B. Profil Lulusan', 1)
    for p in data_input['profil']:
        doc.add_paragraph(f"- {p}", style='List Bullet')

    doc.add_heading('C. Pemahaman Bermakna', 1)
    doc.add_paragraph(ai_data.get('pemahaman', '-'))
    
    doc.add_heading('D. Kegiatan Pembelajaran', 1)
    doc.add_paragraph("1. Pendahuluan").runs[0].bold = True
    doc.add_paragraph(ai_data.get('pendahuluan', '-'))
    doc.add_paragraph("2. Kegiatan Inti").runs[0].bold = True
    doc.add_paragraph(ai_data.get('inti', '-'))
    doc.add_paragraph("3. Penutup").runs[0].bold = True
    doc.add_paragraph(ai_data.get('penutup', '-'))
    
    doc.add_heading('E. Asesmen', 1)
    doc.add_paragraph(ai_data.get('asesmen', '-'))

    # TTD
    doc.add_paragraph("\n\n")
    t = doc.add_table(1, 2)
    t.cell(0,0).text = f"Mengetahui,\nKepala Sekolah\n\n\n{data_input['kepsek']}"
    t.cell(0,1).text = f"Guru Mapel\n\n\n{data_input['guru']}"
    
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

# --- 7. HALAMAN GENERATOR ---
def page_generator():
    st.title("📚 Generator Modul Ajar Otomatis")
    st.markdown("""
        <div class="running-text">
            <marquee style="color:red; font-weight:bold;">Aplikasi ini dibuat oleh Ceng Ucu Muhammad, S.H - SMP IT Nurusy Syifa</marquee>
        </div>
    """, unsafe_allow_html=True)
    
    # --- AUTO DETECT MODEL ---
    active_model = get_available_model()
    
    # FORM
    with st.form("main"):
        c1, c2, c3 = st.columns(3)
        nama_guru = c1.text_input("Guru")
        nama_sekolah = c2.text_input("Sekolah")
        nama_kepsek = c3.text_input("Kepsek")
        
        c4, c5 = st.columns(2)
        mapel = c4.text_input("Mapel", "IPA")
        kelas = c4.selectbox("Kelas", ["VII", "VIII", "IX"])
        waktu = c5.text_input("Waktu", "2 JP")
        topik = c5.text_input("Topik (Wajib)", "Sistem Pencernaan")
        
        profil = st.multiselect("Profil", st.session_state['profil_db'], default=st.session_state['profil_db'][:2])
        
        submitted = st.form_submit_button("🚀 Generate Modul Ajar")

    if submitted:
        if not active_model:
             st.error("❌ API Key tidak valid atau belum diganti. Silakan ganti API Key di kode.")
        elif not topik:
            st.warning("Topik wajib diisi!")
        else:
            with st.spinner("Sedang membuat RPP..."):
                res = generate_rpp_content(active_model, mapel, topik, kelas, waktu, profil)
                if res:
                    data = {'guru':nama_guru, 'sekolah':nama_sekolah, 'kepsek':nama_kepsek, 'mapel':mapel, 'kelas':kelas, 'waktu':waktu, 'profil':profil}
                    docx = create_docx(data, res)
                    st.success("Selesai!")
                    st.download_button("📥 Download Word", docx, f"Modul_{mapel}.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")

# --- 8. DATABASE PROFIL ---
def page_profil():
    st.title("Database Profil")
    baru = st.text_input("Profil Baru")
    if st.button("Tambah") and baru:
        st.session_state['profil_db'].append(baru)
        st.rerun()
    
    for i, p in enumerate(st.session_state['profil_db']):
        c1, c2 = st.columns([4,1])
        c1.write(f"- {p}")
        if c2.button("Hapus", key=f"d{i}"):
            st.session_state['profil_db'].pop(i)
            st.rerun()

# --- 9. NAVIGASI ---
with st.sidebar:
    st.title("Menu")
    menu = st.radio("Pilih:", ["Buat Modul", "Database Profil", "Tentang"])

if menu == "Buat Modul": page_generator()
elif menu == "Database Profil": page_profil()
else: 
    st.title("Tentang"); st.write("Dev: Ceng Ucu Muhammad, S.H\nSMP IT Nurusy Syifa")
