import streamlit as st
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
import datetime
import io

# --- FUNCIONES DE LÓGICA INTERNA ---

def limpiar_dato(valor):
    """Convierte fechas de Excel a texto limpio y quita horas innecesarias."""
    if pd.isna(valor) or str(valor).strip().lower() == "nan":
        return ""
    # Si es una fecha nativa de Python/Pandas
    if isinstance(valor, (datetime.datetime, pd.Timestamp)):
        return valor.strftime('%d/%m/%Y')
    
    val_str = str(valor).strip()
    # Si es el texto largo con horas que mencionaste
    if " 00:00:00" in val_str:
        val_str = val_str.replace(" 00:00:00", "")
        # Opcional: Reordenar de YYYY-MM-DD a DD/MM/YYYY
        if "-" in val_str and len(val_str) == 10:
            y, m, d = val_str.split("-")
            return f"{d}/{m}/{y}"
    return val_str

def es_precio(valor):
    """Detecta si el valor debe llevar el símbolo de $."""
    try:
        v = str(valor).replace('$', '').strip()
        if not v or "/" in v or "-" in v: 
            return False
        float(v)
        return True
    except:
        return False

def generar_pdf(df):
    """Genera el PDF en memoria y lo devuelve como un buffer de bytes."""
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    # Configuración de diseño
    cols = 5
    margin_x, margin_y = 0.5 * cm, 1.0 * cm
    label_w, label_h = (width - 2 * margin_x) / cols, 2.8 * cm
    x, y = margin_x, height - margin_y - label_h
    
    # Identificar columnas por posición (0: Stock, 1: Nombre, 2: Precio, 3: Oferta)
    try:
        col_med = df.columns[1]
        col_100 = df.columns[2]
        col_85 = df.columns[3]
    except IndexError:
        st.error("El archivo no tiene suficientes columnas. Revisa el tutorial.")
        return None

    for i, row in df.iterrows():
        nombre = str(row[col_med])
        if nombre.lower() == "nan" or not nombre.strip():
            continue

        p100 = limpiar_dato(row[col_100])
        p85 = limpiar_dato(row[col_85])

        # Dibujar Cuadro
        c.setLineWidth(0.3)
        c.rect(x, y, label_w, label_h)
        
        # Nombre del Medicamento
        c.setFont("Helvetica-Bold", 7)
        if len(nombre) > 22:
            c.drawCentredString(x + label_w/2, y + label_h - 15, nombre[:22])
            c.drawCentredString(x + label_w/2, y + label_h - 25, nombre[22:44])
        else:
            c.drawCentredString(x + label_w/2, y + label_h - 20, nombre)

        # Líneas y Textos Fijos
        c.line(x, y + 28, x + label_w, y + 28)
        c.line(x + label_w/2, y, x + label_w/2, y + 28)
        c.setFont("Helvetica", 5)
        c.drawString(x + 4, y + 21, "NORMAL")
        c.drawString(x + label_w/2 + 4, y + 21, "OFERTA")

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
            c.setFont("Helvetica-Bold", 7.5)
            c.drawCentredString(x + (label_w * 0.75), y + 8, p85)
        c.setFillColorRGB(0, 0, 0)

        # Lógica de Cuadrícula
        if (i + 1) % cols == 0:
            x = margin_x
            y -= label_h
        else:
            x += label_w
            
        if y < margin_y:
            c.showPage()
            x, y = margin_x, height - margin_y - label_h

    c.save()
    buffer.seek(0)
    return buffer

# --- INTERFAZ DE USUARIO (STREAMLIT) ---

st.set_page_config(page_title="Etiquetas Farmacia", page_icon="💊", layout="centered")

st.title("💊 Generador de Etiquetas para Anaquel")
st.markdown("Convierte tu listado de precios en etiquetas listas para imprimir.")

# Bloque de Tutorial
with st.expander("📖 ¿Cómo preparar mi archivo?"):
    st.markdown("""
    ### 1. Formato de las columnas
    Tu archivo (Excel o CSV) debe tener este orden exacto:
    - **A:** Stock (Se ignora)
    - **B:** Nombre del Medicamento
    - **C:** Precio Normal
    - **D:** Precio Oferta o Fecha de Vencimiento
    
    ### 2. Guardar desde Excel
    Para mejores resultados, guarda como **CSV UTF-8 (delimitado por comas)**.
    
    ### 3. Ejemplo de datos
    | Stock | Medicamento | 100% | 85% |
    | :--- | :--- | :--- | :--- |
    | 10 | Ácido Acetilsalicílico | 30 | 25.5 |
    | 5 | Paracetamol 500mg | 50 | 42 |
    """)

st.divider()

# Subida de archivo
archivo = st.file_uploader("Arrastra tu archivo Excel o CSV aquí", type=["xlsx", "csv"])

if archivo is not None:
    try:
        # Cargar datos
        if archivo.name.endswith('.csv'):
            # Intento de lectura robusta para CSV
            try:
                df = pd.read_csv(archivo, sep=',', encoding='utf-8')
            except:
                archivo.seek(0)
                df = pd.read_csv(archivo, sep=';', encoding='latin-1')
        else:
            df = pd.read_excel(archivo)

        st.success(f"✅ Archivo '{archivo.name}' cargado con éxito.")
        
        # Vista previa
        st.write("Vista previa de los datos:")
        st.dataframe(df.head(5), use_container_width=True)

        # Botón de acción
        if st.button("🚀 Generar PDF de Etiquetas"):
            with st.spinner("Procesando etiquetas..."):
                pdf_output = generar_pdf(df)
                if pdf_output:
                    st.download_button(
                        label="📥 Descargar PDF para Imprimir",
                        data=pdf_output,
                        file_name="Etiquetas_Farmacia.pdf",
                        mime="application/pdf"
                    )
                    st.balloons()
    
    except Exception as e:
        st.error(f"Error al procesar el archivo: {e}")
