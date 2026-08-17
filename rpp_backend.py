"""
Backend logic: generation via Gemini dengan sistem Ekstraksi JSON Anti-Gagal 
dan Penanganan Error Detil.
"""

import io
import json
import streamlit as st # Tambahan agar error bisa langsung tampil di UI web

from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH

from docx_helpers import ModulTable, style_run, add_paragraph_in_cell, add_bottom_border

try:
    import google.generativeai as genai
except ImportError:
    genai = None

# ==========================================================================
# 1. GENERASI KONTEN VIA GEMINI (Sistem Anti-Gagal)
# ==========================================================================

def _clean_json(text):
    """
    Ekstraktor super aman: Memaksa mencari kurung kurawal pertama { 
    dan kurung kurawal terakhir } untuk mengabaikan teks Markdown tambahan dari AI.
    """
    text = text.strip()
    start = text.find('{')
    end = text.rfind('}')
    
    if start != -1 and end != -1:
        return text[start:end+1]
    return text

def _ctx_block(ctx):
    return f"""
Mata Pelajaran : {ctx['mapel']}
Jenjang/Fase   : {ctx['jenjang']} / Fase {ctx['fase']}
Kelas/Semester : {ctx['kelas']} / {ctx['semester']}
Tema           : {ctx['tema']}
Materi/Topik   : {ctx['materi']}
Alokasi Waktu  : {ctx['waktu']}
Model Pembelajaran pilihan guru : {ctx['model_pembelajaran']}
Profil Pelajar Pancasila yang dituju : {', '.join(ctx['profil'])}
""".strip()


PROMPT_BAGIAN_UMUM = """
Kamu adalah asisten penyusun Modul Ajar Kurikulum Merdeka.
Buatkan bagian "INFORMASI UMUM" dan "KOMPONEN INTI" untuk:

{ctx}

Keluarkan HANYA JSON murni dengan skema PERSIS berikut:

{{
  "elemen_a": ["poin penjelasan elemen pemahaman/ruang lingkup 1", "poin 2"],
  "elemen_b": ["poin keterampilan proses 1", "poin 2"],
  "capaian_pembelajaran": "kalimat capaian pembelajaran untuk materi ini",
  "kompetensi_awal": ["poin kompetensi awal yang dibutuhkan peserta didik"],
  "sarana_prasarana": ["poin sarana/media/alat/sumber belajar 1", "poin 2"],
  "target_peserta_didik": ["deskripsi peserta didik reguler", "deskripsi peserta didik pencapaian tinggi"],
  "model_pembelajaran_desc": "deskripsi singkat model pembelajaran",
  "tujuan_pembelajaran": ["poin alur tujuan pembelajaran 1", "poin 2"],
  "pemahaman_bermakna": ["poin pemahaman bermakna 1", "poin 2"],
  "pertanyaan_pemantik": ["pertanyaan pemantik 1", "pertanyaan pemantik 2"],
  "kegiatan_pendahuluan": ["langkah pendahuluan 1", "langkah 2", "langkah 3"],
  "kegiatan_inti": ["langkah kegiatan inti 1", "langkah 2", "langkah 3"],
  "kegiatan_penutup": ["langkah penutup 1", "langkah 2", "langkah 3"],
  "refleksi_guru": "refleksi terkait materi",
  "refleksi_sikap": ["pertanyaan refleksi sikap 1", "pertanyaan refleksi sikap 2"],
  "refleksi_pengetahuan": ["pertanyaan refleksi pengetahuan 1"],
  "refleksi_keterampilan": ["pertanyaan refleksi keterampilan 1"],
  "pengayaan": "deskripsi kegiatan pengayaan",
  "remedial_catatan": "catatan pendekatan remedial"
}}
"""

PROMPT_ASESMEN_LAMPIRAN = """
Kamu adalah asisten penyusun Modul Ajar Kurikulum Merdeka.
Buatkan bagian "ASESMEN/PENILAIAN LENGKAP" dan "LAMPIRAN" untuk:

{ctx}

Keluarkan HANYA JSON murni dengan skema PERSIS berikut:

{{
  "asesmen_konsep": "1 paragraf konsep penilaian",
  "kisi_kisi_tes": {{"kd": "kompetensi dasar", "materi": "materi", "indikator": "indikator soal", "bentuk": "Tes Tertulis", "jumlah_soal": 2}},
  "butir_soal": ["Soal nomor 1 lengkap", "Soal nomor 2 lengkap"],
  "kunci_skor": [{{"no": "1", "kunci": "kunci jawaban ringkas", "skor": 2}}, {{"no": "2", "kunci": "kunci jawaban ringkas", "skor": 2}}],
  "tes_lisan": ["pertanyaan lisan 1", "pertanyaan lisan 2"],
  "kisi_kisi_penugasan": {{"kd": "kompetensi", "materi": "materi", "indikator": "indikator"}},
  "deskripsi_penugasan": "deskripsi tugas",
  "rubrik_penugasan": [{{"aspek": "aspek dinilai 1", "skor": "0-2"}}],
  "kisi_kisi_kinerja": {{"kd": "kompetensi", "materi": "materi", "indikator": "indikator"}},
  "rubrik_kinerja": [{{"indikator": "indikator 1", "rubrik": "kriteria skor"}}],
  "kisi_kisi_proyek": {{"kd": "kompetensi", "materi": "materi", "indikator": "indikator"}},
  "tugas_proyek": ["langkah proyek 1", "langkah 2"],
  "rubrik_proyek": [{{"pernyataan": "aspek 1", "keterangan": "keterangan penilaian"}}],
  "lkpd_petunjuk": "petunjuk pengerjaan LKPD",
  "lkpd_soal": ["soal LKPD 1", "soal LKPD 2"],
  "bahan_bacaan_siswa": "bahan bacaan peserta didik",
  "bahan_bacaan_guru": "bahan bacaan guru",
  "glosarium": [{{"istilah": "istilah 1", "definisi": "definisi singkat"}}],
  "daftar_pustaka": ["referensi 1", "referensi 2"]
}}
"""


def _call_gemini_json(model_name, prompt, tahap_nama):
    try:
        model = genai.GenerativeModel(model_name)
        # Menggunakan format pemanggilan paling aman yang kompatibel 
        # dengan SEMUA versi library google-generativeai di Streamlit
        response = model.generate_content(prompt)
        
        # Ekstraksi dan baca JSON
        text_bersih = _clean_json(response.text)
        return json.loads(text_bersih)
        
    except json.JSONDecodeError as je:
        st.error(f"❌ [Tahap {tahap_nama}] AI gagal memberikan format yang tepat.")
        if 'response' in locals() and hasattr(response, 'text'):
            with st.expander(f"🔍 Klik untuk lihat balasan AI yang error ({tahap_nama})"):
                st.code(response.text)
        return None
    except Exception as e:
        st.error(f"⚠️ [Tahap {tahap_nama}] Error Sistem: {str(e)}")
        return None


def generate_bagian_umum(model_name, ctx):
    prompt = PROMPT_BAGIAN_UMUM.format(ctx=_ctx_block(ctx))
    return _call_gemini_json(model_name, prompt, "Informasi Umum & Inti")

def generate_asesmen_lampiran(model_name, ctx):
    prompt = PROMPT_ASESMEN_LAMPIRAN.format(ctx=_ctx_block(ctx))
    return _call_gemini_json(model_name, prompt, "Asesmen & Lampiran")


# ==========================================================================
# 2. PEMBUATAN DOCX
# ==========================================================================

def _g(d, key, default):
    """Ambil field dari dict AI dengan fallback aman."""
    if not d:
        return default
    val = d.get(key, default)
    return val if val not in (None, "") else default


def create_docx(data_input, ai_umum, ai_asesmen):
    ai_umum = ai_umum or {}
    ai_asesmen = ai_asesmen or {}

    doc = Document()
    style = doc.styles['Normal']
    style.font.name = 'Times New Roman'
    style.font.size = Pt(11)

    for section in doc.sections:
        section.top_margin = Cm(2)
        section.bottom_margin = Cm(2)
        section.left_margin = Cm(2.5)
        section.right_margin = Cm(2.5)

    judul_baris1 = "MODUL AJAR KURIKULUM MERDEKA"
    judul_baris2 = f"{data_input['mapel'].upper()} FASE {data_input['fase']} KELAS {data_input['kelas']}"

    # ---------------- COVER ----------------
    for _ in range(4):
        doc.add_paragraph()
    cover_tbl = doc.add_table(rows=5, cols=2)
    cover_tbl.autofit = True
    cover_rows = [
        ("Nama Sekolah", data_input['sekolah']),
        ("Nama Penyusun", data_input['guru']),
        ("NIK", data_input.get('nik', '')),
        ("Mata Pelajaran", data_input['mapel']),
        ("Fase / Kelas / Semester",
         f"{data_input['fase']} / {data_input['kelas']} ({data_input['semester']})"),
    ]
    for i, (label, val) in enumerate(cover_rows):
        c0, c1 = cover_tbl.rows[i].cells
        add_paragraph_in_cell(c0, label, bold=True, first=True)
        shown = val if val else "________________________"
        add_paragraph_in_cell(c1, f": {shown}", first=True)

    hr = doc.add_paragraph()
    hr.paragraph_format.space_before = Pt(6)
    add_bottom_border(hr)

    doc.add_paragraph()
    doc.add_paragraph()
    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    style_run(p_title.add_run(judul_baris1), bold=True, size=16)
    p_title2 = doc.add_paragraph()
    p_title2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    style_run(p_title2.add_run(judul_baris2), bold=True, size=14)

    doc.add_page_break()

    # ---------------- HALAMAN ISI: JUDUL ULANG ----------------
    p_title3 = doc.add_paragraph()
    p_title3.alignment = WD_ALIGN_PARAGRAPH.CENTER
    style_run(p_title3.add_run(judul_baris1), bold=True, size=13)
    p_title4 = doc.add_paragraph()
    p_title4.alignment = WD_ALIGN_PARAGRAPH.CENTER
    style_run(p_title4.add_run(judul_baris2), bold=True, size=13)
    doc.add_paragraph()

    mt = ModulTable(doc)

    # ============ INFORMASI UMUM ============
    mt.add_section_header("INFORMASI UMUM")
    mt.add_section_header("A. IDENTITAS MODUL")
    mt.add_label_value("Penyusun", data_input['guru'])
    mt.add_label_value("Instansi", data_input['sekolah'])
    mt.add_label_value("Tahun Penyusunan", data_input['tahun'])
    mt.add_label_value("Jenjang Sekolah", data_input['jenjang'])
    mt.add_label_value("Mata Pelajaran", data_input['mapel'])
    mt.add_label_value("Fase / Kelas", f"{data_input['fase']} / {data_input['kelas']}")
    mt.add_label_value("Tema", data_input['tema'])
    mt.add_label_value("Materi", data_input['materi'])
    mt.add_full_content(
        [f"a) Elemen pemahaman dan ruang lingkup pembelajaran"] +
        _g(ai_umum, 'elemen_a', ["-"]) +
        ["b) Elemen keterampilan proses"] +
        _g(ai_umum, 'elemen_b', ["-"])
    )
    mt.add_label_value("Capaian Pembelajaran", _g(ai_umum, 'capaian_pembelajaran', '-'))
    mt.add_label_value("Alokasi Waktu", data_input['waktu'])

    mt.add_section_header("B. KOMPETENSI AWAL")
    mt.add_full_content(_g(ai_umum, 'kompetensi_awal', ['-']), bullet=True)

    mt.add_section_header("C. PROFIL PELAJAR PANCASILA")
    mt.add_full_content(data_input['profil'], bullet=True)

    mt.add_section_header("D. SARANA DAN PRASARANA")
    mt.add_full_content(_g(ai_umum, 'sarana_prasarana', ['-']), bullet=True)

    mt.add_section_header("E. TARGET PESERTA DIDIK")
    mt.add_full_content(_g(ai_umum, 'target_peserta_didik', ['-']), bullet=True)

    mt.add_section_header("F. MODEL PEMBELAJARAN")
    mt.add_full_content([
        f"Model pembelajaran: {data_input['model_pembelajaran']}",
        _g(ai_umum, 'model_pembelajaran_desc', '-')
    ])

    # ============ KOMPONEN INTI ============
    mt.add_section_header("KOMPONEN INTI")

    mt.add_section_header("A. TUJUAN KEGIATAN PEMBELAJARAN")
    mt.add_full_content(_g(ai_umum, 'tujuan_pembelajaran', ['-']), bullet=True,
                         italic_intro="Alur Tujuan Pembelajaran:")

    mt.add_section_header("B. PEMAHAMAN BERMAKNA")
    mt.add_full_content(_g(ai_umum, 'pemahaman_bermakna', ['-']), bullet=True)

    mt.add_section_header("C. PERTANYAAN PEMANTIK")
    mt.add_full_content(_g(ai_umum, 'pertanyaan_pemantik', ['-']), bullet=True)

    mt.add_section_header("D. KEGIATAN PEMBELAJARAN")
    mt.add_full_content(_g(ai_umum, 'kegiatan_pendahuluan', ['-']),
                         italic_intro="Kegiatan Pendahuluan")
    mt.add_full_content(_g(ai_umum, 'kegiatan_inti', ['-']),
                         italic_intro="Kegiatan Inti")
    mt.add_full_content(_g(ai_umum, 'kegiatan_penutup', ['-']),
                         italic_intro="Kegiatan Penutup")

    mt.add_section_header("E. REFLEKSI")
    mt.add_full_content(_g(ai_umum, 'refleksi_guru', '-'))
    mt.add_full_content(_g(ai_umum, 'refleksi_sikap', ['-']), bullet=True,
                         italic_intro="Sikap")
    mt.add_full_content(_g(ai_umum, 'refleksi_pengetahuan', ['-']), bullet=True,
                         italic_intro="Pengetahuan")
    mt.add_full_content(_g(ai_umum, 'refleksi_keterampilan', ['-']), bullet=True,
                         italic_intro="Keterampilan")

    # ---------- F. ASESMEN / PENILAIAN ----------
    mt.add_section_header("F. ASESMEN / PENILAIAN")
    mt.add_full_content(_g(ai_asesmen, 'asesmen_konsep', '-'))

    mt.add_full_content(None, italic_intro="1. Penilaian Kompetensi Sikap")
    mt.add_full_content([
        "Teknik: observasi, penilaian diri, dan penilaian antar teman, "
        "dicatat pada jurnal perkembangan sikap oleh guru mata pelajaran selama satu semester."
    ])

    mt.add_full_content(None, italic_intro="Contoh Jurnal Penilaian Sikap")
    mt.add_nested_table(
        headers=["No", "Waktu", "Nama Siswa", "Catatan Perilaku", "Butir Sikap"],
        rows=[["", "", "", "", ""] for _ in range(4)],
        col_widths_cm=[1, 2.5, 3, 5.5, 3.5]
    )

    mt.add_full_content(None, italic_intro="2. Penilaian Kompetensi Pengetahuan")
    kisi = _g(ai_asesmen, 'kisi_kisi_tes', {})
    mt.add_full_content(None, italic_intro="Kisi-kisi Tes Tertulis")
    mt.add_nested_table(
        headers=["No", "Kompetensi Dasar", "Materi", "Indikator Soal", "Bentuk", "Jumlah Soal"],
        rows=[["1", kisi.get('kd', '-'), kisi.get('materi', '-'), kisi.get('indikator', '-'),
               kisi.get('bentuk', 'Tes Tertulis'), str(kisi.get('jumlah_soal', '-'))]],
        col_widths_cm=[1, 3, 2.5, 4.5, 2, 2]
    )
    mt.add_full_content(_g(ai_asesmen, 'butir_soal', ['-']), italic_intro="Butir Soal")

    kunci_rows = [[k.get('no', str(i + 1)), k.get('kunci', '-'), str(k.get('skor', '-'))]
                  for i, k in enumerate(_g(ai_asesmen, 'kunci_skor', []))]
    if kunci_rows:
        mt.add_full_content(None, italic_intro="Kunci Jawaban dan Pedoman Skor")
        mt.add_nested_table(
            headers=["No. Soal", "Kunci Jawaban", "Skor"],
            rows=kunci_rows,
            col_widths_cm=[2, 11.5, 2]
        )

    mt.add_full_content(_g(ai_asesmen, 'tes_lisan', ['-']), bullet=True, italic_intro="Tes Lisan")

    mt.add_full_content(None, italic_intro="Penugasan")
    kp = _g(ai_asesmen, 'kisi_kisi_penugasan', {})
    mt.add_nested_table(
        headers=["Kompetensi Dasar", "Materi", "Indikator"],
        rows=[[kp.get('kd', '-'), kp.get('materi', '-'), kp.get('indikator', '-')]],
        col_widths_cm=[5, 4, 6.5]
    )
    mt.add_full_content(_g(ai_asesmen, 'deskripsi_penugasan', '-'))
    rp_rows = [[r.get('aspek', '-'), r.get('skor', '-')] for r in _g(ai_asesmen, 'rubrik_penugasan', [])]
    if rp_rows:
        mt.add_nested_table(
            headers=["Aspek yang Dinilai", "Rentang Skor"],
            rows=rp_rows,
            col_widths_cm=[11.5, 4]
        )

    mt.add_full_content(None, italic_intro="3. Penilaian Kompetensi Keterampilan")
    mt.add_full_content(None, italic_intro="Penilaian Kinerja")
    kk = _g(ai_asesmen, 'kisi_kisi_kinerja', {})
    mt.add_nested_table(
        headers=["Kompetensi Dasar", "Materi", "Indikator"],
        rows=[[kk.get('kd', '-'), kk.get('materi', '-'), kk.get('indikator', '-')]],
        col_widths_cm=[5, 4, 6.5]
    )
    rk_rows = [[r.get('indikator', '-'), r.get('rubrik', '-')] for r in _g(ai_asesmen, 'rubrik_kinerja', [])]
    if rk_rows:
        mt.add_nested_table(
            headers=["Indikator", "Rubrik Penskoran"],
            rows=rk_rows,
            col_widths_cm=[5, 10.5]
        )

    mt.add_full_content(None, italic_intro="Penilaian Proyek")
    kpr = _g(ai_asesmen, 'kisi_kisi_proyek', {})
    mt.add_nested_table(
        headers=["Kompetensi Dasar", "Materi", "Indikator"],
        rows=[[kpr.get('kd', '-'), kpr.get('materi', '-'), kpr.get('indikator', '-')]],
        col_widths_cm=[5, 4, 6.5]
    )
    mt.add_full_content(_g(ai_asesmen, 'tugas_proyek', ['-']), bullet=True,
                         italic_intro="Langkah Pengerjaan Proyek")
    rpr_rows = [[r.get('pernyataan', '-'), r.get('keterangan', '-')]
                for r in _g(ai_asesmen, 'rubrik_proyek', [])]
    if rpr_rows:
        mt.add_nested_table(
            headers=["Aspek yang Dinilai", "Keterangan Penilaian"],
            rows=rpr_rows,
            col_widths_cm=[6, 9.5]
        )

    mt.add_section_header("G. KEGIATAN PENGAYAAN DAN REMEDIAL")
    mt.add_full_content(_g(ai_umum, 'remedial_catatan', '-'), italic_intro="Remedial")
    mt.add_full_content(_g(ai_umum, 'pengayaan', '-'), italic_intro="Pengayaan")

    # ============ LAMPIRAN ============
    if data_input.get('pakai_lkpd') == 'Ya':
        mt.add_section_header("LAMPIRAN")

        mt.add_section_header("A. LEMBAR KERJA PESERTA DIDIK (LKPD)")
        mt.add_full_content([f"Nama :", f"Kelas :", _g(ai_asesmen, 'lkpd_petunjuk', '-')])
        mt.add_full_content(_g(ai_asesmen, 'lkpd_soal', ['-']), bullet=True)

        mt.add_section_header("B. BAHAN BACAAN GURU & PESERTA DIDIK")
        mt.add_full_content(_g(ai_asesmen, 'bahan_bacaan_siswa', '-'),
                             italic_intro="Bahan Bacaan Peserta Didik")
        mt.add_full_content(_g(ai_asesmen, 'bahan_bacaan_guru', '-'),
                             italic_intro="Bahan Bacaan Guru")

        mt.add_section_header("C. GLOSARIUM")
        glos = _g(ai_asesmen, 'glosarium', [])
        glos_text = [f"{g.get('istilah', '-')} : {g.get('definisi', '-')}" for g in glos] or ["-"]
        mt.add_full_content(glos_text, bullet=True)

        mt.add_section_header("D. DAFTAR PUSTAKA")
        mt.add_full_content(_g(ai_asesmen, 'daftar_pustaka', ['-']), bullet=True)

    # ---------------- TANDA TANGAN ----------------
    doc.add_paragraph()
    ttd_table = doc.add_table(rows=1, cols=2)
    ttd_table.autofit = False
    for cell in ttd_table.rows[0].cells:
        cell.width = Cm(8.25)
    c1 = ttd_table.cell(0, 0)
    c1.text = f"Mengetahui,\nKepala Sekolah\n\n\n\n( {data_input['kepsek']} )"
    c1.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
    c2 = ttd_table.cell(0, 1)
    c2.text = f"Guru Mata Pelajaran\n\n\n\n( {data_input['guru']} )"
    c2.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER

    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer
