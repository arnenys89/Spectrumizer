# Home Assistant – Sensor Doubler

Een kleine custom integration voor Home Assistant. Ze leest de toestand van een bestaande numerieke sensor, vermenigvuldigt die standaard met **2** en publiceert het resultaat als een afzonderlijke sensor. De bron-sensor wordt niet aangepast.

## Functies

- Configuratie via **Instellingen → Apparaten & diensten → Integratie toevoegen → Sensor Doubler**.
- Kies een bestaande sensor als bron.
- Geef de nieuwe sensor een naam.
- Standaardfactor `2`, desgewenst aanpasbaar.
- Reageert op wijzigingen van de bron-sensor.
- Behoudt de eenheid van de bron-sensor indien opgegeven.
- Geeft geen numerieke waarde terug als de bron niet beschikbaar is of geen numerieke toestand heeft.
- Geen externe service, API-sleutel, Cloudflare Worker of extra Python-dependency nodig.

## Installatie

1. Plaats de map `custom_components/sensor_doubler` in de map `config/custom_components/` van Home Assistant.
2. Herstart Home Assistant.
3. Ga naar **Instellingen → Apparaten & diensten → Integratie toevoegen**.
4. Zoek naar **Sensor Doubler**, selecteer de bron-sensor, geef een naam en laat de factor op `2` staan.

Voor HACS: voeg deze GitHub-repository toe als een **Integration**-repository en installeer vervolgens de integratie. Herstart Home Assistant daarna.

## Voorbeeld

Bron: `sensor.solar_power` met waarde `125.5 W`  
Nieuwe sensor: `sensor.doubled_sensor` met waarde `251.0 W`

De naam en entity-id die Home Assistant uiteindelijk toekent kunnen verschillen op basis van je ingestelde naam en bestaande entiteiten.

## Ontwikkeling

De integratie is opgezet als standalone custom component. Cloudflare is niet nodig voor de sensorberekening. Zie `custom_components/sensor_doubler/` voor de volledige implementatie.
