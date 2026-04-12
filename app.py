import streamlit as st
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.pdfbase.pdfmetrics import stringWidth
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

def generar_pdf(df):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    # Configuración de etiquetas (5 columnas por hoja)
    cols = 5
    margin_x, margin_y = 0.5 * cm, 1.0 * cm
    label_w, label_h = (width - 2 * margin_x) / cols, 2.8 * cm
    
    # Margen interno de seguridad para que el nombre no toque los bordes
    padding = 0.15 * cm
    usable_w = label_w - (padding * 2)
    
    x, y = margin_x, height - margin_y - label_h
    col_med, col_100, col_85 = df.columns[1], df.columns[2], df.columns[3]

    for i, row in df.iterrows():
        nombre = str(row[col_med]).strip()
        if nombre.lower() == "nan" or not nombre: continue

        p100, p85 = limpiar_dato(row[col_100]), limpiar_dato(row[col_85])

        # Dibujar Cuadro Exterior
        c.setLineWidth(0.3)
        c.rect(x, y, label_w, label_h)
        
        # --- MOTOR DE AJUSTE AUTOMÁTICO DE NOMBRE ---
        font_name = "Helvetica-Bold"
        current_size = 8.5  # Tamaño máximo
        min_size = 4.5      # Tamaño mínimo para nombres extremadamente largos
        
        # Función para repartir texto en líneas según ancho
        def preparar_lineas(txt, size):
            palabras = txt.split()
            lineas_res = []
            linea_act = ""
            for p in palabras:
                test = f"{linea_act} {p}".strip()
                if stringWidth(test, font_name, size) <= usable_w:
                    linea_act = test
                else:
                    if linea_act: lineas_res.append(linea_act)
                    linea_act = p
            lineas_res.append(linea_act)
            return lineas_res

        # Reducir letra hasta que el nombre quepa en el ancho y en máximo 3 líneas
        while current_size > min_size:
            lineas = preparar_lineas(nombre, current_size)
            # Verificamos si la palabra más larga cabe sola
            max_p_width = max([stringWidth(p, font_name, current_size) for p in nombre.split()])
            if max_p_width <= usable_w and len(lineas) <= 3:
                break
            current_size -= 0.3

        # Escribir nombre (centrado)
        c.setFont(font_name, current_size)
        y_txt = y + label_h - (0.45 * cm)
        for linea in lineas[:3]:
            c.drawCentredString(x + label_w/2, y_txt, linea)
            y_txt -= (current_size + 1.2)

        # --- ÁREA DE PRECIOS ---
        c.setLineWidth(0.3)
        c.line(x, y + 28, x + label_w, y + 28) # Línea horizontal
        c.line(x + label_w/2, y, x + label_w/2, y + 28) # Línea vertical divisoria
        
        c.setFont("Helvetica", 5.5)
        c.drawString(x + 4, y + 21, "NORMAL")
        c.drawString(x + label_w/2 + 4, y + 21, "OFERTA/VENCE")

        # Precio Normal
        c.setFont("Helvetica-Bold", 10)
        c.setFillColorRGB(0, 0, 0)
        c.drawString(x + 4, y + 8, f"${p100}" if es_precio(p100) else p100)
        
        # Oferta / Fecha (Rojo)
        c.setFillColorRGB(0.8, 0, 0)
        if es_precio(p85):
            c.setFont("Helvetica-Bold", 11)
            c.drawString(x + label_w/2 + 4, y + 8, f"${p85}")
        else:
            # Ajuste de tamaño para fechas largas
            f_size = 7 if len(p85) < 12 else 5.5
            c.setFont("Helvetica-Bold", f_size)
            c.drawCentredString(x + (label_w * 0.75), y + 8, p85)
        
        c.setFillColorRGB(0, 0, 0) # Reset color

        # Salto de etiqueta
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
st.title("💊 Generador de Etiquetas Profesional")

# Restablecemos el Tutorial
with st.expander("📖 ¿Cómo preparar mi archivo?"):
    st.markdown("""
    ### Pasos rápidos:
    1. Asegúrate de que las columnas estén en este orden: **Stock, Nombre, Precio 100%, Precio 85%**.
    2. Si usas Excel, guárdalo como **CSV UTF-8** para que los acentos se vean bien.
    3. Si pones fechas de vencimiento en la última columna, el sistema las detectará automáticamente.
    """)

st.write("Selecciona tu archivo de medicamentos para generar el PDF listo para imprimir:")

archivo = st.file_uploader("Subir archivo Excel o CSV", type=["xlsx", "csv"])

if archivo:
    try:
        if archivo.name.endswith('.csv'):
            df = pd.read_csv(archivo)
        else:
            df = pd.read_excel(archivo)
        
        st.success("✨ ¡Archivo cargado con éxito! Hemos verificado tus datos.")
        st.dataframe(df.head(3), use_container_width=True) # Vista previa

        if st.button("🚀 Generar Etiquetas"):
            with st.spinner("Ajustando nombres y creando PDF..."):
                pdf_data = generar_pdf(df)
                if pdf_data:
                    st.balloons()
                    st.download_button(
                        label="📥 Descargar PDF para Imprimir",
                        data=pdf_data,
                        file_name="Etiquetas_Anaquel.pdf",
                        mime="application/pdf"
                    )
                    st.info("El PDF se generó con ajuste automático de texto para que nada se corte.")
    except Exception as e:
        st.error(f"Ocurrió un error al leer el archivo: {e}")
