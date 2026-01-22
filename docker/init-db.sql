-- =============================================================================
-- NLP2CMD - Database Initialization Script
-- =============================================================================
-- This script creates test tables for integration and E2E tests
-- =============================================================================

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =============================================================================
-- Users Table
-- =============================================================================
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    status VARCHAR(50) DEFAULT 'active',
    city VARCHAR(100),
    country VARCHAR(100),
    age INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- Products Table
-- =============================================================================
CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    sku VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    price DECIMAL(10, 2) NOT NULL,
    category VARCHAR(100),
    stock_quantity INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- Orders Table
-- =============================================================================
CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    order_number VARCHAR(50) UNIQUE NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    total_amount DECIMAL(10, 2) NOT NULL,
    shipping_address TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- Order Items Table
-- =============================================================================
CREATE TABLE IF NOT EXISTS order_items (
    id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES orders(id),
    product_id INTEGER REFERENCES products(id),
    quantity INTEGER NOT NULL,
    unit_price DECIMAL(10, 2) NOT NULL,
    total_price DECIMAL(10, 2) NOT NULL
);

-- =============================================================================
-- Logs Table (for log analysis tests)
-- =============================================================================
CREATE TABLE IF NOT EXISTS logs (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    level VARCHAR(20) NOT NULL,
    source VARCHAR(100),
    message TEXT,
    metadata JSONB
);

-- =============================================================================
-- Insert Sample Data - Users
-- =============================================================================
INSERT INTO users (name, email, status, city, country, age) VALUES
    ('Alice Johnson', 'alice@example.com', 'active', 'Warsaw', 'Poland', 28),
    ('Bob Smith', 'bob@example.com', 'active', 'Krakow', 'Poland', 35),
    ('Charlie Brown', 'charlie@example.com', 'inactive', 'Warsaw', 'Poland', 42),
    ('Diana Ross', 'diana@example.com', 'active', 'Gdansk', 'Poland', 31),
    ('Edward Norton', 'edward@example.com', 'pending', 'Poznan', 'Poland', 29),
    ('Fiona Apple', 'fiona@example.com', 'active', 'Wroclaw', 'Poland', 26),
    ('George Lucas', 'george@example.com', 'active', 'Warsaw', 'Poland', 45),
    ('Hannah Montana', 'hannah@example.com', 'inactive', 'Lodz', 'Poland', 22),
    ('Ivan Petrov', 'ivan@example.com', 'active', 'Krakow', 'Poland', 38),
    ('Julia Roberts', 'julia@example.com', 'active', 'Warsaw', 'Poland', 33)
ON CONFLICT (email) DO NOTHING;

-- =============================================================================
-- Insert Sample Data - Products
-- =============================================================================
INSERT INTO products (sku, name, description, price, category, stock_quantity) VALUES
    ('LAPTOP-001', 'Business Laptop', 'High-performance business laptop', 2499.99, 'Electronics', 50),
    ('PHONE-001', 'Smartphone Pro', 'Latest smartphone with advanced features', 999.99, 'Electronics', 100),
    ('DESK-001', 'Standing Desk', 'Ergonomic standing desk', 599.99, 'Furniture', 25),
    ('CHAIR-001', 'Office Chair', 'Comfortable ergonomic office chair', 349.99, 'Furniture', 40),
    ('MONITOR-001', '4K Monitor', '27-inch 4K professional monitor', 449.99, 'Electronics', 75),
    ('KEYBOARD-001', 'Mechanical Keyboard', 'RGB mechanical gaming keyboard', 149.99, 'Accessories', 200),
    ('MOUSE-001', 'Wireless Mouse', 'Ergonomic wireless mouse', 79.99, 'Accessories', 150),
    ('HEADSET-001', 'Noise Cancelling Headset', 'Premium noise cancelling headset', 299.99, 'Accessories', 60),
    ('WEBCAM-001', 'HD Webcam', '1080p HD webcam for video calls', 129.99, 'Accessories', 80),
    ('TABLET-001', 'Digital Tablet', 'Professional drawing tablet', 699.99, 'Electronics', 30)
ON CONFLICT (sku) DO NOTHING;

-- =============================================================================
-- Insert Sample Data - Orders
-- =============================================================================
INSERT INTO orders (user_id, order_number, status, total_amount, shipping_address) VALUES
    (1, 'ORD-2025-001', 'completed', 2949.98, '123 Main St, Warsaw'),
    (1, 'ORD-2025-002', 'completed', 449.99, '123 Main St, Warsaw'),
    (2, 'ORD-2025-003', 'shipped', 1349.98, '456 Oak Ave, Krakow'),
    (4, 'ORD-2025-004', 'pending', 999.99, '789 Pine Rd, Gdansk'),
    (6, 'ORD-2025-005', 'completed', 229.98, '321 Elm St, Wroclaw'),
    (7, 'ORD-2025-006', 'shipped', 2499.99, '654 Maple Dr, Warsaw'),
    (9, 'ORD-2025-007', 'pending', 749.98, '987 Cedar Ln, Krakow'),
    (10, 'ORD-2025-008', 'completed', 1049.98, '147 Birch Blvd, Warsaw')
ON CONFLICT (order_number) DO NOTHING;

-- =============================================================================
-- Insert Sample Data - Order Items
-- =============================================================================
INSERT INTO order_items (order_id, product_id, quantity, unit_price, total_price) VALUES
    (1, 1, 1, 2499.99, 2499.99),
    (1, 7, 1, 79.99, 79.99),
    (1, 6, 1, 149.99, 149.99),
    (2, 5, 1, 449.99, 449.99),
    (3, 4, 2, 349.99, 699.98),
    (3, 3, 1, 599.99, 599.99),
    (4, 2, 1, 999.99, 999.99),
    (5, 6, 1, 149.99, 149.99),
    (5, 7, 1, 79.99, 79.99),
    (6, 1, 1, 2499.99, 2499.99),
    (7, 10, 1, 699.99, 699.99),
    (8, 2, 1, 999.99, 999.99)
ON CONFLICT DO NOTHING;

-- =============================================================================
-- Insert Sample Data - Logs
-- =============================================================================
INSERT INTO logs (timestamp, level, source, message, metadata) VALUES
    (NOW() - INTERVAL '1 hour', 'INFO', 'api-server', 'Server started successfully', '{"port": 8000}'),
    (NOW() - INTERVAL '55 minutes', 'INFO', 'database', 'Connection pool initialized', '{"pool_size": 10}'),
    (NOW() - INTERVAL '50 minutes', 'WARNING', 'api-server', 'High memory usage detected', '{"memory_percent": 85}'),
    (NOW() - INTERVAL '45 minutes', 'ERROR', 'payment-service', 'Payment gateway timeout', '{"gateway": "stripe", "timeout_ms": 30000}'),
    (NOW() - INTERVAL '40 minutes', 'INFO', 'user-service', 'User logged in', '{"user_id": 1}'),
    (NOW() - INTERVAL '35 minutes', 'ERROR', 'api-server', 'Database connection failed', '{"error": "connection_refused"}'),
    (NOW() - INTERVAL '30 minutes', 'INFO', 'api-server', 'Database connection restored', '{}'),
    (NOW() - INTERVAL '25 minutes', 'WARNING', 'cache', 'Cache miss rate high', '{"miss_rate": 0.45}'),
    (NOW() - INTERVAL '20 minutes', 'ERROR', 'order-service', 'Order processing failed', '{"order_id": 123}'),
    (NOW() - INTERVAL '15 minutes', 'INFO', 'scheduler', 'Scheduled job completed', '{"job": "cleanup"}'),
    (NOW() - INTERVAL '10 minutes', 'DEBUG', 'api-server', 'Request processed', '{"endpoint": "/api/users", "duration_ms": 45}'),
    (NOW() - INTERVAL '5 minutes', 'INFO', 'api-server', 'Health check passed', '{}');

-- =============================================================================
-- Create Indexes for Performance
-- =============================================================================
CREATE INDEX IF NOT EXISTS idx_users_status ON users(status);
CREATE INDEX IF NOT EXISTS idx_users_city ON users(city);
CREATE INDEX IF NOT EXISTS idx_orders_user_id ON orders(user_id);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_order_items_order_id ON order_items(order_id);
CREATE INDEX IF NOT EXISTS idx_logs_level ON logs(level);
CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON logs(timestamp);

-- =============================================================================
-- Create Views for Common Queries
-- =============================================================================
CREATE OR REPLACE VIEW user_order_summary AS
SELECT 
    u.id as user_id,
    u.name,
    u.email,
    u.city,
    COUNT(o.id) as total_orders,
    COALESCE(SUM(o.total_amount), 0) as lifetime_value,
    MAX(o.created_at) as last_order_date
FROM users u
LEFT JOIN orders o ON u.id = o.user_id
GROUP BY u.id, u.name, u.email, u.city;

CREATE OR REPLACE VIEW product_sales_summary AS
SELECT 
    p.id as product_id,
    p.name,
    p.category,
    p.price,
    COALESCE(SUM(oi.quantity), 0) as total_sold,
    COALESCE(SUM(oi.total_price), 0) as total_revenue
FROM products p
LEFT JOIN order_items oi ON p.id = oi.product_id
GROUP BY p.id, p.name, p.category, p.price;

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO nlp2cmd;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO nlp2cmd;
