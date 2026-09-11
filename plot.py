import os
import sys

import openmeteo_requests
import pandas as pd
import requests_cache
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from retry_requests import retry

# Paden in shared memory (/dev/shm)
FINAL_OUTPUT = "/dev/shm/meteo.png"
TEMP_OUTPUT = "/dev/shm/meteo.tmp.png"

# 1. Client setup met cache
cache_session = requests_cache.CachedSession('.cache', expire_after = 3600)
retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
openmeteo = openmeteo_requests.Client(session = retry_session)

# De opgeschoonde basis-URL
url = "https://api.open-meteo.com/v1/forecast"

# Parameters configureren (4 dagen om altijd het sliding window te kunnen vullen)
params = {
        "latitude": 51.155952,
        "longitude": 4.431894,
        "hourly": ["temperature_2m", "rain"],
        "timezone": "Europe/Brussels",
        "forecast_days": 4, 
}
responses = openmeteo.weather_api(url, params = params)
response = responses[0]

# 2. Data verwerken
hourly = response.Hourly()
hourly_temperature_2m = hourly.Variables(0).ValuesAsNumpy()
hourly_rain = hourly.Variables(1).ValuesAsNumpy()

tz_string = response.Timezone().decode()

hourly_data = {
	"date": pd.date_range(
		start = pd.to_datetime(hourly.Time(), unit = "s", utc = True),
		end =  pd.to_datetime(hourly.TimeEnd(), unit = "s", utc = True),
		freq = pd.Timedelta(seconds = hourly.Interval()),
		inclusive = "left"
	).tz_convert(tz_string)
}

hourly_data["temperature_2m"] = hourly_temperature_2m
hourly_data["rain"] = hourly_rain

hourly_dataframe = pd.DataFrame(data = hourly_data)
hourly_dataframe.set_index("date", inplace=True)

# Strip de tijdzone-informatie om UTC-misalignments te voorkomen
hourly_dataframe.index = hourly_dataframe.index.tz_localize(None)

# ========================================================
# SLIDING WINDOW (1 UUR VROEGER GESTART)
# ========================================================

# Huidig uur bepalen en de starttijd 1 uur naar het verleden verschuiven
echte_nu = pd.Timestamp.now().floor('h')
start_window = echte_nu - pd.Timedelta(hours=1)  # Begint 1 uur vroeger
eind_window = echte_nu + pd.Timedelta(days=3)

# Filter de dataframe voor dit aangepaste venster
df_window = hourly_dataframe[(hourly_dataframe.index >= start_window) & (hourly_dataframe.index < eind_window)].copy()

# Grafiek initialiseren
fig, ax1 = plt.subplots(figsize=(14, 6))

# 1. VERTICALE LIJNEN OM MIDDERNACHT (Gecentreerd op 00:00)
middernacht_tijdstippen = df_window[df_window.index.hour == 0].index
for middernacht in middernacht_tijdstippen:
    if start_window < middernacht < eind_window:
        ax1.axvline(middernacht, color='white', linestyle='-', linewidth=2, alpha=0.7, zorder=1)

# Een subtiele rode stippellijn die de ECHTE huidige tijd markeert
if start_window < echte_nu < eind_window:
    ax1.axvline(echte_nu, color='yellow', linestyle=':', linewidth=1.5, alpha=0.9, zorder=4)

# 2. Temperatuur plotten (Rode lijn met kleine stipjes)
ax1.set_ylabel("Temperatuur (°C)", color="crimson", fontsize=12, fontweight="bold")
ax1.plot(df_window.index, df_window["temperature_2m"], 
         color="crimson", linewidth=1.7, marker='o', markersize=4, zorder=3)
ax1.tick_params(axis="y", labelcolor="crimson")
ax1.grid(True, linestyle=":", alpha=0.5, color='white', zorder=1)

# Schaal de Y-as netjes rondom de werkelijke temperaturen
ymin, ymax = df_window["temperature_2m"].min() - 2, df_window["temperature_2m"].max() + 2
ax1.set_ylim(ymin, ymax)

# 3. Regen plotten (Blauwe balken)
ax2 = ax1.twinx()
ax2.set_ylabel("Regen (mm)", color="dodgerblue", fontsize=11, fontweight="bold")
ax2.bar(df_window.index, df_window["rain"], 
        color="dodgerblue", alpha=0.6, width=0.03, zorder=2)
ax2.tick_params(axis="y", labelcolor="dodgerblue")
ax2.set_ylim(bottom=0)

# 4. X-as Formattering (Sluit perfect aan op de nieuwe starttijd)
ax1.set_xlim(start_window, eind_window)
ax1.xaxis.set_major_locator(mdates.HourLocator(byhour=[0, 6, 12, 18]))
ax1.xaxis.set_major_formatter(mdates.DateFormatter('%a %d %b\n%H:%M'))

# 5. RANDEN EN LABELS NAAR WIT OMZETTEN
ax1.tick_params(axis='x', colors='white', labelsize=10)

for spine in ax1.spines.values():
    spine.set_color('white')

for spine in ax2.spines.values():
    spine.set_color('white')

# LEGENDA VERWIJDERD

#plt.title("3-Daagse Schuivende Weersverwachting (Regio Antwerpen)", fontsize=14, fontweight='bold', pad=15)
fig.tight_layout()

# Toon de grafiek
#plt.show()


# 5. Sla eerst op als tijdelijk bestand en vervang daarna atomair
try:
     # Schrijf naar de .tmp.png file in shared memory
     plt.savefig(TEMP_OUTPUT, dpi=150, transparent=True)
     plt.close()

     # Atomaire verplaatsing/herbenoeming binnen /dev/shm
     os.replace(TEMP_OUTPUT, FINAL_OUTPUT)
     print(f"OpenMeteo Grafiek 3 dagen succesvol atomair bijgewerkt in {FINAL_OUTPUT}")
except Exception as e:
     print(f"Fout bij wegschrijven van grafiek: {e}")




