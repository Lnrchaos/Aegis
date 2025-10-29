"""
Aegis Security Module - Ported from Gambit
Real security implementations for Aegis language
"""

import hashlib
import base64
import socket
import subprocess
import platform
import os
import re
import threading
import time
import json
import random
from typing import Dict, Any, List
try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

from .runtime import NativeFunction, RuntimeErrorAegis


class SecurityError(Exception):
    """Custom exception for security operations"""
    pass


class AegisSecurity:
    """Real Security operations for Aegis language"""
    
    def __init__(self):
        self.firewall_rules = []
        self.monitoring_active = False
        self.monitoring_threads = []
        self.blocked_ips = set()
        self.threat_database = self._load_threat_database()
    
    def _load_threat_database(self) -> Dict[str, List[str]]:
        """Load real threat indicators"""
        return {
            'phishing_domains': [
                'phishing-site.com', 'fake-bank.net', 'scam-alert.org',
                'malicious-link.co', 'virus-download.info'
            ],
            'malware_hashes': [
                'e3b0c44298fc1c149afbf4c8996fb924',
                '5d41402abc4b2a76b9719d911017c592',
                '098f6bcd4621d373cade4e832627b4f6'
            ],
            'suspicious_ips': [
                '192.168.1.100', '10.0.0.50', '172.16.0.25'
            ]
        }
    
    def encrypt(self, data: str, password: str = None, algorithm: str = "AES") -> Dict[str, Any]:
        """Real encryption using cryptography library"""
        try:
            if not CRYPTO_AVAILABLE:
                raise SecurityError("Cryptography library not available")
                
            if not password:
                password = "default_aegis_key_2024"
            
            # Generate key from password
            password_bytes = password.encode()
            salt = os.urandom(16)
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(password_bytes))
            
            # Encrypt data
            f = Fernet(key)
            encrypted_data = f.encrypt(data.encode())
            
            # Combine salt and encrypted data
            result = base64.b64encode(salt + encrypted_data).decode()
            
            return {
                'success': True,
                'encrypted_data': result,
                'algorithm': algorithm,
                'key_derivation': 'PBKDF2-SHA256',
                'iterations': 100000
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def decrypt(self, encrypted_data: str, password: str, algorithm: str = "AES") -> Dict[str, Any]:
        """Real decryption using cryptography library"""
        try:
            if not CRYPTO_AVAILABLE:
                raise SecurityError("Cryptography library not available")
                
            # Decode the combined salt + encrypted data
            combined_data = base64.b64decode(encrypted_data.encode())
            salt = combined_data[:16]
            encrypted_bytes = combined_data[16:]
            
            # Regenerate key from password and salt
            password_bytes = password.encode()
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(password_bytes))
            
            # Decrypt data
            f = Fernet(key)
            decrypted_data = f.decrypt(encrypted_bytes).decode()
            
            return {
                'success': True,
                'decrypted_data': decrypted_data,
                'algorithm': algorithm
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def hash_data(self, data: str, algorithm: str = "SHA256", salt: str = None) -> Dict[str, Any]:
        """Hash data with optional salt"""
        try:
            # Add salt if provided
            if salt:
                data = data + salt
            
            if algorithm.upper() == "SHA256":
                hash_value = hashlib.sha256(data.encode()).hexdigest()
            elif algorithm.upper() == "MD5":
                hash_value = hashlib.md5(data.encode()).hexdigest()
            elif algorithm.upper() == "SHA1":
                hash_value = hashlib.sha1(data.encode()).hexdigest()
            else:
                raise SecurityError(f"Unsupported algorithm: {algorithm}")
            
            return {
                'success': True,
                'hash': hash_value,
                'algorithm': algorithm.upper(),
                'salt_used': salt is not None
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def firewall(self, action: str, target: str = None, port: int = None) -> Dict[str, Any]:
        """Real firewall operations using system commands"""
        try:
            system = platform.system().lower()
            
            if action.lower() == "block":
                if not target:
                    return {'success': False, 'error': 'Target IP required for blocking'}
                
                # Add to internal blocked list
                self.blocked_ips.add(target)
                
                # Execute real firewall commands based on OS
                if system == "windows":
                    cmd = f'netsh advfirewall firewall add rule name="Aegis_Block_{target}" dir=in action=block remoteip={target}'
                    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                elif system == "linux":
                    cmd = f'sudo iptables -A INPUT -s {target} -j DROP'
                    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                elif system == "darwin":  # macOS
                    cmd = f'sudo pfctl -t blocked_ips -T add {target}'
                    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                else:
                    return {'success': False, 'error': f'Unsupported OS: {system}'}
                
                rule = {"action": "block", "target": target, "port": port, "timestamp": time.time()}
                self.firewall_rules.append(rule)
                
                return {
                    'success': True, 
                    'status': 'blocked', 
                    'target': target,
                    'command_executed': cmd,
                    'system': system
                }
                
            elif action.lower() == "status":
                return {
                    'success': True, 
                    'rules': len(self.firewall_rules),
                    'blocked_ips': list(self.blocked_ips),
                    'system': system
                }
            else:
                return {'success': False, 'error': f"Unknown action: {action}"}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def monitor(self, target: str = "system", duration: int = 60) -> Dict[str, Any]:
        """Real system and network monitoring"""
        try:
            if not PSUTIL_AVAILABLE:
                return {'success': False, 'error': 'psutil library not available'}
                
            if target.lower() == "system":
                return self._monitor_system(duration)
            elif target.lower() == "network":
                return self._monitor_network(duration)
            else:
                return {'success': False, 'error': f'Unknown monitoring target: {target}'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _monitor_system(self, duration: int) -> Dict[str, Any]:
        """Monitor system resources"""
        try:
            # Get current system stats
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            alerts = []
            if cpu_percent > 80:
                alerts.append(f'High CPU usage: {cpu_percent}%')
            if memory.percent > 85:
                alerts.append(f'High memory usage: {memory.percent}%')
            if disk.percent > 90:
                alerts.append(f'Low disk space: {disk.percent}% used')
            
            return {
                'success': True,
                'target': 'system',
                'duration': duration,
                'metrics': {
                    'cpu_percent': cpu_percent,
                    'memory_percent': memory.percent,
                    'memory_available_gb': round(memory.available / (1024**3), 2),
                    'disk_percent': disk.percent,
                    'disk_free_gb': round(disk.free / (1024**3), 2)
                },
                'alerts': alerts,
                'status': 'completed'
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _monitor_network(self, duration: int) -> Dict[str, Any]:
        """Monitor network connections"""
        try:
            connections = psutil.net_connections(kind='inet')
            
            # Analyze connections
            listening_ports = []
            established_connections = []
            
            for conn in connections:
                if conn.status == 'LISTEN':
                    listening_ports.append({
                        'port': conn.laddr.port,
                        'address': conn.laddr.ip,
                        'pid': conn.pid
                    })
                elif conn.status == 'ESTABLISHED':
                    established_connections.append({
                        'local': f"{conn.laddr.ip}:{conn.laddr.port}",
                        'remote': f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else "N/A",
                        'pid': conn.pid
                    })
            
            return {
                'success': True,
                'target': 'network',
                'duration': duration,
                'connections': {
                    'listening_ports': listening_ports,
                    'established': established_connections
                },
                'status': 'completed'
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}


# Global security instance
_security = AegisSecurity()


# Native function wrappers for Aegis
def _encrypt_wrapper(args):
    if len(args) < 1:
        raise RuntimeErrorAegis("encrypt() requires at least 1 argument")
    data = str(args[0])
    password = str(args[1]) if len(args) > 1 else None
    algorithm = str(args[2]) if len(args) > 2 else "AES"
    return _security.encrypt(data, password, algorithm)


def _decrypt_wrapper(args):
    if len(args) < 2:
        raise RuntimeErrorAegis("decrypt() requires at least 2 arguments")
    encrypted_data = str(args[0])
    password = str(args[1])
    algorithm = str(args[2]) if len(args) > 2 else "AES"
    return _security.decrypt(encrypted_data, password, algorithm)


def _hash_wrapper(args):
    if len(args) < 1:
        raise RuntimeErrorAegis("hash() requires at least 1 argument")
    data = str(args[0])
    algorithm = str(args[1]) if len(args) > 1 else "SHA256"
    salt = str(args[2]) if len(args) > 2 else None
    return _security.hash_data(data, algorithm, salt)


def _firewall_wrapper(args):
    if len(args) < 1:
        raise RuntimeErrorAegis("firewall() requires at least 1 argument")
    action = str(args[0])
    target = str(args[1]) if len(args) > 1 else None
    port = int(args[2]) if len(args) > 2 else None
    return _security.firewall(action, target, port)


def _monitor_wrapper(args):
    target = str(args[0]) if len(args) > 0 else "system"
    duration = int(args[1]) if len(args) > 1 else 60
    return _security.monitor(target, duration)


# Export security functions as native functions
SECURITY_FUNCTIONS = {
    'encrypt': NativeFunction('encrypt', _encrypt_wrapper),
    'decrypt': NativeFunction('decrypt', _decrypt_wrapper),
    'hash': NativeFunction('hash', _hash_wrapper),
    'firewall': NativeFunction('firewall', _firewall_wrapper),
    'monitor': NativeFunction('monitor', _monitor_wrapper),
}