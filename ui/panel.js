/**
 * tools/d5s/ui/panel.js
 * D5S'in core'a sunduğu UI yüzeyi — AGENTS.md Madde 4 sözleşmesi.
 *
 * core sadece bir mount noktası (container) ve bir araç kutusu (api) verir.
 * İSTEK, KLASÖR, ANALİZ ET, GERİ AL — hepsi bu dosyanın sorumluluğu. core
 * bunların hiçbirinin var olduğunu bilmez; başka bir tool (ör. PLC) tamamen
 * farklı alanlar (IP adresi, register listesi) isteyebilir, core etkilenmez.
 */

const STYLE_ID = 'd5s-panel-style';

function ensureStyles() {
  if (document.getElementById(STYLE_ID)) return;
  const style = document.createElement('style');
  style.id = STYLE_ID;
  style.textContent = `
    .d5s-split { display: flex; flex: 1; min-height: 0; overflow: hidden; }
    .d5s-split-left { width: 280px; flex-shrink: 0; border-right: 1px solid var(--border); overflow-y: auto; }
    .d5s-split-right { flex: 1; min-width: 0; overflow-y: auto; display: flex; flex-direction: column; }
    .d5s-form { padding: 16px; flex-shrink: 0; }
    .d5s-result-area { flex: 1; min-height: 0; overflow-y: auto; }
    .d5s-box { display: flex; flex-direction: column; }
    .d5s-header {
      padding: 8px 14px; background: var(--surface); border-bottom: 1px solid var(--border);
      font-family: var(--mono); font-size: 9px; font-weight: 500; color: var(--text-xs);
      text-transform: uppercase; letter-spacing: 0.1em;
    }
    .d5s-body { padding: 14px; }
    .d5s-aciklama {
      font-size: 12px; line-height: 1.6; color: var(--text-dim); margin-bottom: 12px;
      padding-bottom: 12px; border-bottom: 1px solid var(--border);
    }
    .d5s-ozet-row {
      display: flex; justify-content: space-between; align-items: center;
      padding: 6px 0; border-bottom: 1px solid var(--surface-2);
    }
    .d5s-ozet-row:last-child { border-bottom: none; }
    .d5s-ozet-kural { font-size: 11px; color: var(--text-dim); font-family: var(--sans); }
    .d5s-ozet-sayi { font-family: var(--mono); font-size: 14px; font-weight: 500; color: var(--blue); }
    .d5s-ozet-toplam {
      display: flex; justify-content: space-between; margin-top: 10px; padding-top: 10px;
      border-top: 1px solid var(--border); font-family: var(--mono); font-size: 10px;
      color: var(--text-dim); text-transform: uppercase; letter-spacing: 0.08em;
    }
    .d5s-score-card { display: flex; align-items: stretch; gap: 0; margin-bottom: 12px; border: 1px solid var(--border); }
    .d5s-score-total {
      display: flex; flex-direction: column; align-items: center; justify-content: center;
      padding: 10px 16px; border-right: 1px solid var(--border); background: var(--surface); min-width: 76px;
    }
    .d5s-score-grade { font-family: var(--mono); font-size: 22px; font-weight: 500; line-height: 1; }
    .d5s-score-grade.g-A, .d5s-score-grade.g-B { color: var(--green); }
    .d5s-score-grade.g-C, .d5s-score-grade.g-D { color: var(--amber); }
    .d5s-score-grade.g-F { color: var(--red); }
    .d5s-score-total-num { font-family: var(--mono); font-size: 9px; color: var(--text-dim); margin-top: 2px; }
    .d5s-score-phases { flex: 1; display: flex; flex-wrap: wrap; }
    .d5s-score-phase { flex: 1; min-width: 90px; padding: 6px 10px; border-right: 1px solid var(--surface-2); }
    .d5s-score-phase:last-child { border-right: none; }
    .d5s-score-phase-label { font-family: var(--mono); font-size: 8px; color: var(--text-xs); text-transform: uppercase; letter-spacing: 0.06em; }
    .d5s-score-phase-val { font-family: var(--mono); font-size: 15px; font-weight: 500; margin-top: 2px; }
    .d5s-score-phase-val.s-high { color: var(--green); }
    .d5s-score-phase-val.s-mid  { color: var(--amber); }
    .d5s-score-phase-val.s-low  { color: var(--red); }
    .d5s-filter-row { display: flex; flex-wrap: wrap; gap: 1px; margin-bottom: 8px; }
    .d5s-filter-tab {
      font-family: var(--mono); font-size: 9px; font-weight: 500; letter-spacing: 0.06em;
      text-transform: uppercase; padding: 5px 10px; border: 1px solid var(--border);
      background: var(--bg); color: var(--text-dim); cursor: pointer;
    }
    .d5s-filter-tab:hover { border-color: var(--blue); color: var(--blue); }
    .d5s-filter-tab.active { background: var(--blue); border-color: var(--blue); color: #FFFFFF; }
    .d5s-bulk-row { display: flex; gap: 1px; margin-bottom: 10px; }
    .d5s-bulk-btn {
      font-family: var(--mono); font-size: 9px; letter-spacing: 0.06em; text-transform: uppercase;
      padding: 5px 10px; border: 1px solid var(--border); background: var(--surface);
      color: var(--text-dim); cursor: pointer;
    }
    .d5s-bulk-btn:hover { border-color: var(--text-dim); color: var(--text); }
    .d5s-items-wrap { border: 1px solid var(--border); max-height: 340px; overflow-y: auto; margin-bottom: 12px; }
    .d5s-item-row { display: flex; align-items: flex-start; gap: 8px; padding: 7px 10px; border-bottom: 1px solid var(--surface-2); font-size: 11px; }
    .d5s-item-row:last-child { border-bottom: none; }
    .d5s-item-row.deselected { opacity: 0.45; }
    .d5s-item-row input[type=checkbox] { margin-top: 2px; accent-color: var(--blue); cursor: pointer; flex-shrink: 0; }
    .d5s-item-body { flex: 1; min-width: 0; }
    .d5s-item-top { display: flex; align-items: center; gap: 6px; margin-bottom: 2px; flex-wrap: wrap; }
    .d5s-item-phase-badge {
      font-family: var(--mono); font-size: 8px; font-weight: 500; color: var(--blue-dim);
      background: var(--blue-light); padding: 1px 5px; text-transform: uppercase; letter-spacing: 0.05em;
    }
    .d5s-item-action { font-family: var(--mono); font-size: 8px; color: var(--text-xs); text-transform: uppercase; }
    .d5s-item-risk { font-family: var(--mono); font-size: 8px; padding: 1px 5px; text-transform: uppercase; }
    .d5s-item-risk.low    { color: var(--green); background: #ECFDF5; }
    .d5s-item-risk.medium { color: var(--amber); background: #FFFBEB; }
    .d5s-item-risk.high   { color: var(--red);   background: #FEF2F2; }
    .d5s-item-source { font-family: var(--mono); font-size: 10px; color: var(--text); word-break: break-all; }
    .d5s-item-reason { color: var(--text-dim); line-height: 1.4; margin-top: 2px; }
    .d5s-items-empty { padding: 16px; text-align: center; color: var(--text-xs); font-family: var(--mono); font-size: 10px; text-transform: uppercase; }
    .d5s-selection-count { font-family: var(--mono); font-size: 10px; color: var(--text-dim); margin-bottom: 10px; text-transform: uppercase; letter-spacing: 0.06em; }
    .d5s-selection-count b { color: var(--blue); font-size: 12px; }
    .d5s-footer { padding: 10px 14px; background: var(--surface); border-top: 1px solid var(--border); display: flex; gap: 1px; align-items: center; }
    .d5s-placeholder {
      flex: 1; display: flex; align-items: center; justify-content: center;
      color: var(--text-xs); font-family: var(--mono); font-size: 11px;
      text-transform: uppercase; letter-spacing: 0.08em;
    }
  `;
  document.head.appendChild(style);
}

const FAZ_ETIKET = { seiri: 'Seiri', seiton: 'Seiton', seiso: 'Seiso', seiketsu: 'Seiketsu', shitsuke: 'Shitsuke' };
const FAZ_SIRA = ['seiri', 'seiton', 'seiso', 'seiketsu', 'shitsuke'];

function esc(s) {
  return String(s ?? '').replace(/[&<>"']/g, c => ({ '&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;' }[c]));
}
function fmtBytes(n) {
  if (!n) return '';
  const kb = n / 1024;
  if (kb < 1024) return `${kb.toFixed(0)} KB`;
  return `${(kb/1024).toFixed(1)} MB`;
}
function scoreClass(v) {
  if (v >= 80) return 's-high';
  if (v >= 60) return 's-mid';
  return 's-low';
}

export function mount(container, api, toolId) {
  ensureStyles();

  let currentKlasor = '';

  container.innerHTML = `
    <div class="d5s-split">
      <div class="d5s-split-left">
        <div class="d5s-form">
          <div class="field-block">
            <label class="field-label">// İstek</label>
            <textarea id="d5sIstek" rows="3"
              placeholder="Ne yapmak istiyorsun?  —  Örn: Belgelerimi düzenle, eski dosyaları arşive at"></textarea>
          </div>
          <div class="field-block">
            <label class="field-label">// Klasör</label>
            <div class="folder-row">
              <input type="text" id="d5sKlasor" placeholder="/data/kullanici/belgeler">
              <button class="btn-secondary" id="d5sSecBtn" style="border-top:2px solid var(--text-dim)">SEÇ</button>
            </div>
          </div>
          <div class="btn-row">
            <button class="btn-primary" id="d5sAnalizBtn">▶ ANALİZ ET</button>
            <button class="btn-secondary" id="d5sClrBtn">CLR</button>
          </div>
          <div class="btn-row" style="margin-top:6px">
            <button class="btn-danger" id="d5sGeriAlBtn" style="width:100%;white-space:normal">↩ SON İŞLEMİ GERİ AL</button>
          </div>
        </div>
      </div>
      <div class="d5s-split-right">
        <div class="d5s-result-area" id="d5sResultArea">
          <div class="d5s-placeholder">// Analiz sonucu burada görünecek</div>
        </div>
      </div>
    </div>
  `;

  const istekEl  = container.querySelector('#d5sIstek');
  const klasorEl = container.querySelector('#d5sKlasor');
  const resultEl = container.querySelector('#d5sResultArea');

  container.querySelector('#d5sSecBtn').onclick = async () => {
    const path = await api.pickFolder();
    if (path) klasorEl.value = path;
  };

  container.querySelector('#d5sClrBtn').onclick = () => {
    istekEl.value = '';
    resultEl.innerHTML = '<div class="d5s-placeholder">// Analiz sonucu burada görünecek</div>';
    api.gizlefeedback();
    api.resetPipeline();
  };

  container.querySelector('#d5sAnalizBtn').onclick = async () => {
    const istek  = istekEl.value.trim();
    const klasor = klasorEl.value.trim();
    if (!istek)  { api.gosterfeedback('İstek boş — ne yapmak istediğini yaz.', 'err'); return; }
    if (!klasor) { api.gosterfeedback('Klasör seçilmedi.', 'err'); return; }
    currentKlasor = klasor;

    const btn = container.querySelector('#d5sAnalizBtn');
    btn.disabled = true;
    resultEl.innerHTML = '<div class="d5s-placeholder">// Analiz sonucu burada görünecek</div>';
    try {
      const d = await api.analyze(toolId, { istek, klasor });
      if (d.hata || d.detail) return;
      if (d.bos) return;
      renderResult(d);
    } finally {
      btn.disabled = false;
    }
  };

  container.querySelector('#d5sGeriAlBtn').onclick = async () => {
    const klasor = klasorEl.value.trim() || currentKlasor;
    if (!klasor) { api.gosterfeedback('Klasör belirtilmemiş.', 'err'); return; }

    let sid = api.lastSessionId();
    if (!sid) {
      const hd = await api.history(klasor, 1);
      if (!hd.oturumlar || hd.oturumlar.length === 0) {
        api.gosterfeedback('Bu klasör için geri alınacak işlem bulunamadı.', 'err');
        return;
      }
      const o = hd.oturumlar[0];
      const tarih = o.baslangic ? new Date(o.baslangic).toLocaleString('tr-TR') : '?';
      if (!confirm(`${tarih} tarihli işlemi geri almak istediğinden emin misin?\n(${o.basarili} başarılı, ${o.basarisiz} başarısız işlem)`)) return;
      sid = o.session_id;
    } else {
      if (!confirm('Son işlemi geri almak istediğinden emin misin?')) return;
    }
    await api.rollback(toolId, klasor, sid);
  };

  function renderResult(data) {
    let currentItems = data.items || [];
    let selectedIds  = new Set(currentItems.map(i => i.id));
    let activeFilter = 'all';

    function visibleItems() {
      return activeFilter === 'all' ? currentItems : currentItems.filter(i => i.phase === activeFilter);
    }
    function scoreCardHtml(score) {
      if (!score || !score.fazlar) return '';
      return `
        <div class="d5s-score-card">
          <div class="d5s-score-total">
            <div class="d5s-score-grade g-${score.grade}">${score.grade}</div>
            <div class="d5s-score-total-num">${score.total}/100</div>
          </div>
          <div class="d5s-score-phases">
            ${FAZ_SIRA.map(f => {
              const p = score.fazlar[f];
              if (!p) return '';
              return `
                <div class="d5s-score-phase">
                  <div class="d5s-score-phase-label">${FAZ_ETIKET[f] || f}</div>
                  <div class="d5s-score-phase-val ${scoreClass(p.skor)}">${p.skor}</div>
                </div>`;
            }).join('')}
          </div>
        </div>`;
    }

    resultEl.innerHTML = `
      <div class="d5s-box">
        <div class="d5s-header">// Analiz Sonucu</div>
        <div class="d5s-body">
          <div class="d5s-aciklama">${esc(data.aciklama || '')}</div>
          ${scoreCardHtml(data.score)}
          <div>
            ${(data.ozet || []).map(o => `
              <div class="d5s-ozet-row">
                <span class="d5s-ozet-kural">${esc(o.etiket)}</span>
                <span class="d5s-ozet-sayi">${o.sayi}</span>
              </div>`).join('')}
          </div>
          <div class="d5s-ozet-toplam"><span>Toplam</span><span>${data.toplam} ÖĞE</span></div>
        </div>
        ${currentItems.length > 0 ? `
          <div class="d5s-body" style="border-top:1px solid var(--border)">
            <div class="d5s-filter-row" id="d5sFilterRow"></div>
            <div class="d5s-bulk-row">
              <button class="d5s-bulk-btn" data-act="all">HEPSİNİ SEÇ</button>
              <button class="d5s-bulk-btn" data-act="none">HİÇBİRİNİ SEÇME</button>
              <button class="d5s-bulk-btn" data-act="gecici">SADECE GEÇİCİ DOSYALARI SEÇ</button>
            </div>
            <div class="d5s-selection-count" id="d5sSelectionCount"></div>
            <div class="d5s-items-wrap" id="d5sItemsTable"></div>
          </div>` : ''}
        <div class="d5s-footer">
          <button class="btn-primary" id="d5sOnayBtn">✓ SEÇİLENİ UYGULA</button>
          <button class="btn-secondary" id="d5sRaporBtn">⬇ HTML RAPOR İNDİR</button>
        </div>
      </div>
    `;

    function buildFilterTabs() {
      const present = FAZ_SIRA.filter(f => currentItems.some(i => i.phase === f));
      const row = resultEl.querySelector('#d5sFilterRow');
      if (!row) return;
      const tabs = [{ key: 'all', label: 'Tümü' }, ...present.map(f => ({ key: f, label: FAZ_ETIKET[f] || f }))];
      row.innerHTML = tabs.map(t => `
        <button class="d5s-filter-tab${t.key === activeFilter ? ' active' : ''}" data-filter="${t.key}">${t.label}</button>
      `).join('');
      row.querySelectorAll('[data-filter]').forEach(b => {
        b.onclick = () => { activeFilter = b.dataset.filter; buildFilterTabs(); renderItemsTable(); };
      });
    }

    function renderItemsTable() {
      const wrap = resultEl.querySelector('#d5sItemsTable');
      if (!wrap) return;
      const items = visibleItems();
      wrap.innerHTML = items.length === 0
        ? '<div class="d5s-items-empty">BU FAZDA ÖĞE YOK</div>'
        : items.map(i => `
          <div class="d5s-item-row${selectedIds.has(i.id) ? '' : ' deselected'}">
            <input type="checkbox" data-id="${i.id}" ${selectedIds.has(i.id) ? 'checked' : ''}>
            <div class="d5s-item-body">
              <div class="d5s-item-top">
                <span class="d5s-item-phase-badge">${esc(i.faz_etiket || i.phase)}</span>
                <span class="d5s-item-action">${esc(i.action)}</span>
                <span class="d5s-item-risk ${esc(i.risk)}">${esc(i.risk)}</span>
                ${i.size_bytes ? `<span class="d5s-item-action">${fmtBytes(i.size_bytes)}</span>` : ''}
              </div>
              <div class="d5s-item-source">${esc(i.source)}${i.destination ? ' → ' + esc(i.destination) : ''}</div>
              <div class="d5s-item-reason">${esc(i.reason)}</div>
            </div>
          </div>`).join('');
      wrap.querySelectorAll('input[type=checkbox]').forEach(cb => {
        cb.onchange = () => {
          if (cb.checked) selectedIds.add(cb.dataset.id); else selectedIds.delete(cb.dataset.id);
          renderItemsTable();
        };
      });
      updateSelectionCount();
    }

    function updateSelectionCount() {
      const el = resultEl.querySelector('#d5sSelectionCount');
      if (el) el.innerHTML = `<b>${selectedIds.size}</b> / ${currentItems.length} öğe seçili`;
      const btn = resultEl.querySelector('#d5sOnayBtn');
      if (btn) { btn.textContent = `✓ SEÇİLENİ UYGULA (${selectedIds.size})`; btn.disabled = selectedIds.size === 0; }
    }

    if (currentItems.length > 0) {
      buildFilterTabs();
      renderItemsTable();
      resultEl.querySelectorAll('.d5s-bulk-btn').forEach(btn => {
        btn.onclick = () => {
          if (btn.dataset.act === 'all') visibleItems().forEach(i => selectedIds.add(i.id));
          else if (btn.dataset.act === 'none') visibleItems().forEach(i => selectedIds.delete(i.id));
          else if (btn.dataset.act === 'gecici') {
            selectedIds.clear();
            currentItems.forEach(i => {
              const r = (i.reason || '').toLowerCase();
              if (r.includes('geçici') || r.includes('gecici')) selectedIds.add(i.id);
            });
          }
          renderItemsTable();
        };
      });
    }

    resultEl.querySelector('#d5sOnayBtn').onclick = async () => {
      if (currentItems.length > 0 && selectedIds.size === 0) {
        api.gosterfeedback('En az bir öğe seçilmeli.', 'err');
        return;
      }
      const d = await api.execute(toolId, data.plan_id, currentItems.length > 0 ? Array.from(selectedIds) : null);
      if (!d.hata) resultEl.innerHTML = '<div class="d5s-placeholder">// Analiz sonucu burada görünecek</div>';
    };

    resultEl.querySelector('#d5sRaporBtn').onclick = () => api.raporIndir(data.plan_id);
  }
}

export function unmount(container) {
  container.innerHTML = '';
}
