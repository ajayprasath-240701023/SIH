/**
 * Crypto Fraud Attribution System — Frontend Logic
 *
 * Handles API calls, vis-network graph rendering, animated risk gauge,
 * transaction table, case save/load, and report download.
 */

// ═══════════════════════════════════════════════════════════
//  State
// ═══════════════════════════════════════════════════════════
const API = '';  // same-origin
let currentResult = null;
let network = null;

// ═══════════════════════════════════════════════════════════
//  Init
// ═══════════════════════════════════════════════════════════
document.addEventListener('DOMContentLoaded', async () => {
    await loadDemoWallets();
    await loadSavedCases();

    // Enter key triggers trace
    document.getElementById('walletInput').addEventListener('keydown', e => {
        if (e.key === 'Enter') runTrace();
    });
});

// ═══════════════════════════════════════════════════════════
//  Demo Wallets
// ═══════════════════════════════════════════════════════════
async function loadDemoWallets() {
    try {
        const resp = await fetch(`${API}/api/demo-wallets`);
        const data = await resp.json();

        // Update mode badge
        const badge = document.getElementById('modeBadge');
        const modeText = document.getElementById('modeText');
        modeText.textContent = data.mode.toUpperCase();
        badge.className = `mode-badge ${data.mode}`;

        // Render demo wallet buttons
        const container = document.getElementById('demoWallets');
        container.innerHTML = '';
        (data.wallets || []).forEach(addr => {
            const btn = document.createElement('button');
            btn.className = 'demo-wallet-btn';
            btn.textContent = addr;
            btn.title = addr;
            btn.onclick = () => {
                document.getElementById('walletInput').value = addr;
                runTrace();
            };
            container.appendChild(btn);
        });
    } catch (e) {
        console.warn('Could not load demo wallets:', e);
    }
}

// ═══════════════════════════════════════════════════════════
//  Run Trace
// ═══════════════════════════════════════════════════════════
async function runTrace() {
    const addr = document.getElementById('walletInput').value.trim();
    if (!addr) {
        showToast('Please enter a wallet address.', 'error');
        return;
    }

    const depth = parseInt(document.getElementById('depthSelect').value, 10);
    const btn = document.getElementById('traceBtn');
    const overlay = document.getElementById('loadingOverlay');

    btn.classList.add('loading');
    btn.disabled = true;
    overlay.classList.add('active');

    try {
        const resp = await fetch(`${API}/api/trace`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ wallet_address: addr, depth }),
        });

        if (!resp.ok) {
            const err = await resp.json().catch(() => ({}));
            throw new Error(err.detail || `HTTP ${resp.status}`);
        }

        currentResult = await resp.json();
        renderResults(currentResult);
        showToast(`Trace complete — ${currentResult.total_wallets} wallets found.`, 'success');
    } catch (e) {
        showToast(`Trace failed: ${e.message}`, 'error');
        console.error(e);
    } finally {
        btn.classList.remove('loading');
        btn.disabled = false;
        overlay.classList.remove('active');
    }
}

// ═══════════════════════════════════════════════════════════
//  Render Results
// ═══════════════════════════════════════════════════════════
function renderResults(result) {
    document.getElementById('emptyState').classList.add('hidden');
    document.getElementById('resultsSection').classList.remove('hidden');

    renderStats(result);
    renderGraph(result);
    renderRisk(result.risk);
    renderExchanges(result.exchange_matches);
    renderTransactions(result.edges);
}

// ── Stats ────────────────────────────────────────────────
function renderStats(result) {
    animateNumber('statWallets', result.total_wallets);
    animateNumber('statTransactions', result.total_transactions);
    animateNumber('statValue', result.total_value_eth, true);
    animateNumber('statExchanges', result.exchange_matches.length);
}

function animateNumber(id, target, isFloat = false) {
    const el = document.getElementById(id);
    const start = 0;
    const duration = 1200;
    const startTime = performance.now();

    function tick(now) {
        const elapsed = now - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const eased = 1 - Math.pow(1 - progress, 3);
        const val = start + (target - start) * eased;
        el.textContent = isFloat ? val.toFixed(2) : Math.round(val);
        if (progress < 1) requestAnimationFrame(tick);
    }
    requestAnimationFrame(tick);
}

// ── Graph ────────────────────────────────────────────────
function renderGraph(result) {
    const container = document.getElementById('graphContainer');

    const nodeColors = {
        suspect:       { background: '#f87171', border: '#ef4444', font: '#fff' },
        intermediary:  { background: '#fb923c', border: '#f97316', font: '#fff' },
        exchange:      { background: '#34d399', border: '#10b981', font: '#fff' },
        victim:        { background: '#a78bfa', border: '#8b5cf6', font: '#fff' },
        unknown:       { background: '#64748b', border: '#475569', font: '#fff' },
    };

    const nodeShapes = {
        suspect: 'diamond',
        exchange: 'box',
        victim: 'triangle',
        intermediary: 'dot',
        unknown: 'dot',
    };

    const nodes = new vis.DataSet(
        result.nodes.map(n => {
            const colors = nodeColors[n.type] || nodeColors.unknown;
            return {
                id: n.id,
                label: n.label || shortAddr(n.id),
                shape: nodeShapes[n.type] || 'dot',
                color: {
                    background: colors.background,
                    border: colors.border,
                    highlight: { background: colors.background, border: '#fff' },
                },
                font: { color: colors.font, size: 12, face: 'Inter' },
                size: n.type === 'suspect' ? 30 : (n.type === 'exchange' ? 26 : 20),
                borderWidth: 2,
                shadow: { enabled: true, size: 10, color: colors.background + '40' },
                title: `${n.type.toUpperCase()}: ${n.id}${n.exchange_name ? ' (' + n.exchange_name + ')' : ''}`,
            };
        })
    );

    const edges = new vis.DataSet(
        result.edges.map((e, i) => ({
            id: `e${i}`,
            from: e.from_addr,
            to: e.to_addr,
            label: e.label || '',
            arrows: 'to',
            color: { color: 'rgba(56,189,248,0.4)', highlight: '#38bdf8' },
            font: { color: '#94a3b8', size: 10, face: 'JetBrains Mono', strokeWidth: 0 },
            width: Math.max(1, Math.min(e.value_eth * 2, 6)),
            smooth: { type: 'curvedCW', roundness: 0.15 },
            title: `${e.value_eth.toFixed(4)} ETH\nTx: ${e.tx_hash}`,
        }))
    );

    const options = {
        physics: {
            barnesHut: {
                gravitationalConstant: -3000,
                centralGravity: 0.3,
                springLength: 150,
                damping: 0.3,
            },
            stabilization: { iterations: 150 },
        },
        interaction: {
            hover: true,
            tooltipDelay: 200,
            zoomView: true,
            dragView: true,
        },
        layout: {
            improvedLayout: true,
        },
    };

    if (network) network.destroy();
    network = new vis.Network(container, { nodes, edges }, options);
}

function shortAddr(addr) {
    if (addr.length > 12) return addr.slice(0, 6) + '…' + addr.slice(-4);
    return addr;
}

// ── Risk Gauge ───────────────────────────────────────────
function renderRisk(risk) {
    const score = risk.score;
    const circumference = 2 * Math.PI * 65; // r=65

    const fill = document.getElementById('gaugeFill');
    const offset = circumference - (score / 100) * circumference;

    // Color based on level
    let color;
    if (risk.level === 'High')        color = '#f87171';
    else if (risk.level === 'Medium') color = '#fb923c';
    else                              color = '#34d399';

    fill.style.stroke = color;
    // Animate with a slight delay
    setTimeout(() => {
        fill.style.strokeDashoffset = offset;
    }, 100);

    // Animate score number
    const el = document.getElementById('riskScore');
    el.style.color = color;
    animateScoreNumber(el, score);

    // Badge
    const badge = document.getElementById('riskBadge');
    badge.textContent = risk.level;
    badge.className = `risk-level-badge ${risk.level.toLowerCase()}`;

    // Reasons
    const list = document.getElementById('riskReasons');
    list.innerHTML = '';
    (risk.reasons || []).forEach(r => {
        const li = document.createElement('li');
        li.textContent = r;
        list.appendChild(li);
    });
}

function animateScoreNumber(el, target) {
    const duration = 1500;
    const start = performance.now();
    function tick(now) {
        const p = Math.min((now - start) / duration, 1);
        const eased = 1 - Math.pow(1 - p, 4);
        el.textContent = Math.round(target * eased);
        if (p < 1) requestAnimationFrame(tick);
    }
    requestAnimationFrame(tick);
}

// ── Exchange Matches ─────────────────────────────────────
function renderExchanges(matches) {
    const list = document.getElementById('exchangeList');
    list.innerHTML = '';

    if (!matches || matches.length === 0) {
        list.innerHTML = '<li style="color:var(--text-muted); font-size:12px; padding:8px 0;">No exchange wallets identified in traced flow.</li>';
        return;
    }

    matches.forEach(m => {
        const li = document.createElement('li');
        li.className = 'exchange-item';
        li.innerHTML = `
            <div class="exchange-info">
                <div class="exchange-icon">🏦</div>
                <div>
                    <div class="exchange-name">${m.exchange_name}</div>
                    <div class="exchange-addr">${shortAddr(m.address)}</div>
                </div>
            </div>
            <div class="exchange-amount">${m.total_received_eth.toFixed(4)} ETH</div>
        `;
        list.appendChild(li);
    });
}

// ── Transaction Table ────────────────────────────────────
function renderTransactions(edges) {
    const tbody = document.getElementById('txTableBody');
    const countEl = document.getElementById('txCount');
    tbody.innerHTML = '';

    if (!edges || edges.length === 0) {
        countEl.textContent = '0 transactions';
        return;
    }

    countEl.textContent = `${edges.length} transactions`;

    // De-duplicate by tx_hash (keep unique)
    const seen = new Set();
    const uniqueEdges = edges.filter(e => {
        if (seen.has(e.tx_hash)) return false;
        seen.add(e.tx_hash);
        return true;
    });

    uniqueEdges.forEach(e => {
        const tr = document.createElement('tr');
        const time = e.timestamp ? new Date(e.timestamp * 1000).toLocaleString() : '—';
        tr.innerHTML = `
            <td class="addr" title="${e.tx_hash}">${shortAddr(e.tx_hash)}</td>
            <td class="addr" title="${e.from_addr}">${shortAddr(e.from_addr)}</td>
            <td class="addr" title="${e.to_addr}">${shortAddr(e.to_addr)}</td>
            <td class="value-cell">${e.value_eth.toFixed(4)}</td>
            <td>${time}</td>
        `;
        tbody.appendChild(tr);
    });
}

// ═══════════════════════════════════════════════════════════
//  Actions
// ═══════════════════════════════════════════════════════════

// ── Download Report ──────────────────────────────────────
async function downloadReport() {
    if (!currentResult) {
        showToast('Run a trace first.', 'error');
        return;
    }

    try {
        const resp = await fetch(`${API}/api/trace/${currentResult.case_id}/report`);
        if (!resp.ok) throw new Error('Report generation failed');
        const html = await resp.text();

        const blob = new Blob([html], { type: 'text/html' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `Investigation_Report_${currentResult.case_id}.html`;
        a.click();
        URL.revokeObjectURL(url);
        showToast('Report downloaded.', 'success');
    } catch (e) {
        showToast(`Report error: ${e.message}`, 'error');
    }
}

// ── Save Case ────────────────────────────────────────────
async function saveCase() {
    if (!currentResult) {
        showToast('Run a trace first.', 'error');
        return;
    }

    try {
        const resp = await fetch(`${API}/api/cases`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(currentResult),
        });

        if (!resp.ok) throw new Error('Save failed');
        const saved = await resp.json();
        showToast(`Case ${saved.case_id} saved.`, 'success');
        await loadSavedCases();
    } catch (e) {
        showToast(`Save error: ${e.message}`, 'error');
    }
}

// ── Load Saved Cases ─────────────────────────────────────
async function loadSavedCases() {
    try {
        const resp = await fetch(`${API}/api/cases`);
        const cases = await resp.json();
        const container = document.getElementById('savedCases');

        if (cases.length === 0) {
            container.innerHTML = '<p style="color: var(--text-muted); font-size: 11px; padding: 8px 0;">No saved cases yet.</p>';
            return;
        }

        container.innerHTML = '';
        cases.forEach(c => {
            const div = document.createElement('div');
            div.className = 'case-item';
            div.onclick = () => loadCase(c.case_id);
            div.innerHTML = `
                <div class="case-id">${c.case_id}</div>
                <div class="case-meta">${shortAddr(c.wallet_address)}</div>
                <span class="case-risk risk-level-badge ${c.risk_level.toLowerCase()}">${c.risk_level} (${c.risk_score})</span>
            `;
            container.appendChild(div);
        });
    } catch (e) {
        console.warn('Could not load cases:', e);
    }
}

// ── Load a specific saved case ───────────────────────────
async function loadCase(caseId) {
    try {
        const resp = await fetch(`${API}/api/cases/${caseId}`);
        if (!resp.ok) throw new Error('Case not found');
        const detail = await resp.json();
        currentResult = detail.trace_result;
        document.getElementById('walletInput').value = currentResult.wallet_address;
        renderResults(currentResult);
        showToast(`Loaded case ${caseId}.`, 'success');
    } catch (e) {
        showToast(`Load error: ${e.message}`, 'error');
    }
}

// ── Reset ────────────────────────────────────────────────
function resetView() {
    currentResult = null;
    document.getElementById('walletInput').value = '';
    document.getElementById('resultsSection').classList.add('hidden');
    document.getElementById('emptyState').classList.remove('hidden');

    // Reset gauge
    const fill = document.getElementById('gaugeFill');
    fill.style.strokeDashoffset = 408;
    document.getElementById('riskScore').textContent = '0';

    if (network) {
        network.destroy();
        network = null;
    }
}

// ═══════════════════════════════════════════════════════════
//  Toast
// ═══════════════════════════════════════════════════════════
function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(50px)';
        toast.style.transition = 'all 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}
