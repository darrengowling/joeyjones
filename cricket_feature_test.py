#!/usr/bin/env python3
"""
SPORTS_CRICKET_ENABLED Environment Variable Feature Testing
Tests the newly implemented cricket feature flag functionality
"""

import os
import subprocess
import time
import requests
import tempfile
from datetime import datetime
from pathlib import Path

class CricketFeatureTester:
    def __init__(self):
        self.backend_dir = Path("/app/backend")
        self.env_file = self.backend_dir / ".env"
        self.server_file = self.backend_dir / "server.py"
        self.base_url = "https://uefa-auction-hub.preview.emergentagent.com/api"
        
    def log(self, message: str, level: str = "INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
        
    def backup_env_file(self):
        """Create backup of current .env file"""
        if self.env_file.exists():
            backup_content = self.env_file.read_text()
            return backup_content
        return None
        
    def restore_env_file(self, backup_content):
        """Restore .env file from backup"""
        if backup_content:
            self.env_file.write_text(backup_content)
        
    def update_env_file(self, cricket_value=None):
        """Update .env file with cricket flag value"""
        if not self.env_file.exists():
            self.log("No .env file found", "ERROR")
            return False
            
        lines = []
        cricket_found = False
        
        with open(self.env_file, 'r') as f:
            for line in f:
                if line.strip().startswith('SPORTS_CRICKET_ENABLED'):
                    if cricket_value is not None:
                        lines.append(f'SPORTS_CRICKET_ENABLED={cricket_value}\n')
                        cricket_found = True
                    # If cricket_value is None, we skip this line (remove it)
                else:
                    lines.append(line)
        
        # Add cricket flag if not found and value provided
        if cricket_value is not None and not cricket_found:
            lines.append(f'SPORTS_CRICKET_ENABLED={cricket_value}\n')
            
        with open(self.env_file, 'w') as f:
            f.writelines(lines)
            
        return True
        
    def restart_backend_service(self):
        """Restart backend service using supervisor"""
        try:
            # Restart backend service
            result = subprocess.run(['sudo', 'supervisorctl', 'restart', 'backend'], 
                                  capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                self.log(f"Failed to restart backend: {result.stderr}", "ERROR")
                return False
                
            # Wait for service to start
            time.sleep(5)
            
            # Check if service is running
            status_result = subprocess.run(['sudo', 'supervisorctl', 'status', 'backend'], 
                                         capture_output=True, text=True, timeout=10)
            
            if "RUNNING" not in status_result.stdout:
                self.log(f"Backend service not running: {status_result.stdout}", "ERROR")
                return False
                
            self.log("Backend service restarted successfully")
            return True
            
        except subprocess.TimeoutExpired:
            self.log("Timeout while restarting backend service", "ERROR")
            return False
        except Exception as e:
            self.log(f"Error restarting backend: {str(e)}", "ERROR")
            return False
            
    def get_backend_logs(self, lines=50):
        """Get recent backend logs"""
        try:
            # Check both out and err logs for cricket feature messages
            out_result = subprocess.run(['tail', '-n', str(lines), '/var/log/supervisor/backend.out.log'], 
                                      capture_output=True, text=True, timeout=10)
            err_result = subprocess.run(['tail', '-n', str(lines), '/var/log/supervisor/backend.err.log'], 
                                      capture_output=True, text=True, timeout=10)
            
            # Combine both logs
            combined_logs = out_result.stdout + "\n" + err_result.stdout
            return combined_logs
        except Exception as e:
            self.log(f"Error getting backend logs: {str(e)}", "ERROR")
            return ""
            
    def check_server_startup_logs(self, expected_value):
        """Check if server logs contain cricket feature status"""
        logs = self.get_backend_logs(100)  # Get more logs for startup
        
        # Look for the cricket feature log message
        cricket_log_found = False
        logged_value = None
        
        for line in logs.split('\n'):
            if "Cricket feature enabled:" in line:
                cricket_log_found = True
                # Extract the boolean value from log
                if "Cricket feature enabled: True" in line:
                    logged_value = True
                elif "Cricket feature enabled: False" in line:
                    logged_value = False
                break
                
        if not cricket_log_found:
            self.log("Cricket feature log message not found in startup logs", "ERROR")
            return False
            
        if logged_value != expected_value:
            self.log(f"Cricket feature logged as {logged_value}, expected {expected_value}", "ERROR")
            return False
            
        self.log(f"✅ Cricket feature correctly logged as: {logged_value}")
        return True
        
    def test_api_connectivity(self):
        """Test that API is still accessible after cricket flag changes"""
        try:
            response = requests.get(f"{self.base_url}/", timeout=10)
            if response.status_code == 200:
                self.log("✅ API connectivity working")
                return True
            else:
                self.log(f"API returned status {response.status_code}", "ERROR")
                return False
        except Exception as e:
            self.log(f"API connectivity failed: {str(e)}", "ERROR")
            return False
            
    def test_existing_functionality(self):
        """Test that existing endpoints still work"""
        try:
            # Test clubs endpoint
            response = requests.get(f"{self.base_url}/clubs", timeout=10)
            if response.status_code != 200:
                self.log(f"Clubs endpoint failed: {response.status_code}", "ERROR")
                return False
                
            # Test leagues endpoint
            response = requests.get(f"{self.base_url}/leagues", timeout=10)
            if response.status_code != 200:
                self.log(f"Leagues endpoint failed: {response.status_code}", "ERROR")
                return False
                
            self.log("✅ Existing functionality working")
            return True
            
        except Exception as e:
            self.log(f"Existing functionality test failed: {str(e)}", "ERROR")
            return False
            
    def test_environment_variable_reading(self):
        """Test 1: Environment Variable Reading"""
        self.log("=== Test 1: Environment Variable Reading ===")
        
        # Backup original env file
        backup = self.backup_env_file()
        
        try:
            # Test with explicit true value
            self.log("Testing with SPORTS_CRICKET_ENABLED=true")
            self.update_env_file("true")
            
            if not self.restart_backend_service():
                return False
                
            if not self.check_server_startup_logs(True):
                return False
                
            if not self.test_api_connectivity():
                return False
                
            # Test with explicit false value
            self.log("Testing with SPORTS_CRICKET_ENABLED=false")
            self.update_env_file("false")
            
            if not self.restart_backend_service():
                return False
                
            if not self.check_server_startup_logs(False):
                return False
                
            if not self.test_api_connectivity():
                return False
                
            self.log("✅ Environment variable reading working correctly")
            return True
            
        finally:
            # Restore original env file
            self.restore_env_file(backup)
            
    def test_default_value_handling(self):
        """Test 2: Default Value Handling"""
        self.log("=== Test 2: Default Value Handling ===")
        
        # Backup original env file
        backup = self.backup_env_file()
        
        try:
            # Remove cricket flag from env file
            self.log("Testing with SPORTS_CRICKET_ENABLED removed from .env")
            self.update_env_file(None)  # Remove the variable
            
            if not self.restart_backend_service():
                return False
                
            # Should default to False
            if not self.check_server_startup_logs(False):
                return False
                
            if not self.test_api_connectivity():
                return False
                
            self.log("✅ Default value handling working correctly")
            return True
            
        finally:
            # Restore original env file
            self.restore_env_file(backup)
            
    def test_boolean_conversion(self):
        """Test 3: Boolean Conversion"""
        self.log("=== Test 3: Boolean Conversion ===")
        
        # Backup original env file
        backup = self.backup_env_file()
        
        try:
            test_cases = [
                ("true", True),
                ("True", True),
                ("TRUE", True),
                ("false", False),
                ("False", False),
                ("FALSE", False),
                ("yes", False),  # Should be False (not recognized as true)
                ("1", False),    # Should be False (not recognized as true)
                ("", False),     # Empty string should be False
            ]
            
            for test_value, expected_bool in test_cases:
                self.log(f"Testing SPORTS_CRICKET_ENABLED='{test_value}' -> expected: {expected_bool}")
                self.update_env_file(test_value)
                
                if not self.restart_backend_service():
                    return False
                    
                if not self.check_server_startup_logs(expected_bool):
                    return False
                    
                if not self.test_api_connectivity():
                    return False
                    
            self.log("✅ Boolean conversion working correctly")
            return True
            
        finally:
            # Restore original env file
            self.restore_env_file(backup)
            
    def test_logging_functionality(self):
        """Test 4: Logging Functionality"""
        self.log("=== Test 4: Logging Functionality ===")
        
        # Backup original env file
        backup = self.backup_env_file()
        
        try:
            # Test that logging works for both true and false values
            for test_value, expected_bool in [("true", True), ("false", False)]:
                self.log(f"Testing logging for SPORTS_CRICKET_ENABLED={test_value}")
                self.update_env_file(test_value)
                
                if not self.restart_backend_service():
                    return False
                    
                # Check logs contain the expected message
                logs = self.get_backend_logs(50)
                expected_log = f"Cricket feature enabled: {expected_bool}"
                
                if expected_log not in logs:
                    self.log(f"Expected log message '{expected_log}' not found", "ERROR")
                    return False
                    
                self.log(f"✅ Logging working for {test_value} -> {expected_bool}")
                
            return True
            
        finally:
            # Restore original env file
            self.restore_env_file(backup)
            
    def test_server_startup_stability(self):
        """Test 5: Server Startup Stability"""
        self.log("=== Test 5: Server Startup Stability ===")
        
        # Backup original env file
        backup = self.backup_env_file()
        
        try:
            # Test multiple restarts with different values
            test_values = ["true", "false", "True", "FALSE"]
            
            for test_value in test_values:
                self.log(f"Testing server stability with SPORTS_CRICKET_ENABLED={test_value}")
                self.update_env_file(test_value)
                
                if not self.restart_backend_service():
                    return False
                    
                # Wait a bit more to ensure stability
                time.sleep(3)
                
                if not self.test_api_connectivity():
                    return False
                    
                # Check for any error logs
                logs = self.get_backend_logs(20)
                if "ERROR" in logs or "Exception" in logs or "Traceback" in logs:
                    self.log(f"Error found in logs after restart with {test_value}", "ERROR")
                    self.log(f"Recent logs: {logs}")
                    return False
                    
            self.log("✅ Server startup stability confirmed")
            return True
            
        finally:
            # Restore original env file
            self.restore_env_file(backup)
            
    def test_existing_functionality_integrity(self):
        """Test 6: Existing Functionality Integrity"""
        self.log("=== Test 6: Existing Functionality Integrity ===")
        
        # Backup original env file
        backup = self.backup_env_file()
        
        try:
            # Test with cricket flag enabled
            self.log("Testing existing functionality with cricket flag enabled")
            self.update_env_file("true")
            
            if not self.restart_backend_service():
                return False
                
            if not self.test_existing_functionality():
                return False
                
            # Test with cricket flag disabled
            self.log("Testing existing functionality with cricket flag disabled")
            self.update_env_file("false")
            
            if not self.restart_backend_service():
                return False
                
            if not self.test_existing_functionality():
                return False
                
            self.log("✅ Existing functionality integrity maintained")
            return True
            
        finally:
            # Restore original env file
            self.restore_env_file(backup)
            
    def run_all_tests(self):
        """Run all cricket feature tests"""
        self.log("🏏 Starting SPORTS_CRICKET_ENABLED Feature Tests")
        
        results = {}
        
        test_suites = [
            ("environment_variable_reading", self.test_environment_variable_reading),
            ("default_value_handling", self.test_default_value_handling),
            ("boolean_conversion", self.test_boolean_conversion),
            ("logging_functionality", self.test_logging_functionality),
            ("server_startup_stability", self.test_server_startup_stability),
            ("existing_functionality_integrity", self.test_existing_functionality_integrity),
        ]
        
        for test_name, test_func in test_suites:
            try:
                self.log(f"\n--- Running {test_name} ---")
                results[test_name] = test_func()
                
                if results[test_name]:
                    self.log(f"✅ {test_name} PASSED")
                else:
                    self.log(f"❌ {test_name} FAILED")
                    
            except Exception as e:
                self.log(f"❌ {test_name} CRASHED: {str(e)}", "ERROR")
                results[test_name] = False
                
        # Final restart to ensure system is in good state
        self.log("\n--- Final System Restart ---")
        if not self.restart_backend_service():
            self.log("Warning: Final restart failed", "ERROR")
            
        return results

def main():
    """Main test execution"""
    tester = CricketFeatureTester()
    results = tester.run_all_tests()
    
    # Print summary
    print("\n" + "="*60)
    print("SPORTS_CRICKET_ENABLED FEATURE TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:35} {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All cricket feature tests passed!")
        print("✅ SPORTS_CRICKET_ENABLED environment variable is working correctly")
        return True
    else:
        print("⚠️  Some cricket feature tests failed")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)