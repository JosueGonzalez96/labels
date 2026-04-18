import streamlit as st
import pandas as pd
from docx import Document
from docx.shared import Cm, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import datetime
import io

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
    """Añade bordes negros a una celda de la tabla"""
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    for border in ['top', 'left', 'bottom', 'right']:
        node = OxmlElement(f'w:{border}')
        node.set(qn('w:val'), 'single')
        node.set(qn('w:sz'), '4') # Tamaño del borde
        node.set(qn('w:color'), '000000')
        tcPr.append(node)

def generar_word(df):
    doc = Document()
    
    # Configuración de márgenes estrechos para aprovechar la hoja
    section = doc.sections[0]
    section.left_margin = Cm(0.5)
    section.right_margin = Cm(0.5)
    section.top_margin = Cm(1.0)
    section.bottom_margin = Cm(1.0)

    cols_count = 5
    rows_needed = (len(df) // cols_count) + (1 if len(df) % cols_count != 0 else 0)
    
    # Crear tabla base
    table = doc.add_table(rows=rows_needed, cols=cols_count)
    table.autofit = False 
    
    # Definir ancho de columnas
    for col in table.columns:
        col.width = Cm(4.0)

    col_med, col_100, col_85 = df.columns[1], df.columns[2], df.columns[3]

    for i, row in df.iterrows():
        r_idx = i // cols_count
        c_idx = i % cols_count
        cell = table.cell(r_idx, c_idx)
        set_cell_border(cell)
        
        # Limpieza de datos
        nombre = str(row[col_med]).strip()
        if nombre.lower() == "nan" or not nombre: continue
        p100 = limpiar_dato(row[col_100])
        p85 = limpiar_dato(row[col_85])

        # Construcción del contenido de la celda
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # Nombre del producto
        run_n = p.add_run(f"{nombre}\n")
        run_n.bold = True
        run_n.font.size = Pt(8)
        
        # Precios
        p_precios = cell.add_paragraph()
        p_precios.alignment = WD_ALIGN_PARAGRAPH.LEFT
        
        # Precio Normal
        run_norm = p_precios.add_run(f"NORMAL: ${p100 if es_precio(p100) else p100}")
        run_norm.font.size = Pt(7)
        
        # Precio Oferta (En una nueva línea dentro de la misma celda)
        p_oferta = cell.add_paragraph()
        p_oferta.alignment = WD_ALIGN_PARAGRAPH.LEFT
        run_o = p_oferta.add_run(f"OFERTA: ${p85}" if es_precio(p85) else f"VENCE: {p85}")
        run_o.bold = True
        run_o.font.size = Pt(9)
        # Color rojo (aproximado)
        run_o.font.color.rgb = None # Word maneja colores de forma distinta, pero puedes editarlo luego

    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

# --- INTERFAZ STREAMLIT ---
st.set_page_config(page_title="Etiquetas Farmacia Word", page_icon="💊")
st.title("💊 Generador de Etiquetas (Word Editable)")

archivo = st.file_uploader("Subir archivo Excel o CSV", type=["xlsx", "csv"])

if archivo:
    try:
        df = pd.read_csv(archivo) if archivo.name.endswith('.csv') else pd.read_excel(archivo)
        st.success("✨ ¡Archivo cargado!")

        if st.button("🚀 Generar Etiquetas Word"):
            with st.spinner("Creando documento editable..."):
                word_data = generar_word(df)
                st.download_button(
                    label="📥 Descargar Word Editable",
                    data=word_data,
                    file_name="Etiquetas_Editables.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )
    except Exception as e:
        st.error(f"Error: {e}")
