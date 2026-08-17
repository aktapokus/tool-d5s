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

// ── İkonlar — monokrom SVG, emoji/renkli glyph yok (platform standardı). ──
const ICON_UNDO = "<svg viewBox='0 0 24 24' width='15' height='15' fill='none' stroke='currentColor' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round' style='vertical-align:-2px'><path d='M9 14 4 9l5-5'/><path d='M4 9h10a6 6 0 0 1 0 12h-1'/></svg>";
const ICON_CHECK = "<svg viewBox='0 0 24 24' width='15' height='15' fill='none' stroke='currentColor' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round' style='vertical-align:-2px'><polyline points='20 6 9 17 4 12'/></svg>";
const ICON_DOWNLOAD = "<svg viewBox='0 0 24 24' width='15' height='15' fill='none' stroke='currentColor' stroke-width='1.7' stroke-linecap='round' stroke-linejoin='round' style='vertical-align:-2px'><path d='M12 3v12'/><polyline points='7 10 12 15 17 10'/><path d='M4 19h16'/></svg>";

function ensureStyles() {
  if (document.getElementById(STYLE_ID)) return;
  const style = document.createElement('style');
  style.id = STYLE_ID;
  style.textContent = `
    .d5s-page { display: flex; flex-direction: column; flex: 1; min-height: 0; }
    .d5s-footer-bar { flex-shrink: 0; border-top: 1px solid var(--border); background: var(--surface); padding: 14px 16px; }
    .d5s-form { padding: 0; flex-shrink: 0; }
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

// ── i18n — sadece bu eski bir core'a (api.t henüz yok) karşı çalışırken
// bozulmamak için TR güvenlik ağı (AGENTS.md Madde 6 Kural 2). Tek doğruluk
// kaynağı locale/tr.json + locale/en.json (bkz. core/static/index.html
// toolSec()). ──
const T_FALLBACK = {
  sonuc_placeholder: '// Analiz sonucu burada görünecek', istek_etiket: '// İstek',
  istek_placeholder: 'Ne yapmak istiyorsun?', istek_varsayilan: 'Belgelerimi düzenle, eski dosyaları arşive at',
  analiz_et_btn: 'ANALİZ ET', clr_btn: 'CLR', geri_al_btn: 'SON İŞLEMİ GERİ AL',
  istek_bos_uyari: 'İstek boş — ne yapmak istediğini yaz.', henuz_analiz_yok: 'Henüz bir analiz yapılmadı.',
  geri_alinacak_yok: 'Bu klasör için geri alınacak işlem bulunamadı.',
  gecmis_geri_al_onay: '{tarih} tarihli işlemi geri almak istediğinden emin misin?\n({basarili} başarılı, {basarisiz} başarısız işlem)',
  son_islem_geri_al_onay: 'Son işlemi geri almak istediğinden emin misin?', analiz_sonucu_baslik: '// Analiz Sonucu',
  toplam_etiket: 'Toplam', oge_birimi: 'ÖĞE', hepsini_sec: 'HEPSİNİ SEÇ', hicbirini_secme: 'HİÇBİRİNİ SEÇME',
  sadece_gecici_sec: 'SADECE GEÇİCİ DOSYALARI SEÇ', tumu_filtre: 'Tümü', faz_bos: 'BU FAZDA ÖĞE YOK',
  secili_oge: '<b>{n}</b> / {toplam} öğe seçili', secileni_uygula: 'SEÇİLENİ UYGULA',
  html_rapor_indir: 'HTML RAPOR İNDİR', en_az_bir_oge: 'En az bir öğe seçilmeli.',
};

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

  function t(key, vars) {
    let s = (typeof api.t === 'function') ? api.t(key) : undefined;
    if (s === undefined || s === null || s === key) s = T_FALLBACK[key] ?? key;
    if (vars) for (const k in vars) s = s.split(`{${k}}`).join(vars[k]);
    return s;
  }

  let currentKlasor = '';

  container.innerHTML = `
    <div class="d5s-page">
      <div class="d5s-result-area" id="d5sResultArea">
        <div class="d5s-placeholder">${esc(t('sonuc_placeholder'))}</div>
      </div>
      <div class="d5s-footer-bar">
        <div class="d5s-form">
          <div class="field-block">
            <label class="field-label">${esc(t('istek_etiket'))}</label>
            <textarea id="d5sIstek" rows="2" placeholder="${esc(t('istek_placeholder'))}">${esc(t('istek_varsayilan'))}</textarea>
          </div>
          <div class="btn-row">
            <button class="btn-primary" id="d5sAnalizBtn">▶ ${esc(t('analiz_et_btn'))}</button>
            <button class="btn-secondary" id="d5sClrBtn">${esc(t('clr_btn'))}</button>
            <button class="btn-danger" id="d5sGeriAlBtn">${ICON_UNDO} ${esc(t('geri_al_btn'))}</button>
          </div>
        </div>
      </div>
    </div>
  `;

  const istekEl  = container.querySelector('#d5sIstek');
  const resultEl = container.querySelector('#d5sResultArea');

  container.querySelector('#d5sClrBtn').onclick = () => {
    istekEl.value = '';
    resultEl.innerHTML = `<div class="d5s-placeholder">${esc(t('sonuc_placeholder'))}</div>`;
    api.gizlefeedback();
    api.resetPipeline();
  };

  container.querySelector('#d5sAnalizBtn').onclick = async () => {
    const istek = istekEl.value.trim();
    if (!istek) { api.gosterfeedback(t('istek_bos_uyari'), 'err'); return; }

    const klasor = await api.pickFolder();
    if (!klasor) return;
    currentKlasor = klasor;

    const btn = container.querySelector('#d5sAnalizBtn');
    btn.disabled = true;
    resultEl.innerHTML = `<div class="d5s-placeholder">${esc(t('sonuc_placeholder'))}</div>`;
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
    const klasor = currentKlasor;
    if (!klasor) { api.gosterfeedback(t('henuz_analiz_yok'), 'err'); return; }

    let sid = api.lastSessionId();
    if (!sid) {
      const hd = await api.history(klasor, 1);
      if (!hd.oturumlar || hd.oturumlar.length === 0) {
        api.gosterfeedback(t('geri_alinacak_yok'), 'err');
        return;
      }
      const o = hd.oturumlar[0];
      const tarih = o.baslangic ? new Date(o.baslangic).toLocaleString('tr-TR') : '?';
      if (!confirm(t('gecmis_geri_al_onay', { tarih, basarili: o.basarili, basarisiz: o.basarisiz }))) return;
      sid = o.session_id;
    } else {
      if (!confirm(t('son_islem_geri_al_onay'))) return;
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
        <div class="d5s-header">${esc(t('analiz_sonucu_baslik'))}</div>
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
          <div class="d5s-ozet-toplam"><span>${esc(t('toplam_etiket'))}</span><span>${data.toplam} ${esc(t('oge_birimi'))}</span></div>
        </div>
        ${currentItems.length > 0 ? `
          <div class="d5s-body" style="border-top:1px solid var(--border)">
            <div class="d5s-filter-row" id="d5sFilterRow"></div>
            <div class="d5s-bulk-row">
              <button class="d5s-bulk-btn" data-act="all">${esc(t('hepsini_sec'))}</button>
              <button class="d5s-bulk-btn" data-act="none">${esc(t('hicbirini_secme'))}</button>
              <button class="d5s-bulk-btn" data-act="gecici">${esc(t('sadece_gecici_sec'))}</button>
            </div>
            <div class="d5s-selection-count" id="d5sSelectionCount"></div>
            <div class="d5s-items-wrap" id="d5sItemsTable"></div>
          </div>` : ''}
        <div class="d5s-footer">
          <button class="btn-primary" id="d5sOnayBtn">${ICON_CHECK} ${esc(t('secileni_uygula'))}</button>
          <button class="btn-secondary" id="d5sRaporBtn">${ICON_DOWNLOAD} ${esc(t('html_rapor_indir'))}</button>
        </div>
      </div>
    `;

    function buildFilterTabs() {
      const present = FAZ_SIRA.filter(f => currentItems.some(i => i.phase === f));
      const row = resultEl.querySelector('#d5sFilterRow');
      if (!row) return;
      const tabs = [{ key: 'all', label: t('tumu_filtre') }, ...present.map(f => ({ key: f, label: FAZ_ETIKET[f] || f }))];
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
        ? `<div class="d5s-items-empty">${esc(t('faz_bos'))}</div>`
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
      if (el) el.innerHTML = t('secili_oge', { n: selectedIds.size, toplam: currentItems.length });
      const btn = resultEl.querySelector('#d5sOnayBtn');
      if (btn) { btn.innerHTML = `${ICON_CHECK} ${esc(t('secileni_uygula'))} (${selectedIds.size})`; btn.disabled = selectedIds.size === 0; }
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
        api.gosterfeedback(t('en_az_bir_oge'), 'err');
        return;
      }
      const d = await api.execute(toolId, data.plan_id, currentItems.length > 0 ? Array.from(selectedIds) : null);
      if (!d.hata) resultEl.innerHTML = `<div class="d5s-placeholder">${esc(t('sonuc_placeholder'))}</div>`;
    };

    resultEl.querySelector('#d5sRaporBtn').onclick = () => api.raporIndir(data.plan_id);
  }
}

export function unmount(container) {
  container.innerHTML = '';
}
