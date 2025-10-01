#!/usr/bin/env python3
"""
Aegis Package Manager (aegpm)
Manages dependencies, versions, and package installation for Aegis projects.
"""

import json
import os
import sys
import hashlib
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, asdict
import urllib.request
import urllib.parse


@dataclass
class PackageInfo:
    name: str
    version: str
    source: str  # git URL, registry URL, or local path
    checksum: Optional[str] = None
    dependencies: Dict[str, str] = None  # name -> version constraint


@dataclass
class LockEntry:
    name: str
    version: str
    source: str
    checksum: str
    dependencies: Dict[str, str]


class AegisPackageManager:
    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path.cwd()
        self.manifest_path = self.project_root / "aegpm.json"
        self.lock_path = self.project_root / "aeg.lock"
        self.vendor_path = self.project_root / "vendor"
        self.cache_path = Path.home() / ".aegpm" / "cache"
        self.cache_path.mkdir(parents=True, exist_ok=True)
        
    def init(self, name: str, version: str = "1.0.0") -> None:
        """Initialize a new Aegis project with package manifest."""
        if self.manifest_path.exists():
            print("Project already initialized")
            return
            
        manifest = {
            "name": name,
            "version": version,
            "dependencies": {},
            "devDependencies": {},
            "scripts": {
                "test": "aeg test",
                "build": "aeg build",
                "run": "aeg run"
            }
        }
        
        with open(self.manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)
        print(f"Initialized project {name} v{version}")
        
    def add(self, package: str, version: str = "latest", dev: bool = False) -> None:
        """Add a dependency to the project."""
        manifest = self._load_manifest()
        deps_key = "devDependencies" if dev else "dependencies"
        
        if deps_key not in manifest:
            manifest[deps_key] = {}
            
        manifest[deps_key][package] = version
        self._save_manifest(manifest)
        print(f"Added {package}@{version} to {'dev' if dev else 'runtime'} dependencies")
        
    def remove(self, package: str) -> None:
        """Remove a dependency from the project."""
        manifest = self._load_manifest()
        removed = False
        
        for deps_key in ["dependencies", "devDependencies"]:
            if package in manifest.get(deps_key, {}):
                del manifest[deps_key][package]
                removed = True
                
        if removed:
            self._save_manifest(manifest)
            print(f"Removed {package}")
        else:
            print(f"Package {package} not found")
            
    def install(self) -> None:
        """Install all dependencies from manifest."""
        manifest = self._load_manifest()
        lockfile = self._load_lockfile()
        
        # Resolve dependency tree
        resolved = self._resolve_dependencies(manifest)
        
        # Install packages
        self.vendor_path.mkdir(exist_ok=True)
        for pkg_name, pkg_info in resolved.items():
            self._install_package(pkg_name, pkg_info)
            
        # Update lockfile
        self._save_lockfile(resolved)
        print(f"Installed {len(resolved)} packages")
        
    def update(self, package: str = None) -> None:
        """Update dependencies."""
        if package:
            manifest = self._load_manifest()
            # Update specific package version
            for deps_key in ["dependencies", "devDependencies"]:
                if package in manifest.get(deps_key, {}):
                    manifest[deps_key][package] = "latest"
            self._save_manifest(manifest)
        self.install()
        
    def publish(self, registry: str = "https://registry.aegis.dev") -> None:
        """Publish package to registry."""
        manifest = self._load_manifest()
        if not manifest.get("name") or not manifest.get("version"):
            print("Package must have name and version to publish")
            return
            
        # Create tarball
        tarball_path = self._create_tarball()
        
        # Upload to registry
        self._upload_package(tarball_path, registry)
        print(f"Published {manifest['name']}@{manifest['version']}")
        
    def _load_manifest(self) -> Dict:
        if not self.manifest_path.exists():
            return {}
        with open(self.manifest_path) as f:
            return json.load(f)
            
    def _save_manifest(self, manifest: Dict) -> None:
        with open(self.manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)
            
    def _load_lockfile(self) -> Dict[str, LockEntry]:
        if not self.lock_path.exists():
            return {}
        with open(self.lock_path) as f:
            data = json.load(f)
        return {name: LockEntry(**entry) for name, entry in data.items()}
        
    def _save_lockfile(self, resolved: Dict[str, PackageInfo]) -> None:
        lock_data = {}
        for name, pkg in resolved.items():
            lock_data[name] = asdict(LockEntry(
                name=pkg.name,
                version=pkg.version,
                source=pkg.source,
                checksum=pkg.checksum or "",
                dependencies=pkg.dependencies or {}
            ))
        with open(self.lock_path, 'w') as f:
            json.dump(lock_data, f, indent=2)
            
    def _resolve_dependencies(self, manifest: Dict) -> Dict[str, PackageInfo]:
        """Resolve dependency tree with version constraints."""
        resolved = {}
        to_resolve = []
        
        # Add direct dependencies
        for deps_key in ["dependencies", "devDependencies"]:
            for name, version in manifest.get(deps_key, {}).items():
                to_resolve.append((name, version))
                
        while to_resolve:
            name, version = to_resolve.pop(0)
            if name in resolved:
                continue
                
            pkg_info = self._fetch_package_info(name, version)
            resolved[name] = pkg_info
            
            # Add sub-dependencies
            for dep_name, dep_version in pkg_info.dependencies.items():
                to_resolve.append((dep_name, dep_version))
                
        return resolved
        
    def _fetch_package_info(self, name: str, version: str) -> PackageInfo:
        """Fetch package information from registry or git."""
        # Try registry first
        try:
            return self._fetch_from_registry(name, version)
        except:
            # Fallback to git
            return self._fetch_from_git(name, version)
            
    def _fetch_from_registry(self, name: str, version: str) -> PackageInfo:
        """Fetch package from registry."""
        registry_url = f"https://registry.aegis.dev/{name}/{version}"
        with urllib.request.urlopen(registry_url) as response:
            data = json.loads(response.read())
        return PackageInfo(**data)
        
    def _fetch_from_git(self, name: str, version: str) -> PackageInfo:
        """Fetch package from git repository."""
        # Assume name is git URL for now
        git_url = name if name.startswith('http') else f"https://github.com/{name}.git"
        return PackageInfo(
            name=name.split('/')[-1].replace('.git', ''),
            version=version,
            source=git_url,
            dependencies={}
        )
        
    def _install_package(self, name: str, pkg_info: PackageInfo) -> None:
        """Install a single package to vendor directory."""
        pkg_dir = self.vendor_path / name
        
        if pkg_info.source.startswith('http'):
            # Git clone
            if pkg_dir.exists():
                subprocess.run(['git', 'pull'], cwd=pkg_dir, check=True)
            else:
                subprocess.run(['git', 'clone', pkg_info.source, str(pkg_dir)], check=True)
        else:
            # Local path
            pkg_dir.symlink_to(Path(pkg_info.source).resolve())
            
    def _create_tarball(self) -> Path:
        """Create tarball of current project."""
        import tarfile
        tarball_path = self.cache_path / f"{self._load_manifest()['name']}.tar.gz"
        with tarfile.open(tarball_path, 'w:gz') as tar:
            tar.add(self.project_root, arcname='.')
        return tarball_path
        
    def _upload_package(self, tarball_path: Path, registry: str) -> None:
        """Upload package to registry."""
        # Implementation would upload to registry
        print(f"Would upload {tarball_path} to {registry}")


def main():
    if len(sys.argv) < 2:
        print("Usage: aegpm <command> [args...]")
        print("Commands: init, add, remove, install, update, publish")
        return
        
    pm = AegisPackageManager()
    command = sys.argv[1]
    
    if command == "init":
        name = sys.argv[2] if len(sys.argv) > 2 else "my-aegis-project"
        version = sys.argv[3] if len(sys.argv) > 3 else "1.0.0"
        pm.init(name, version)
    elif command == "add":
        package = sys.argv[2]
        version = sys.argv[3] if len(sys.argv) > 3 else "latest"
        dev = "--dev" in sys.argv
        pm.add(package, version, dev)
    elif command == "remove":
        package = sys.argv[2]
        pm.remove(package)
    elif command == "install":
        pm.install()
    elif command == "update":
        package = sys.argv[2] if len(sys.argv) > 2 else None
        pm.update(package)
    elif command == "publish":
        registry = sys.argv[2] if len(sys.argv) > 2 else "https://registry.aegis.dev"
        pm.publish(registry)
    else:
        print(f"Unknown command: {command}")


if __name__ == "__main__":
    main()
