import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime

# Configuración de la página estilo MikroTik
st.set_page_config(page_title="Calculadora FTTH Pro", layout="centered")

st.markdown("""
    <style>
    html, body, [class*="css"] {
        font-family: "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }
    .main-title {
        color: #333333;
        font-weight: 700;
        border-bottom: 2px solid #0055ff;
        padding-bottom: 10px;
    }
    .stNumberInput > label {
        font-weight: 600;
    }
    .alert-box {
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 10px;
        font-size: 0.95em;
    }
    .alert-error { background-color: #ffdde1; color: #85141d; border-left: 5px solid #e32636; }
    .alert-warning { background-color: #fff3cd; color: #856404; border-left: 5px solid #ffc107; }
    .alert-ok { background-color: #d4edda; color: #155724; border-left: 5px solid #28a745; }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h2 class='main-title'>⚙️ Calculadora FTTH Inteligente</h2>", unsafe_allow_html=True)
st.write("Diagnóstico bidireccional automático con función de exportación de informes para cuadrillas.")

# --- PARÁMETROS TÉCNICOS IDEALES ---
PERDIDAS = {
    "70/30": {"pasante": 1.90, "abonado": 15.15},
    "50/50": {"pasante": 3.50, "abonado": 12.50},
    "Terminal": {"pasante": 0.00, "abonado": 9.50}
}

# --- CONFIGURACIÓN DEL RAMAL ---
st.sidebar.header("🛠️ Estructura del Ramal")
cantidad_cajas = st.sidebar.slider("Cantidad de cajas:", 1, 6, 4)

estructura_ramal = []
for i in range(cantidad_cajas):
    if i == cantidad_cajas - 1:
        tipo = st.sidebar.selectbox(f"Caja {i+1} (Final):", ["Terminal", "70/30", "50/50"], index=0)
    else:
        tipo = st.sidebar.selectbox(f"Caja {i+1}:", ["70/30", "50/50", "Terminal"], index=0)
    estructura_ramal.append(tipo)

# --- PUNTO DE MEDICIÓN FLEXIBLE ---
st.subheader("📥 Datos de Medición en Campo")

opciones_origen = ["NAP Directo"]
for i, tipo in enumerate(estructura_ramal):
    opciones_origen.append(f"Caja {i+1} ({tipo}) - Boca Abonado")
    if tipo != "Terminal":
        opciones_origen.append(f"Caja {i+1} ({tipo}) - Salida Pasante")

punto_medido = st.selectbox("¿Dónde realizaste la medición?", opciones_origen)

col1, col2 = st.columns(2)
with col1:
    val_datos = st.number_input("Datos 1490nm Medidos (dBm):", value=-1.50, step=0.1)
with col2:
    val_video = st.number_input("Video 1550nm Medidos (dBm):", value=15.22, step=0.1)

# Función para armar el PDF de forma dinámica
def generar_pdf_informe(datos_origen, tabla_df, punto_m, v_dat, v_vid):
    pdf = FPDF()
    pdf.add_page()
    
    # Encabezado Estilo Tecnico
    pdf.set_fill_color(0, 85, 255) # Azul institucional
    pdf.rect(0, 0, 210, 35, "F")
    
    pdf.set_font("Arial", "B", 16)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 10, "INFORME TECNICO DE MEDICION FTTH", ln=True, align="L")
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 5, f"Fecha de emision: {datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=True, align="L")
    
    pdf.ln(20)
    pdf.set_text_color(0, 0, 0)
    
    # Seccion 1: Datos de la medicion de entrada
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "1. Datos Ingresados en Campo", ln=True)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(3)
    
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 6, f"Punto donde se midio: {punto_m}", ln=True)
    pdf.cell(0, 6, f"Valor Datos (1490nm) cargado: {v_dat} dBm", ln=True)
    pdf.cell(0, 6, f"Valor Video (1550nm) cargado: {v_vid} dBm", ln=True)
    pdf.ln(5)
    
    # Origen calculado de la red
    pdf.set_fill_color(240, 244, 254)
    pdf.set_font("Arial", "B", 10)
    origen_texto = f" Origen Reconstruido en NAP -> Datos: {round(datos_origen['datos'], 2)} dBm  |  Video: {round(datos_origen['video'], 2)} dBm"
    pdf.cell(0, 8, origen_texto, ln=True, fill=True)
    pdf.ln(5)
    
    # Seccion 2: Tabla de Proyección
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "2. Proyeccion Teorica de la Cascada", ln=True)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(4)
    
    # Encabezados de tabla de PDF
    pdf.setfont("Arial", "B", 9)
    pdf.set_fill_color(220, 230, 255)
    pdf.cell(40, 8, " Caja", 1, 0, "L", True)
    pdf.cell(38, 8, " Datos Abonado", 1, 0, "C", True)
    pdf.cell(38, 8, " Video Abonado", 1, 0, "C", True)
    pdf.cell(37, 8, " Pasante Datos", 1, 0, "C", True)
    pdf.cell(37, 8, " Pasante Video", 1, 1, "C", True)
    
    # Filas de la tabla
    pdf.set_font("Arial", "", 9)
    for _, fila in tabla_df.iterrows():
        pdf.cell(40, 8, f" {fila['Caja']}", 1, 0, "L")
        pdf.cell(38, 8, f"{fila['Datos Abonado']} dBm", 1, 0, "C")
        pdf.cell(38, 8, f"{fila['Video Abonado']} dBm", 1, 0, "C")
        pdf.cell(37, 8, f"{fila['Pasante Datos']}", 1, 0, "C")
        pdf.cell(37, 8, f"{fila['Pasante Video']}", 1, 1, "C")
        
    pdf.ln(10)
    pdf.set_font("Arial", "I", 9)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 5, "* Umbral minimo recomendado para Video (1550nm) en abonado: -8.00 dBm.", ln=True)
    pdf.cell(0, 5, "* Valores calculados en base a coeficientes optimos de preconectorizado de cooperativa.", ln=True)
    
    return pdf.output()

if st.button("🚀 Procesar Todo el Ramal y Diagnosticar"):
    in_caja1_d = val_datos
    in_caja1_v = val_video
    
    if punto_medido != "NAP Directo":
        partes = punto_medido.split(" ")
        idx_origen = int(partes[1]) - 1
        es_pasante = "Pasante" in punto_medido
        
        tipo_propio = estructura_ramal[idx_origen]
        p_aplicada = PERDIDAS[tipo_propio]["pasante"] if es_pasante else PERDIDAS[tipo_propio]["abonado"]
        in_caja1_d += p_aplicada
        in_caja1_v += p_aplicada
        
        for i in range(idx_origen - 1, -1, -1):
            in_caja1_d += PERDIDAS[estructura_ramal[i]]["pasante"]
            in_caja1_v += PERDIDAS[estructura_ramal[i]]["pasante"]

    resultados = []
    curr_d = in_caja1_d
    curr_v = in_caja1_v
    
    st.markdown("### 📊 Estado y Proyección Completa del Ramal")
    st.info(f"**Punto de partida reconstruído en el inicio (NAP):** Datos: {round(in_caja1_d, 2)} dBm | Video: {round(in_caja1_v, 2)} dBm")
    
    for idx, tipo in enumerate(estructura_ramal):
        p_pasante = PERDIDAS[tipo]["pasante"]
        p_abo = PERDIDAS[tipo]["abonado"]
        
        teorico_abo_d = curr_d - p_abo
        teorico_abo_v = curr_v - p_abo
        teorico_pas_d = curr_d - p_pasante if tipo != "Terminal" else None
        teorico_pas_v = curr_v - p_pasante if tipo != "Terminal" else None
        
        resultados.append({
            "Caja": f"Caja {idx+1} ({tipo})",
            "Datos Abonado": round(teorico_abo_d, 2),
            "Video Abonado": round(teorico_abo_v, 2),
            "Pasante Datos": round(teorico_pas_d, 2) if teorico_pas_d is not None else "N/A",
            "Pasante Video": round(teorico_pas_v, 2) if teorico_pas_v is not None else "N/A"
        })
        
        st.markdown(f"#### 📍 Análisis de Caja {idx+1} ({tipo})")
        if teorico_abo_v < -8.0:
            st.markdown(f"<div class='alert-box alert-error'>🔴 **CRÍTICO EN VIDEO:** El nivel óptico de TV es {round(teorico_abo_v,2)} dBm (Menor a -8 dBm). **ONT pixelará.**</div>", unsafe_allow_html=True)
        elif teorico_abo_v < -4.5:
            st.markdown(f"<div class='alert-box alert-warning'>⚠️ **VIDEO BAJO:** Nivel en {round(teorico_abo_v,2)} dBm. Límite de operación operativa.</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='alert-box alert-ok'>🟢 **VIDEO ÓPTIMO:** {round(teorico_abo_v,2)} dBm. Potencia excelente.</div>", unsafe_allow_html=True)
        
        if teorico_pas_d is not None:
            curr_d = teorico_pas_d
            curr_v = teorico_pas_v

    df_final = pd.DataFrame(resultados)
    st.markdown("### 📋 Tabla Resumen de Proyección Teórica")
    st.dataframe(df_final.set_index("Caja"), use_container_width=True)
    
    # --- BOTÓN PARA DESCARGAR EL INFORME EN PDF GENERADO ---
    st.markdown("---")
    st.markdown("### 📥 Guardar Reporte Técnico")
    
    datos_origen_dict = {"datos": in_caja1_d, "video": in_caja1_v}
    pdf_bytes = generar_pdf_informe(datos_origen_dict, df_final, punto_medido, val_datos, val_video)
    
    st.download_button(
        label="📄 Descargar Informe de Diagnóstico (PDF)",
        data=pdf_bytes,
        file_name=f"Informe_Tramo_FTTH_{datetime.now().strftime('%d%m%Y')}.pdf",
        mime="application/pdf"
    )
