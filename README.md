# OpenMeteo Weather Plotter

Een Python script dat automatisch actuele weerdata ophaalt via de **Open-Meteo API** en een strakke, transparante 3-daagse weergrafiek genereert. De grafiek toont het temperatuurverloop en de verwachte regenval binnen een rollend tijdsvenster (*sliding window*).

Het script is ontworpen om efficiënt en veilig op de achtergrond te draaien (bijvoorbeeld via een cronjob), dankzij het gebruik van caching en een **atomaire bestandsoverdracht** in shared memory (`/dev/shm`).

## 🚀 Kenmerken
* **Sliding Window:** Toont een weersverwachting voor de komende 3 dagen, beginnend vanaf exact 1 uur in het verleden om recente context te behouden.
* **Dubbele Y-as:** Temperatuur (°C) als een rode lijnplot en regenval (mm) als blauwe staafdiagrammen gecombineerd in één overzicht.
* **Geoptimaliseerd voor Dashboards:** De grafiek wordt opgeslagen met een transparante achtergrond en witte assen, ideaal voor integratie in (donkere) smart home dashboards of displays.
* **Robuust & Efficiënt:** 
  * Maakt gebruik van een lokale cache (`.cache.sqlite`) om de API-limieten te respecteren.
  * Automatische retries met een backoff-factor bij netwerkfouten.
  * Slaat de grafiek eerst tijdelijk op (`.tmp.png`) en vervangt het doelbestand daarna atomair om leesfouten door andere processen te voorkomen.

## 🛠️ Vereisten

Zorg ervoor dat je de benodigde Python packages hebt geïnstalleerd:

```bash
pip install openmeteo-requests pandas requests-cache matplotlib retry-requests
```

## 📋 Installatie & Gebruik

1. **Kloon of navigeer naar je repository:**
   ```bash
   cd ~/git/openMeteo
   ```

2. **Voer het script uit:**
   ```bash
   python plot.py
   ```

3. **Bekijk de output:**
   Het script genereert en vernieuwt de grafiek live in het shared memory van Linux:
   * Tijdelijk bestand: `/dev/shm/meteo.tmp.png`
   * Definitieve grafiek: `/dev/shm/meteo.png`

## ⏱️ Automatisering met Crontab

Omdat het script gebruikmaakt van een *sliding window*, is het ideaal om de grafiek elk uur automatisch te verversen via een cronjob.

1. Open de crontab-editor van je gebruiker:
   ```bash
   crontab -e
   ```

2. Voeg de volgende regel toe onderaan het bestand om het script **elk uur (op de 5e minuut)** uit te voeren:
   ```text
   5 * * * * /usr/bin/python3 /home/jan/git/openMeteo/plot.py >> /home/jan/git/openMeteo/cron.log 2>&1
   ```
   *(Let op: Controleer met `which python3` of jouw Python-pad inderdaad `/usr/bin/python3` is, en pas dit indien nodig aan).*

## ⚙️ Configuratie

De locatiecoördinaten in het script staan momenteel ingesteld op de **regio Antwerpen** (Latitude: `51.155952`, Longitude: `4.431894`). Je kunt deze parameters direct in `plot.py` aanpassen naar jouw eigen locatie:

```python
params = {
        "latitude": 51.155952,
        "longitude": 4.431894,
        "hourly": ["temperature_2m", "rain"],
        "timezone": "Europe/Brussels",
        "forecast_days": 4, 
}
```

## 🔒 Git Opmerking
De lokale API-cache wordt opgeslagen in `.cache.sqlite`. Dit bestand is toegevoegd aan de `.gitignore` om te voorkomen dat er onnodige runtime-data naar GitHub gepusht wordt.

