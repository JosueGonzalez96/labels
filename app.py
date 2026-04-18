# --- INTERFAZ STREAMLIT ---
st.set_page_config(page_title="Etiquetas Farmacia Word", page_icon="💊")
st.title("💊 Generador de Etiquetas (Word Editable)")

# --- REINCORPORACIÓN DEL TUTORIAL ---
with st.expander("📖 ¿Cómo preparar mi archivo?"):
    st.markdown("""
    ### Pasos rápidos para Word:
    1. Asegúrate de que las columnas estén en este orden: **Stock, Nombre, Precio 100%, Precio 85%**.
    2. Si usas Excel, puedes subir el `.xlsx` directamente o un **CSV UTF-8**.
    3. El archivo Word generado contendrá una tabla; si algún nombre se ve desalineado, podrás ajustarlo manualmente antes de imprimir.
    """)

st.write("Selecciona tu archivo de medicamentos para generar el documento editable:")
# ... resto del código del file_uploader
