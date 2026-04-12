from reportlab.pdfbase.pdfmetrics import stringWidth

def generar_pdf(df):
    """Genera PDF con ajuste de fuente milimétrico para que NADA se corte."""
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    cols = 5
    margin_x, margin_y = 0.5 * cm, 1.0 * cm
    label_w, label_h = (width - 2 * margin_x) / cols, 2.8 * cm
    
    # Área útil para el texto (dejando márgenes internos)
    usable_width = label_w - 0.4 * cm 
    
    x, y = margin_x, height - margin_y - label_h
    
    col_med, col_100, col_85 = df.columns[1], df.columns[2], df.columns[3]

    for i, row in df.iterrows():
        nombre = str(row[col_med]).strip()
        if nombre.lower() == "nan" or not nombre: continue

        p100 = limpiar_dato(row[col_100])
        p85 = limpiar_dato(row[col_85])

        # Dibujar recuadro
        c.setLineWidth(0.3)
        c.rect(x, y, label_w, label_h)
        
        # --- LÓGICA DE AJUSTE AUTOMÁTICO (AUTOSIZE) ---
        font_name = "Helvetica-Bold"
        max_font_size = 8.5  # Tamaño ideal para nombres cortos
        min_font_size = 4.5  # Lo mínimo legal antes de que sea ilegible
        
        current_font_size = max_font_size
        
        # Función para probar si el texto cabe en un tamaño dado
        def intentar_ajuste(texto, size):
            palabras = texto.split()
            lineas = []
            linea_actual = ""
            for p in palabras:
                test_linea = f"{linea_actual} {p}".strip()
                # Calculamos el ancho real que ocuparía el texto en puntos
                ancho_test = stringWidth(test_linea, font_name, size)
                if ancho_test <= usable_width:
                    linea_actual = test_linea
                else:
                    lineas.append(linea_actual)
                    linea_actual = p
            lineas.append(linea_actual)
            return lineas

        # Bucle para reducir la letra hasta que el texto quepa en máximo 3 líneas
        while current_font_size > min_font_size:
            lineas_propuestas = intentar_ajuste(nombre, current_font_size)
            if len(lineas_propuestas) <= 3:
                break
            current_font_size -= 0.5

        # Dibujar las líneas calculadas
        c.setFont(font_name, current_font_size)
        y_texto = y + label_h - (0.4 * cm) # Punto de inicio
        for linea in lineas_propuestas[:3]: # Aseguramos que no pase de 3
            c.drawCentredString(x + label_w/2, y_texto, linea)
            y_texto -= (current_font_size + 1.5)

        # --- ÁREA DE PRECIOS ---
        c.setLineWidth(0.3)
        c.line(x, y + 28, x + label_w, y + 28)
        c.line(x + label_w/2, y, x + label_w/2, y + 28)
        
        c.setFont("Helvetica", 5.5)
        c.drawString(x + 4, y + 20, "NORMAL")
        c.drawString(x + label_w/2 + 4, y + 20, "OFERTA/VENCE")

        # Precio 100%
        c.setFont("Helvetica-Bold", 10)
        c.setFillColorRGB(0, 0, 0)
        txt_100 = f"${p100}" if es_precio(p100) else p100
        c.drawString(x + 4, y + 7, txt_100)
        
        # Precio 85% o Fecha
        c.setFillColorRGB(0.8, 0, 0)
        if es_precio(p85):
            c.setFont("Helvetica-Bold", 11)
            c.drawString(x + label_w/2 + 4, y + 7, f"${p85}")
        else:
            # También ajustamos el tamaño de la fecha si es muy larga
            size_fecha = 7.5 if len(p85) < 12 else 6
            c.setFont("Helvetica-Bold", size_fecha)
            c.drawCentredString(x + (label_w * 0.75), y + 7, p85)
        
        c.setFillColorRGB(0, 0, 0)

        # Control de cuadrícula
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
