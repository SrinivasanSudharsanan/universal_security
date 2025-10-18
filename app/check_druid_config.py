#!/usr/bin/env python3
"""
Check Druid configuration
"""

from config import get_settings

def check_druid_config():
    settings = get_settings()
    
    print("🔍 Checking Druid Configuration:")
    print("=" * 40)
    
    if hasattr(settings, 'druid_config'):
        config = settings.druid_config
        print("Druid Config Found:")
        for key, value in config.items():
            print(f"  {key}: {value}")
        
        # Check for placeholder values
        placeholder_keys = []
        for key, value in config.items():
            if "your-" in str(value).lower() or "example" in str(value).lower():
                placeholder_keys.append(key)
        
        if placeholder_keys:
            print(f"\n⚠️  Placeholder values found in: {', '.join(placeholder_keys)}")
            print("   Please update these with your actual Druid connection details")
        else:
            print("\n✅ No placeholder values found")
            
    else:
        print("❌ No druid_config found in settings")

if __name__ == "__main__":
    check_druid_config()