import discord
import os
import psutil
import time
import requests
from dotenv import load_dotenv
from deep_translator import GoogleTranslator
 
load_dotenv()
 
start_time = time.time()
 
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
 
# =========================
# HELPERS CLIMA
# =========================
 
WMO_CODES = {
    0:  ("☀️",  "Despejado"),
    1:  ("🌤️", "Mayormente despejado"),
    2:  ("⛅",  "Parcialmente nublado"),
    3:  ("☁️",  "Nublado"),
    45: ("🌫️", "Niebla"),
    48: ("🌫️", "Niebla con escarcha"),
    51: ("🌦️", "Llovizna ligera"),
    53: ("🌦️", "Llovizna moderada"),
    55: ("🌧️", "Llovizna intensa"),
    61: ("🌧️", "Lluvia ligera"),
    63: ("🌧️", "Lluvia moderada"),
    65: ("🌧️", "Lluvia intensa"),
    71: ("🌨️", "Nevada ligera"),
    73: ("🌨️", "Nevada moderada"),
    75: ("❄️",  "Nevada intensa"),
    77: ("🌨️", "Granizo fino"),
    80: ("🌦️", "Chubascos ligeros"),
    81: ("🌧️", "Chubascos moderados"),
    82: ("⛈️",  "Chubascos intensos"),
    85: ("🌨️", "Chubascos de nieve"),
    86: ("❄️",  "Chubascos de nieve intensos"),
    95: ("⛈️",  "Tormenta eléctrica"),
    96: ("⛈️",  "Tormenta con granizo"),
    99: ("⛈️",  "Tormenta con granizo intenso"),
}
 
def describir_viento(kmh):
    if kmh < 1:   return "Calma"
    elif kmh < 6:  return "Ventolina"
    elif kmh < 20: return "Brisa ligera"
    elif kmh < 40: return "Brisa moderada"
    elif kmh < 62: return "Viento fuerte"
    elif kmh < 75: return "Temporal"
    else:          return "Huracán"
 
def direccion_viento(grados):
    puntos = ["N", "NE", "E", "SE", "S", "SO", "O", "NO"]
    return puntos[round(grados / 45) % 8]
 
def uv_descripcion(uv):
    if uv <= 2:  return "Bajo"
    elif uv <= 5: return "Moderado"
    elif uv <= 7: return "Alto"
    elif uv <= 10: return "Muy alto"
    else:          return "Extremo"
 
def formato_clima(nombre, pais, current, daily):
    codigo = current.get("weather_code", 0)
    emoji, estado = WMO_CODES.get(codigo, ("🌡️", "Desconocido"))
 
    temp        = current["temperature_2m"]
    sensacion   = current["apparent_temperature"]
    humedad     = current["relative_humidity_2m"]
    viento_kmh  = current["wind_speed_10m"]
    racha       = current["wind_gusts_10m"]
    dir_grados  = current["wind_direction_10m"]
    lluvia      = current["precipitation"]
    presion     = current["surface_pressure"]
    visib       = current.get("visibility")
    uv          = current.get("uv_index")
    nubosidad   = current.get("cloud_cover")
    punto_rocio = current.get("dew_point_2m")
 
    dir_texto   = direccion_viento(dir_grados)
    viento_desc = describir_viento(viento_kmh)
 
    temp_max  = daily["temperature_2m_max"][0]
    temp_min  = daily["temperature_2m_min"][0]
    lluvia_d  = daily["precipitation_sum"][0]
    sol_seg   = daily.get("sunshine_duration", [None])[0]
    sol_horas = round(sol_seg / 3600, 1) if sol_seg is not None else None
 
    lineas = [
        f"**🌍 {nombre}**",
        f"{emoji} **{estado}**",
        "",
        f"🌡️ **Temperatura:** {temp}°C  (sensación {sensacion}°C)",
        f"🔺 Máx: {temp_max}°C  🔻 Mín: {temp_min}°C",
        "",
        f"💧 **Humedad:** {humedad}%",
    ]
    if punto_rocio is not None:
        lineas.append(f"🌫️ **Punto de rocío:** {punto_rocio}°C")
    lineas += [
        "",
        f"💨 **Viento:** {viento_kmh} km/h ({dir_texto}) — {viento_desc}",
        f"🌬️ **Racha máx:** {racha} km/h",
        "",
        f"🌧️ **Precipitación actual:** {lluvia} mm",
        f"🗓️ **Precipitación hoy:** {lluvia_d} mm",
        "",
        f"🔵 **Presión:** {round(presion)} hPa",
    ]
    if nubosidad is not None:
        lineas.append(f"☁️ **Nubosidad:** {nubosidad}%")
    if visib is not None:
        lineas.append(f"👁️ **Visibilidad:** {round(visib / 1000, 1)} km")
    if uv is not None:
        lineas.append(f"🔆 **Índice UV:** {uv} ({uv_descripcion(uv)})")
    if sol_horas is not None:
        lineas.append(f"🌞 **Horas de sol hoy:** {sol_horas} h")
 
    return "\n".join(lineas)
 
# =========================
# BOT LISTO
# =========================
@client.event
async def on_ready():
    print(f'Bot conectado como {client.user}')
 
# =========================
# MENSAJES
# =========================
@client.event
async def on_message(message):
    if message.author.bot:
        return
 
    # BOT STATS
    if message.content.startswith('!botstats'):
        uptime_seconds = int(time.time() - start_time)
        h = uptime_seconds // 3600
        m = (uptime_seconds % 3600) // 60
        s = uptime_seconds % 60
        cpu = psutil.cpu_percent(interval=1)
        ram = psutil.virtual_memory()
        load_text = f"📈 Load: {round(os.getloadavg()[0], 2)} (1m)" if hasattr(os, "getloadavg") else "📈 Load: no disponible"
        await message.channel.send(
            f"📊 **Estado del bot:**\n"
            f"⏱️ Uptime: {h}h {m}m {s}s\n"
            f"🧠 CPU: {cpu}%\n"
            f"💾 RAM: {ram.percent}% ({round(ram.used / (1024**3), 2)} GB)\n"
            f"{load_text}"
        )
        return
 
    # TRADUCCIÓN
    if message.content.startswith('!t '):
        args = message.content.split(' ')
        if len(args) < 3:
            await message.channel.send("Uso: `!t <idioma> <texto>`")
            return
        idioma = args[1]
        texto  = ' '.join(args[2:])
        try:
            traduccion = GoogleTranslator(source='auto', target=idioma).translate(texto)
            await message.channel.send(f"🌐 ({idioma}) {traduccion}")
        except Exception as e:
            print(e)
            await message.channel.send("⚠️ Error al traducir")
        return
 
    # CLIMA
    if message.content.startswith('!clima'):
        ciudad = ' '.join(message.content.split(' ')[1:]).strip()
        if not ciudad:
            await message.channel.send("Uso: `!clima <ciudad>` o `!clima <ciudad>, <país>`")
            return
        try:
            # Separar ciudad y país si el usuario escribe "!clima Toledo, España"
            if ',' in ciudad:
                partes = ciudad.split(',', 1)
                nombre_busqueda = partes[0].strip()
                filtro_pais = partes[1].strip().lower()
            else:
                nombre_busqueda = ciudad
                filtro_pais = None
 
            geo_res = requests.get(
                f"https://geocoding-api.open-meteo.com/v1/search?name={nombre_busqueda}&count=10",
                timeout=10
            ).json()
 
            if "results" not in geo_res or not geo_res["results"]:
                await message.channel.send("❌ Ciudad no encontrada.")
                return
 
            resultados = geo_res["results"]
 
            # Filtrar por país si el usuario lo especificó
            if filtro_pais:
                filtrados = [
                    r for r in resultados
                    if filtro_pais in r.get("country", "").lower()
                    or filtro_pais in r.get("country_code", "").lower()
                ]
                if filtrados:
                    resultados = filtrados
 
            # Ver si hay varias ciudades con el mismo nombre en distintos países
            paises_distintos = list({r["country"] for r in resultados})
 
            if len(paises_distintos) > 1 and not filtro_pais:
                # Mostrar opciones al usuario
                opciones = "\n".join([
                    f"**{i+1}.** {r['name']}, {r.get('admin1', '')} — {r['country']}"
                    for i, r in enumerate(resultados[:5])
                ])
                await message.channel.send(
                    f"⚠️ Hay varias ciudades llamadas **{nombre_busqueda}**. "
                    f"Sé más específico usando:\n`!clima {nombre_busqueda}, <país>`\n\n"
                    f"Resultados encontrados:\n{opciones}"
                )
                return
 
            # Tomar el primer resultado
            r = resultados[0]
            lat, lon, nombre, pais = r["latitude"], r["longitude"], r["name"], r["country"]
            region = r.get("admin1", "")
 
            w = requests.get(
                f"https://api.open-meteo.com/v1/forecast?"
                f"latitude={lat}&longitude={lon}"
                f"&current=temperature_2m,apparent_temperature,relative_humidity_2m,"
                f"dew_point_2m,precipitation,weather_code,surface_pressure,"
                f"wind_speed_10m,wind_direction_10m,wind_gusts_10m,"
                f"cloud_cover,visibility,uv_index"
                f"&daily=temperature_2m_max,temperature_2m_min,"
                f"precipitation_sum,sunshine_duration"
                f"&timezone=auto",
                timeout=10
            ).json()
 
            # Incluir región si hay ambigüedad dentro del mismo país
            nombre_completo = f"{nombre}, {region}, {pais}" if region else f"{nombre}, {pais}"
            await message.channel.send(formato_clima(nombre_completo, "", w["current"], w["daily"]))
        except Exception as e:
            print(e)
            await message.channel.send("⚠️ Error obteniendo el clima.")
        return
 
client.run(os.getenv("TOKEN"))