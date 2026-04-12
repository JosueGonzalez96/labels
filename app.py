from reportlab.pdfbase.pdfmetrics import stringWidth

def generar_pdf(df):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    cols = 5
    margin_x, margin_y = 0.5 * cm, 1.0 * cm
    label_w, label_h = (width - 2 * margin_x) / cols, 2.8 * cm
    
    # Margen interno para que el texto no toque las líneas negras
    padding = 0.2 * cm
    usable_w = label_w - (padding * 2)
    
    x, y = margin_x, height - margin_y - label_h
    col_med, col_100, col_85 = df.columns[1], df.columns[2], df.columns[3]

    for i, row in df.iterrows():
        nombre = str(row[col_med]).strip()
        if nombre.lower() == "nan" or not nombre: continue

        p100 = limpiar_dato(row[col_100])
        p85 = limpiar_dato(row[col_85])

        # Dibujar Cuadro
        c.setLineWidth(0.3)
        c.rect(x, y, label_w, label_h)
        
        # --- AJUSTE DINÁMICO DE TEXTO ---
        font_name = "Helvetica-Bold"
        base_size = 8.5 # Tamaño máximo deseado
        min_size = 4.0  # Tamaño mínimo para que no desaparezca
        
        # Función para dividir texto y verificar si cabe
        def obtener_lineas(texto, size):
            palabras = texto.split()
            lineas = []
            linea_act = ""
            for p in palabras:
                test = f"{linea_act} {p}".strip()
                if stringWidth(test, font_name, size) <= usable_w:
                    linea_act = test
                else:
                    if linea_act: lineas.append(linea_act)
                    linea_act = p
            lineas.append(linea_act)
            return lineas

        # Buscamos el tamaño de fuente ideal
        current_size = base_size
        lineas_finales = obtener_lineas(nombre, current_size)
        
        # Si con el tamaño base ocupa más de 3 líneas o una palabra sola se sale, bajamos la letra
        while current_size > min_size:
            # Verificar si alguna palabra individual es más ancha que el cuadro
            palabra_mas_larga = max(nombre.split(), key=len)
            if (stringWidth(palabra_mas_larga, font_name, current_size) <= usable_w and 
                len(obtener_lineas(nombre, current_size)) <= 3):
                break
            current_size -= 0.5
            lineas_finales = obtener_lineas(nombre, current_size)

        # Dibujar líneas de texto centradas
        c.setFont(font_name, current_size)
        y_txt = y + label_h - (0.5 * cm)
        for linea in lineas_finales[:3]: # Máximo 3 líneas
            c.drawCentredString(x + label_w/2, y_txt, linea)
            y_txt -= (current_size + 1.5)

        # --- ÁREA DE PRECIOS ---
        c.setLineWidth(0.3)
        c.line(x, y + 28, x + label_w, y + 28)
        c.line(x + label_w/2, y, x + label_w/2, y + 28)
        
        c.setFont("Helvetica", 5.5)
        c.drawString(x + 4, y + 21, "NORMAL")
        c.drawString(x + label_w/2 + 4, y + 21, "OFERTA/VENCE")

        # Precio Normal
        c.setFont("Helvetica-Bold", 10)
        c.setFillColorRGB(0, 0, 0)
        c.drawString(x + 4, y + 8, f"${p100}" if es_precio(p100) else p100)
        
        # Oferta / Fecha
        c.setFillColorRGB(0.8, 0, 0)
        if es_precio(p85):
            c.setFont("Helvetica-Bold", 11)
            c.drawString(x + label_w/2 + 4, y + 8, f"${p85}")
        else:
            # Ajuste extra para la fecha si es muy larga
            f_size = 7 if stringWidth(p85, font_name, 7) <= (usable_w/2) else 5.5
            c.setFont(font_name, f_size)
            c.drawCentredString(x + (label_w * 0.75), y + 8, p85)
        
        c.setFillColorRGB(0, 0, 0)

        # Posicionamiento de cuadrícula
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
