-- Insert CLS policies for employees and sales tables
INSERT INTO column_level_security_policies 
(table_name, column_name, role_name, access_type, mask_type, custom_mask_rule, is_active)
VALUES

-- employees table policies
('employees', 'name', 'admin', 'allow', NULL, NULL, true),
('employees', 'name', 'analyst', 'allow', NULL, NULL, true),
('employees', 'name', 'hr', 'allow', NULL, NULL, true),
('employees', 'name', 'employee', 'allow', NULL, NULL, true),
('employees', 'name', 'guest', 'mask', 'partial', '#######', true),

('employees', 'department', 'admin', 'allow', NULL, NULL, true),
('employees', 'department', 'analyst', 'allow', NULL, NULL, true),
('employees', 'department', 'hr', 'allow', NULL, NULL, true),
('employees', 'department', 'employee', 'allow', NULL, NULL, true),
('employees', 'department', 'guest', 'allow', NULL, NULL, true),

('employees', 'access_level', 'admin', 'allow', NULL, NULL, true),
('employees', 'access_level', 'analyst', 'allow', NULL, NULL, true),
('employees', 'access_level', 'hr', 'allow', NULL, NULL, true),
('employees', 'access_level', 'employee', 'deny', NULL, NULL, true),
('employees', 'access_level', 'guest', 'deny', NULL, NULL, true),

('employees', 'salary_sum', 'admin', 'allow', NULL, NULL, true),
('employees', 'salary_sum', 'analyst', 'mask', 'partial', '$$$,###', true),
('employees', 'salary_sum', 'hr', 'allow', NULL, NULL, true),
('employees', 'salary_sum', 'employee', 'deny', NULL, NULL, true),
('employees', 'salary_sum', 'guest', 'deny', NULL, NULL, true),

('employees', 'count', 'admin', 'allow', NULL, NULL, true),
('employees', 'count', 'analyst', 'allow', NULL, NULL, true),
('employees', 'count', 'hr', 'allow', NULL, NULL, true),
('employees', 'count', 'employee', 'allow', NULL, NULL, true),
('employees', 'count', 'guest', 'allow', NULL, NULL, true),

('employees', '__time', 'admin', 'allow', NULL, NULL, true),
('employees', '__time', 'analyst', 'allow', NULL, NULL, true),
('employees', '__time', 'hr', 'allow', NULL, NULL, true),
('employees', '__time', 'employee', 'allow', NULL, NULL, true),
('employees', '__time', 'guest', 'allow', NULL, NULL, true),

-- sales table policies
('sales', 'product', 'admin', 'allow', NULL, NULL, true),
('sales', 'product', 'analyst', 'allow', NULL, NULL, true),
('sales', 'product', 'sales', 'allow', NULL, NULL, true),
('sales', 'product', 'employee', 'allow', NULL, NULL, true),
('sales', 'product', 'guest', 'allow', NULL, NULL, true),

('sales', 'customer', 'admin', 'allow', NULL, NULL, true),
('sales', 'customer', 'analyst', 'mask', 'partial', 'XXXX-####', true),
('sales', 'customer', 'sales', 'allow', NULL, NULL, true),
('sales', 'customer', 'employee', 'deny', NULL, NULL, true),
('sales', 'customer', 'guest', 'deny', NULL, NULL, true),

('sales', 'region', 'admin', 'allow', NULL, NULL, true),
('sales', 'region', 'analyst', 'allow', NULL, NULL, true),
('sales', 'region', 'sales', 'allow', NULL, NULL, true),
('sales', 'region', 'employee', 'allow', NULL, NULL, true),
('sales', 'region', 'guest', 'allow', NULL, NULL, true),

('sales', 'quarter', 'admin', 'allow', NULL, NULL, true),
('sales', 'quarter', 'analyst', 'allow', NULL, NULL, true),
('sales', 'quarter', 'sales', 'allow', NULL, NULL, true),
('sales', 'quarter', 'employee', 'allow', NULL, NULL, true),
('sales', 'quarter', 'guest', 'allow', NULL, NULL, true),

('sales', 'amount_sum', 'admin', 'allow', NULL, NULL, true),
('sales', 'amount_sum', 'analyst', 'allow', NULL, NULL, true),
('sales', 'amount_sum', 'sales', 'allow', NULL, NULL, true),
('sales', 'amount_sum', 'employee', 'mask', 'partial', '$$$,###', true),
('sales', 'amount_sum', 'guest', 'deny', NULL, NULL, true),

('sales', 'count', 'admin', 'allow', NULL, NULL, true),
('sales', 'count', 'analyst', 'allow', NULL, NULL, true),
('sales', 'count', 'sales', 'allow', NULL, NULL, true),
('sales', 'count', 'employee', 'allow', NULL, NULL, true),
('sales', 'count', 'guest', 'allow', NULL, NULL, true),

('sales', '__time', 'admin', 'allow', NULL, NULL, true),
('sales', '__time', 'analyst', 'allow', NULL, NULL, true),
('sales', '__time', 'sales', 'allow', NULL, NULL, true),
('sales', '__time', 'employee', 'allow', NULL, NULL, true),
('sales', '__time', 'guest', 'allow', NULL, NULL, true);

-- Verify policies were inserted
SELECT 
    table_name, 
    COUNT(*) as policy_count 
FROM column_level_security_policies 
GROUP BY table_name 
ORDER BY table_name;

-- Show sample policies
SELECT 
    table_name, 
    column_name, 
    role_name, 
    access_type,
    mask_type
FROM column_level_security_policies 
WHERE table_name IN ('employees', 'sales')
ORDER BY table_name, column_name, role_name
LIMIT 10;
