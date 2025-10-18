-- Fix permissions for CLS tables
GRANT ALL PRIVILEGES ON TABLE column_level_security_policies TO public;
GRANT ALL PRIVILEGES ON TABLE security_audit_log TO public;

-- Grant sequence permissions too
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO public;

-- Verify permissions
SELECT 
    table_name,
    grantee,
    privilege_type
FROM information_schema.table_privileges 
WHERE table_name IN ('column_level_security_policies', 'security_audit_log')
ORDER BY table_name, grantee;

-- Also check current user and available users
SELECT current_user;
\du
