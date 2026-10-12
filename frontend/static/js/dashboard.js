/**
 * Financial Risk & Scenario Analysis Dashboard - Frontend Logic
 */

const API = ""; // same origin

let niiChart = null;
let radarChart = null;
let historyChart = null;
let dashboardData = null;

// --------------- Utils ---------------
function $(sel) { return document.querySelector(sel); }
function $$(sel) { return document.querySelectorAll(sel); }

function toast(msg, type = "success") {
  let el = $(".toast");
  if (!el) {
    el = document.createElement("div");
    el.className = "toast";
    document.body.appendChild(el);
  }
  el.textContent = msg;
  el.className = `toast ${type} show`;
  setTimeout(() => el.classList.remove("show"), 2800);
}

async function api(path, options = {}) {
  const res = await fetch(API + path, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options
  });
  if (!res.ok) throw new Error(`API ${path} → ${res.status}`);
  return res.json();
}

// --------------- Navigation ---------------
function setupNav() {
  $$(".nav-item").forEach(item => {
    item.addEventListener("click", (e) => {
      e.preventDefault();
      const view = item.dataset.view;
      $$(".nav-item").forEach(n => n.classList.remove("active"));
      item.classList.add("active");
      $$(".view").forEach(v => v.classList.remove("active"));
      $(`#view-${view}`).classList.add("active");

      if (view === "history" && !historyChart) loadHistoryChart();
      if (view === "peers") renderPeers();
      if (view === "stress") loadScenarios();
    });
  });
}

// --------------- Sliders ---------------
function setupSliders() {
  const pairs = [
    ["sliderHorizon", "valHorizon", "labHorizon"],
    ["sliderRate", "valRate", "labRate"],
    ["sliderNCO", "valNCO", "labNCO"]
  ];
  pairs.forEach(([sliderId, valId, labId]) => {
    const slider = $(`#${sliderId}`);
    const val = $(`#${valId}`);
    const lab = $(`#${labId}`);
    if (!slider) return;
    slider.addEventListener("input", () => {
      val.textContent = slider.value;
      if (lab) lab.value = slider.value;
    });
  });

  // Sync lab inputs → main sliders
  ["labHorizon", "labRate", "labNCO"].forEach(id => {
    const el = $(`#${id}`);
    if (!el) return;
    el.addEventListener("change", () => {
      const map = { labHorizon: "sliderHorizon", labRate: "sliderRate", labNCO: "sliderNCO" };
      const s = $(`#${map[id]}`);
      if (s) {
        s.value = el.value;
        s.dispatchEvent(new Event("input"));
      }
    });
  });
}

// --------------- Charts ---------------
function initNIIChart(labels, values) {
  const ctx = $("#niiChart").getContext("2d");
  if (niiChart) niiChart.destroy();
  niiChart = new Chart(ctx, {
    type: "line",
    data: {
      labels,
      datasets: [{
        label: "Net Interest Income ($M)",
        data: values,
        borderColor: "#a78bfa",
        backgroundColor: "rgba(167,139,250,0.12)",
        fill: true,
        tension: 0.35,
        pointRadius: 4,
        pointBackgroundColor: "#a78bfa",
        borderWidth: 2.5
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: "#1a2332",
          titleColor: "#e8edf5",
          bodyColor: "#a78bfa",
          borderColor: "#2d3a4f",
          borderWidth: 1,
          callbacks: {
            label: ctx => ` $${ctx.parsed.y.toFixed(1)}M`
          }
        }
      },
      scales: {
        x: {
          grid: { color: "rgba(45,58,79,0.5)" },
          ticks: { color: "#8b9bb4", font: { size: 11 } }
        },
        y: {
          grid: { color: "rgba(45,58,79,0.5)" },
          ticks: {
            color: "#8b9bb4",
            font: { size: 11 },
            callback: v => "$" + v + "M"
          }
        }
      }
    }
  });
}

function initRadarChart(baseVals, stressVals) {
  const labels = ["ALLL", "BAR", "DIL", "NIM", "COF", "YOEA", "LDR", "ER", "LR", "ROA"];
  // Normalize roughly for display (different scales)
  const scale = {
    ALLL: 3, BAR: 4, DIL: 2, NIM: 6, COF: 4, YOEA: 8, LDR: 100, ER: 100, LR: 30, ROA: 2
  };
  const norm = (obj) => labels.map(k => {
    const v = obj[k] ?? 0;
    return Math.min(100, (v / scale[k]) * 100);
  });

  const ctx = $("#radarChart").getContext("2d");
  if (radarChart) radarChart.destroy();
  radarChart = new Chart(ctx, {
    type: "radar",
    data: {
      labels,
      datasets: [
        {
          label: "Q4 2023",
          data: norm(baseVals),
          borderColor: "#5b8def",
          backgroundColor: "rgba(91,141,239,0.2)",
          pointBackgroundColor: "#5b8def",
          borderWidth: 2
        },
        {
          label: "Stress",
          data: norm(stressVals),
          borderColor: "#a78bfa",
          backgroundColor: "rgba(167,139,250,0.15)",
          pointBackgroundColor: "#a78bfa",
          borderWidth: 2
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        r: {
          beginAtZero: true,
          max: 100,
          ticks: { display: false },
          grid: { color: "rgba(45,58,79,0.7)" },
          angleLines: { color: "rgba(45,58,79,0.7)" },
          pointLabels: { color: "#8b9bb4", font: { size: 10 } }
        }
      }
    }
  });
}

async function loadHistoryChart() {
  try {
    const data = await api("/api/industry-history");
    const ctx = $("#historyChart").getContext("2d");
    if (historyChart) historyChart.destroy();
    historyChart = new Chart(ctx, {
      type: "line",
      data: {
        labels: data.map(d => d.year),
        datasets: [
          {
            label: "Charge-Off Rate (%)",
            data: data.map(d => d.charge_off_rate),
            borderColor: "#f87171",
            backgroundColor: "transparent",
            yAxisID: "y",
            tension: 0.2,
            pointRadius: 0,
            borderWidth: 2
          },
          {
            label: "New Consumer Loan Origination ($B)",
            data: data.map(d => d.loan_origination),
            borderColor: "#34d399",
            backgroundColor: "transparent",
            yAxisID: "y1",
            tension: 0.2,
            pointRadius: 0,
            borderWidth: 2
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { mode: "index", intersect: false },
        plugins: {
          legend: {
            labels: { color: "#8b9bb4", boxWidth: 12, font: { size: 11 } }
          },
          tooltip: {
            backgroundColor: "#1a2332",
            titleColor: "#e8edf5",
            bodyColor: "#e8edf5",
            borderColor: "#2d3a4f",
            borderWidth: 1
          }
        },
        scales: {
          x: {
            grid: { color: "rgba(45,58,79,0.4)" },
            ticks: { color: "#8b9bb4", maxTicksLimit: 15, font: { size: 10 } }
          },
          y: {
            type: "linear",
            position: "left",
            title: { display: true, text: "Charge-Off %", color: "#f87171", font: { size: 11 } },
            grid: { color: "rgba(45,58,79,0.4)" },
            ticks: { color: "#f87171", font: { size: 10 } }
          },
          y1: {
            type: "linear",
            position: "right",
            title: { display: true, text: "Origination $B", color: "#34d399", font: { size: 11 } },
            grid: { drawOnChartArea: false },
            ticks: { color: "#34d399", font: { size: 10 } }
          }
        }
      }
    });
  } catch (e) {
    console.error(e);
    toast("Failed to load industry history", "error");
  }
}

// --------------- Dashboard load ---------------
async function loadDashboard() {
  try {
    dashboardData = await api("/api/dashboard");
    const d = dashboardData;

    // Observation
    if (d.observations && d.observations.length) {
      $("#obsText").textContent = d.observations[0].content;
    }

    // NII
    if (d.nii_projections && d.nii_projections.length) {
      const labels = d.nii_projections.map(p => p.period);
      const values = d.nii_projections.map(p => p.projected_nii);
      initNIIChart(labels, values);
      $("#niiStart").textContent = `$${values[0]}M`;
      $("#niiEnd").textContent = `$${values[values.length - 1]}M`;
      const lastPeriod = d.nii_projections[d.nii_projections.length - 1].period;
      $("#niiEndLabel").innerHTML = `${lastPeriod} → <strong id="niiEnd">$${values[values.length - 1]}M</strong>`;
    }

    // Radar
    if (d.radar && d.radar.base && d.radar.stress) {
      initRadarChart(d.radar.base.values, d.radar.stress.values);
    }

    // ROA / RA
    if (d.latest_metrics) {
      $("#roaBase").textContent = (d.latest_metrics.roa || 0.87).toFixed(2) + "%";
    }
    // Default stress values from original UI spirit
    $("#roaStress").textContent = "0.89%";
    $("#raBase").textContent = "4.09%";
    $("#raStress").textContent = "5.05%";

    // KPI grid
    const kpis = [
      { label: "NIM", val: (d.latest_metrics?.nim || 3.45) + "%" },
      { label: "Efficiency", val: (d.latest_metrics?.efficiency_ratio || 62.1) + "%" },
      { label: "Capital Ratio", val: (d.latest_metrics?.capital_ratio || 12.5) + "%" },
      { label: "Charge-Off", val: (d.latest_metrics?.charge_off_rate || 0.48) + "%" }
    ];
    $("#kpiGrid").innerHTML = kpis.map(k => `
      <div class="kpi-card">
        <div class="kpi-label">${k.label}</div>
        <div class="kpi-val">${k.val}</div>
      </div>
    `).join("");

    // Scenario params
    if (d.scenario) {
      $("#sliderHorizon").value = d.scenario.horizon_months;
      $("#valHorizon").textContent = d.scenario.horizon_months;
      $("#sliderRate").value = d.scenario.rate_change_bp;
      $("#valRate").textContent = d.scenario.rate_change_bp;
      $("#sliderNCO").value = d.scenario.net_charge_off_rate;
      $("#valNCO").textContent = d.scenario.net_charge_off_rate;
      $("#stressParamsDisplay").innerHTML =
        `Rate Change: <strong>${d.scenario.rate_change_bp} bp</strong> · Net Charge Off: <strong>${d.scenario.net_charge_off_rate}%</strong>`;
    }

  } catch (e) {
    console.error(e);
    toast("Failed to load dashboard data", "error");
  }
}

// --------------- Stress run ---------------
async function runStress(fromLab = false) {
  const horizon = fromLab ? +$("#labHorizon").value : +$("#sliderHorizon").value;
  const rate = fromLab ? +$("#labRate").value : +$("#sliderRate").value;
  const nco = fromLab ? +$("#labNCO").value : +$("#sliderNCO").value;

  try {
    const result = await api("/api/stress", {
      method: "POST",
      body: JSON.stringify({
        horizon_months: horizon,
        rate_change_bp: rate,
        net_charge_off_rate: nco
      })
    });

    // Update NII chart
    const labels = result.nii_projections.map(p => p.period);
    const values = result.nii_projections.map(p => p.projected_nii);
    initNIIChart(labels, values);
    $("#niiStart").textContent = `$${result.summary.base_nii}M`;
    $("#niiEnd").textContent = `$${result.summary.final_nii}M`;
    const lastP = result.nii_projections[result.nii_projections.length - 1].period;
    $("#niiEndLabel").innerHTML = `${lastP} → <strong id="niiEnd">$${result.summary.final_nii}M</strong>`;

    // Radar
    if (result.radar_stress && dashboardData?.radar?.base) {
      initRadarChart(dashboardData.radar.base.values, result.radar_stress);
    }

    // Summary numbers
    $("#roaBase").textContent = result.summary.base_roa.toFixed(2) + "%";
    $("#roaStress").textContent = result.summary.stress_roa.toFixed(2) + "%";
    const roaDelta = result.summary.roa_change;
    $("#roaTrend").textContent = roaDelta >= 0
      ? `Trending better ▲ ${Math.abs(roaDelta).toFixed(2)}%`
      : `Trending worse ▼ ${Math.abs(roaDelta).toFixed(2)}%`;
    $("#roaTrend").className = "trend " + (roaDelta >= 0 ? "better" : "worse");

    $("#raBase").textContent = result.summary.ra_yoea_base.toFixed(2) + "%";
    $("#raStress").textContent = result.summary.ra_yoea_stress.toFixed(2) + "%";
    const raDelta = result.summary.ra_yoea_delta;
    $("#raTrend").textContent = raDelta >= 0
      ? `Trending better ▲ ${Math.abs(raDelta).toFixed(2)}%`
      : `Trending worse ▼ ${Math.abs(raDelta).toFixed(2)}%`;
    $("#raTrend").className = "trend " + (raDelta >= 0 ? "better" : "worse");

    $("#stressParamsDisplay").innerHTML =
      `Rate Change: <strong>${rate} bp</strong> · Net Charge Off: <strong>${nco}%</strong>`;

    // Observation banner
    $("#obsText").textContent = result.observation;

    // Lab result panel
    if (fromLab) {
      $("#labResult").innerHTML = `
        <div class="result-row"><span>Base NII</span><strong>$${result.summary.base_nii}M</strong></div>
        <div class="result-row"><span>Projected NII (end)</span><strong>$${result.summary.final_nii}M</strong></div>
        <div class="result-row"><span>Base ROA</span><strong>${result.summary.base_roa}%</strong></div>
        <div class="result-row"><span>Stressed ROA</span><strong>${result.summary.stress_roa}%</strong></div>
        <div class="result-row"><span>RA-YOEA change</span><strong>${result.summary.ra_yoea_delta > 0 ? "+" : ""}${result.summary.ra_yoea_delta}%</strong></div>
        <p style="margin-top:1rem;color:var(--text-muted);font-size:0.85rem">${result.observation}</p>
      `;
    }

    toast("Stress scenario calculated");
  } catch (e) {
    console.error(e);
    toast("Stress run failed", "error");
  }
}

// --------------- Save scenario ---------------
async function saveScenario() {
  const horizon = +$("#sliderHorizon").value;
  const rate = +$("#sliderRate").value;
  const nco = +$("#sliderNCO").value;
  try {
    const res = await api("/api/save-scenario", {
      method: "POST",
      body: JSON.stringify({
        name: `Stress ${rate}bp / ${nco}% / ${horizon}m`,
        horizon_months: horizon,
        rate_change_bp: rate,
        net_charge_off_rate: nco
      })
    });
    toast(`Scenario saved: ${res.name}`);
    loadScenarios();
  } catch (e) {
    toast("Save failed", "error");
  }
}

async function loadScenarios() {
  try {
    const list = await api("/api/scenarios");
    const ul = $("#scenarioList");
    if (!list.length) {
      ul.innerHTML = "<li>No saved scenarios yet</li>";
      return;
    }
    ul.innerHTML = list.map(s => `
      <li>
        <span>${s.name} <small style="color:var(--text-muted)">(${s.rate_change_bp}bp, ${s.net_charge_off_rate}%, ${s.horizon_months}m)</small></span>
        <button data-h="${s.horizon_months}" data-r="${s.rate_change_bp}" data-n="${s.net_charge_off_rate}">Load</button>
      </li>
    `).join("");
    ul.querySelectorAll("button").forEach(btn => {
      btn.addEventListener("click", () => {
        $("#sliderHorizon").value = btn.dataset.h;
        $("#valHorizon").textContent = btn.dataset.h;
        $("#labHorizon").value = btn.dataset.h;
        $("#sliderRate").value = btn.dataset.r;
        $("#valRate").textContent = btn.dataset.r;
        $("#labRate").value = btn.dataset.r;
        $("#sliderNCO").value = btn.dataset.n;
        $("#valNCO").textContent = btn.dataset.n;
        $("#labNCO").value = btn.dataset.n;
        runStress(true);
      });
    });
  } catch (e) {
    console.error(e);
  }
}

// --------------- Peers ---------------
function renderPeers() {
  if (!dashboardData || !dashboardData.peer_comparisons) return;
  const tbody = $("#peerTable tbody");
  tbody.innerHTML = dashboardData.peer_comparisons.map(p => {
    const diffClass = p.difference >= 0 ? "diff-pos" : "diff-neg";
    const sign = p.difference >= 0 ? "+" : "";
    return `
      <tr>
        <td>${p.metric}</td>
        <td>${p.institution}</td>
        <td>${p.peer_avg}</td>
        <td class="${diffClass}">${sign}${p.difference}</td>
      </tr>
    `;
  }).join("");

  $("#peerInsight").innerHTML = `
    <strong>Key takeaway:</strong> The credit union outperforms peers on ROA and NIM,
    while maintaining a better (lower) efficiency ratio. Capital position is also slightly stronger than the peer average.
  `;
}

// --------------- Modal ---------------
function setupModal() {
  $("#btnMoreObs").addEventListener("click", () => {
    const modal = $("#obsModal");
    const body = $("#modalBody");
    if (dashboardData?.observations) {
      body.innerHTML = dashboardData.observations.map(o => `
        <div class="modal-obs">
          <div class="cat">${o.category} · ${o.period || ""}</div>
          <strong>${o.title}</strong>
          <p style="margin-top:0.4rem;color:var(--text-muted)">${o.content}</p>
        </div>
      `).join("");
    }
    modal.classList.add("open");
  });
  $("#closeModal").addEventListener("click", () => $("#obsModal").classList.remove("open"));
  $("#obsModal").addEventListener("click", (e) => {
    if (e.target === $("#obsModal")) $("#obsModal").classList.remove("open");
  });
}

// --------------- Init ---------------
document.addEventListener("DOMContentLoaded", () => {
  setupNav();
  setupSliders();
  setupModal();

  $("#btnRunStress").addEventListener("click", () => runStress(false));
  $("#btnLabRun").addEventListener("click", () => runStress(true));
  $("#btnSaveScenario").addEventListener("click", saveScenario);
  $("#btnRefresh").addEventListener("click", () => {
    loadDashboard();
    toast("Data refreshed");
  });

  loadDashboard();
});
