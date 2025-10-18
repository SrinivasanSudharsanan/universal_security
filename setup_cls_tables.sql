-- Create the column_level_security_policies table
CREATE TABLE IF NOT EXISTS column_level_security_policies (
    id SERIAL PRIMARY KEY,
    table_name VARCHAR(100) NOT NULL,
    column_name VARCHAR(100) NOT NULL,
    role_name VARCHAR(50) NOT NULL,
    access_type VARCHAR(10) NOT NULL CHECK (access_type IN ('allow', 'deny', 'mask')),
    mask_type VARCHAR(20),
    custom_mask_rule TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(table_name, column_name, role_name)
);

-- Create security_audit_log table
CREATE TABLE IF NOT EXISTS security_audit_log (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(100),
    user_roles TEXT[],
    action_type VARCHAR(50),
    sql_query TEXT,
    secured_sql TEXT,
    result_count INTEGER,
    execution_time_ms INTEGER DEFAULT 0,
    success BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_cls_policies_table ON column_level_security_policies(table_name);
CREATE INDEX IF NOT EXISTS idx_cls_policies_role ON column_level_security_policies(role_name);
CREATE INDEX IF NOT EXISTS idx_audit_log_user_id ON security_audit_log(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_created_at ON security_audit_log(created_at);

-- Verify tables were created
SELECT 
    table_name,
    (SELECT COUNT(*) FROM information_schema.columns WHERE table_name = t.table_name) as column_count
FROM information_schema.tables t
WHERE t.table_name IN ('column_level_security_policies', 'security_audit_log')
AND t.table_schema = 'public';
