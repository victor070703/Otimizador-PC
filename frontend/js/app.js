/* ════════════════════════════════════════════════════
   STATE
════════════════════════════════════════════════════ */
let activeMode   = 'gaming';
let modeOn       = true;
let currentPage  = 'dashboard';

const MODE_DATA = {
  gaming: {
    label:  'Modo Gaming ativo',
    desc:   'Serviços não essenciais pausados • GPU e CPU priorizados',
    cls:    'gaming',
    icon:   'ti-device-gamepad-2',
    pageSub:'Visão geral · Modo Gaming ativo',
  },
  daily: {
    label:  'Modo Uso Diário ativo',
    desc:   'Balanceado para produtividade e estabilidade do sistema',
    cls:    'daily',
    icon:   'ti-device-laptop',
    pageSub:'Visão geral · Modo Uso Diário ativo',
  },
  custom: {
    label:  'Modo Personalizado',
    desc:   'Configure manualmente os parâmetros de otimização',
    cls:    'custom',
    icon:   'ti-adjustments-horizontal',
    pageSub:'Visão geral · Modo Personalizado ativo',
  },
};

/* ════════════════════════════════════════════════════
   INIT
════════════════════════════════════════════════════ */
function init() {
  startMetricsLoop();
}

if (window.pywebview) {
  init();
} else {
  window.addEventListener('pywebviewready', init);
}

/* ════════════════════════════════════════════════════
   METRICS (dashboard)
════════════════════════════════════════════════════ */
function startMetricsLoop() {
  fetchMetrics();
  setInterval(fetchMetrics, 2000);
}

async function fetchMetrics() {
  try {
    updateMetrics(await API.getMetrics());
  } catch (_) {}
}

function updateMetrics(d) {
  const cpu  = d.cpu  || {};
  const ram  = d.ram  || {};
  const gpu  = d.gpu  || {};
  const disk = d.disk || {};

  // CPU
  setText('cpu-val', fmt(cpu.percent) + '%');
  setText('cpu-sub', shorten(cpu.model, 28));
  setBar ('cpu-bar', cpu.percent, barColor(cpu.percent));

  // RAM
  setText('ram-val', `${ram.used_gb ?? 0} GB`);
  setText('ram-sub', `de ${ram.total_gb ?? 0} GB usados`);
  setBar ('ram-bar', ram.percent, barColor(ram.percent));

  // GPU
  if (gpu.available && gpu.percent > 0) {
    setText('gpu-val', fmt(gpu.percent) + '%');
    setBar ('gpu-bar', gpu.percent, barColor(gpu.percent));
  } else {
    setText('gpu-val', '—');
    setBar ('gpu-bar', 0, '#22c55e');
  }
  const gpuTemp = gpu.temp > 0 ? ` · ${gpu.temp}°C` : '';
  setText('gpu-sub', shorten((gpu.name || '—') + gpuTemp, 30));

  // Disco
  const io = ((disk.read_mb ?? 0) + (disk.write_mb ?? 0)).toFixed(1);
  setText('disk-val', `${io} MB/s`);
  setText('disk-sub', `${disk.free_gb ?? 0} GB livres`);
  setBar ('disk-bar', disk.percent, barColor(disk.percent));

  // Footer clock
  const now = new Date();
  setText('status-time', now.toLocaleTimeString('pt-BR', {hour:'2-digit', minute:'2-digit', second:'2-digit'}));
}

/* ════════════════════════════════════════════════════
   PROCESSES PAGE
════════════════════════════════════════════════════ */
async function loadProcesses() {
  const list = document.getElementById('process-list');
  list.innerHTML = loadingHTML('Carregando processos...');
  try {
    renderProcesses(await API.getProcesses(25));
  } catch (_) {
    list.innerHTML = errorHTML('Erro ao carregar processos.');
  }
}

function renderProcesses(procs) {
  const list  = document.getElementById('process-list');
  const badge = document.getElementById('proc-badge');
  const high  = procs.filter(p => p.cpu > 10 || p.ram_bytes > 400 * 1024 * 1024).length;

  if (badge) {
    badge.textContent = `${high} com alto consumo`;
    badge.className   = high > 0 ? 'badge badge-amber' : 'badge badge-green';
  }

  if (!procs.length) {
    list.innerHTML = '<div class="loading-row">Nenhum processo encontrado.</div>';
    return;
  }

  list.innerHTML = procs.map(p => `
    <div class="proc-row" id="proc-${p.pid}">
      <div class="proc-icon"><i class="ti ${esc(p.icon)}"></i></div>
      <div class="proc-name">
        <p>${esc(p.name)}</p>
        <span>PID ${p.pid}${p.status ? ' · ' + p.status : ''}</span>
      </div>
      <div class="proc-stats">
        <div class="proc-stat">
          <div class="val ${valCls(p.cpu, 10, 5)}">${p.cpu}%</div>
          <div class="lbl">CPU</div>
        </div>
        <div class="proc-stat">
          <div class="val ${valCls(p.ram_bytes/(1024*1024), 400, 150)}">${esc(p.ram_label)}</div>
          <div class="lbl">RAM</div>
        </div>
      </div>
      <button class="kill-btn" onclick="killProcess(${p.pid}, this)">Encerrar</button>
    </div>`
  ).join('');
}

async function killProcess(pid, btn) {
  btn.disabled = true;
  btn.textContent = '...';
  try {
    const r = await API.killProcess(pid);
    if (r.success) {
      const row = document.getElementById(`proc-${pid}`);
      if (row) row.classList.add('killed');
      btn.textContent = 'Encerrado';
      showToast(r.message, 'success');
    } else {
      btn.disabled = false;
      btn.textContent = 'Encerrar';
      showToast(r.message, 'error');
    }
  } catch (_) {
    btn.disabled = false;
    btn.textContent = 'Encerrar';
    showToast('Erro ao comunicar com o sistema.', 'error');
  }
}

/* ════════════════════════════════════════════════════
   SERVICES PAGE
════════════════════════════════════════════════════ */
async function loadServices() {
  const list = document.getElementById('services-list');
  list.innerHTML = loadingHTML('Carregando serviços...');
  try {
    renderServices(await API.getServices());
  } catch (_) {
    list.innerHTML = errorHTML('Erro ao carregar serviços.');
  }
}

function renderServices(svcs) {
  const list  = document.getElementById('services-list');
  const badge = document.getElementById('svc-badge');
  const runningCount = svcs.filter(s => s.running).length;

  if (badge) {
    badge.textContent = `${runningCount} em execução`;
    badge.className   = runningCount > 0 ? 'badge badge-amber' : 'badge badge-green';
  }

  if (!svcs.length) {
    list.innerHTML = '<div class="loading-row">Nenhum serviço encontrado para este sistema.</div>';
    return;
  }

  list.innerHTML = svcs.map(s => `
    <div class="proc-row" id="svc-${esc(s.id)}">
      <div class="proc-icon"><i class="ti ${esc(s.icon)}"></i></div>
      <div class="proc-name">
        <p>${esc(s.name)}</p>
        <span>${esc(s.desc)}</span>
      </div>
      <div class="proc-stats">
        <div class="proc-stat">
          <div class="val ${s.running ? 'val-mid' : 'val-low'}" style="font-size:11px">${esc(s.status)}</div>
          <div class="lbl">Estado</div>
        </div>
      </div>
      ${s.running
        ? `<button class="stop-btn" onclick="stopService('${esc(s.id)}', this)">Parar</button>`
        : `<button class="stop-btn" disabled>Parado</button>`}
    </div>`
  ).join('');
}

async function stopService(id, btn) {
  btn.disabled = true;
  btn.textContent = '...';
  try {
    const r = await API.stopService(id);
    if (r.success) {
      btn.textContent = 'Parado';
      const row = document.getElementById(`svc-${id}`);
      if (row) {
        const val = row.querySelector('.val');
        if (val) { val.textContent = 'Parado'; val.className = 'val val-low'; }
      }
      showToast(r.message, 'success');
    } else {
      btn.disabled = false;
      btn.textContent = 'Parar';
      showToast(r.message, 'error');
    }
  } catch (_) {
    btn.disabled = false;
    btn.textContent = 'Parar';
    showToast('Erro ao comunicar com o sistema.', 'error');
  }
}

/* ════════════════════════════════════════════════════
   CLEANUP PAGE
════════════════════════════════════════════════════ */
async function loadCleanup() {
  const list = document.getElementById('cleanup-list');
  list.innerHTML = loadingHTML('Calculando tamanhos...');
  try {
    renderCleanup(await API.getCleanupItems());
  } catch (_) {
    list.innerHTML = errorHTML('Erro ao calcular espaço ocupado.');
  }
}

function renderCleanup(items) {
  const list  = document.getElementById('cleanup-list');
  const badge = document.getElementById('cleanup-badge');

  // Update top metric cards
  const byId = Object.fromEntries(items.map(i => [i.id, i]));
  updateCleanCard('user_caches', 'clean-cache-val', 'clean-cache-sub', byId, '~/Library/Caches');
  updateCleanCard('user_logs',   'clean-logs-val',  'clean-logs-sub',  byId, '~/Library/Logs');
  updateCleanCard('trash',       'clean-trash-val', 'clean-trash-sub', byId, '~/.Trash');
  // Windows aliases
  updateCleanCard('user_temp',   'clean-cache-val', 'clean-cache-sub', byId, '%TEMP%');
  updateCleanCard('system_temp', 'clean-logs-val',  'clean-logs-sub',  byId, 'C:\\Windows\\Temp');

  const total = items.reduce((s, i) => s + (i.size_bytes || 0), 0);
  if (badge) {
    badge.textContent = `${fmtBytes(total)} no total`;
    badge.className   = total > 500 * 1024 * 1024 ? 'badge badge-amber' : 'badge badge-gray';
  }

  if (!items.length) {
    list.innerHTML = '<div class="loading-row">Nenhum item encontrado.</div>';
    return;
  }

  list.innerHTML = items.map(item => `
    <div class="proc-row" id="clean-${esc(item.id)}">
      <div class="proc-icon"><i class="ti ${esc(item.icon)}"></i></div>
      <div class="proc-name">
        <p>${esc(item.name)}</p>
        <span>${esc(item.desc || item.path || '')}</span>
      </div>
      <div class="proc-stats">
        <div class="proc-stat">
          <div class="val">${esc(item.size_label)}</div>
          <div class="lbl">Tamanho</div>
        </div>
      </div>
      <button class="stop-btn" onclick="cleanItem('${esc(item.id)}', this)">Limpar</button>
    </div>`
  ).join('');
}

function updateCleanCard(id, valId, subId, byId, fallbackSub) {
  const item = byId[id];
  if (!item) return;
  setText(valId, item.size_label);
  setText(subId, item.path || fallbackSub);
}

async function cleanItem(id, btn) {
  btn.disabled = true;
  btn.textContent = '...';
  try {
    const r = await API.cleanItem(id);
    if (r.success) {
      const row = document.getElementById(`clean-${id}`);
      if (row) row.classList.add('killed');
      btn.textContent = 'Limpo';
      showToast(r.message, 'success');
    } else {
      btn.disabled = false;
      btn.textContent = 'Limpar';
      showToast(r.message, 'error');
    }
  } catch (_) {
    btn.disabled = false;
    btn.textContent = 'Limpar';
  }
}

/* ════════════════════════════════════════════════════
   HISTORY PAGE
════════════════════════════════════════════════════ */
async function loadHistory() {
  const list = document.getElementById('history-list');
  list.innerHTML = loadingHTML('Carregando histórico...');
  try {
    renderHistory(await API.getHistory());
  } catch (_) {
    list.innerHTML = errorHTML('Erro ao carregar histórico.');
  }
}

function renderHistory(entries) {
  const list = document.getElementById('history-list');

  if (!entries || !entries.length) {
    list.innerHTML = `
      <div class="loading-row" style="flex-direction:column;gap:6px;padding:32px 16px;">
        <i class="ti ti-history" style="font-size:28px;color:var(--border-primary);animation:none"></i>
        <span>Nenhuma otimização realizada ainda.</span>
        <span style="font-size:11px">Clique em "Otimizar agora" para começar.</span>
      </div>`;
    return;
  }

  const modeLabels = { gaming: 'Gaming', daily: 'Uso Diário', custom: 'Personalizado' };

  list.innerHTML = entries.map(e => `
    <div class="history-row">
      <div class="history-icon"><i class="ti ti-check"></i></div>
      <div class="history-info">
        <div class="history-title">${esc(e.summary || 'Otimização concluída')}</div>
        <div class="history-desc">
          ${e.killed ? `${e.killed} processo(s) encerrado(s) · ` : ''}
          ${e.stopped ? `${e.stopped} serviço(s) pausado(s) · ` : ''}
          ${e.cleaned ? `${e.cleaned} item(s) limpo(s) · ` : ''}
          ${e.freed_disk_label ? `${e.freed_disk_label} liberados` : ''}
        </div>
        <div class="history-meta">${esc(e.timestamp || '')}</div>
      </div>
      <div class="history-badge">${esc(modeLabels[e.mode] || e.mode || '—')}</div>
    </div>`
  ).join('');
}

/* ════════════════════════════════════════════════════
   PRE-OPTIMIZATION MODAL
════════════════════════════════════════════════════ */
let _previewData = null;

async function openOptimizeModal() {
  const overlay = document.getElementById('optimize-modal');
  const body    = document.getElementById('modal-body');
  const sub     = document.getElementById('modal-subtitle');
  const est     = document.getElementById('modal-estimates');
  const confirmBtn = document.getElementById('confirm-btn');

  _previewData = null;
  body.innerHTML    = loadingHTML('Analisando sistema...');
  sub.textContent   = `Modo ${activeMode === 'gaming' ? 'Gaming' : activeMode === 'daily' ? 'Uso Diário' : 'Personalizado'}`;
  est.innerHTML     = '';
  confirmBtn.disabled = true;
  overlay.classList.add('open');

  try {
    const data = await API.getOptimizationPreview(activeMode);
    _previewData = data;
    renderModalBody(data);
    renderModalEstimates(data);
    confirmBtn.disabled = false;
  } catch (e) {
    body.innerHTML = errorHTML('Erro ao analisar o sistema.');
  }
}

function renderModalBody(data) {
  const body = document.getElementById('modal-body');
  let html   = '';

  // ── Processos ──
  if (data.processes && data.processes.length) {
    html += `
      <div>
        <div class="modal-section-label"><i class="ti ti-activity"></i> Processos a encerrar</div>
        <div class="check-list">
          ${data.processes.map(p => `
            <label class="check-item">
              <input type="checkbox" name="proc" value="${p.pid}" checked />
              <div class="check-item-icon"><i class="ti ${esc(p.icon)}"></i></div>
              <div class="check-item-info">
                <div class="check-item-name">${esc(p.name)}</div>
                <div class="check-item-desc">PID ${p.pid}</div>
              </div>
              <span class="check-item-tag ${p.cpu > 10 ? 'red' : p.cpu > 5 ? 'amber' : 'gray'}">
                ${p.cpu}% CPU · ${esc(p.ram_label)}
              </span>
            </label>`
          ).join('')}
        </div>
      </div>`;
  }

  // ── Serviços ──
  if (data.services && data.services.length) {
    html += `
      <div>
        <div class="modal-section-label"><i class="ti ti-server"></i> Serviços a pausar</div>
        <div class="check-list">
          ${data.services.map(s => `
            <label class="check-item">
              <input type="checkbox" name="svc" value="${esc(s.id)}" checked />
              <div class="check-item-icon"><i class="ti ${esc(s.icon)}"></i></div>
              <div class="check-item-info">
                <div class="check-item-name">${esc(s.name)}</div>
                <div class="check-item-desc">${esc(s.desc)}</div>
              </div>
              <span class="check-item-tag amber">Em execução</span>
            </label>`
          ).join('')}
        </div>
      </div>`;
  }

  // ── Limpeza ──
  if (data.cleanup && data.cleanup.length) {
    html += `
      <div>
        <div class="modal-section-label"><i class="ti ti-trash"></i> Arquivos a limpar</div>
        <div class="check-list">
          ${data.cleanup.map(c => `
            <label class="check-item">
              <input type="checkbox" name="clean" value="${esc(c.id)}" checked />
              <div class="check-item-icon"><i class="ti ${esc(c.icon)}"></i></div>
              <div class="check-item-info">
                <div class="check-item-name">${esc(c.name)}</div>
                <div class="check-item-desc">${esc(c.desc || c.path || '')}</div>
              </div>
              <span class="check-item-tag green">${esc(c.size_label)}</span>
            </label>`
          ).join('')}
        </div>
      </div>`;
  }

  if (!html) {
    html = '<div class="loading-row" style="animation:none">✓ Sistema já otimizado — nada a fazer.</div>';
  }

  document.getElementById('modal-body').innerHTML = html;
}

function renderModalEstimates(data) {
  const est = document.getElementById('modal-estimates');
  est.innerHTML = `
    <div class="modal-estimate">
      <i class="ti ti-device-desktop"></i>
      RAM liberada: <strong>${data.estimated_ram_label || '—'}</strong>
    </div>
    <div class="modal-estimate">
      <i class="ti ti-device-floppy"></i>
      Disco liberado: <strong>${data.estimated_disk_label || '—'}</strong>
    </div>`;
}

function closeOptimizeModal() {
  document.getElementById('optimize-modal').classList.remove('open');
}

function handleModalOverlayClick(e) {
  if (e.target === document.getElementById('optimize-modal')) closeOptimizeModal();
}

async function confirmOptimize() {
  const confirmBtn = document.getElementById('confirm-btn');
  confirmBtn.disabled = true;
  confirmBtn.innerHTML = '<i class="ti ti-loader-2" style="animation:spin 1s linear infinite"></i> Otimizando...';

  // Collect checked items
  const modal  = document.getElementById('optimize-modal');
  const pids   = [...modal.querySelectorAll('input[name="proc"]:checked')].map(el => parseInt(el.value));
  const svcs   = [...modal.querySelectorAll('input[name="svc"]:checked')].map(el => el.value);
  const cleans = [...modal.querySelectorAll('input[name="clean"]:checked')].map(el => el.value);

  try {
    const result = await API.runOptimization({
      mode:             activeMode,
      kill_pids:        pids,
      stop_service_ids: svcs,
      clean_item_ids:   cleans,
    });

    closeOptimizeModal();

    const done = [...result.killed, ...result.stopped, ...result.cleaned];
    showToast(
      `Otimização concluída! ${done.length} ação(ões) realizadas.` +
      (result.freed_disk_label !== '0 KB' ? ` · ${result.freed_disk_label} de disco liberados.` : ''),
      'success'
    );

    // Refresh history tab if open
    if (currentPage === 'historico') loadHistory();

  } catch (e) {
    showToast('Erro ao executar otimização.', 'error');
  } finally {
    confirmBtn.disabled = false;
    confirmBtn.innerHTML = '<i class="ti ti-check"></i> Confirmar e otimizar';
  }
}

/* ════════════════════════════════════════════════════
   NAVIGATION
════════════════════════════════════════════════════ */
const PAGE_TITLES = {
  dashboard: 'Painel',
  processos: 'Processos',
  servicos:  'Serviços',
  limpeza:   'Limpeza',
  historico: 'Histórico',
};

const PAGE_LOADERS = {
  processos: loadProcesses,
  servicos:  loadServices,
  limpeza:   loadCleanup,
  historico: loadHistory,
};

function showPage(page, btn) {
  currentPage = page;
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
  document.getElementById('page-' + page).classList.add('active');
  btn.classList.add('active');
  setText('page-title', PAGE_TITLES[page] || page);
  if (PAGE_LOADERS[page]) PAGE_LOADERS[page]();
}

/* ════════════════════════════════════════════════════
   MODE SWITCHING
════════════════════════════════════════════════════ */
function setMode(mode) {
  activeMode = mode;
  document.querySelectorAll('.mode-btn').forEach(b => b.classList.remove('active'));
  const btn = document.querySelector(`.mode-btn.${mode}`);
  if (btn) btn.classList.add('active');

  const d = MODE_DATA[mode];
  if (!d) return;

  const banner = document.getElementById('mode-banner');
  banner.className = `mode-banner ${d.cls}`;
  const iconEl = banner.querySelector(':scope > i');
  if (iconEl) iconEl.className = `ti ${d.icon}`;
  setText('banner-title', d.label);
  setText('banner-desc', d.desc);
  setText('page-sub', d.pageSub);
}

function toggleMode() {
  modeOn = !modeOn;
  const el = document.getElementById('mode-toggle');
  if (el) el.className = `toggle${modeOn ? ' active' : ''}`;
}

/* ════════════════════════════════════════════════════
   TOAST
════════════════════════════════════════════════════ */
function showToast(message, type = 'success') {
  const wrap = document.getElementById('toast-wrap');
  if (!wrap) return;
  const icon  = type === 'success' ? 'ti-circle-check' : 'ti-alert-circle';
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.innerHTML = `<i class="ti ${icon}"></i>${esc(message)}`;
  wrap.appendChild(toast);
  setTimeout(() => toast.remove(), 4000);
}

/* ════════════════════════════════════════════════════
   HELPERS
════════════════════════════════════════════════════ */
function setText(id, val) {
  const el = document.getElementById(id);
  if (el) el.textContent = val;
}

function setBar(id, pct, color) {
  const el = document.getElementById(id);
  if (!el) return;
  el.style.width      = `${Math.min(100, Math.max(0, pct || 0))}%`;
  el.style.background = color;
}

function barColor(pct) {
  if (pct >= 80) return '#ef4444';
  if (pct >= 50) return '#f59e0b';
  return '#22c55e';
}

function valCls(val, hi, mid) {
  if (val >= hi)  return 'val-high';
  if (val >= mid) return 'val-mid';
  return 'val-low';
}

function fmt(val) { return (val ?? 0).toFixed(0); }

function fmtBytes(b) {
  if (b >= 1024 ** 3) return `${(b / (1024 ** 3)).toFixed(1)} GB`;
  if (b >= 1024 ** 2) return `${Math.round(b / (1024 ** 2))} MB`;
  return `${Math.round(b / 1024)} KB`;
}

function shorten(s, len) {
  if (!s) return '—';
  return s.length <= len ? s : s.slice(0, len - 1) + '…';
}

function esc(s) {
  if (typeof s !== 'string') return String(s ?? '');
  return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

function loadingHTML(msg) {
  return `<div class="loading-row"><i class="ti ti-loader-2"></i> ${esc(msg)}</div>`;
}

function errorHTML(msg) {
  return `<div class="loading-row"><i class="ti ti-alert-circle" style="animation:none;color:#ef4444"></i> ${esc(msg)}</div>`;
}
