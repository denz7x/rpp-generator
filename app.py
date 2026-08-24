
import streamlit as st
import google.generativeai as genai
from pathlib import Path
try:
    from rpp_backend import generate_modul, create_docx, TEMPLATE_PATH
except Exception as e:
    st.error("Gagal memuat rpp_backend.py. Pastikan file rpp_backend.py berada satu folder dengan app.py dan requirements.txt sudah terpasang.")
    st.code(f"{type(e).__name__}: {e}")
    st.stop()

st.set_page_config(page_title="MODUL AJAR GENERATOR", page_icon="🚀", layout="wide")

st.markdown("""
<style>
[data-testid="stHeader"],[data-testid="stToolbar"],[data-testid="stDecoration"],
[data-testid="stStatusWidget"],#MainMenu,footer{display:none!important}
.block-container{padding-top:1rem!important;max-width:1100px!important}
.header{background:linear-gradient(135deg,#4338ca,#2563eb,#06b6d4);padding:20px;border-radius:16px;color:white;text-align:center;margin-bottom:15px}
.card{background:white;padding:18px;border-radius:14px;margin-bottom:12px;border:1px solid #e5e7eb}
</style>
<div class="header">
<h1 style="margin:0">🚀 GENERATOR MODUL AJAR</h1>
<p style="margin:5px 0 0">Template Word tetap • Isi disusun AI • Deep Learning</p>
</div>
""", unsafe_allow_html=True)

try:
    KEY = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=KEY)
except Exception:
    st.error("GOOGLE_API_KEY belum diatur di Streamlit Secrets.")
    st.stop()

@st.cache_data(ttl=300)
def models():
    try:
        ms=[m.name for m in genai.list_models() if "generateContent" in m.supported_generation_methods]
        for x in ["models/gemini-3.6-flash","models/gemini-2.5-flash","models/gemini-1.5-flash"]:
            if x in ms:return x
        return ms[0] if ms else None
    except:return None

model=models()
if not model:
    st.error("Tidak ada model Gemini yang mendukung generateContent.")
    st.stop()

if "ai" not in st.session_state: st.session_state.ai=None
if "data" not in st.session_state: st.session_state.data=None

with st.form("modul_form"):
    st.subheader("🧑‍🏫 Identitas Penyusun")
    c1,c2=st.columns(2)
    with c1:
        guru=st.text_input("Nama Guru / Penyusun")
        sekolah=st.text_input("Nama Sekolah", value="SMP IT Nurusy Syifa")
        nik=st.text_input("NIP / NIK", "")
        kepsek=st.text_input("Nama Kepala Sekolah", "")
        tahun=st.text_input("Tahun Penyusunan", "2026")
    with c2:
        jenjang=st.selectbox("Jenjang",["SMP/MTs","SD/MI","SMA/MA"])
        mapel=st.text_input("Mata Pelajaran","Ilmu Pengetahuan Sosial (IPS)")
        fase=st.selectbox("Fase",["A","B","C","D","E","F"],index=3)
        kelas=st.selectbox("Kelas",["I","II","III","IV","V","VI","VII","VIII","IX","X","XI","XII"],index=6)
        semester=st.selectbox("Semester",["Ganjil","Genap"])
    st.subheader("📚 Parameter Modul")
    tema=st.text_input("Bab / Tema","Keluarga Awal Kehidupan")
    materi=st.text_input("Materi / Topik","Sejarah keluarga, lokasi, peta, sosialisasi, nilai dan norma, interaksi antarwilayah, kebutuhan")
    waktu=st.text_input("Alokasi Waktu","30 JP (15 kali pertemuan)")
    model_pembelajaran=st.selectbox("Model Pembelajaran",["Discovery Learning","Problem Based Learning","Project Based Learning","Group Investigation","Resitasi","Cooperative Learning"])
    profil=st.multiselect("Dimensi Profil Lulusan",["Keimanan dan Ketakwaan terhadap Tuhan Yang Maha Esa, dan Berakhlak Mulia","Kewargaan","Penalaran Kritis","Kreativitas","Kolaborasi","Kemandirian","Kesehatan","Komunikasi"],default=["Penalaran Kritis","Kolaborasi","Kemandirian"])
    lampiran=st.radio("Sertakan Lampiran?",["Ya","Tidak"],horizontal=True)
    go=st.form_submit_button("🚀 GENERATE SEKARANG",use_container_width=True)

if go:
    if not guru or not sekolah or not materi:
        st.error("Nama guru, sekolah, dan materi wajib diisi.")
    else:
        data={"guru":guru,"sekolah":sekolah,"nik":nik,"kepsek":kepsek,"tahun":tahun,"jenjang":jenjang,
              "mapel":mapel,"fase":fase,"kelas":kelas,"semester":semester,"tema":tema or materi,
              "materi":materi,"waktu":waktu,"model_pembelajaran":model_pembelajaran,
              "profil":profil,"pakai_lkpd":lampiran}
        with st.spinner("✨ AI sedang menyusun modul sesuai struktur template..."):
            ai=generate_modul(model,data)
        if ai:
            st.session_state.ai=ai
            st.session_state.data=data
            st.success("Modul berhasil disusun.")

if st.session_state.ai and st.session_state.data:
    st.divider()
    st.subheader("👁️ Pratinjau Isi")
    ai=st.session_state.ai
    with st.expander("Tujuan Pembelajaran",True):
        st.write("\n".join(ai.get("tujuan_pembelajaran",[])))
    with st.expander("Langkah Pembelajaran"):
        for x in ai.get("pertemuan",[]): st.markdown("**"+x.get("judul","")+"**"); st.write("\n".join(x.get("isi",[])))
    try:
        file=create_docx(st.session_state.data,st.session_state.ai)
        st.download_button("📥 UNDUH FILE WORD (.DOCX)",data=file,file_name=f"Modul_Ajar_{st.session_state.data['mapel']}.docx",mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",use_container_width=True)
    except Exception as e:
        st.error(f"Gagal membuat DOCX: {e}")

st.caption(f"Template aktif: {TEMPLATE_PATH.name}")
