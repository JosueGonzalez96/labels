import streamlit as st
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
import datetime
import io

# --- FUNCIONES DE SOPORTE ---
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
    try:
        c = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter
        
        cols = 5
        margin_x, margin_y = 0.5 * cm, 1.0 * cm
        label_w, label_h = (width - 2 * margin_x) / cols, 2.8 * cm
        x, y = margin_x, height - margin_y - label_h
        
        # Columnas por posición (1: Medicamento, 2: 100%, 3: 85%)
        col_med, col_100, col_85 = df.columns[1], df.columns[2], df.columns[3]

        for i, row in df.iterrows():
            try:
                nombre = str(row[col_med]).strip()
                if nombre.lower() == "nan" or not nombre: continue

                p100 = limpiar_dato(row[col_100])
                p85 = limpiar_dato(row[col_85])

                # Dibujar Cuadro
                c.setLineWidth(0.3)
                c.rect(x, y, label_w, label_h)
                
                # --- AJUSTE DE TEXTO GARANTIZADO ---
                # Determinamos el tamaño de fuente según el largo total
                largo = len(nombre)
                if largo > 60: f_size = 5
                elif largo > 45: f_size = 6
                elif largo > 30: f_size = 7
                else: f_size = 8.5
                
                c.setFont("Helvetica-Bold", f_size)
                
                # Partir el texto en líneas de máximo N caracteres
                # (Ajuste empírico: a menor fuente, caben más caracteres)
                chars_por_linea = int(140 / f_size) 
                
                palabras = nombre.split()
                lineas = []
                linea_act = ""
                
                for p in palabras:
                    if len(linea_act + p) <= chars_por_linea:
                        linea_act += p + " "
                    else:
                        lineas.append(linea_act.strip())
                        linea_act = p + " "
                lineas.append(linea_act.strip())

                # Dibujar las líneas (centradas)
                y_txt = y + label_h - (0.4 * cm)
                for linea in lineas[:3]: # Máximo 3 líneas
                    # Si una sola palabra es más larga que el límite, la forzamos a cortarse
                    if len(linea) > chars_por_linea:
                        linea = linea[:chars_por_linea-2] + ".."
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
                txt_100 = f"${p100}" if es_precio(p100) else p100
                c.drawString(x + 4, y + 8, txt_100)
                
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
            except:
                continue # Si una etiqueta falla, saltar a la siguiente

        c.save()
        buffer.seek(0)
        return buffer
    except Exception as e:
        st.error(f"Error crítico: {e}")
        return None

# --- INTERFAZ ---
st.set_page_config(page_title="Etiquetas Farmacia", page_icon="💊")
st.title("💊 Generador de Etiquetas")

archivo = st.file_uploader("Sube tu Excel o CSV", type=["xlsx", "csv"])

if archivo:
    try:
        if archivo.name.endswith('.csv'):
            df = pd.read_csv(archivo)
        else:
            df = pd.read_excel(archivo)
        
        st.success("Archivo cargado")
        if st.button("🚀 Generar PDF"):
            res = generar_pdf(df)
            if res:
                st.download_button("📥 Descargar PDF", res, "Etiquetas.pdf", "application/pdf")
    except Exception as e:
        st.error(f"Error al leer archivo: {e}")
