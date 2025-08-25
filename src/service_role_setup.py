#!/usr/bin/env python3
"""
Module to set the service role key in the database session before running the bot.
This ensures the database trigger can authenticate when calling edge functions.
"""

import os
import requests
import logging
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

def setup_service_role_key():
    """Set the service role key in the database session for trigger authentication."""
    load_dotenv()
    
    supabase_url = os.getenv('VITE_SUPABASE_URL')
    service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    if not supabase_url or not service_key:
        logger.error("Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY environment variables")
        return False
    
    headers = {
        'apikey': service_key,
        'Authorization': f'Bearer {service_key}',
        'Content-Type': 'application/json'
    }
    
    try:
        # Set the service role key in the database session
        response = requests.post(
            f'{supabase_url}/rest/v1/rpc/set_service_role_key',
            headers=headers,
            json={'key_value': service_key}
        )
        
        if response.status_code == 200:
            logger.info("✅ Service role key set successfully in database session")
            return True
        else:
            logger.error(f"❌ Failed to set service role key: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error setting service role key: {e}")
        return False

def verify_trigger_function():
    """Test the trigger function to ensure it can call the edge function."""
    load_dotenv()
    
    supabase_url = os.getenv('VITE_SUPABASE_URL')
    service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
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
            logger.info(f"✅ Trigger function test successful: {result}")
            return True
        else:
            logger.error(f"❌ Trigger function test failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error testing trigger function: {e}")
        return False

def initialize_service_role():
    """Initialize the service role key and verify trigger function."""
    logger.info("Setting up service role key for database trigger...")
    
    if setup_service_role_key():
        logger.info("Verifying trigger function...")
        return verify_trigger_function()
    else:
        logger.error("Failed to set service role key. Please check your environment variables.")
        return False
