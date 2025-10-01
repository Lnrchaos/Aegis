# Aegis Programming Language

A cybersecurity-focused programming language with built-in security primitives, dual-mode operation (red team/blue team), and comprehensive tooling.

[![Tests](https://github.com/aegis-lang/aegis/workflows/Tests/badge.svg)](https://github.com/aegis-lang/aegis/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/aegis-lang/aegis.git
cd aegis

# Install in development mode
pip install -e .

# Or install from PyPI (when available)
pip install aegis-lang
```

### Basic Usage

```bash
# Start the interactive REPL
aegis

# Initialize a new project
aegpm init my-security-project

# Format your code
aegfmt scan.aeg

# Run tests
aegtest run
```

### First Program

```aeg
~ Hello World in Aegis
set message = "Hello, Aegis!"
print(message)

~ Cybersecurity operations
.mode blue
firewall enable
monitor network
```

## Features

### Core Language
- **Variables**: `set x = value` (declare-if-undefined semantics)
- **Functions**: `def name(params) { body }`
- **Control Flow**: `if/then/else/however/unless/yet`, `while/until`, `for/in`
- **Classes**: Object-oriented programming with inheritance and method overriding
- **Error Handling**: `try/catch/finally`, `throw`, `assert`
- **Async/Await**: Asynchronous programming with promises

### Cybersecurity Features
- **Dual-Mode Operation**: Red team (offensive) and blue team (defensive) modes
- **Security Keywords**: Built-in commands for penetration testing and defense
- **Interactive REPL**: Command-line interface with syntax highlighting
- **Keyword Chaining**: Combine multiple security operations

### Tooling
- **Package Manager**: `aegpm` for dependency management
- **Formatter**: `aegfmt` for code formatting
- **Test Runner**: `aegtest` for unit testing
- **REPL**: Interactive development environment

## Installation

```bash
# Clone the repository
git clone https://github.com/your-org/aegis.git
cd aegis

# Install dependencies
pip install -r requirements.txt

# Make tools executable
chmod +x aegpm.py aegfmt.py aegtest.py
```

## Quick Start

### 1. Create a New Project

```bash
# Initialize a new Aegis project
python aegpm.py init my-security-tool

# Add dependencies
python aegpm.py add crypto-utils
python aegpm.py add network-scanner --dev

# Install dependencies
python aegpm.py install
```

### 2. Write Your First Program

Create `main.aeg`:

```aegis
~ My first Aegis program
set target = "192.168.1.1"

def scan_port(host, port) {
    ~ Port scanning logic
    return "open"
}

def main() {
    set result = scan_port(target, 80)
    print("Port 80 is " + result)
}

main()
```

### 3. Run Your Program

```bash
# Run directly
python -m aegis main.aeg

# Or use the REPL
python -m aegis
```

## Language Syntax

### Variables and Functions

```aegis
~ Variables (declare-if-undefined)
set x = 42
set message = "Hello, Aegis!"

~ Functions
def greet(name) {
    return "Hello, " + name + "!"
}

def add(a, b) {
    return a + b
}
```

### Control Flow

```aegis
~ Conditional logic
if (x > 10) then {
    print("x is greater than 10")
} else {
    print("x is 10 or less")
}

~ Loops
while (x < 100) do {
    set x = x + 1
}

for (i in [1, 2, 3, 4, 5]) {
    print("Number: " + i)
}
```

### Classes and Objects

```aegis
~ Class definition
class SecurityScanner {
    set target = ""
    
    def __init__(host) {
        set this.target = host
    }
    
    def scan_port(port) {
        ~ Port scanning logic
        return "open"
    }
    
    def scan_all() {
        set results = []
        for (port in [80, 443, 22, 21]) {
            set result = this.scan_port(port)
            set results = results + [result]
        }
        return results
    }
}

~ Usage
set scanner = new SecurityScanner("192.168.1.1")
set results = scanner.scan_all()
```

### Error Handling

```aegis
~ Try/catch blocks
try {
    set result = risky_operation()
    print("Success: " + result)
} catch (error) {
    print("Error occurred: " + error.message)
} finally {
    print("Cleanup completed")
}

~ Assertions
assert (x > 0), "x must be positive"
```

### Async Programming

```aegis
~ Async functions
async def fetch_data(url) {
    ~ Simulate network request
    await sleep(1000)
    return "data from " + url
}

~ Promise handling
set promise = fetch_data("https://api.example.com")
promise.then(data => {
    print("Received: " + data)
})
```

## Cybersecurity Features

### Dual-Mode Operation

```aegis
~ Switch to red team mode
.mode red

~ Offensive operations
tunnel active
firewall down
generate payload for android 15
inject target_process

~ Switch to blue team mode  
.mode blue

~ Defensive operations
firewall up
monitor traffic
quarantine suspicious_file
alert if attack_detected
```

### Security Command Chaining

```aegis
~ Complex security workflows
if (tunnel active and firewall down) then {
    generate payload for android 15 and inject
} unless keylogger detected

~ Monitoring and response
monitor traffic and trace source and quarantine if malicious
```

## Package Management

### Creating Packages

```bash
# Initialize package
aegpm init my-security-library

# Add dependencies
aegpm add crypto-utils@^1.2.0
aegpm add network-scanner@latest --dev

# Publish to registry
aegpm publish
```

### Using Packages

```aegis
~ Import packages
import crypto from "crypto-utils"
import scanner from "network-scanner"

~ Use imported functions
set hash = crypto.sha256("password")
set results = scanner.scan("192.168.1.0/24")
```

## Testing

### Writing Tests

Create `tests/security.test.aeg`:

```aegis
~ Test file for security functions
import assert from "test-utils"

def test_encryption() {
    set plaintext = "secret data"
    set encrypted = encrypt(plaintext)
    set decrypted = decrypt(encrypted)
    
    assert_equal(plaintext, decrypted, "Encryption round-trip")
}

def test_port_scan() {
    set result = scan_port("localhost", 80)
    assert_true(result in ["open", "closed"], "Port scan result")
}

~ Run tests
test_encryption()
test_port_scan()
```

### Running Tests

```bash
# Run all tests
aegtest run

# Run specific test pattern
aegtest run "*security*"

# Create test template
aegtest create network-tests
```

## Development Tools

### Code Formatting

```bash
# Format a file
aegfmt main.aeg

# Format entire project
aegfmt src/ --recursive

# Check formatting
aegfmt main.aeg --check
```

### Interactive REPL

```bash
# Start REPL
python -m aegis

# REPL commands
>> set x = 42
42
>> def add(a, b) { return a + b }
>> add(5, 3)
8
>> .mode red
[ok] mode set to red
>> firewall down
[red] Firewall disabled (stub)
>> .exit
```

## Standard Library

### Core Modules

- **crypto**: Encryption, hashing, digital signatures
- **http**: HTTP client and server
- **html**: HTML parsing and manipulation
- **encoding**: Base64, hex, URL encoding
- **regex**: Regular expressions
- **time**: Date and time operations
- **fs**: File system operations
- **json**: JSON serialization
- **yaml**: YAML serialization
- **random**: Random number generation
- **math**: Mathematical functions
- **process**: Process and system operations

### Usage

```aegis
~ Import modules
set crypto = require("crypto")
set http = require("http")
set fs = require("fs")

~ Use module functions
set hash = crypto.sha256("data")
set response = http.get("https://api.example.com")
set content = fs.read_file("config.json")
```

## Examples

### Network Scanner

```aegis
class NetworkScanner {
    set target = ""
    set ports = []
    
    def __init__(host) {
        set this.target = host
        set this.ports = [22, 23, 25, 53, 80, 110, 443, 993, 995]
    }
    
    def scan() {
        set results = []
        for (port in this.ports) {
            set status = this.scan_port(port)
            set results = results + [{"port": port, "status": status}]
        }
        return results
    }
    
    def scan_port(port) {
        ~ Simulate port scanning
        if (port in [80, 443, 22]) {
            return "open"
        }
        return "closed"
    }
}

~ Usage
set scanner = new NetworkScanner("192.168.1.1")
set results = scanner.scan()
print("Scan results: " + results)
```

### Security Monitor

```aegis
class SecurityMonitor {
    set alerts = []
    
    def monitor_traffic() {
        while (true) {
            set traffic = this.capture_traffic()
            if (this.is_suspicious(traffic)) {
                this.alert("Suspicious traffic detected")
            }
            sleep(1000)
        }
    }
    
    def is_suspicious(traffic) {
        ~ Check for suspicious patterns
        return traffic.source in ["malicious-ip.com"]
    }
    
    def alert(message) {
        set this.alerts = this.alerts + [message]
        print("[ALERT] " + message)
    }
}

~ Start monitoring
set monitor = new SecurityMonitor()
monitor.monitor_traffic()
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Support

- Documentation: [docs.aegis.dev](https://docs.aegis.dev)
- Issues: [GitHub Issues](https://github.com/your-org/aegis/issues)
- Community: [Discord](https://discord.gg/aegis)