/* Spectrumizer live spectrum Lovelace card. */
class SpectrumizerCard extends HTMLElement {
  setConfig(config) {
    if (!config || !config.entity) throw new Error("Geef een Spectrumizer-sensor op via 'entity'.");
    this.config = { name: "Live spectrum", max_frequency: null, ...config };
    this.attachShadow({ mode: "open" });
    this._render();
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  getCardSize() { return 4; }

  _render() {
    if (!this.shadowRoot || !this._hass || !this.config) return;
    const state = this._hass.states[this.config.entity];
    const attrs = state?.attributes || {};
    const frequencies = attrs.frequencies || [];
    const magnitudes = attrs.magnitudes || [];
    const ready = attrs.ready === true && frequencies.length === magnitudes.length && frequencies.length > 1;
    const peak = state && state.state !== "unknown" && state.state !== "unavailable" ? Number(state.state) : null;
    const maxFrequency = Number(this.config.max_frequency) > 0
      ? Number(this.config.max_frequency)
      : (Number(attrs.sampling_rate_hz) / 2 || 1);
    this.shadowRoot.innerHTML = `
      <ha-card header="${this._escape(this.config.name)}">
        <div class="content">
          <div class="summary">
            <div><span class="label">Dominante frequentie</span><strong>${peak === null || !Number.isFinite(peak) ? "—" : peak.toFixed(3) + " Hz"}</strong></div>
            <div><span class="label">Samples</span><strong>${attrs.samples_collected ?? 0} / ${attrs.window_size ?? "—"}</strong></div>
            <div><span class="label">Resolutie</span><strong>${attrs.frequency_resolution_hz ?? "—"} Hz</strong></div>
          </div>
          <div class="chart-wrap">${ready ? this._chart(frequencies, magnitudes, maxFrequency, peak) : '<div class="empty">Samples verzamelen… Het spectrum verschijnt zodra het venster gevuld is.</div>'}</div>
          <div class="footer">${this._escape(attrs.source_entity || "")} · ${attrs.sampling_rate_hz ?? "—"} samples/s</div>
        </div>
      </ha-card>
      <style>
        :host { display:block; }
        .content { padding:16px; }
        .summary { display:flex; flex-wrap:wrap; gap:20px; margin-bottom:12px; }
        .summary > div { display:flex; flex-direction:column; gap:4px; min-width:100px; }
        .label,.footer { color:var(--secondary-text-color); font-size:12px; }
        strong { font-size:18px; font-weight:500; }
        .chart-wrap { width:100%; overflow:hidden; }
        svg { display:block; width:100%; height:auto; }
        .empty { min-height:180px; display:grid; place-items:center; text-align:center; color:var(--secondary-text-color); }
        .footer { margin-top:10px; overflow-wrap:anywhere; }
      </style>`;
  }

  _chart(freqs, mags, maxFreq, peak) {
    const width = 720, height = 260, left = 48, right = 14, top = 14, bottom = 34;
    const plotW = width-left-right, plotH = height-top-bottom;
    const points = freqs.map((f,i)=>({f:Number(f),m:Number(mags[i])}))
      .filter(p=>Number.isFinite(p.f)&&Number.isFinite(p.m)&&p.f>=0&&p.f<=maxFreq);
    if (!points.length) return '<div class="empty">Geen spectrumdata beschikbaar.</div>';
    const maxMag = Math.max(...points.map(p=>p.m), 1e-12);
    const bars = points.map(p=>{
      const x=left+(p.f/maxFreq)*plotW;
      const barH=(p.m/maxMag)*plotH;
      const w=Math.max(1,Math.min(8,plotW/points.length*0.8));
      const isPeak=peak!==null&&Math.abs(p.f-peak)<(Number(this._hass.states[this.config.entity]?.attributes?.frequency_resolution_hz)||0.0001)/2;
      return `<rect x="${(x-w/2).toFixed(2)}" y="${(top+plotH-barH).toFixed(2)}" width="${w.toFixed(2)}" height="${Math.max(0,barH).toFixed(2)}" fill="${isPeak?'var(--accent-color)':'var(--primary-color)'}" opacity="${isPeak?1:0.78}"><title>${p.f.toFixed(3)} Hz: ${p.m.toFixed(5)}</title></rect>`;
    }).join("");
    const grid = [0,0.25,0.5,0.75,1].map(t=>{
      const y=top+plotH*(1-t);
      return `<line x1="${left}" y1="${y}" x2="${width-right}" y2="${y}" stroke="var(--divider-color)" stroke-width="1"/><text x="${left-8}" y="${y+4}" text-anchor="end" fill="var(--secondary-text-color)" font-size="11">${(maxMag*t).toPrecision(2)}</text>`;
    }).join("");
    const ticks = [0,0.25,0.5,0.75,1].map(t=>{
      const x=left+plotW*t;
      return `<text x="${x}" y="${height-10}" text-anchor="middle" fill="var(--secondary-text-color)" font-size="11">${(maxFreq*t).toPrecision(3)}</text>`;
    }).join("");
    return `<svg viewBox="0 0 ${width} ${height}" role="img" aria-label="Live FFT spectrum">
      ${grid}${bars}${ticks}
      <text x="12" y="${top+plotH/2}" transform="rotate(-90 12 ${top+plotH/2})" text-anchor="middle" fill="var(--secondary-text-color)" font-size="11">Amplitude</text>
      <text x="${left+plotW/2}" y="${height-1}" text-anchor="middle" fill="var(--secondary-text-color)" font-size="11">Frequentie (Hz)</text>
    </svg>`;
  }

  _escape(value) {
    return String(value).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  }

  static getConfigElement() { return document.createElement("spectrumizer-card-editor"); }
  static getStubConfig() { return { entity: "sensor.spectrum" }; }
}
customElements.define("spectrumizer-card", SpectrumizerCard);

class SpectrumizerCardEditor extends HTMLElement {
  setConfig(config) {
    this._config = { ...config };
    if (!this.shadowRoot) this.attachShadow({ mode: "open" });
    this._render();
  }
  set hass(hass) { this._hass = hass; this._render(); }
  _render() {
    if (!this.shadowRoot || !this._hass) return;
    const entities = Object.keys(this._hass.states).filter(id => id.startsWith("sensor."));
    this.shadowRoot.innerHTML = `
      <div class="field"><label>FFT-sensor</label><select id="entity">${entities.map(e=>`<option value="${e}" ${e===this._config.entity?'selected':''}>${e}</option>`).join("")}</select></div>
      <div class="field"><label>Kaarttitel</label><input id="name" value="${String(this._config.name||"Live spectrum").replace(/&/g,"&amp;").replace(/"/g,"&quot;")}"></div>
      <div class="field"><label>Maximale frequentie (Hz, optioneel)</label><input id="max_frequency" type="number" min="0" step="any" value="${this._config.max_frequency||""}"></div>
      <style>.field{display:flex;flex-direction:column;gap:6px;margin:12px 0}label{font-size:13px;color:var(--secondary-text-color)}input,select{padding:8px;background:var(--card-background-color);color:var(--primary-text-color);border:1px solid var(--divider-color);border-radius:4px}</style>`;
    this.shadowRoot.querySelectorAll("input,select").forEach(el=>el.addEventListener("change",()=>{
      const value={...this._config,entity:this.shadowRoot.getElementById("entity").value,name:this.shadowRoot.getElementById("name").value};
      const max=Number(this.shadowRoot.getElementById("max_frequency").value);
      if(max>0)value.max_frequency=max;else delete value.max_frequency;
      this._config=value;
      this.dispatchEvent(new CustomEvent("config-changed",{detail:{config:value},bubbles:true,composed:true}));
    }));
  }
}
customElements.define("spectrumizer-card-editor", SpectrumizerCardEditor);

window.customCards = window.customCards || [];
window.customCards.push({type:"spectrumizer-card",name:"Spectrumizer Live Spectrum",description:"Live FFT spectrum chart for Spectrumizer integration."});
