import streamlit as st
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
import datetime
import io

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

def generar_pdf(df):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    cols = 5
    margin_x, margin_y = 0.5 * cm, 1.0 * cm
    label_w, label_h = (width - 2 * margin_x) / cols, 2.8 * cm
    x, y = margin_x, height - margin_y - label_h
    
    # Identificar columnas por posición (1: Medicamento, 2: 100%, 3: 85%)
    col_med, col_100, col_85 = df.columns[1], df.columns[2], df.columns[3]

    for i, row in df.iterrows():
        nombre = str(row[col_med]).strip()
        if nombre.lower() == "nan" or not nombre: continue

        p100 = limpiar_dato(row[col_100])
        p85 = limpiar_dato(row[col_85])

        # Dibujar Cuadro
        c.setLineWidth(0.3)
        c.rect(x, y, label_w, label_h)
        
        # --- AJUSTE DE TEXTO SIN CORTES ---
        # Si el nombre es muy largo, achicamos la letra
        if len(nombre) > 50: f_size = 5.5
        elif len(nombre) > 35: f_size = 6.5
        else: f_size = 8
        
        c.setFont("Helvetica-Bold", f_size)
        
        # Dividir en palabras y crear líneas
        palabras = nombre.split()
        lineas = []
        linea_act = ""
        limite_chars = 25 if f_size < 7 else 20
        
        for p in palabras:
            if len(linea_act + p) <= limite_chars:
                linea_act += p + " "
            else:
                lineas.append(linea_act.strip())
                linea_act = p + " "
        lineas.append(linea_act.strip())

        # Dibujar líneas (máximo 3 para no chocar con precios)
        y_txt = y + label_h - 12
        for linea in lineas[:3]:
            c.drawCentredString(x + label_w/2, y_txt, linea)
            y_txt -= (f_size + 2)

        # --- ÁREA DE PRECIOS ---
        c.line(x, y + 28, x + label_w, y + 28)
        c.line(x + label_w/2, y, x + label_w/2, y + 28)
        
        c.setFont("Helvetica", 5)
        c.drawString(x + 4, y + 21, "NORMAL")
        c.drawString(x + label_w/2 + 4, y + 21, "OFERTA/VENCE")

        # Precio Normal
        c.setFont("Helvetica-Bold", 10)
        c.setFillColorRGB(0, 0, 0)
        c.drawString(x + 4, y + 8, f"${p100}" if es_precio(p100) else p100)
        
        # Precio Oferta o Fecha (Rojo)
        c.setFillColorRGB(0.8, 0, 0)
        if es_precio(p85):
            c.setFont("Helvetica-Bold", 11)
            c.drawString(x + label_w/2 + 4, y + 8, f"${p85}")
        else:
            c.setFont("Helvetica-Bold", 7)
            c.drawCentredString(x + (label_w * 0.75), y + 8, p85)
        c.setFillColorRGB(0, 0, 0)

        # Posicionamiento
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

# --- INTERFAZ STREAMLIT ---
st.set_page_config(page_title="Etiquetas Farmacia", page_icon="💊")
st.title("💊 Generador de Etiquetas")

with st.expander("📖 Instrucciones"):
    st.write("Asegúrate de que tu archivo tenga este orden: Stock, Medicamento, Precio, Oferta.")

archivo = st.file_uploader("Sube tu Excel o CSV", type=["xlsx", "csv"])

if archivo:
    try:
        if archivo.name.endswith('.csv'):
            df = pd.read_csv(archivo)
        else:
            df = pd.read_excel(archivo)
        
        st.success("Archivo listo")
        if st.button("🚀 Generar PDF"):
            pdf_data = generar_pdf(df)
            st.download_button("📥 Descargar PDF", pdf_data, "Etiquetas.pdf", "application/pdf")
    except Exception as e:
        st.error(f"Error: {e}")
