# Spectrumizer — live FFT voor Home Assistant

Spectrumizer bemonstert een numerieke Home Assistant-sensor aan een ingestelde frequentie, past een Hann-venster toe en berekent een Fast Fourier Transform (FFT). De sensorwaarde is de dominante niet-nulfrequentie in Hz. De volledige frequentiebins en amplitudes worden als attributen aangeboden voor de live Lovelace-grafiek.

## Integratie

- Selecteer een bestaande numerieke sensor.
- Instelbare samplefrequentie: 0,1–100 samples/s.
- FFT-venster: 32, 64, 128, 256, 512 of 1024 samples.
- Sensorwaarde: dominante frequentie in Hz.
- Attributen: `frequencies`, `magnitudes`, `peak_magnitude`, `sampling_rate_hz`, `frequency_resolution_hz`, `samples_collected` en `ready`.
- De oorspronkelijke sensor blijft ongewijzigd.

**Belangrijk:** FFT-resultaten zijn alleen betrouwbaar als de bronsensor voldoende snel verandert en regelmatig kan worden bemonsterd. De maximale meetbare frequentie is de Nyquist-frequentie: de helft van de samplefrequentie. Als de bron maar één keer per seconde verandert, kan een ingestelde samplefrequentie van 10 Hz geen nieuwe informatie creëren.

## Installatie van de integratie

1. Kopieer `custom_components/spectrumizer` naar `config/custom_components/spectrumizer`.
2. Herstart Home Assistant.
3. Ga naar **Instellingen → Apparaten & diensten → Integratie toevoegen**.
4. Kies **Spectrumizer** en selecteer de bron-sensor.
5. Stel samplefrequentie en venstergrootte in.

De frequentieresolutie is `samplefrequentie / venstergrootte`. Bij 10 Hz en 256 samples is dat ongeveer 0,0391 Hz.

## Live spectrumkaart installeren

1. Kopieer `www/spectrumizer-card.js` naar `config/www/spectrumizer-card.js`.
2. Ga naar **Instellingen → Dashboards → Resources** en voeg toe:
   - URL: `/local/spectrumizer-card.js`
   - Type: **JavaScript-module**
3. Voeg deze kaart toe aan een dashboard. Vervang de entity door de entity-id van je Spectrumizer-sensor:

```yaml
type: custom:spectrumizer-card
entity: sensor.spectrum
name: Live FFT-spectrum
# Optioneel: toon alleen frequenties tot 5 Hz
# max_frequency: 5
```

De kaart toont de dominante frequentie, het aantal verzamelde samples en het spectrum dat live wordt bijgewerkt.

## HACS

Voeg deze repository in HACS toe als aangepaste **Integration**-repository. Installeer Spectrumizer en herstart Home Assistant. De JavaScript-kaart is een aparte Lovelace-resource en moet apart worden geregistreerd zoals hierboven beschreven.
