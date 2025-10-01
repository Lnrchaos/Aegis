from setuptools import setup, find_packages

setup(
    name="aegis-lang",
    version="1.0.0",
    description="Cybersecurity-focused programming language with dual-mode operation",
    author="Aegis Team",
    author_email="team@aegis-lang.org",
    url="https://github.com/aegis-lang/aegis",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "pyyaml>=6.0",
        "toml>=0.10.2",
        "requests>=2.28.0",
        "beautifulsoup4>=4.11.0",
    ],
    entry_points={
        "console_scripts": [
            "aegis=aegis.repl:main",
            "aegpm=aegpm:main",
            "aegfmt=aegfmt:main",
            "aegtest=aegtest:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Security",
        "Topic :: Software Development :: Interpreters",
    ],
    keywords="cybersecurity, programming-language, security, red-team, blue-team",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
)
