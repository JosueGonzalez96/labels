import streamlit as st
import pandas as pd
from docx import Document
from docx.shared import Cm, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import datetime
import io

st.set_page_config(page_title="Etiquetas Farmacia Word", page_icon="💊")

# --- FUNCIONES DE LIMPIEZA ---
def limpiar_dato(valor):
    if pd.isna(valor) or str(valor).strip().lower() == "nan":
        return ""
    if isinstance(valor, (datetime.datetime, pd.Timestamp)):
        return valor.strftime('%d/%m/%Y')
    val_str = str(valor).strip()
    if " 00:00:00" in val_str:
        val_str = val_str.replace(" 00:00:00", "")
    return val_str

def es_precio(valor):
    try:
        v = str(valor).replace('$', '').strip()
        if not v or "/" in v or "-" in v: return False
        float(v)
        return True
    except: return False

def set_cell_border(cell):
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    for border in ['top', 'left', 'bottom', 'right']:
        node = OxmlElement(f'w:{border}')
        node.set(qn('w:val'), 'single')
        node.set(qn('w:sz'), '4') 
        node.set(qn('w:color'), '000000')
        tcPr.append(node)

def generar_word(df):
    doc = Document()
    section = doc.sections[0]
    section.left_margin, section.right_margin = Cm(0.5), Cm(0.5)
    section.top_margin, section.bottom_margin = Cm(1.0), Cm(1.0)

    cols_count = 5
    rows_needed = (len(df) // cols_count) + (1 if len(df) % cols_count != 0 else 0)
    table = doc.add_table(rows=rows_needed, cols=cols_count)
    table.autofit = False 
    
    for col in table.columns:
        col.width = Cm(4.0)

    col_med, col_100, col_85 = df.columns[1], df.columns[2], df.columns[3]

    for i, row in df.iterrows():
        r_idx, c_idx = i // cols_count, i % cols_count
        cell = table.cell(r_idx, c_idx)
        set_cell_border(cell)
        
        nombre = str(row[col_med]).strip()
        if nombre.lower() == "nan" or not nombre: continue
        p100, p85 = limpiar_dato(row[col_100]), limpiar_dato(row[col_85])

        # --- SECCIÓN SUPERIOR: NOMBRE ---
        p_nombre = cell.paragraphs[0]
        p_nombre.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run_n = p_nombre.add_run(nombre)
        run_n.bold = True
        run_n.font.size = Pt(8.5)
        
        # Simular la línea horizontal con un borde inferior en el párrafo del nombre
        p_nombre.paragraph_format.space_after = Pt(2)
        
        # --- SECCIÓN INFERIOR: PRECIOS (Usando una sub-tabla para dividir Normal y Oferta) ---
        sub_table = cell.add_table(rows=2, cols=2)
        sub_table.autofit = True
        
        # Etiquetas
        lbl_norm = sub_table.cell(0,0).paragraphs[0]
        lbl_norm.add_run("NORMAL").font.size = Pt(5.5)
        
        lbl_ofer = sub_table.cell(0,1).paragraphs[0]
        lbl_ofer.add_run("OFERTA/DESCUENTO").font.size = Pt(5.5)
        
        # Valores de Precio
        # Precio Normal
        val_norm = sub_table.cell(1,0).paragraphs[0]
        run_v_n = val_norm.add_run(f"${p100}" if es_precio(p100) else p100)
        run_v_n.bold = True
        run_v_n.font.size = Pt(10)
        
        # Precio Oferta / Fecha (ROJO)
        val_ofer = sub_table.cell(1,1).paragraphs[0]
        texto_o = f"${p85}" if es_precio(p85) else p85
        run_v_o = val_ofer.add_run(texto_o)
        run_v_o.bold = True
        run_v_o.font.color.rgb = RGBColor(204, 0, 0) # Rojo
        run_v_o.font.size = Pt(11) if es_precio(p85) else Pt(7)

    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

# --- INTERFAZ ---
st.title("💊 Generador de Etiquetas Profesional (Word)")

with st.expander("📖 ¿Cómo preparar mi archivo?"):
    st.markdown("""
    ### Pasos rápidos:
    1. Columnas: **Stock, Nombre, Precio 100%, Precio 85%**.
    2. El archivo de salida respeta el diseño original: Nombre arriba y precios divididos abajo.
    3. Al ser Word, puedes corregir cualquier texto manualmente antes de imprimir.
    """)

archivo = st.file_uploader("Subir archivo de medicamentos", type=["xlsx", "csv"])

if archivo:
    try:
        df = pd.read_csv(archivo) if archivo.name.endswith('.csv') else pd.read_excel(archivo)
        st.success("✨ ¡Archivo cargado!")
        if st.button("🚀 Generar Etiquetas Word"):
            word_file = generar_word(df)
            st.download_button(
                label="📥 Descargar Word",
                data=word_file,
                file_name="Etiquetas_Farmacia_Editables.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
    except Exception as e:
        st.error(f"Error: {e}")
