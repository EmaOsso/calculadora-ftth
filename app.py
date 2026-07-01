import streamlit as st
import pandas as pd

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
st.write("Diagnóstico bidireccional automático con detección de fallas en mangueras drop y troncales.")

# --- PARÁMETROS TÉCNICOS IDEALES (Simulación) ---
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

# Armamos la lista de opciones para que el usuario elija DÓNDE midió
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

if st.button("🚀 Procesar Todo el Ramal y Diagnosticar"):
    
    # --- PASO 1: Calcular la Entrada Absoluta de la Caja 1 (o NAP) ---
    # Reconstruimos hacia atrás para saber el origen exacto
    in_caja1_d = val_datos
    in_caja1_v = val_video
    
    if punto_medido != "NAP Directo":
        # Extraer el índice de caja desde el texto seleccionado
        partes = punto_medido.split(" ")
        idx_origen = int(partes[1]) - 1
        es_pasante = "Pasante" in punto_medido
        
        # Primero sumamos la pérdida de la misma caja donde se midió
        tipo_propio = estructura_ramal[idx_origen]
        p_aplicada = PERDIDAS[tipo_propio]["pasante"] if es_pasante else PERDIDAS[tipo_propio]["abonado"]
        in_caja1_d += p_aplicada
        in_caja1_v += p_aplicada
        
        # Luego sumamos los pasantes de todas las cajas previas
        for i in range(idx_origen - 1, -1, -1):
            in_caja1_d += PERDIDAS[estructura_ramal[i]]["pasante"]
            in_caja1_v += PERDIDAS[estructura_ramal[i]]["pasante"]

    # --- PASO 2: Calcular toda la cascada Aguas Abajo desde el Origen Calculado ---
    resultados = []
    curr_d = in_caja1_d
    curr_v = in_caja1_v
    
    st.markdown("### 📊 Estado y Proyección Completa del Ramal")
    
    # Imprimimos el valor calculado en el Origen
    st.info(f"**Punto de partida reconstruído en el inicio del tramo (NAP):** Datos: {round(in_caja1_d, 2)} dBm | Video: {round(in_caja1_v, 2)} dBm")
    
    for idx, tipo in enumerate(estructura_ramal):
        p_pasante = PERDIDAS[tipo]["pasante"]
        p_abo = PERDIDAS[tipo]["abonado"]
        
        # Teóricos calculados
        teorico_abo_d = curr_d - p_abo
        teorico_abo_v = curr_v - p_abo
        teorico_pas_d = curr_d - p_pasante if tipo != "Terminal" else None
        teorico_pas_v = curr_v - p_pasante if tipo != "Terminal" else None
        
        # Guardamos datos para la tabla
        resultados.append({
            "Caja": f"Caja {idx+1} ({tipo})",
            "Datos Abonado": round(teorico_abo_d, 2),
            "Video Abonado": round(teorico_abo_v, 2),
            "Pasante Datos": round(teorico_pas_d, 2) if teorico_pas_d is not None else "N/A",
            "Pasante Video": round(teorico_pas_v, 2) if teorico_pas_v is not None else "N/A"
        })
        
        # Bloque de Diagnóstico Visual en vivo por cada Caja
        st.markdown(f"#### 📍 Análisis de Caja {idx+1} ({tipo})")
        
        # Validación de alertas críticas de video
        if teorico_abo_v < -8.0:
            st.markdown(f"<div class='alert-box alert-error'>🔴 **CRÍTICO EN VIDEO:** El nivel óptico para TV en abonados es de {round(teorico_abo_v,2)} dBm. Está por debajo de -8 dBm. **Resultado:** La ONT va a pixelar fuerte o dará Sin Señal.</div>", unsafe_allow_html=True)
        elif teorico_abo_v < -4.5:
            st.markdown(f"<div class='alert-box alert-warning'>⚠️ **VIDEO BAJO:** Nivel en {round(teorico_abo_v,2)} dBm. Está en el límite de operación, cualquier conector sucio matará la TV.</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='alert-box alert-ok'>🟢 **VIDEO ÓPTIMO:** {round(teorico_abo_v,2)} dBm. Potencia excelente para video RF Overlay.</div>", unsafe_allow_html=True)

        # Si el usuario ingresó un valor real para esta caja, comparamos desvíos
        if punto_medido != "NAP Directo":
            partes = punto_medido.split(" ")
            idx_M = int(partes[1]) - 1
            
            # Si estamos parados analizando la caja donde el usuario detectó problemas reales en su red anterior:
            if idx == idx_M and val_datos < -22.0 and tipo == "70/30":
                st.markdown("<div class='alert-box alert-error'>🚨 **DIAGNÓSTICO AUTOMÁTICO:** Se detecta una caída anormal en el Ramal. Si tus valores reales medidos no coinciden con esta tabla, tenés **Valor Pasante Mal (Suciedad Crítica o Fusión con Atenuación)** entre la NAP y esta caja. Revisar acopladores hembra.</div>", unsafe_allow_html=True)
        
        # Siguiente iteración
        if teorico_pas_d is not None:
            curr_d = teorico_pas_d
            curr_v = teorico_pas_v

    # Mostrar la tabla final unificada
    df = pd.DataFrame(resultados)
    st.markdown("### 📋 Tabla Resumen de Proyección Teórica")
    st.dataframe(df.set_index("Caja"), use_container_width=True)
