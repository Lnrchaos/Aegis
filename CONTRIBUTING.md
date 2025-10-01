# Contributing to Aegis

Thank you for your interest in contributing to Aegis! This document provides guidelines for contributing to the project.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/your-username/aegis-lang.git
   cd aegis-lang
   ```
3. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```
4. **Make your changes**
5. **Add tests** for new functionality
6. **Submit a pull request**

## Development Setup

### Prerequisites
- Python 3.8 or higher
- Git

### Installation
```bash
# Clone the repository
git clone https://github.com/aegis-lang/aegis-lang.git
cd aegis-lang

# Install in development mode
pip install -e .

# Install development dependencies
pip install -r requirements.txt
```

### Testing
```bash
# Run the REPL to test basic functionality
python -m aegis

# Run tests (when available)
python -m aegtest run
```

## Code Style

- Follow **PEP 8** for Python code
- Use **meaningful variable names**
- Add **docstrings** to functions and classes
- Keep **line length under 100 characters**
- Use **type hints** where appropriate

### Example:
```python
def scan_network(target: str, ports: list[int]) -> dict:
    """
    Scan a network target for open ports.
    
    Args:
        target: IP address or hostname to scan
        ports: List of ports to check
        
    Returns:
        Dictionary with scan results
    """
    results = {}
    for port in ports:
        if is_port_open(target, port):
            results[port] = "open"
    return results
```

## Submitting Changes

### Before Submitting
1. **Ensure all tests pass**
2. **Update documentation** if needed
3. **Add your name** to CONTRIBUTORS.md
4. **Write a clear commit message**

### Commit Message Format
```
type(scope): brief description

Longer description if needed

Fixes #123
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

### Pull Request Template
```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Tests pass locally
- [ ] New tests added for new functionality
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No breaking changes (or clearly documented)
```

## Areas for Contribution

### High Priority
- **Language Server Protocol (LSP)** implementation
- **Performance optimizations**
- **Additional cybersecurity keywords**
- **Enhanced error messages**
- **Better documentation**

### Medium Priority
- **IDE extensions** (VS Code, Vim, Emacs)
- **Cloud execution platform**
- **Enterprise features**
- **Additional standard library modules**

### Low Priority
- **Alternative syntax highlighting themes**
- **Additional example programs**
- **Community tutorials**

## Security Considerations

When contributing security-related features:

1. **Never include real exploits** in examples
2. **Use placeholder data** for sensitive information
3. **Add appropriate warnings** for dangerous operations
4. **Follow responsible disclosure** for security issues

## Getting Help

- **GitHub Issues**: For bug reports and feature requests
- **Discussions**: For questions and general discussion
- **Discord**: For real-time chat (if available)

## Recognition

Contributors will be:
- Listed in CONTRIBUTORS.md
- Mentioned in release notes
- Given credit in documentation

## Code of Conduct

We are committed to providing a welcoming and inclusive experience for everyone. Please:

- Be respectful and constructive
- Focus on what's best for the community
- Show empathy towards other community members
- Accept constructive criticism gracefully

## License

By contributing to Aegis, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to Aegis! 🚀
