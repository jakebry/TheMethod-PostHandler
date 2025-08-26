#!/usr/bin/env python3
"""
Service Role Setup Module

This module handles setting up the service role key in the database session for trigger authentication.
It can be used both as a library (imported by other modules) and as a standalone script.

Usage as library:
    from src.service_role_setup import initialize_service_role
    success = initialize_service_role()

Usage as script:
    python -m src.service_role_setup
"""

import os
import sys
import requests
import logging
from dotenv import load_dotenv

# Configure logging
logger = logging.getLogger(__name__)

def setup_service_role_key():
    """Set the service role key in the database session for trigger authentication."""
    load_dotenv()
    
    supabase_url = os.getenv('VITE_SUPABASE_URL')
    service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    # Add debug logging for production troubleshooting (SAFE - no sensitive data)
    logger.info(f"Environment check - VITE_SUPABASE_URL: {'SET' if supabase_url else 'NOT SET'}")
    logger.info(f"Environment check - SUPABASE_SERVICE_ROLE_KEY: {'SET' if service_key else 'NOT SET'}")
    
    if not supabase_url or not service_key:
        logger.error("❌ Configuration Error: Missing required environment variables")
        logger.error("   Make sure your .env file contains both variables:")
        logger.error("     VITE_SUPABASE_URL=your_supabase_url")
        logger.error("     SUPABASE_SERVICE_ROLE_KEY=your_service_role_key")
        logger.error("   For Fly.io deployment, ensure these are set as secrets:")
        logger.error("     fly secrets set VITE_SUPABASE_URL=your_url")
        logger.error("     fly secrets set SUPABASE_SERVICE_ROLE_KEY=your_key")
        return False
    
    headers = {
        'apikey': service_key,
        'Authorization': f'Bearer {service_key}',
        'Content-Type': 'application/json'
    }
    
    try:
        # Set the service role key in the database session
        logger.info(f"Setting service role key at: {supabase_url}/rest/v1/rpc/set_service_role_key")
        response = requests.post(
            f'{supabase_url}/rest/v1/rpc/set_service_role_key',
            headers=headers,
            json={'key_value': service_key}
        )
        
        if response.status_code == 200:
            result = response.json()
            if result is True:
                logger.info("✅ Service role key set successfully in database session")
            else:
                logger.warning(f"⚠️  Service role key setup completed but returned: {result}")
                logger.warning("   This may indicate a configuration issue")
            return True
        else:
            # HTTP error - this is an actual failure
            logger.error(f"❌ HTTP Error: Failed to set service role key")
            logger.error(f"   Status Code: {response.status_code}")
            # SAFE: Don't log the full response as it might contain sensitive data
            logger.error(f"   Response: [REDACTED - check Supabase logs for details]")
            return False
            
    except requests.exceptions.RequestException as e:
        # Network/HTTP request errors
        logger.error(f"❌ Network Error: Failed to connect to database")
        logger.error(f"   Error: {e}")
        return False
    except Exception as e:
        # Other unexpected errors
        logger.error(f"❌ Unexpected Error: {e}")
        return False

def verify_trigger_function():
    """Test the trigger function to ensure it can call the edge function."""
    load_dotenv()
    
    supabase_url = os.getenv('VITE_SUPABASE_URL')
    service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    # Add debug logging for production troubleshooting (SAFE - no sensitive data)
    logger.info(f"Trigger function check - VITE_SUPABASE_URL: {'SET' if supabase_url else 'NOT SET'}")
    logger.info(f"Trigger function check - SUPABASE_SERVICE_ROLE_KEY: {'SET' if service_key else 'NOT SET'}")
    
    headers = {
        'apikey': service_key,
        'Authorization': f'Bearer {service_key}'
    }
    
    try:
        # Test the process_images_immediately function
        response = requests.get(
            f'{supabase_url}/rest/v1/rpc/process_images_immediately',
            headers=headers
        )
        
        if response.status_code == 200:
            result = response.json()
            
            # Distinguish between different types of successful responses
            if result is True:
                logger.info(f"✅ Trigger function test successful: {result}")
                logger.info("   Function executed and completed successfully")
            elif result is False:
                logger.info(f"✅ Trigger function test completed successfully")
                logger.info("   Function returned: False (likely no images queued for processing)")
                logger.info("   This is normal operation when there's no work to do")
            elif isinstance(result, dict):
                # Handle dictionary responses that might contain status info
                if result.get('error'):
                    logger.warning(f"⚠️  Trigger function executed but encountered an issue:")
                    logger.warning(f"   Response: {result}")
                    return False
                else:
                    logger.info(f"✅ Trigger function test successful: {result}")
            else:
                logger.info(f"✅ Trigger function test successful: {result}")
            
            return True
        else:
            # HTTP error - this is an actual failure
            logger.error(f"❌ HTTP Error: Trigger function test failed")
            logger.error(f"   Status Code: {response.status_code}")
            logger.error(f"   Response: [REDACTED - check Supabase logs for details]")
            return False
            
    except requests.exceptions.RequestException as e:
        # Network/HTTP request errors
        logger.error(f"❌ Network Error: Failed to connect to trigger function")
        logger.error(f"   Error: {e}")
        return False
    except Exception as e:
        # Other unexpected errors
        logger.error(f"❌ Unexpected Error: {e}")
        return False

def initialize_service_role():
    """Initialize the service role key and verify trigger function."""
    logger.info("🚀 Initializing service role key for database trigger...")
    
    if setup_service_role_key():
        logger.info("🔍 Verifying trigger function...")
        return verify_trigger_function()
    else:
        logger.error("❌ Failed to set service role key. Please check your environment variables.")
        return False

def main():
    """Main function for standalone script execution."""
    # Configure logging for standalone use
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    
    print("Setting up service role key for database trigger...")
    
    if setup_service_role_key():
        print("\nVerifying trigger function...")
        verify_trigger_function()
    else:
        print("Failed to set service role key. Please check your environment variables.")

if __name__ == "__main__":
    main()
