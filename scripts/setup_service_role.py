#!/usr/bin/env python3
"""
Script to set the service role key in the database session before running the bot.
This ensures the database trigger can authenticate when calling edge functions.
"""

import os
import sys
import requests
from dotenv import load_dotenv

# Add the project root to the Python path so we can find the .env file
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sys.path.insert(0, project_root)

def setup_service_role_key():
    """Set the service role key in the database session for trigger authentication."""
    # Load .env from project root
    env_path = os.path.join(project_root, '.env')
    if not os.path.exists(env_path):
        print(f"Error: .env file not found at {env_path}")
        return False
    
    load_dotenv(env_path)
    
    supabase_url = os.getenv('VITE_SUPABASE_URL')
    service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    if not supabase_url or not service_key:
        print("Error: Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY environment variables")
        print(f"Make sure your .env file contains both variables:")
        print(f"  VITE_SUPABASE_URL=your_supabase_url")
        print(f"  SUPABASE_SERVICE_ROLE_KEY=your_service_role_key")
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
            print("✅ Service role key set successfully in database session")
            return True
        else:
            print(f"❌ Failed to set service role key: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error setting service role key: {e}")
        return False

def verify_trigger_function():
    """Test the trigger function to ensure it can call the edge function."""
    # Load .env from project root
    env_path = os.path.join(project_root, '.env')
    load_dotenv(env_path)
    
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
            print(f"✅ Trigger function test successful: {result}")
            return True
        else:
            print(f"❌ Trigger function test failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing trigger function: {e}")
        return False

if __name__ == "__main__":
    print("Setting up service role key for database trigger...")
    
    if setup_service_role_key():
        print("\nVerifying trigger function...")
        verify_trigger_function()
    else:
        print("Failed to set service role key. Please check your environment variables.")
