#!/usr/bin/env python3
"""
Quick SPORTS_CRICKET_ENABLED Environment Variable Test
"""

import os
import subprocess
import time
import requests
from pathlib import Path

def log(message: str, level: str = "INFO"):
    print(f"[{level}] {message}")

def get_backend_logs():
    """Get recent backend logs"""
    try:
        result = subprocess.run(['tail', '-n', '20', '/var/log/supervisor/backend.err.log'], 
                              capture_output=True, text=True, timeout=10)
        return result.stdout
    except Exception as e:
        log(f"Error getting backend logs: {str(e)}", "ERROR")
        return ""

def test_current_state():
    """Test current cricket feature state"""
    log("=== Testing Current Cricket Feature State ===")
    
    # Check current .env file
    env_file = Path("/app/backend/.env")
    if env_file.exists():
        content = env_file.read_text()
        log(f"Current .env content:\n{content}")
        
        # Extract cricket flag value
        cricket_value = None
        for line in content.split('\n'):
            if line.strip().startswith('SPORTS_CRICKET_ENABLED'):
                cricket_value = line.split('=')[1].strip()
                break
        
        log(f"SPORTS_CRICKET_ENABLED value in .env: {cricket_value}")
    
    # Check recent logs
    logs = get_backend_logs()
    log("Recent backend logs:")
    for line in logs.split('\n')[-10:]:
        if line.strip():
            log(f"  {line}")
    
    # Look for cricket feature log
    cricket_logged = False
    for line in logs.split('\n'):
        if "Cricket feature enabled:" in line:
            log(f"Found cricket log: {line}")
            cricket_logged = True
    
    if not cricket_logged:
        log("No cricket feature log found", "ERROR")
        return False
    
    # Test API connectivity
    try:
        response = requests.get("https://cricket-fantasy-app-2.preview.emergentagent.com/api/", timeout=10)
        if response.status_code == 200:
            log("✅ API connectivity working")
        else:
            log(f"API returned status {response.status_code}", "ERROR")
            return False
    except Exception as e:
        log(f"API connectivity failed: {str(e)}", "ERROR")
        return False
    
    return True

def test_boolean_conversion():
    """Test boolean conversion with different values"""
    log("=== Testing Boolean Conversion ===")
    
    env_file = Path("/app/backend/.env")
    backup = env_file.read_text() if env_file.exists() else None
    
    test_cases = [
        ("true", True),
        ("false", False),
        ("True", True),
        ("FALSE", False),
    ]
    
    try:
        for test_value, expected_bool in test_cases:
            log(f"Testing {test_value} -> {expected_bool}")
            
            # Update .env file
            lines = []
            if backup:
                for line in backup.split('\n'):
                    if line.strip().startswith('SPORTS_CRICKET_ENABLED'):
                        lines.append(f'SPORTS_CRICKET_ENABLED={test_value}')
                    else:
                        lines.append(line)
            
            env_file.write_text('\n'.join(lines))
            
            # Restart backend
            result = subprocess.run(['sudo', 'supervisorctl', 'restart', 'backend'], 
                                  capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                log(f"Failed to restart backend: {result.stderr}", "ERROR")
                continue
            
            time.sleep(8)  # Wait for startup
            
            # Check logs
            logs = get_backend_logs()
            expected_log = f"Cricket feature enabled: {expected_bool}"
            
            if expected_log in logs:
                log(f"✅ {test_value} correctly converted to {expected_bool}")
            else:
                log(f"❌ {test_value} not correctly converted", "ERROR")
                log(f"Recent logs: {logs.split('Cricket feature enabled:')[-1][:50] if 'Cricket feature enabled:' in logs else 'No cricket log found'}")
        
        return True
        
    finally:
        # Restore original .env
        if backup:
            env_file.write_text(backup)
            subprocess.run(['sudo', 'supervisorctl', 'restart', 'backend'], 
                          capture_output=True, text=True, timeout=30)
            time.sleep(5)

def main():
    log("🏏 Quick Cricket Feature Test")
    
    # Test 1: Current state
    if not test_current_state():
        log("❌ Current state test failed")
        return False
    
    # Test 2: Boolean conversion
    if not test_boolean_conversion():
        log("❌ Boolean conversion test failed")
        return False
    
    log("✅ All quick cricket tests passed!")
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)