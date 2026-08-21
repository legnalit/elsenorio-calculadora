import streamlit as st
from openai import OpenAI
import base64
import re

st.set_page_config(page_title="Calculadora Inteligente de Materiales", page_icon="🏗️", layout="centered")

st.title("🏗️ Calculadora de Materiales con IA")
st.write("Sube una foto de tu reforma, plano o boceto, y nuestra IA calculará los materiales necesarios de nuestro almacén.")

# --- BASE DE DATOS COMPLETA CON PRECIOS 100% LEROY MERLIN ---
PRODUCTOS_ALMACEN = {
    "Tabique de ladrillo": [
        {"nombre": "Saco Cemento Gris Cemex 25kg", "precio": 4.35, "factor": 0.3, "unidad": "sacos"},
        {"nombre": "Ladrillo Perforado 24x11.5x7 cm", "precio": 0.31, "factor": 40.0, "unidad": "unidades"}
    ],
    "Alicatar pared/suelo": [
        {"nombre": "Azulejo Cerámico Blanco Brillo 20x30 (m²)", "precio": 9.99, "factor": 1.1, "unidad": "m²"},
        {"nombre": "Saco Cemento Cola Gris Brico 25kg", "precio": 5.25, "factor": 0.2, "unidad": "sacos"}
    ],
    "Enlucir con yeso": [
        {"nombre": "Saco de Yeso Controlado Longips 17kg", "precio": 1.52, "factor": 0.5, "unidad": "sacos"}
    ],
    "Tabique de pladur": [
        {"nombre": "Placa de Cartón-yeso Placo 13mm (m²)", "precio": 2.82, "factor": 2.0, "unidad": "m²"},
        {"nombre": "Perfil Montante Metálico 48mm 3m", "precio": 3.45, "factor": 0.9, "unidad": "unidades"},
        {"nombre": "Pasta para Juntas Placo 5kg", "precio": 11.20, "factor": 0.1, "unidad": "botes"}
    ],
    "Solera de hormigón con mallazo": [
        {"nombre": "Hormigón Seco H-25 PRO Cemex 25kg", "precio": 2.99, "factor": 4.0, "unidad": "sacos"},
        {"nombre": "Mallazo de acero Electrosoldado 2x1m", "precio": 8.95, "factor": 0.5, "unidad": "paneles"}
    ],
    "Tabique de rasillón 40x20x7": [
        {"nombre": "Rasillón perforado Ceranor 40x20x7cm", "precio": 0.66, "factor": 11.6, "unidad": "unidades"},
        {"nombre": "Mortero Seco Gris Molins M-7.5 25kg", "precio": 2.78, "factor": 0.6, "unidad": "sacos"}
    ],
    "Pintura de paredes": [
        {"nombre": "Pintura de interior Luxens Blanco Mate 15L", "precio": 24.29, "factor": 0.02, "unidad": "botes"},
        {"nombre": "Imprimación fijadora de paredes 5L", "precio": 14.50, "factor": 0.04, "unidad": "botes"}
    ]
}

st.sidebar.header("⚙️ Configuración")
api_key = st.sidebar.text_input("Introduce tu OpenAI API Key", type="password")

opciones_menu = ["Selecciona una opción"] + list(PRODUCTOS_ALMACEN.keys())
opcion_obra = st.selectbox("¿Qué tipo de obra vas a realizar?", opciones_menu)
foto = st.file_uploader("Sube la foto del espacio, plano o boceto manual (JPG/PNG)", type=["jpg", "jpeg", "png"])

if st.button("Calcular Presupuesto Automático"):
    if not api_key:
        st.error("Por favor, introduce tu OpenAI API Key en la barra lateral izquierda.")
    elif opcion_obra == "Selecciona una opción":
        st.error("Por favor, selecciona qué tipo de obra vas a realizar.")
    elif foto is None:
        st.error("Por favor, sube una imagen o plano.")
    else:
        with st.spinner("🧠 La IA está analizando visualmente tu imagen..."):
            try:
                client = OpenAI(api_key=api_key)
                
                ext = foto.name.split('.')[-1].lower()
                tipo_meco = "image/jpeg" if ext not in ['png', 'jpg', 'jpeg', 'webp'] else f"image/{ext}"
                if ext == "jpg": tipo_meco = "image/jpeg"
                
                base64_img = base64.b64encode(foto.read()).decode('utf-8')
                
                prompt_ia = (
                    f"Analiza esta imagen para la tarea: '{opcion_obra}'. "
                    "Estima los metros cuadrados de superficie afectados. "
                    "Responde únicamente con este formato de dos líneas:\n"
                    "METROS: [escribe solo el número, ej: 14.2]\n"
                    "EXPLICACION: [escribe una frase breve]"
                )
                
                # LLAMADA ULTRAESTABLE: Se extrae la propiedad de texto como pide la nueva versión
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt_ia},
                                {"type": "image_url", "image_url": {"url": f"data:{tipo_meco};base64,{base64_img}"}}
                            ],
                        }
                    ],
                    max_tokens=250
                )
                
                respuesta_texto = response.choices[0].message.content
                
                m2 = 10.0
                explicacion = "Cálculo estimado por proporciones visuales de la obra."
                
                match_m = re.search(r"METROS:\s*([\d.]+)", respuesta_texto, re.IGNORECASE)
                match_e = re.search(r"EXPLICACION:\s*(.*)", respuesta_texto, re.IGNORECASE)
                
                if match_m: m2 = float(match_m.group(1))
                if match_e: explicacion = match_e.group(1).strip()
                
                st.success("✨ ¡Análisis visual completado con éxito!")
                st.info(f"**Criterio de la IA:** {explicacion}")
                st.metric(label="Superficie Estimada Detectada", value=f"{m2} m²")
                
                st.subheader("📋 Tu Carrito de Materiales en Almacén")
                materiales_seleccionados = PRODUCTOS_ALMACEN[opcion_obra]
                total_pedido = 0.0
                
                for prod in materiales_seleccionados:
                    unidad_medida = prod.get("unidad", "sacos")
                    cantidad = round(m2 * prod["factor"], 1) if unidad_medida in ["m²", "botes"] else round(m2 * prod["factor"])
                    if cantidad == 0: cantidad = 1
                    subtotal = cantidad * prod["precio"]
                    total_pedido += subtotal
                    
                    st.write(f"• **{cantidad} {unidad_medida}** de _{prod['nombre']}_ — **{subtotal:.2f}€**")
                
                st.markdown(f"### 💰 **Total Presupuesto: {total_pedido:.2f}€**")
                st.markdown("---")
                st.info("💡 Haz una captura de pantalla de este presupuesto y envíanosla por WhatsApp al 626 401 461 para prepararte el material.")
                
            except Exception as e:
                st.error(f"Hubo un error al procesar los datos: {e}")
