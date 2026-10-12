-- Financial Risk & Scenario Analysis Dashboard
-- MySQL Schema

CREATE DATABASE IF NOT EXISTS financial_risk CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE financial_risk;

-- Credit Unions / Institutions
CREATE TABLE institutions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    code VARCHAR(50) UNIQUE,
    peer_group VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Historical financial metrics (quarterly)
CREATE TABLE financial_metrics (
    id INT AUTO_INCREMENT PRIMARY KEY,
    institution_id INT NOT NULL,
    period VARCHAR(20) NOT NULL,          -- e.g. 'Q4 2023'
    period_date DATE NOT NULL,
    roa DECIMAL(8,4),                    -- Return on Assets %
    roe DECIMAL(8,4),
    nim DECIMAL(8,4),                    -- Net Interest Margin %
    npl_ratio DECIMAL(8,4),              -- Non-performing loans
    charge_off_rate DECIMAL(8,4),
    capital_ratio DECIMAL(8,4),
    liquidity_ratio DECIMAL(8,4),
    efficiency_ratio DECIMAL(8,4),
    net_interest_income DECIMAL(18,2),   -- in millions
    total_assets DECIMAL(18,2),
    loan_portfolio DECIMAL(18,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (institution_id) REFERENCES institutions(id),
    UNIQUE KEY uq_inst_period (institution_id, period)
);

-- Radar chart metrics (ALLL, BAR, DIL, NIM, COF, YOEA, LDR, ER, LR, ROA)
CREATE TABLE radar_metrics (
    id INT AUTO_INCREMENT PRIMARY KEY,
    institution_id INT NOT NULL,
    period VARCHAR(20) NOT NULL,
    all_l DECIMAL(8,4),   -- Allowance for Loan Losses
    bar DECIMAL(8,4),     -- something like Basel or risk metric
    dil DECIMAL(8,4),
    nim DECIMAL(8,4),
    cof DECIMAL(8,4),     -- Cost of Funds
    yoea DECIMAL(8,4),    -- Yield on Earning Assets
    ldr DECIMAL(8,4),     -- Loan to Deposit Ratio
    er DECIMAL(8,4),      -- Efficiency Ratio
    lr DECIMAL(8,4),      -- Liquidity Ratio
    roa DECIMAL(8,4),
    FOREIGN KEY (institution_id) REFERENCES institutions(id),
    UNIQUE KEY uq_radar (institution_id, period)
);

-- Stress scenario parameters (saved scenarios)
CREATE TABLE stress_scenarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    institution_id INT NOT NULL,
    name VARCHAR(100) NOT NULL,
    horizon_months INT DEFAULT 18,
    rate_change_bp INT DEFAULT 500,
    net_charge_off_rate DECIMAL(6,4) DEFAULT 0.52,
    is_default BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (institution_id) REFERENCES institutions(id)
);

-- Projected Net Interest Income under stress
CREATE TABLE nii_projections (
    id INT AUTO_INCREMENT PRIMARY KEY,
    scenario_id INT NOT NULL,
    period VARCHAR(20) NOT NULL,
    period_date DATE NOT NULL,
    projected_nii DECIMAL(18,2),
    FOREIGN KEY (scenario_id) REFERENCES stress_scenarios(id) ON DELETE CASCADE
);

-- Historical industry data (charge-off rates & loan origination)
CREATE TABLE industry_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    year INT NOT NULL,
    charge_off_rate DECIMAL(8,4),        -- percent
    new_consumer_loan_origination DECIMAL(18,2), -- billions USD
    UNIQUE KEY uq_year (year)
);

-- Peer group comparison
CREATE TABLE peer_comparisons (
    id INT AUTO_INCREMENT PRIMARY KEY,
    institution_id INT NOT NULL,
    period VARCHAR(20) NOT NULL,
    metric_name VARCHAR(50) NOT NULL,
    institution_value DECIMAL(12,4),
    peer_avg_value DECIMAL(12,4),
    difference DECIMAL(12,4),
    FOREIGN KEY (institution_id) REFERENCES institutions(id)
);

-- Observations / insights generated
CREATE TABLE observations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    institution_id INT NOT NULL,
    period VARCHAR(20),
    category VARCHAR(50),
    title VARCHAR(255),
    content TEXT,
    severity ENUM('info','warning','critical') DEFAULT 'info',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (institution_id) REFERENCES institutions(id)
);

-- Users for simple auth (optional demo)
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(80) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(150),
    role VARCHAR(50) DEFAULT 'analyst',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert sample institution
INSERT INTO institutions (name, code, peer_group) VALUES
('Idaho Central Credit Union', 'ICCU', 'Mid-size Credit Unions'),
('Sample Peer Average', 'PEER', 'Mid-size Credit Unions');

-- Sample financial metrics
INSERT INTO financial_metrics (institution_id, period, period_date, roa, roe, nim, npl_ratio, charge_off_rate, capital_ratio, liquidity_ratio, efficiency_ratio, net_interest_income, total_assets, loan_portfolio) VALUES
(1, 'Q4 2023', '2023-12-31', 0.87, 9.2, 3.45, 0.62, 0.48, 12.5, 18.2, 62.1, 242.6, 8500.0, 6200.0),
(1, 'Q1 2024', '2024-03-31', 0.89, 9.4, 3.48, 0.58, 0.45, 12.6, 18.5, 61.8, 248.2, 8650.0, 6320.0),
(1, 'Q2 2024', '2024-06-30', 0.91, 9.6, 3.52, 0.55, 0.42, 12.8, 18.9, 61.2, 255.1, 8800.0, 6450.0);

-- Radar metrics Q4 2023
INSERT INTO radar_metrics (institution_id, period, all_l, bar, dil, nim, cof, yoea, ldr, er, lr, roa) VALUES
(1, 'Q4 2023', 1.25, 2.1, 0.85, 3.45, 1.8, 5.25, 78.5, 62.1, 18.2, 0.87),
(1, 'Q2 2025 Stress', 1.45, 2.4, 1.05, 3.10, 2.3, 5.40, 82.0, 65.5, 16.8, 0.89);

-- Default stress scenario
INSERT INTO stress_scenarios (institution_id, name, horizon_months, rate_change_bp, net_charge_off_rate, is_default) VALUES
(1, 'Base Stress Scenario', 18, 500, 0.52, TRUE);

-- NII projections under stress (18 months)
INSERT INTO nii_projections (scenario_id, period, period_date, projected_nii) VALUES
(1, 'Q4 2023', '2023-12-31', 242.6),
(1, 'Q1 2024', '2024-03-31', 248.0),
(1, 'Q2 2024', '2024-06-30', 252.5),
(1, 'Q3 2024', '2024-09-30', 255.8),
(1, 'Q4 2024', '2024-12-31', 258.2),
(1, 'Q1 2025', '2025-03-31', 261.0),
(1, 'Q2 2025', '2025-06-30', 266.3);

-- Industry history (simplified from chart)
INSERT INTO industry_history (year, charge_off_rate, new_consumer_loan_origination) VALUES
(1974, 0.35, 50), (1975, 0.40, 55), (1976, 0.38, 60), (1977, 0.42, 70),
(1978, 0.45, 80), (1979, 0.50, 90), (1980, 0.65, 95), (1981, 0.80, 100),
(1982, 1.10, 105), (1983, 1.30, 110), (1984, 1.20, 120), (1985, 1.40, 130),
(1986, 1.50, 140), (1987, 1.60, 150), (1988, 1.55, 160), (1989, 1.70, 170),
(1990, 1.90, 180), (1991, 1.80, 175), (1992, 1.40, 180), (1993, 1.20, 190),
(1994, 1.10, 200), (1995, 1.00, 220), (1996, 0.95, 240), (1997, 0.90, 260),
(1998, 0.85, 280), (1999, 0.80, 300), (2000, 0.75, 320), (2001, 0.90, 340),
(2002, 1.00, 360), (2003, 0.95, 400), (2004, 0.85, 450), (2005, 0.80, 500),
(2006, 0.75, 550), (2007, 0.90, 600), (2008, 1.80, 650), (2009, 2.80, 700),
(2010, 2.90, 750), (2011, 1.80, 800), (2012, 1.20, 850), (2013, 0.90, 900),
(2014, 0.70, 950), (2015, 0.60, 1000), (2016, 0.55, 1100), (2017, 0.50, 1200),
(2018, 0.48, 1300), (2019, 0.52, 1400), (2020, 0.65, 1500), (2021, 0.45, 1600),
(2022, 0.55, 1700), (2023, 0.60, 1800);

-- Peer comparisons
INSERT INTO peer_comparisons (institution_id, period, metric_name, institution_value, peer_avg_value, difference) VALUES
(1, 'Q4 2023', 'ROA', 0.87, 0.72, 0.15),
(1, 'Q4 2023', 'NIM', 3.45, 3.20, 0.25),
(1, 'Q4 2023', 'Efficiency Ratio', 62.1, 68.5, -6.4),
(1, 'Q4 2023', 'Capital Ratio', 12.5, 11.8, 0.7);

-- Observations
INSERT INTO observations (institution_id, period, category, title, content, severity) VALUES
(1, 'Q4 2023', 'PERFORMANCE', 'PERFORMANCE v. PEER GROUP',
 'The credit union has a higher ROA (Return on Assets) than its peer group, indicating that it is more profitable. However, the credit union has a lower efficiency ratio which signals room for operational improvement under stress.',
 'info'),
(1, 'Q2 2025', 'STRESS', 'Stress Scenario Impact',
 'Under a 500 bp rate shock and elevated charge-off rate of 0.52%, projected Net Interest Income still grows modestly to $266.3M by Q2 2025, showing resilience.',
 'warning');

-- Demo user (password: admin123 - bcrypt hash will be generated in app)
INSERT INTO users (username, password_hash, full_name, role) VALUES
('admin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.G2oYqKzqKzqKzq', 'Boris Fuzayloff', 'analyst');
