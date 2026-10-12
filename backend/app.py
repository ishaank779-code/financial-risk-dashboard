"""
Financial Risk & Scenario Analysis Dashboard
Backend - Flask + MySQL
"""
from flask import Flask, jsonify, request, send_from_directory, render_template
from flask_cors import CORS
from config import Config
from models import (
    db, Institution, FinancialMetric, RadarMetric, StressScenario,
    NIIProjection, IndustryHistory, PeerComparison, Observation
)
from datetime import datetime, timedelta
from decimal import Decimal
import os

# Paths
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")
TEMPLATE_DIR = os.path.join(FRONTEND_DIR, "templates")
STATIC_DIR = os.path.join(FRONTEND_DIR, "static")

app = Flask(
    __name__,
    template_folder=TEMPLATE_DIR,
    static_folder=STATIC_DIR,
    static_url_path="/static"
)
app.config.from_object(Config)
CORS(app)
db.init_app(app)


# --------------- Helpers ---------------
def to_float(val):
    if val is None:
        return None
    return float(val)


def generate_stress_projection(base_nii, horizon_months, rate_change_bp, nco_rate):
    """
    Simple but realistic stress model:
    - Higher rate shock (rate_change_bp) can increase NII short-term (asset sensitivity)
      but also pressure funding costs.
    - Higher net charge-off rate reduces NII via credit losses.
    Returns list of (period_label, date, projected_nii)
    """
    projections = []
    current = Decimal(str(base_nii))
    start = datetime(2023, 12, 31)

    # Impact factors
    rate_impact = Decimal(str(rate_change_bp)) / Decimal("10000") * Decimal("0.35")  # partial pass-through
    credit_drag = Decimal(str(nco_rate)) / Decimal("100") * Decimal("12")  # annualized drag approx

    quarters = max(1, horizon_months // 3)
    for i in range(quarters + 1):
        q_date = start + timedelta(days=90 * i)
        year = q_date.year
        q = (q_date.month - 1) // 3 + 1
        label = f"Q{q} {year}"

        if i == 0:
            proj = current
        else:
            # Growth + rate benefit - credit losses
            growth = Decimal("0.015") + rate_impact * Decimal("0.4") - credit_drag * Decimal("0.08")
            current = current * (Decimal("1") + growth)
            proj = current

        projections.append({
            "period": label,
            "period_date": q_date.strftime("%Y-%m-%d"),
            "projected_nii": round(float(proj), 1)
        })
    return projections


def compute_radar_stress(base_radar, rate_change_bp, nco_rate):
    """Adjust radar metrics under stress."""
    factor = 1 + (rate_change_bp / 10000) * 0.15
    credit = 1 + (nco_rate / 100) * 0.8
    return {
        "all_l": round(to_float(base_radar.all_l) * credit, 2),
        "bar": round(to_float(base_radar.bar) * factor, 2),
        "dil": round(to_float(base_radar.dil) * credit, 2),
        "nim": round(to_float(base_radar.nim) * (1 - (rate_change_bp / 10000) * 0.1), 2),
        "cof": round(to_float(base_radar.cof) * factor, 2),
        "yoea": round(to_float(base_radar.yoea) * (1 + (rate_change_bp / 10000) * 0.12), 2),
        "ldr": round(to_float(base_radar.ldr) * 1.04, 1),
        "er": round(to_float(base_radar.er) * 1.05, 1),
        "lr": round(to_float(base_radar.lr) * 0.92, 1),
        "roa": round(to_float(base_radar.roa) * (1 - (nco_rate / 100) * 0.3 + (rate_change_bp / 10000) * 0.05), 2),
    }


# --------------- API Routes ---------------

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/health")
def health():
    return jsonify({"status": "ok", "service": "Financial Risk Dashboard", "db": "connected"})


@app.route("/api/institution")
def get_institution():
    inst = Institution.query.filter_by(code="ICCU").first()
    if not inst:
        return jsonify({"error": "Institution not found"}), 404
    return jsonify({
        "id": inst.id,
        "name": inst.name,
        "code": inst.code,
        "peer_group": inst.peer_group
    })


@app.route("/api/dashboard")
def dashboard_data():
    """Main dashboard payload."""
    inst = Institution.query.filter_by(code="ICCU").first()
    if not inst:
        return jsonify({"error": "No data"}), 404

    # Latest metrics
    metrics = FinancialMetric.query.filter_by(institution_id=inst.id).order_by(
        FinancialMetric.period_date.desc()
    ).all()
    latest = metrics[0] if metrics else None

    # Radar
    radar_base = RadarMetric.query.filter_by(institution_id=inst.id, period="Q4 2023").first()
    radar_stress = RadarMetric.query.filter_by(institution_id=inst.id, period="Q2 2025 Stress").first()

    # Default scenario
    scenario = StressScenario.query.filter_by(institution_id=inst.id, is_default=True).first()
    projections = []
    if scenario:
        projections = [
            {
                "period": p.period,
                "period_date": p.period_date.isoformat() if p.period_date else None,
                "projected_nii": to_float(p.projected_nii)
            }
            for p in sorted(scenario.projections, key=lambda x: x.period_date or datetime.min)
        ]

    # Observations
    obs = Observation.query.filter_by(institution_id=inst.id).order_by(Observation.id).all()

    # Peer
    peers = PeerComparison.query.filter_by(institution_id=inst.id).all()

    return jsonify({
        "institution": {
            "id": inst.id,
            "name": inst.name,
            "code": inst.code,
            "peer_group": inst.peer_group
        },
        "latest_metrics": {
            "period": latest.period if latest else None,
            "roa": to_float(latest.roa) if latest else None,
            "roe": to_float(latest.roe) if latest else None,
            "nim": to_float(latest.nim) if latest else None,
            "net_interest_income": to_float(latest.net_interest_income) if latest else None,
            "charge_off_rate": to_float(latest.charge_off_rate) if latest else None,
            "efficiency_ratio": to_float(latest.efficiency_ratio) if latest else None,
            "capital_ratio": to_float(latest.capital_ratio) if latest else None,
        } if latest else {},
        "radar": {
            "base": {
                "period": radar_base.period,
                "values": {
                    "ALLL": to_float(radar_base.all_l),
                    "BAR": to_float(radar_base.bar),
                    "DIL": to_float(radar_base.dil),
                    "NIM": to_float(radar_base.nim),
                    "COF": to_float(radar_base.cof),
                    "YOEA": to_float(radar_base.yoea),
                    "LDR": to_float(radar_base.ldr),
                    "ER": to_float(radar_base.er),
                    "LR": to_float(radar_base.lr),
                    "ROA": to_float(radar_base.roa),
                }
            } if radar_base else None,
            "stress": {
                "period": radar_stress.period,
                "values": {
                    "ALLL": to_float(radar_stress.all_l),
                    "BAR": to_float(radar_stress.bar),
                    "DIL": to_float(radar_stress.dil),
                    "NIM": to_float(radar_stress.nim),
                    "COF": to_float(radar_stress.cof),
                    "YOEA": to_float(radar_stress.yoea),
                    "LDR": to_float(radar_stress.ldr),
                    "ER": to_float(radar_stress.er),
                    "LR": to_float(radar_stress.lr),
                    "ROA": to_float(radar_stress.roa),
                }
            } if radar_stress else None,
        },
        "scenario": {
            "id": scenario.id if scenario else None,
            "name": scenario.name if scenario else "Base Stress",
            "horizon_months": scenario.horizon_months if scenario else 18,
            "rate_change_bp": scenario.rate_change_bp if scenario else 500,
            "net_charge_off_rate": to_float(scenario.net_charge_off_rate) if scenario else 0.52,
        },
        "nii_projections": projections,
        "observations": [
            {
                "id": o.id,
                "category": o.category,
                "title": o.title,
                "content": o.content,
                "severity": o.severity,
                "period": o.period
            } for o in obs
        ],
        "peer_comparisons": [
            {
                "metric": p.metric_name,
                "institution": to_float(p.institution_value),
                "peer_avg": to_float(p.peer_avg_value),
                "difference": to_float(p.difference)
            } for p in peers
        ]
    })


@app.route("/api/stress", methods=["POST"])
def run_stress():
    """Run stress scenario with user parameters and return updated projections + radar."""
    data = request.get_json() or {}
    horizon = int(data.get("horizon_months", 18))
    rate_bp = int(data.get("rate_change_bp", 500))
    nco = float(data.get("net_charge_off_rate", 0.52))

    # Clamp values
    horizon = max(3, min(36, horizon))
    rate_bp = max(0, min(1000, rate_bp))
    nco = max(0.1, min(5.0, nco))

    inst = Institution.query.filter_by(code="ICCU").first()
    base_metric = FinancialMetric.query.filter_by(institution_id=inst.id, period="Q4 2023").first()
    base_radar = RadarMetric.query.filter_by(institution_id=inst.id, period="Q4 2023").first()

    base_nii = to_float(base_metric.net_interest_income) if base_metric else 242.6

    projections = generate_stress_projection(base_nii, horizon, rate_bp, nco)
    stressed_radar = compute_radar_stress(base_radar, rate_bp, nco) if base_radar else {}

    # RA-YOEA improvement / change
    base_roa = to_float(base_radar.roa) if base_radar else 0.87
    stress_roa = stressed_radar.get("ROA", base_roa)
    ra_yoea_base = 4.09  # illustrative from original UI
    ra_yoea_stress = round(ra_yoea_base + (stress_roa - base_roa) * 2 + (rate_bp / 1000) * 0.3, 2)

    return jsonify({
        "parameters": {
            "horizon_months": horizon,
            "rate_change_bp": rate_bp,
            "net_charge_off_rate": nco
        },
        "nii_projections": projections,
        "radar_stress": stressed_radar,
        "summary": {
            "base_nii": base_nii,
            "final_nii": projections[-1]["projected_nii"] if projections else base_nii,
            "base_roa": base_roa,
            "stress_roa": stress_roa,
            "roa_change": round(stress_roa - base_roa, 2),
            "ra_yoea_base": ra_yoea_base,
            "ra_yoea_stress": ra_yoea_stress,
            "ra_yoea_delta": round(ra_yoea_stress - ra_yoea_base, 2)
        },
        "observation": (
            f"Under a {rate_bp} bp rate shock and net charge-off rate of {nco}%, "
            f"projected Net Interest Income moves from ${base_nii}M to "
            f"${projections[-1]['projected_nii']}M over {horizon} months. "
            f"ROA shifts from {base_roa}% to {stress_roa}%."
        )
    })


@app.route("/api/industry-history")
def industry_history():
    rows = IndustryHistory.query.order_by(IndustryHistory.year).all()
    return jsonify([
        {
            "year": r.year,
            "charge_off_rate": to_float(r.charge_off_rate),
            "loan_origination": to_float(r.new_consumer_loan_origination)
        } for r in rows
    ])


@app.route("/api/metrics/history")
def metrics_history():
    inst = Institution.query.filter_by(code="ICCU").first()
    rows = FinancialMetric.query.filter_by(institution_id=inst.id).order_by(
        FinancialMetric.period_date
    ).all()
    return jsonify([
        {
            "period": r.period,
            "roa": to_float(r.roa),
            "nim": to_float(r.nim),
            "nii": to_float(r.net_interest_income),
            "charge_off": to_float(r.charge_off_rate)
        } for r in rows
    ])


@app.route("/api/save-scenario", methods=["POST"])
def save_scenario():
    data = request.get_json() or {}
    inst = Institution.query.filter_by(code="ICCU").first()
    name = data.get("name", f"Custom Scenario {datetime.now().strftime('%Y%m%d-%H%M')}")
    horizon = int(data.get("horizon_months", 18))
    rate_bp = int(data.get("rate_change_bp", 500))
    nco = float(data.get("net_charge_off_rate", 0.52))

    scenario = StressScenario(
        institution_id=inst.id,
        name=name,
        horizon_months=horizon,
        rate_change_bp=rate_bp,
        net_charge_off_rate=nco,
        is_default=False
    )
    db.session.add(scenario)
    db.session.flush()

    base_metric = FinancialMetric.query.filter_by(institution_id=inst.id, period="Q4 2023").first()
    base_nii = to_float(base_metric.net_interest_income) if base_metric else 242.6
    projections = generate_stress_projection(base_nii, horizon, rate_bp, nco)

    for p in projections:
        proj = NIIProjection(
            scenario_id=scenario.id,
            period=p["period"],
            period_date=datetime.strptime(p["period_date"], "%Y-%m-%d").date(),
            projected_nii=p["projected_nii"]
        )
        db.session.add(proj)

    db.session.commit()
    return jsonify({"success": True, "scenario_id": scenario.id, "name": name})


@app.route("/api/scenarios")
def list_scenarios():
    inst = Institution.query.filter_by(code="ICCU").first()
    scenarios = StressScenario.query.filter_by(institution_id=inst.id).order_by(
        StressScenario.created_at.desc()
    ).all()
    return jsonify([
        {
            "id": s.id,
            "name": s.name,
            "horizon_months": s.horizon_months,
            "rate_change_bp": s.rate_change_bp,
            "net_charge_off_rate": to_float(s.net_charge_off_rate),
            "is_default": s.is_default
        } for s in scenarios
    ])


# --------------- Run ---------------
if __name__ == "__main__":
    with app.app_context():
        # Ensure tables exist (safe if already created via schema.sql)
        db.create_all()
    app.run(host="0.0.0.0", port=5000, debug=True)
