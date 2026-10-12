from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Institution(db.Model):
    __tablename__ = "institutions"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    code = db.Column(db.String(50), unique=True)
    peer_group = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    metrics = db.relationship("FinancialMetric", backref="institution", lazy=True)
    radar = db.relationship("RadarMetric", backref="institution", lazy=True)
    scenarios = db.relationship("StressScenario", backref="institution", lazy=True)
    observations = db.relationship("Observation", backref="institution", lazy=True)

class FinancialMetric(db.Model):
    __tablename__ = "financial_metrics"
    id = db.Column(db.Integer, primary_key=True)
    institution_id = db.Column(db.Integer, db.ForeignKey("institutions.id"), nullable=False)
    period = db.Column(db.String(20), nullable=False)
    period_date = db.Column(db.Date, nullable=False)
    roa = db.Column(db.Numeric(8, 4))
    roe = db.Column(db.Numeric(8, 4))
    nim = db.Column(db.Numeric(8, 4))
    npl_ratio = db.Column(db.Numeric(8, 4))
    charge_off_rate = db.Column(db.Numeric(8, 4))
    capital_ratio = db.Column(db.Numeric(8, 4))
    liquidity_ratio = db.Column(db.Numeric(8, 4))
    efficiency_ratio = db.Column(db.Numeric(8, 4))
    net_interest_income = db.Column(db.Numeric(18, 2))
    total_assets = db.Column(db.Numeric(18, 2))
    loan_portfolio = db.Column(db.Numeric(18, 2))

class RadarMetric(db.Model):
    __tablename__ = "radar_metrics"
    id = db.Column(db.Integer, primary_key=True)
    institution_id = db.Column(db.Integer, db.ForeignKey("institutions.id"), nullable=False)
    period = db.Column(db.String(20), nullable=False)
    all_l = db.Column(db.Numeric(8, 4))
    bar = db.Column(db.Numeric(8, 4))
    dil = db.Column(db.Numeric(8, 4))
    nim = db.Column(db.Numeric(8, 4))
    cof = db.Column(db.Numeric(8, 4))
    yoea = db.Column(db.Numeric(8, 4))
    ldr = db.Column(db.Numeric(8, 4))
    er = db.Column(db.Numeric(8, 4))
    lr = db.Column(db.Numeric(8, 4))
    roa = db.Column(db.Numeric(8, 4))

class StressScenario(db.Model):
    __tablename__ = "stress_scenarios"
    id = db.Column(db.Integer, primary_key=True)
    institution_id = db.Column(db.Integer, db.ForeignKey("institutions.id"), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    horizon_months = db.Column(db.Integer, default=18)
    rate_change_bp = db.Column(db.Integer, default=500)
    net_charge_off_rate = db.Column(db.Numeric(6, 4), default=0.52)
    is_default = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    projections = db.relationship("NIIProjection", backref="scenario", lazy=True, cascade="all, delete-orphan")

class NIIProjection(db.Model):
    __tablename__ = "nii_projections"
    id = db.Column(db.Integer, primary_key=True)
    scenario_id = db.Column(db.Integer, db.ForeignKey("stress_scenarios.id"), nullable=False)
    period = db.Column(db.String(20), nullable=False)
    period_date = db.Column(db.Date, nullable=False)
    projected_nii = db.Column(db.Numeric(18, 2))

class IndustryHistory(db.Model):
    __tablename__ = "industry_history"
    id = db.Column(db.Integer, primary_key=True)
    year = db.Column(db.Integer, unique=True, nullable=False)
    charge_off_rate = db.Column(db.Numeric(8, 4))
    new_consumer_loan_origination = db.Column(db.Numeric(18, 2))

class PeerComparison(db.Model):
    __tablename__ = "peer_comparisons"
    id = db.Column(db.Integer, primary_key=True)
    institution_id = db.Column(db.Integer, db.ForeignKey("institutions.id"), nullable=False)
    period = db.Column(db.String(20), nullable=False)
    metric_name = db.Column(db.String(50), nullable=False)
    institution_value = db.Column(db.Numeric(12, 4))
    peer_avg_value = db.Column(db.Numeric(12, 4))
    difference = db.Column(db.Numeric(12, 4))

class Observation(db.Model):
    __tablename__ = "observations"
    id = db.Column(db.Integer, primary_key=True)
    institution_id = db.Column(db.Integer, db.ForeignKey("institutions.id"), nullable=False)
    period = db.Column(db.String(20))
    category = db.Column(db.String(50))
    title = db.Column(db.String(255))
    content = db.Column(db.Text)
    severity = db.Column(db.String(20), default="info")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(150))
    role = db.Column(db.String(50), default="analyst")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
