-- Universal Security Framework - PostgreSQL Schema

-- Security Roles
CREATE TABLE IF NOT EXISTS security_roles (
    role_id SERIAL PRIMARY KEY,
    role_name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    is_system_role BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Security Users
CREATE TABLE IF NOT EXISTS security_users (
    user_id VARCHAR(255) PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User-Role Mapping
CREATE TABLE IF NOT EXISTS security_user_roles (
    user_id VARCHAR(255) REFERENCES security_users(user_id) ON DELETE CASCADE,
    role_id INTEGER REFERENCES security_roles(role_id) ON DELETE CASCADE,
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, role_id)
);

-- Data Sources
CREATE TABLE IF NOT EXISTS security_data_sources (
    source_id SERIAL PRIMARY KEY,
    source_name VARCHAR(255) NOT NULL,
    engine_type VARCHAR(50) NOT NULL,
    connection_config JSONB,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tables Registry
CREATE TABLE IF NOT EXISTS security_tables (
    table_id SERIAL PRIMARY KEY,
    source_id INTEGER REFERENCES security_data_sources(source_id),
    table_name VARCHAR(255) NOT NULL,
    schema_name VARCHAR(255),
    description TEXT,
    is_sensitive BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(source_id, table_name)
);

-- Columns Registry
CREATE TABLE IF NOT EXISTS security_columns (
    column_id SERIAL PRIMARY KEY,
    table_id INTEGER REFERENCES security_tables(table_id),
    column_name VARCHAR(255) NOT NULL,
    data_type VARCHAR(100),
    is_sensitive BOOLEAN DEFAULT FALSE,
    sensitivity_level VARCHAR(50) DEFAULT 'low',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(table_id, column_name)
);

-- Row-Level Security Policies
CREATE TABLE IF NOT EXISTS security_rls_policies (
    policy_id SERIAL PRIMARY KEY,
    policy_name VARCHAR(255) NOT NULL,
    table_id INTEGER REFERENCES security_tables(table_id),
    role_id INTEGER REFERENCES security_roles(role_id),
    filter_condition TEXT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    priority INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Column-Level Security Policies
CREATE TABLE IF NOT EXISTS security_cls_policies (
    policy_id SERIAL PRIMARY KEY,
    policy_name VARCHAR(255) NOT NULL,
    role_id INTEGER REFERENCES security_roles(role_id),
    column_id INTEGER REFERENCES security_columns(column_id),
    access_type VARCHAR(50) NOT NULL, -- allow, deny, mask
    mask_type VARCHAR(50), -- full, partial, hash, email, phone
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User Security Settings
CREATE TABLE IF NOT EXISTS security_user_settings (
    user_id VARCHAR(255) PRIMARY KEY REFERENCES security_users(user_id),
    max_rows_per_query INTEGER DEFAULT 1000,
    query_timeout_seconds INTEGER DEFAULT 30,
    allowed_engines TEXT[] DEFAULT '{"druid","postgres","mysql"}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Audit Log
CREATE TABLE IF NOT EXISTS security_audit_log (
    audit_id SERIAL PRIMARY KEY,
    user_id VARCHAR(255),
    action_type VARCHAR(100) NOT NULL,
    sql_query TEXT,
    secured_sql TEXT,
    execution_time_ms INTEGER,
    success BOOLEAN,
    error_message TEXT,
    source_ip INET,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert Default Data
INSERT INTO security_roles (role_name, description, is_system_role) VALUES
('admin', 'Full system access', TRUE),
('data_engineer', 'Engineering data access', FALSE),
('business_analyst', 'Business intelligence access', FALSE),
('reporting_user', 'Standard reporting access', FALSE),
('public', 'Limited public access', TRUE)
ON CONFLICT (role_name) DO NOTHING;

INSERT INTO security_users (user_id, username, email, is_active) VALUES
('admin', 'admin', 'admin@company.com', TRUE),
('engineering_manager', 'eng_manager', 'eng@company.com', TRUE),
('business_user', 'business_user', 'business@company.com', TRUE)
ON CONFLICT (user_id) DO NOTHING;

INSERT INTO security_user_roles (user_id, role_id) VALUES
('admin', (SELECT role_id FROM security_roles WHERE role_name = 'admin')),
('engineering_manager', (SELECT role_id FROM security_roles WHERE role_name = 'data_engineer')),
('business_user', (SELECT role_id FROM security_roles WHERE role_name = 'business_analyst'))
ON CONFLICT (user_id, role_id) DO NOTHING;

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_rls_policies_table_role ON security_rls_policies(table_id, role_id);
CREATE INDEX IF NOT EXISTS idx_cls_policies_role_column ON security_cls_policies(role_id, column_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_user_time ON security_audit_log(user_id, created_at);
CREATE INDEX IF NOT EXISTS idx_user_roles_user ON security_user_roles(user_id);
