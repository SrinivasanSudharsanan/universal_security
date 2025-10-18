# scripts/verify_structure.py
import os
from pathlib import Path

def verify_structure():
    base_dir = Path("polylytics")
    expected_structure = {
        "app/main.py": True,
        "app/config.py": True,
        "app/utils/db_utils.py": True,
        "app/utils/security_utils.py": True,
        "app/utils/sql_utils.py": True,
        "app/utils/logger.py": True,
        "app/api/endpoints/query.py": True,
        "app/api/endpoints/policies.py": True,
        "app/api/endpoints/audit.py": True,
        "app/api/endpoints/health.py": True,
        "app/api/dependencies.py": True,
        "app/security/engine/security_engine.py": True,
        "app/security/engine/connectors.py": True,
        "app/security/auth/jwt_auth.py": True,
        "app/security/auth/oauth.py": True,
        "app/security/auth/identity.py": True,
        "app/security/policies/__init__.py": True,
        "app/security/policies/policy_manager.py": True,
        "app/security/policies/row_level/__init__.py": True,
        "app/security/policies/row_level/rls_engine.py": True,
        "app/security/policies/row_level/filter_parser.py": True,
        "app/security/policies/row_level/dynamic_rules.py": True,
        "app/security/policies/column_level/__init__.py": True,
        "app/security/policies/column_level/cls_engine.py": True,
        "app/security/policies/column_level/allowed_columns.py": True,
        "app/security/policies/column_level/column_masking.py": True,
        "app/security/policies/role_based/__init__.py": True,
        "app/security/policies/role_based/role_engine.py": True,
        "app/security/policies/role_based/permissions.py": True,
        "app/security/policies/role_based/dynamic_roles.py": True,
        "app/security/policies/mask/__init__.py": True,
        "app/security/policies/mask/mask_engine.py": True,
        "app/security/policies/mask/mask_types.py": True,
        "app/security/policies/mask/mask_rules.py": True,
        "app/security/sql/sql_rewriter.py": True,
        "app/security/sql/parser.py": True,
        "app/security/sql/analyzer.py": True,
        "app/security/sql/transformer.py": True,
        "app/database/models.py": True,
        "app/database/init_db.py": True,
        "app/engines/druid_connector.py": True,
        "app/engines/iceberg_connector.py": True,
        "app/engines/snowflake_connector.py": True,
        "app/engines/databricks_connector.py": True,
        "app/audit/audit_logger.py": True,
        "app/audit/metrics.py": True,
        "app/audit/alerts.py": True,
        "app/observability/logger.py": True,
        "app/observability/prometheus_metrics.py": True,
        "app/observability/tracing.py": True,
    }
    
    missing_files = []
    existing_files = []
    
    for file_path, required in expected_structure.items():
        full_path = base_dir / file_path
        if full_path.exists():
            existing_files.append(file_path)
        else:
            missing_files.append(file_path)
    
    print("=== Structure Verification ===")
    print(f"✅ Existing files: {len(existing_files)}")
    print(f"❌ Missing files: {len(missing_files)}")
    
    if missing_files:
        print("\nMissing files:")
        for file in missing_files:
            print(f"  - {file}")
    
    return missing_files

if __name__ == "__main__":
    verify_structure()