import streamlit as st
import pandas as pd

# Configuración de la página estilo MikroTik (Limpio, tipografía sans-serif, ancho optimizado)
st.set_page_config(page_title="OBRA TEK - Calculadora FTTH", layout="centered")

# Estilos CSS para emular la tipografía y colores limpios de la web de MikroTik
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
    </style>
""", unsafe_allow_html=True)

st.markdown("<h2 class='main-title'>⚙️ OBRA TEK — Calculadora FTTH Preconectorizada</h2>", unsafe_allow_html=True)
st.write("Herramienta de diagnóstico para cálculo de presupuesto óptico (Datos 1490nm / Video 1550nm).")

# --- PARÁMETROS TÉCNICOS (Basados en tu simulación real) ---
PERDIDAS = {
    "70/30": {"pasante": 1.90, "abonado": 15.15},
    "50/50": {"pasante": 3.50, "abonado": 12.50},
    "Terminal": {"pasante": 999, "abonado": 9.50}  # No tiene pasante
}

# --- CONFIGURACIÓN DEL RAMAL ---
st.sidebar.header("Configuración del Ramal")
modo = st.sidebar.radio("Dirección del Cálculo:", ["Aguas Abajo (Hacia adelante)", "Aguas Arriba (A la inversa)"])

# Estructura fija o dinámica del ramal
cantidad_cajas = st.sidebar.slider("Cantidad de cajas en el ramal:", 1, 6, 4)
estructura_ramal = []
for i in range(cantidad_cajas):
    if i == cantidad_cajas - 1:
        tipo = st.sidebar.selectbox(f"Tipo Caja {i+1} (Final):", ["Terminal", "70/30", "50/50"], index=0)
    else:
        tipo = st.sidebar.selectbox(f"Tipo Caja {i+1}:", ["70/30", "50/50", "Terminal"], index=0)
    estructura_ramal.append(tipo)

# --- MODO AGUAS ABAJO ---
if modo == "Aguas Abajo (Hacia adelante)":
    st.subheader("📥 Entrada: Valores en la NAP Directo")
    
    col1, col2 = st.columns(2)
    with col1:
        nap_datos = st.number_input("Datos 1490nm (dBm):", value=-1.50, step=0.1)
    with col2:
        nap_video = st.number_input("Video 1550nm (dBm):", value=15.22, step=0.1)
        
    if st.button("Calcular Ramal"):
        resultados = []
        curr_d = nap_datos
        curr_v = nap_video
        
        for idx, tipo in enumerate(estructura_ramal):
            p_pasante = PERDIDAS[tipo]["pasante"]
            p_abo = PERDIDAS[tipo]["abonado"]
            
            # Cálculo local de la caja activa
            abo_d = curr_d - p_abo
            abo_v = curr_v - p_abo
            
            # Valores que quedan en el pasante saliente de esta caja
            pas_d = curr_d - p_pasante if tipo != "Terminal" else None
            pas_v = curr_v - p_pasante if tipo != "Terminal" else None
            
            resultados.append({
                "Caja": f"Caja {idx+1} ({tipo})",
                "Datos Abonado (dBm)": round(abo_d, 2),
                "Video Abonado (dBm)": round(abo_v, 2),
                "Pasante Datos (dBm)": round(pas_d, 2) if pas_d is not None else "N/A",
                "Pasante Video (dBm)": round(pas_v, 2) if pas_v is not None else "N/A"
            })
            
            # La señal entrante de la siguiente caja es el pasante actual
            if pas_d is not None:
                curr_d = pas_d
                curr_v = pas_v
                
        df = pd.DataFrame(resultados)
        st.markdown("### 📊 Proyección Teórica del Ramal")
        st.dataframe(df.set_index("Caja"), use_container_width=True)

# --- MODO AGUAS ARRIBA ---
else:
    st.subheader("📤 Entrada: Medición Inversa desde el Problema")
    
    caja_medida = st.selectbox("¿En qué caja mediste?", [f"Caja {i+1}" for i in range(cantidad_cajas)])
    idx_medida = int(caja_medida.split(" ")[1]) - 1
    tipo_medida = estructura_ramal[idx_medida]
    
    col1, col2 = st.columns(2)
    with col1:
        val_datos = st.number_input(f"Datos medidos en ABONADO de la {caja_medida} (dBm):", value=-24.30, step=0.1)
    with col2:
        val_video = st.number_input(f"Video medido en ABONADO de la {caja_medida} (dBm):", value=-8.13, step=0.1)
        
    if st.button("Calcular Origen Requerido"):
        # Calculamos primero el valor que debió entrar a esa caja específica
        p_abo_destino = PERDIDAS[tipo_medida]["abonado"]
        in_caja_d = val_datos + p_abo_destino
        in_caja_v = val_video + p_abo_destino
        
        # Viajamos hacia atrás en el ramal sumando las pérdidas de los pasantes anteriores
        curr_d = in_caja_d
        curr_v = in_caja_v
        
        for i in range(idx_medida - 1, -1, -1):
            tipo_anterior = estructura_ramal[i]
            curr_d += PERDIDAS[tipo_anterior]["pasante"]
            curr_v += PERDIDAS[tipo_anterior]["pasante"]
            
        st.markdown("### 🔍 Resultado del Diagnóstico")
        st.write(f"Para que la **{caja_medida}** reciba lo que mediste, la señal en la **NAP directo** debería haber sido:")
        
        st.metric(label="Datos 1490nm Requeridos en NAP", value=f"{round(curr_d, 2)} dBm")
        st.metric(label="Video 1550nm Requerido en NAP", value=f"{round(curr_v, 2)} dBm")
        
        st.info("💡 Consejo de cuadrilla: Si tus valores requeridos son mucho más altos que los que medís en directo en la NAP (ej: te pide -1.5 pero tenés -6.7), la diferencia es exactamente la atenuación extra por suciedad o estrangulamiento que tenés acumulada aguas arriba.")
