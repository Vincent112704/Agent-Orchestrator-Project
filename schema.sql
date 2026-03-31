-- ============================================================
-- Personalization Orchestrator Database Schema (SQLite)
-- ============================================================

-- Drop existing tables (if needed)
DROP TABLE IF EXISTS inventory_audit;
DROP TABLE IF EXISTS recommendation_logs;
DROP TABLE IF EXISTS orchestration_decisions;
DROP TABLE IF EXISTS customer_events;
DROP TABLE IF EXISTS budget_tracker;
DROP TABLE IF EXISTS customer_products;
DROP TABLE IF EXISTS customer_affinities;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS customers;
DROP TABLE IF EXISTS users;

-- ============================================================
-- 1. USERS TABLE
-- ============================================================
CREATE TABLE users (
    user_id TEXT PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    is_active BOOLEAN DEFAULT 1,
    last_login TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_is_active ON users(is_active);
CREATE INDEX idx_users_created_at ON users(created_at);

-- ============================================================
-- 2. CUSTOMERS TABLE
-- ============================================================
CREATE TABLE customers (
    customer_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL UNIQUE,
    segment TEXT NOT NULL DEFAULT 'new',
    web_engagement REAL DEFAULT 0.5,
    mobile_engagement REAL DEFAULT 0.5,
    email_engagement REAL DEFAULT 0.5,
    email_unsubscribed BOOLEAN DEFAULT 0,
    email_frequency_max_per_week INTEGER DEFAULT 3,
    email_last_sent_at TIMESTAMP NULL,
    recency_days INTEGER DEFAULT 999,
    frequency INTEGER DEFAULT 0,
    frequency_period TEXT DEFAULT '90_days',
    monetary REAL DEFAULT 0.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    CHECK (segment IN ('new', 'at_risk', 'loyal', 'high_value', 'vip'))
);

CREATE INDEX idx_customers_user_id ON customers(user_id);
CREATE INDEX idx_customers_segment ON customers(segment);
CREATE INDEX idx_customers_monetary ON customers(monetary);
CREATE INDEX idx_customers_recency ON customers(recency_days);
CREATE INDEX idx_customers_created_at ON customers(created_at);

-- ============================================================
-- 3. CUSTOMER_AFFINITIES TABLE
-- ============================================================
CREATE TABLE customer_affinities (
    affinity_id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id TEXT NOT NULL,
    category TEXT NOT NULL,
    affinity_score REAL NOT NULL,
    updated_reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE CASCADE,
    UNIQUE (customer_id, category)
);

CREATE INDEX idx_affinities_customer_id ON customer_affinities(customer_id);
CREATE INDEX idx_affinities_category ON customer_affinities(category);
CREATE INDEX idx_affinities_score ON customer_affinities(affinity_score);

-- ============================================================
-- 4. PRODUCTS TABLE
-- ============================================================
CREATE TABLE products (
    product_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    price REAL NOT NULL,
    inventory INTEGER NOT NULL DEFAULT 0,
    rating REAL DEFAULT 0.0,
    description TEXT,
    image_url TEXT,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_products_category ON products(category);
CREATE INDEX idx_products_name ON products(name);
CREATE INDEX idx_products_inventory ON products(inventory);
CREATE INDEX idx_products_is_active ON products(is_active);
CREATE INDEX idx_products_created_at ON products(created_at);

-- ============================================================
-- 5. CUSTOMER_PRODUCTS TABLE
-- ============================================================
CREATE TABLE customer_products (
    customer_product_id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id TEXT NOT NULL,
    product_id TEXT NOT NULL,
    interaction_type TEXT NOT NULL,
    interaction_count INTEGER DEFAULT 1,
    last_interaction_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE CASCADE,
    CHECK (interaction_type IN (
        'view', 'click', 'add_to_cart', 'purchase', 'wishlist', 
        'email_open', 'email_click', 'recommendation_shown'
    ))
);

CREATE INDEX idx_customer_products_customer ON customer_products(customer_id);
CREATE INDEX idx_customer_products_product ON customer_products(product_id);
CREATE INDEX idx_customer_products_interaction ON customer_products(interaction_type);
CREATE INDEX idx_customer_products_last_interaction ON customer_products(last_interaction_at);
CREATE INDEX idx_customer_products_composite ON customer_products(customer_id, product_id, interaction_type);

-- ============================================================
-- 6. ORCHESTRATION_DECISIONS TABLE
-- ============================================================
CREATE TABLE orchestration_decisions (
    decision_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    channel TEXT NOT NULL,
    consistency_score REAL NOT NULL,
    latency_ms INTEGER NOT NULL,
    constraint_violations TEXT,
    reasoning TEXT NOT NULL,
    lsmith_trace_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE CASCADE,
    CHECK (channel IN ('web', 'mobile', 'email', 'multi_channel'))
);

CREATE INDEX idx_orchestration_customer ON orchestration_decisions(customer_id);
CREATE INDEX idx_orchestration_channel ON orchestration_decisions(channel);
CREATE INDEX idx_orchestration_timestamp ON orchestration_decisions(timestamp);
CREATE INDEX idx_orchestration_consistency ON orchestration_decisions(consistency_score);
CREATE INDEX idx_orchestration_created ON orchestration_decisions(created_at);
CREATE INDEX idx_orchestration_customer_timestamp ON orchestration_decisions(customer_id, timestamp);

-- ============================================================
-- 7. RECOMMENDATION_LOGS TABLE
-- ============================================================
CREATE TABLE recommendation_logs (
    recommendation_id INTEGER PRIMARY KEY AUTOINCREMENT,
    decision_id TEXT NOT NULL,
    channel TEXT NOT NULL,
    product_id TEXT,
    confidence REAL NOT NULL,
    reasoning TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'approved',
    status_reason TEXT,
    shown_to_customer BOOLEAN DEFAULT 0,
    shown_at TIMESTAMP NULL,
    customer_interaction TEXT,
    interaction_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (decision_id) REFERENCES orchestration_decisions(decision_id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE SET NULL,
    CHECK (status IN ('approved', 'modified', 'denied', 'fallback')),
    CHECK (customer_interaction IN ('click', 'purchase', 'ignore', 'dismiss', NULL))
);

CREATE INDEX idx_recommendation_decision ON recommendation_logs(decision_id);
CREATE INDEX idx_recommendation_channel ON recommendation_logs(channel);
CREATE INDEX idx_recommendation_product ON recommendation_logs(product_id);
CREATE INDEX idx_recommendation_status ON recommendation_logs(status);
CREATE INDEX idx_recommendation_interaction ON recommendation_logs(customer_interaction);

-- ============================================================
-- 8. CUSTOMER_EVENTS TABLE
-- ============================================================
CREATE TABLE customer_events (
    event_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    channel TEXT,
    product_id TEXT,
    event_data TEXT,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE SET NULL,
    CHECK (event_type IN (
        'page_view', 'product_view', 'click', 'add_to_cart', 
        'purchase', 'email_open', 'email_click', 'app_open', 
        'app_tap', 'notification_click', 'wishlist_add'
    ))
);

CREATE INDEX idx_events_customer ON customer_events(customer_id);
CREATE INDEX idx_events_event_type ON customer_events(event_type);
CREATE INDEX idx_events_timestamp ON customer_events(timestamp);
CREATE INDEX idx_events_channel ON customer_events(channel);
CREATE INDEX idx_events_customer_timestamp ON customer_events(customer_id, timestamp);

-- ============================================================
-- 9. BUDGET_TRACKER TABLE
-- ============================================================
CREATE TABLE budget_tracker (
    budget_id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE NOT NULL UNIQUE,
    daily_limit REAL NOT NULL DEFAULT 1000.00,
    spent_today REAL NOT NULL DEFAULT 0.00,
    remaining REAL NOT NULL DEFAULT 1000.00,
    num_emails_sent INTEGER NOT NULL DEFAULT 0,
    max_emails_per_day INTEGER DEFAULT 6666,
    cost_per_email REAL DEFAULT 0.15,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_budget_date ON budget_tracker(date);

-- ============================================================
-- 10. INVENTORY_AUDIT TABLE
-- ============================================================
CREATE TABLE inventory_audit (
    audit_id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id TEXT NOT NULL,
    inventory_before INTEGER NOT NULL,
    inventory_after INTEGER NOT NULL,
    change_reason TEXT NOT NULL,
    related_decision_id TEXT,
    notes TEXT,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE CASCADE,
    FOREIGN KEY (related_decision_id) REFERENCES orchestration_decisions(decision_id) ON DELETE SET NULL,
    CHECK (change_reason IN (
        'purchase', 'restock', 'adjustment', 'conflict_resolution', 
        'orchestration_allocation', 'return', 'damage', 'correction'
    ))
);

CREATE INDEX idx_audit_product ON inventory_audit(product_id);
CREATE INDEX idx_audit_timestamp ON inventory_audit(timestamp);
CREATE INDEX idx_audit_reason ON inventory_audit(change_reason);

-- ============================================================
-- SAMPLE DATA (Optional - for testing)
-- ============================================================

-- Insert sample users
INSERT INTO users (user_id, email, password_hash, is_active) VALUES
('USER_001', 'sarah@example.com', '$2b$12$abcdef1234567890', 1),
('USER_002', 'john@example.com', '$2b$12$abcdef1234567890', 1);

-- Insert sample customers
INSERT INTO customers (customer_id, user_id, segment, web_engagement, mobile_engagement, email_engagement, recency_days, frequency, monetary) VALUES
('CUST_001', 'USER_001', 'high_value', 0.92, 0.88, 0.78, 2, 15, 1200.50),
('CUST_002', 'USER_002', 'loyal', 0.75, 0.65, 0.85, 5, 8, 450.00);

-- Insert sample products
INSERT INTO products (product_id, name, category, price, inventory, rating, is_active) VALUES
('PROD_001', 'MAC Red Lipstick', 'lipstick', 40.00, 50, 4.8, 1),
('PROD_002', 'Revlon Red Lipstick', 'lipstick', 28.00, 120, 4.5, 1),
('PROD_003', 'Red Lip Liner', 'lip_liner', 20.00, 80, 4.6, 1),
('PROD_004', 'Urban Decay Eyeshadow Palette', 'eyeshadow', 65.00, 30, 4.9, 1),
('PROD_005', 'CeraVe Moisturizer', 'skincare', 18.00, 200, 4.7, 1);

-- Insert sample customer affinities
INSERT INTO customer_affinities (customer_id, category, affinity_score) VALUES
('CUST_001', 'lipstick', 0.95),
('CUST_001', 'eyeshadow', 0.72),
('CUST_001', 'skincare', 0.35),
('CUST_002', 'lipstick', 0.70),
('CUST_002', 'skincare', 0.85);

-- Insert today's budget tracker
INSERT INTO budget_tracker (date, daily_limit, spent_today, remaining, num_emails_sent) VALUES
(DATE('now'), 1000.00, 500.00, 500.00, 3334);