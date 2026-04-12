import streamlit as st
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
import io

# --- Funciones de procesamiento (Lógica que ya probamos) ---
def limpiar_dato(valor):
    if pd.isna(valor): return ""
    val_str = str(valor).strip()
    return val_str.replace(" 00:00:00", "")

def es_precio(valor):
    try:
        v = str(valor).replace('$', '').strip()
        if not v or "/" in v or "-" in v: return False
        float(v)
        return True
    except: return False

def generar_pdf(df):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    cols = 5
    margin_x, margin_y = 0.5 * cm, 1.0 * cm
    label_w, label_h = (width - 2 * margin_x) / cols, 2.8 * cm
    x, y = margin_x, height - margin_y - label_h
    
    # Usar las columnas por posición
    col_med, col_100, col_85 = df.columns[1], df.columns[2], df.columns[3]

    for i, row in df.iterrows():
        nombre = str(row[col_med])
        if nombre.lower() == "nan" or not nombre.strip(): continue
        p100, p85 = limpiar_dato(row[col_100]), limpiar_dato(row[col_85])

        c.setLineWidth(0.3)
        c.rect(x, y, label_w, label_h)
        c.setFont("Helvetica-Bold", 7)
        if len(nombre) > 22:
            c.drawCentredString(x + label_w/2, y + label_h - 15, nombre[:22])
            c.drawCentredString(x + label_w/2, y + label_h - 25, nombre[22:44])
        else:
            c.drawCentredString(x + label_w/2, y + label_h - 20, nombre)

        c.line(x, y + 28, x + label_w, y + 28)
        c.line(x + label_w/2, y, x + label_w/2, y + 28)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(x + 4, y + 8, f"${p100}" if es_precio(p100) else p100)
        c.setFillColorRGB(0.8, 0, 0)
        if es_precio(p85):
            c.drawString(x + label_w/2 + 4, y + 8, f"${p85}")
        else:
            c.setFont("Helvetica-Bold", 7)
            c.drawCentredString(x + (label_w * 0.75), y + 8, p85)
        c.setFillColorRGB(0, 0, 0)

        if (i + 1) % cols == 0:
            x = margin_x
            y -= label_h
        else: x += label_w
        if y < margin_y:
            c.showPage()
            x, y = margin_x, height - margin_y - label_h

    c.save()
    buffer.seek(0)
    return buffer

# --- Interfaz de Usuario con Streamlit ---
st.set_page_config(page_title="Generador de Etiquetas Farmacia", page_icon="💊")
st.title("💊 Generador de Etiquetas")
st.write("Sube tu archivo Excel o CSV para generar las etiquetas de anaquel.")

uploaded_file = st.file_uploader("Elige un archivo", type=['csv', 'xlsx'])

if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        
        st.success("Archivo cargado correctamente")
        st.dataframe(df.head()) # Vista previa

        if st.button("🚀 Generar PDF"):
            pdf_data = generar_pdf(df)
            st.download_button(
                label="📥 Descargar Etiquetas PDF",
                data=pdf_data,
                file_name="etiquetas_farmacia.pdf",
                mime="application/pdf"
            )
    except Exception as e:
        st.error(f"Hubo un error: {e}")
