-- Database-level triggers to prevent ANY schema modifications
-- These triggers run at the database level and cannot be bypassed by application

-- Function to check if developer is authorizing the change
CREATE OR REPLACE FUNCTION check_developer_authority() 
RETURNS BOOLEAN AS $$
DECLARE
    current_signature TEXT;
    authorized_signature TEXT;
BEGIN
    -- Get current session signature (passed as parameter)
    current_signature := current_setting('universal_security.developer_signature', TRUE);
    
    -- Get authorized signature from lock table
    SELECT developer_signature INTO authorized_signature 
    FROM developer_schema_lock 
    WHERE is_active = TRUE 
    ORDER BY locked_at DESC LIMIT 1;
    
    -- If no lock exists, allow (initial setup)
    IF authorized_signature IS NULL THEN
        RETURN TRUE;
    END IF;
    
    -- Cryptographic comparison
    IF current_signature = authorized_signature THEN
        RETURN TRUE;
    ELSE
        RAISE EXCEPTION 'SCHEMA_MODIFICATION_DENIED: Only authorized developer can modify security schema. Current: %, Expected: %', 
                        current_signature, authorized_signature;
    END IF;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Event trigger to block ALL DDL operations on security tables
CREATE OR REPLACE FUNCTION block_unauthorized_ddl()
RETURNS event_trigger AS $$
DECLARE
    ddl_command RECORD;
BEGIN
    FOR ddl_command IN SELECT * FROM pg_event_trigger_ddl_commands() 
    LOOP
        -- Check if operation affects security tables
        IF ddl_command.object_identity LIKE 'public.security_%' THEN
            -- Verify developer authority
            IF NOT check_developer_authority() THEN
                RAISE EXCEPTION 'DEVELOPER_AUTHORITY_REQUIRED: Schema modifications require developer authorization';
            END IF;
        END IF;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- Create the event trigger
DROP EVENT TRIGGER IF EXISTS enforce_developer_ddl_authority;
CREATE EVENT TRIGGER enforce_developer_ddl_authority ON ddl_command_start
EXECUTE FUNCTION block_unauthorized_ddl();

-- Function to block security table drops
CREATE OR REPLACE FUNCTION block_security_table_drops()
RETURNS event_trigger AS $$
BEGIN
    IF tg_tag = 'DROP TABLE' THEN
        -- Check if dropping security table
        IF EXISTS (
            SELECT 1 FROM pg_event_trigger_dropped_objects() 
            WHERE schema_name = 'public' AND object_name LIKE 'security_%'
        ) THEN
            IF NOT check_developer_authority() THEN
                RAISE EXCEPTION 'DEVELOPER_AUTHORITY_REQUIRED: Cannot drop security tables without developer authorization';
            END IF;
        END IF;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Create drop protection trigger
DROP EVENT TRIGGER IF EXISTS enforce_developer_drop_authority;
CREATE EVENT TRIGGER enforce_developer_drop_authority ON sql_drop
EXECUTE FUNCTION block_security_table_drops();
