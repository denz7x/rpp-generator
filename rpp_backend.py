
"""
Backend Modul Ajar Generator V2
- Menggunakan DOCX contoh sebagai MASTER TEMPLATE.
- AI hanya menghasilkan isi.
- Format, heading, tabel, margin, font, dan struktur template dipertahankan.
"""
import io, json, re
from pathlib import Path
import streamlit as st
from docx import Document
from docx.shared import Pt

try:
    import google.generativeai as genai
except ImportError:
    genai = None

BASE_DIR = Path(__file__).resolve().parent
TEMPLATE_PATH = BASE_DIR / "Modul Ajar 1 IPS K-VII (Deep Learning).docx"

def _clean_json(text):
    text = (text or "").strip()
    if "```" in text:
        text = re.sub(r"```(?:json)?", "", text).replace("```", "").strip()
    a, b = text.find("{"), text.rfind("}")
    return text[a:b+1] if a >= 0 and b > a else text

def _ctx_block(ctx):
    return f"""
Nama sekolah: {ctx['sekolah']}
Nama penyusun: {ctx['guru']}
NIP/NIK: {ctx.get('nik','')}
Kepala sekolah: {ctx.get('kepsek','')}
Tahun penyusunan: {ctx.get('tahun','')}
Jenjang: {ctx['jenjang']}
Mata pelajaran: {ctx['mapel']}
Fase: {ctx['fase']}
Kelas: {ctx['kelas']}
Semester: {ctx['semester']}
Bab/Tema: {ctx['tema']}
Materi/Topik: {ctx['materi']}
Alokasi waktu: {ctx['waktu']}
Model pembelajaran: {ctx['model_pembelajaran']}
Profil/Dimensi yang dipilih: {', '.join(ctx.get('profil',[]))}
""".strip()

PROMPT = r"""
Anda adalah penyusun Modul Ajar Kurikulum Merdeka dengan pendekatan Deep Learning.
Gunakan DATA GURU di bawah ini.

PENTING:
1. Pertahankan istilah dan urutan komponen seperti template modul contoh:
   IDENTITAS MODUL; IDENTIFIKASI KESIAPAN PESERTA DIDIK;
   KARAKTERISTIK MATERI PELAJARAN; DIMENSI PROFIL LULUSAN;
   DESAIN PEMBELAJARAN; CAPAIAN PEMBELAJARAN; LINTAS DISIPLIN ILMU;
   TUJUAN PEMBELAJARAN; TOPIK PEMBELAJARAN KONTEKSTUAL;
   KERANGKA PEMBELAJARAN; PRAKTIK PEDAGOGIK; KEMITRAAN PEMBELAJARAN;
   LINGKUNGAN BELAJAR; PEMANFAATAN DIGITAL;
   LANGKAH-LANGKAH PEMBELAJARAN BERDIFERENSIASI;
   ASESMEN PEMBELAJARAN.
2. Tulis isi yang spesifik terhadap mata pelajaran, fase, kelas, bab, materi dan alokasi waktu.
3. Gunakan pendekatan Deep Learning: Mindful, Meaningful, Joyful Learning.
4. Jangan membuat pembahasan yang tidak relevan dengan materi.
5. Untuk langkah pembelajaran, buat 15 pertemuan seperti struktur template contoh. Jika alokasi waktu pengguna berbeda, sesuaikan pembagian topik secara wajar tetapi tetap gunakan 15 blok pertemuan agar format template tetap konsisten.
6. Setiap pertemuan wajib memiliki: Topik, KEGIATAN PENDAHULUAN, KEGIATAN INTI, Pembelajaran Berdiferensiasi bila relevan, KEGIATAN PENUTUP.
7. Buat asesmen diagnostik, formatif, dan sumatif yang benar-benar terkait materi.
8. Buat soal pilihan ganda dan esai yang relevan dengan materi.
9. Keluarkan HANYA JSON valid, tanpa Markdown.

SKEMA JSON:
{
 "identitas": ["Nama Sekolah : ...","Nama Penyusun : ...","Mata Pelajaran : ...","Kelas / Fase /Semester : ...","Alokasi Waktu : ...","Tahun Pelajaran : ..."],
 "identifikasi_kesiapan": ["Pengetahuan Awal: ...","Minat: ...","Latar Belakang: ...","Kebutuhan Belajar:","Visual: ...","Auditori: ...","Kinestetik: ..."],
 "karakteristik_materi": ["Jenis Pengetahuan yang Akan Dicapai:","Konseptual: ...","Prosedural: ...","Relevansi dengan Kehidupan Nyata Peserta Didik: ...","Tingkat Kesulitan: ...","Struktur Materi: ...","Integrasi Nilai dan Karakter:","..."],
 "dimensi_profil_lulusan": ["..."],
 "capaian_pembelajaran": ["Pada akhir Fase ..., murid memiliki kemampuan sebagai berikut.","Pemahaman Konsep: ...","Keterampilan Proses: ..."],
 "lintas_disiplin_ilmu": ["..."],
 "tujuan_pembelajaran": ["Pertemuan 1-2: ...","Pertemuan 3: ...","..."],
 "topik_kontekstual": ["JUDUL BAB: deskripsi kontekstual ..."],
 "praktik_pedagogik": ["Model Pembelajaran: ...","Pendekatan: Deep Learning (Mindful, Meaningful, Joyful Learning)","Mindful Learning: ...","Meaningful Learning: ...","Joyful Learning: ...","Metode Pembelajaran: ...","Strategi Pembelajaran Berdiferensiasi:","Diferensiasi Konten: ...","Diferensiasi Proses: ...","Diferensiasi Produk: ..."],
 "kemitraan": ["Lingkungan Sekolah: ...","Lingkungan Luar Sekolah/Masyarakat: ...","Mitra Digital: ..."],
 "lingkungan_belajar": ["Lingkungan Fisik: ...","Lingkungan Virtual: ...","Lingkungan Psikologis: ..."],
 "pemanfaatan_digital": ["..."],
 "pertemuan": [
   {"judul":"PERTEMUAN 1-2 (4 JP : 2 x 80 MENIT)","isi":["Topik: ...","KEGIATAN PENDAHULUAN (15 MENIT)","Salam dan Doa: ...","Apersepsi: ...","Tujuan Pembelajaran: ...","KEGIATAN INTI (55 MENIT)","Eksplorasi Konsep: ...","Aktivitas Kelompok: ...","Presentasi: ...","Pembelajaran Berdiferensiasi:","Proses: ...","KEGIATAN PENUTUP (10 MENIT)","Refleksi: ...","Tindak Lanjut: ...","Penutup: ..."]},
   {"judul":"PERTEMUAN 3 (2 JP : 80 MENIT)","isi":["..."]},
   {"judul":"PERTEMUAN 4-5 (4 JP : 2 x 80 MENIT)","isi":["..."]},
   {"judul":"PERTEMUAN 6 (2 JP : 80 MENIT)","isi":["..."]},
   {"judul":"PERTEMUAN 7 (2 JP : 80 MENIT)","isi":["..."]},
   {"judul":"PERTEMUAN 8 (2 JP : 80 MENIT)","isi":["..."]},
   {"judul":"PERTEMUAN 9 (2 JP : 80 MENIT)","isi":["..."]},
   {"judul":"PERTEMUAN 10-11 (4 JP : 2 x 80 MENIT)","isi":["..."]},
   {"judul":"PERTEMUAN 12-13 (4 JP : 2 x 80 MENIT)","isi":["..."]},
   {"judul":"PERTEMUAN 14-15 (4 JP : 2 x 80 MENIT)","isi":["..."]}
 ],
 "asesmen_diagnostik": ["..."],
 "asesmen_formatif": ["..."],
 "asesmen_sumatif": ["Produk (Proyek): ...","Praktik (Kinerja): ...","Tes Tertulis: ...","Contoh Tes Tertulis :","Pilihan Ganda","1. ...","a. ...","b. ...","c. ...","d. ...","2. ...","a. ...","b. ...","c. ...","d. ...","3. ...","a. ...","b. ...","c. ...","d. ...","Esai","1. ...","2. ...","3. ..."],
 "lkpd": ["Petunjuk LKPD: ...","1. ...","2. ...","3. ..."],
 "bahan_bacaan": ["Bahan Bacaan Peserta Didik: ...","Bahan Bacaan Guru: ..."],
 "glosarium": ["Istilah : definisi"],
 "daftar_pustaka": ["..."]
}

DATA GURU:
{ctx}
"""

def _call(model_name, ctx):
    if genai is None:
        st.error("Library google-generativeai belum terpasang.")
        return None
    try:
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(PROMPT.format(ctx=_ctx_block(ctx)))
        return json.loads(_clean_json(response.text))
    except Exception as e:
        st.error(f"Gagal menghasilkan modul: {e}")
        if 'response' in locals() and getattr(response, "text", None):
            with st.expander("Lihat respons AI"):
                st.code(response.text)
        return None

def generate_modul(model_name, ctx):
    return _call(model_name, ctx)

def _replace_paragraph_text(p, text):
    # Mempertahankan paragraph style dan properti paragraf.
    runs = p.runs
    if not runs:
        p.add_run(str(text))
        return
    runs[0].text = str(text)
    for r in runs[1:]:
        r.text = ""

def _is_heading(p):
    return p.style.name.startswith("Heading")

def _set_heading(p, text):
    _replace_paragraph_text(p, text)

def _insert_before(ref_p, text, style="Normal"):
    p = ref_p.insert_paragraph_before(str(text))
    p.style = style
    return p

def _fill_section(doc, heading_idx, next_heading_idx, lines):
    paras = doc.paragraphs
    heading = paras[heading_idx]
    next_p = paras[next_heading_idx] if next_heading_idx is not None else None
    # Reacquire paragraph list after insertions by using XML sibling references.
    body = []
    cur = heading._p.getnext()
    stop = next_p._p if next_p else None
    while cur is not None and cur is not stop:
        if cur.tag.endswith('}p'):
            from docx.text.paragraph import Paragraph
            body.append(Paragraph(cur, heading._parent))
        cur = cur.getnext()

    lines = [str(x) for x in (lines or []) if str(x).strip()]
    if not lines:
        lines = [""]
    for i, text in enumerate(lines):
        if i < len(body):
            _replace_paragraph_text(body[i], text)
        else:
            if next_p:
                _insert_before(next_p, text, "Normal")
            else:
                p = doc.add_paragraph(text)
    for p in body[len(lines):]:
        _replace_paragraph_text(p, "")

def _find_heading(doc, exact):
    for p in doc.paragraphs:
        if p.text.strip() == exact:
            return p
    return None

def _section_range(doc, heading_text, next_heading_text):
    paras = doc.paragraphs
    a = next((i for i,p in enumerate(paras) if p.text.strip()==heading_text), None)
    b = next((i for i,p in enumerate(paras) if p.text.strip()==next_heading_text), None) if next_heading_text else None
    return a,b

def _replace_section(doc, heading_text, lines, next_heading_text=None):
    a,b = _section_range(doc, heading_text, next_heading_text)
    if a is None:
        return
    _fill_section(doc, a, b, lines)

def _all_heading_texts(doc):
    return [p.text.strip() for p in doc.paragraphs if _is_heading(p) and p.text.strip()]

def create_docx(data_input, ai):
    if not TEMPLATE_PATH.exists():
        raise FileNotFoundError(f"Template tidak ditemukan: {TEMPLATE_PATH}")
    doc = Document(str(TEMPLATE_PATH))

    # Judul dinamis
    p = _find_heading(doc, "MATA PELAJARAN : ILMU PENGETAHUAN SOSIAL (IPS)")
    if p:
        _set_heading(p, f"MATA PELAJARAN : {data_input['mapel'].upper()}")
    p = _find_heading(doc, "BAB 1: KELUARGA AWAL KEHIDUPAN")
    if p:
        _set_heading(p, f"BAB: {data_input['tema'].upper()}")

    # Identitas tabel cover
    if doc.tables:
        t = doc.tables[0]
        if len(t.rows) >= 2:
            txt = t.cell(1,0).text
            _replace_cell = lambda cell, val: setattr(cell, "text", val)
            _replace_cell(t.cell(1,0), f"Nama Sekolah : {data_input['sekolah']}")
            # Hanya mengubah placeholder data, tidak mengubah struktur tabel.
            _replace_cell(t.cell(1,0), f"Nama Sekolah       : {data_input['sekolah']}")

    # Ganti identitas di halaman isi
    ident = ai.get("identitas", [])
    _replace_section(doc, "A. IDENTITAS MODUL", ident, "B. IDENTIFIKASI KESIAPAN PESERTA DIDIK")

    # Bagian-bagian utama
    _replace_section(doc, "B. IDENTIFIKASI KESIAPAN PESERTA DIDIK", ai.get("identifikasi_kesiapan"), "C. KARAKTERISTIK MATERI PELAJARAN")
    _replace_section(doc, "C. KARAKTERISTIK MATERI PELAJARAN", ai.get("karakteristik_materi"), "D. DIMENSI PROFIL LULUSAN")
    _replace_section(doc, "D. DIMENSI PROFIL LULUSAN", ai.get("dimensi_profil_lulusan"), "DESAIN PEMBELAJARAN")
    _replace_section(doc, "A. CAPAIAN PEMBELAJARAN (CP) NOMOR 46 : TAHUN 2025", ai.get("capaian_pembelajaran"), "B. LINTAS DISIPLIN ILMU")
    _replace_section(doc, "B. LINTAS DISIPLIN ILMU", ai.get("lintas_disiplin_ilmu"), "C. TUJUAN PEMBELAJARAN")
    _replace_section(doc, "C. TUJUAN PEMBELAJARAN", ai.get("tujuan_pembelajaran"), "D. TOPIK PEMBELAJARAN KONTEKSTUAL")
    _replace_section(doc, "D. TOPIK PEMBELAJARAN KONTEKSTUAL", ai.get("topik_kontekstual"), "E. KERANGKA PEMBELAJARAN")
    _replace_section(doc, "PRAKTIK PEDAGOGIK", ai.get("praktik_pedagogik"), "KEMITRAAN PEMBELAJARAN")
    _replace_section(doc, "KEMITRAAN PEMBELAJARAN", ai.get("kemitraan"), "LINGKUNGAN BELAJAR")
    _replace_section(doc, "LINGKUNGAN BELAJAR", ai.get("lingkungan_belajar"), "PEMANFAATAN DIGITAL")
    _replace_section(doc, "PEMANFAATAN DIGITAL", ai.get("pemanfaatan_digital"), "F. LANGKAH-LANGKAH PEMBELAJARAN BERDIFERENSIASI")

    # Pertemuan: isi tiap blok, termasuk judul blok.
    for item in ai.get("pertemuan", []):
        title = item.get("judul","").strip()
        if not title:
            continue
        p = _find_heading(doc, title)
        if not p:
            # Cocokkan berdasarkan nomor pertemuan jika AI sedikit mengubah format judul.
            m = re.search(r"PERTEMUAN\s+([0-9\-]+)", title)
            if m:
                key = m.group(1)
                for hp in doc.paragraphs:
                    if hp.style.name == "Heading 4" and hp.text.strip().startswith("PERTEMUAN " + key):
                        p = hp; break
        if p:
            _set_heading(p, title)
            paras = doc.paragraphs
            idx = paras.index(p)
            # Cari heading berikutnya
            next_p = None
            for q in paras[idx+1:]:
                if q.style.name.startswith("Heading"):
                    next_p = q; break
            _fill_section(doc, idx, paras.index(next_p) if next_p else None, item.get("isi", []))

    _replace_section(doc, "ASESMEN DIAGNOSTIK", ai.get("asesmen_diagnostik"), "ASESMEN FORMATIF")
    _replace_section(doc, "ASESMEN FORMATIF", ai.get("asesmen_formatif"), "ASESMEN SUMATIF")
    _replace_section(doc, "ASESMEN SUMATIF", ai.get("asesmen_sumatif"), None)

    # Konten lampiran hanya jika pengguna meminta.
    if data_input.get("pakai_lkpd") == "Ya":
        _append_lampiran(doc, ai)

    # Ganti placeholder pada tabel tanda tangan tanpa mengubah layout.
    if len(doc.tables) >= 2:
        t = doc.tables[-1]
        if len(t.rows) and len(t.columns) >= 2:
            left, right = t.cell(0,0), t.cell(0,1)
            left.text = f"Mengetahui,\nKepala Sekolah\n\n\n\n{data_input.get('kepsek','..........................................')}"
            right.text = f"{data_input.get('sekolah','')}, ......................... 20..\nGuru Mata Pelajaran\n\n\n\n{data_input['guru']}"

    # Normal style mengikuti template; jangan memaksa font baru.
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

def _append_lampiran(doc, ai):
    # Menambahkan lampiran mengikuti gaya Normal/Heading dari template.
    doc.add_page_break()
    h = doc.add_paragraph("LAMPIRAN", style="Heading 2")
    doc.add_paragraph("A. LEMBAR KERJA PESERTA DIDIK (LKPD)", style="Heading 3")
    for x in ai.get("lkpd", []): doc.add_paragraph(str(x))
    doc.add_paragraph("B. BAHAN BACAAN GURU & PESERTA DIDIK", style="Heading 3")
    for x in ai.get("bahan_bacaan", []): doc.add_paragraph(str(x))
    doc.add_paragraph("C. GLOSARIUM", style="Heading 3")
    for x in ai.get("glosarium", []): doc.add_paragraph(str(x))
    doc.add_paragraph("D. DAFTAR PUSTAKA", style="Heading 3")
    for x in ai.get("daftar_pustaka", []): doc.add_paragraph(str(x))
