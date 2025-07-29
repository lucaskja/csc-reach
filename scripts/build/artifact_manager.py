#!/usr/bin/env python3
"""
Build Artifact Management System for CSC-Reach
Handles artifact storage, verification, and distribution management.
"""

import os
import sys
import json
import hashlib
import shutil
import zipfile
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import subprocess


class ArtifactManager:
    """Manages build artifacts with comprehensive verification and storage."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.build_dir = project_root / 'build'
        self.dist_dir = self.build_dir / 'dist'
        self.artifacts_dir = self.build_dir / 'artifacts'
        self.cache_dir = self.build_dir / 'cache'
        self.logs_dir = self.build_dir / 'logs'
        
        # Ensure directories exist
        for directory in [self.artifacts_dir, self.cache_dir, self.logs_dir]:
            directory.mkdir(parents=True, exist_ok=True)
        
        # Artifact configuration
        self.artifact_config = {
            'windows': {
                'executable': {
                    'name': 'CSC-Reach.exe',
                    'min_size_mb': 10,
                    'max_size_mb': 500,
                    'required_files': ['config', 'assets', 'multichannel_messaging'],
                    'verification': ['pe_format', 'dependencies', 'smoke_test']
                },
                'distribution': {
                    'name': 'CSC-Reach-Windows.zip',
                    'min_size_mb': 50,
                    'max_size_mb': 1000,
                    'contents': ['CSC-Reach.exe', 'config/', 'assets/'],
                    'verification': ['zip_integrity', 'contents_check']
                }
            },
            'macos': {
                'application': {
                    'name': 'CSC-Reach.app',
                    'min_size_mb': 150,
                    'max_size_mb': 1000,
                    'required_files': ['Contents/Info.plist', 'Contents/MacOS/CSC-Reach'],
                    'verification': ['bundle_structure', 'executable_format', 'smoke_test']
                },
                'distribution': {
                    'name': 'CSC-Reach-macOS.dmg',
                    'min_size_mb': 80,
                    'max_size_mb': 800,
                    'contents': ['CSC-Reach.app'],
                    'verification': ['dmg_integrity', 'contents_check']
                }
            }
        }
    
    def calculate_file_hash(self, file_path: Path, algorithm: str = 'sha256') -> str:
        """Calculate file hash for integrity verification."""
        hash_obj = hashlib.new(algorithm)
        
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_obj.update(chunk)
        
        return hash_obj.hexdigest()
    
    def get_file_info(self, file_path: Path) -> Dict:
        """Get comprehensive file information."""
        if not file_path.exists():
            return {'exists': False}
        
        stat = file_path.stat()
        
        return {
            'exists': True,
            'size_bytes': stat.st_size,
            'size_mb': round(stat.st_size / (1024 * 1024), 2),
            'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
            'sha256': self.calculate_file_hash(file_path),
            'md5': self.calculate_file_hash(file_path, 'md5')
        }
    
    def verify_windows_executable(self, exe_path: Path) -> Dict:
        """Verify Windows executable integrity and format."""
        results = {'valid': True, 'issues': [], 'info': {}}
        
        if not exe_path.exists():
            results['valid'] = False
            results['issues'].append('Executable file not found')
            return results
        
        # Get file info
        file_info = self.get_file_info(exe_path)
        results['info'] = file_info
        
        # Check file size
        config = self.artifact_config['windows']['executable']
        if file_info['size_mb'] < config['min_size_mb']:
            results['valid'] = False
            results['issues'].append(f"File too small: {file_info['size_mb']} MB < {config['min_size_mb']} MB")
        elif file_info['size_mb'] > config['max_size_mb']:
            results['issues'].append(f"File unusually large: {file_info['size_mb']} MB > {config['max_size_mb']} MB")
        
        # Check PE format (Windows executable)
        try:
            with open(exe_path, 'rb') as f:
                signature = f.read(2)
                if signature != b'MZ':
                    results['valid'] = False
                    results['issues'].append('Invalid PE executable format')
                else:
                    results['info']['pe_format'] = 'valid'
        except Exception as e:
            results['valid'] = False
            results['issues'].append(f'Error reading executable: {e}')
        
        # Check for required dependencies
        exe_dir = exe_path.parent
        for required_file in config['required_files']:
            dep_path = exe_dir / required_file
            if not dep_path.exists():
                results['issues'].append(f'Missing dependency: {required_file}')
        
        return results
    
    def verify_macos_application(self, app_path: Path) -> Dict:
        """Verify macOS application bundle integrity."""
        results = {'valid': True, 'issues': [], 'info': {}}
        
        if not app_path.exists():
            results['valid'] = False
            results['issues'].append('Application bundle not found')
            return results
        
        # Get bundle info
        try:
            size_result = subprocess.run(['du', '-s', str(app_path)], 
                                       capture_output=True, text=True)
            if size_result.returncode == 0:
                size_kb = int(size_result.stdout.split()[0])
                size_mb = round(size_kb / 1024, 2)
                results['info']['size_mb'] = size_mb
            else:
                results['info']['size_mb'] = 0
        except:
            results['info']['size_mb'] = 0
        
        # Check bundle size
        config = self.artifact_config['macos']['application']
        if results['info']['size_mb'] < config['min_size_mb']:
            results['valid'] = False
            results['issues'].append(f"Bundle too small: {results['info']['size_mb']} MB < {config['min_size_mb']} MB")
        elif results['info']['size_mb'] > config['max_size_mb']:
            results['issues'].append(f"Bundle unusually large: {results['info']['size_mb']} MB > {config['max_size_mb']} MB")
        
        # Check bundle structure
        for required_file in config['required_files']:
            file_path = app_path / required_file
            if not file_path.exists():
                results['valid'] = False
                results['issues'].append(f'Missing required file: {required_file}')
        
        # Verify Info.plist
        info_plist = app_path / 'Contents' / 'Info.plist'
        if info_plist.exists():
            try:
                # Check if plutil is available for validation
                plutil_result = subprocess.run(['plutil', '-lint', str(info_plist)], 
                                             capture_output=True, text=True)
                if plutil_result.returncode == 0:
                    results['info']['info_plist'] = 'valid'
                    
                    # Extract bundle information
                    try:
                        bundle_id_result = subprocess.run([
                            'plutil', '-extract', 'CFBundleIdentifier', 'raw', str(info_plist)
                        ], capture_output=True, text=True)
                        if bundle_id_result.returncode == 0:
                            results['info']['bundle_id'] = bundle_id_result.stdout.strip()
                        
                        version_result = subprocess.run([
                            'plutil', '-extract', 'CFBundleShortVersionString', 'raw', str(info_plist)
                        ], capture_output=True, text=True)
                        if version_result.returncode == 0:
                            results['info']['version'] = version_result.stdout.strip()
                    except:
                        pass
                else:
                    results['issues'].append('Info.plist format issues')
            except:
                results['issues'].append('Could not validate Info.plist')
        
        # Check executable format
        executable = app_path / 'Contents' / 'MacOS' / 'CSC-Reach'
        if executable.exists():
            try:
                file_result = subprocess.run(['file', str(executable)], 
                                           capture_output=True, text=True)
                if 'Mach-O' in file_result.stdout:
                    results['info']['executable_format'] = 'valid_macho'
                else:
                    results['valid'] = False
                    results['issues'].append('Invalid executable format (not Mach-O)')
            except:
                results['issues'].append('Could not verify executable format')
        
        return results
    
    def run_smoke_test(self, executable_path: Path, platform: str) -> Dict:
        """Run smoke test on the built application."""
        results = {'passed': False, 'output': '', 'error': '', 'exit_code': None}
        
        try:
            if platform == 'windows':
                cmd = [str(executable_path), '--help']
            else:  # macOS
                cmd = [str(executable_path / 'Contents' / 'MacOS' / 'CSC-Reach'), '--help']
            
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                cwd=executable_path.parent if platform == 'windows' else executable_path.parent
            )
            
            results['exit_code'] = process.returncode
            results['output'] = process.stdout
            results['error'] = process.stderr
            
            # Consider exit codes 0 and 1 as success (some apps exit with 1 for --help)
            if process.returncode in [0, 1]:
                results['passed'] = True
            
        except subprocess.TimeoutExpired:
            results['error'] = 'Smoke test timed out'
            results['exit_code'] = 124
        except Exception as e:
            results['error'] = f'Smoke test failed: {e}'
        
        return results
    
    def verify_artifact(self, artifact_path: Path, platform: str, artifact_type: str) -> Dict:
        """Comprehensive artifact verification."""
        print(f"🔍 Verifying {platform} {artifact_type}: {artifact_path.name}")
        
        verification_results = {
            'artifact_path': str(artifact_path),
            'platform': platform,
            'type': artifact_type,
            'timestamp': datetime.now().isoformat(),
            'valid': True,
            'issues': [],
            'warnings': [],
            'info': {},
            'tests': {}
        }
        
        # Platform-specific verification
        if platform == 'windows' and artifact_type == 'executable':
            exe_results = self.verify_windows_executable(artifact_path)
            verification_results['tests']['executable_check'] = exe_results
            if not exe_results['valid']:
                verification_results['valid'] = False
                verification_results['issues'].extend(exe_results['issues'])
            verification_results['info'].update(exe_results['info'])
            
            # Run smoke test
            smoke_results = self.run_smoke_test(artifact_path, platform)
            verification_results['tests']['smoke_test'] = smoke_results
            if not smoke_results['passed']:
                verification_results['warnings'].append('Smoke test did not pass')
        
        elif platform == 'macos' and artifact_type == 'application':
            app_results = self.verify_macos_application(artifact_path)
            verification_results['tests']['application_check'] = app_results
            if not app_results['valid']:
                verification_results['valid'] = False
                verification_results['issues'].extend(app_results['issues'])
            verification_results['info'].update(app_results['info'])
            
            # Run smoke test
            smoke_results = self.run_smoke_test(artifact_path, platform)
            verification_results['tests']['smoke_test'] = smoke_results
            if not smoke_results['passed']:
                verification_results['warnings'].append('Smoke test did not pass')
        
        # Distribution package verification
        elif artifact_type in ['distribution', 'zip', 'dmg']:
            file_info = self.get_file_info(artifact_path)
            verification_results['info'] = file_info
            
            if not file_info['exists']:
                verification_results['valid'] = False
                verification_results['issues'].append('Distribution file not found')
        
        # Print results
        if verification_results['valid']:
            print(f"✅ {artifact_path.name} verification passed")
            if verification_results['warnings']:
                for warning in verification_results['warnings']:
                    print(f"⚠️  Warning: {warning}")
        else:
            print(f"❌ {artifact_path.name} verification failed")
            for issue in verification_results['issues']:
                print(f"   • {issue}")
        
        return verification_results
    
    def store_artifact(self, source_path: Path, platform: str, artifact_type: str, 
                      metadata: Optional[Dict] = None) -> Path:
        """Store artifact with metadata and verification results."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create platform-specific storage directory
        storage_dir = self.artifacts_dir / platform / timestamp
        storage_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy artifact
        if source_path.is_dir():
            dest_path = storage_dir / source_path.name
            shutil.copytree(source_path, dest_path)
        else:
            dest_path = storage_dir / source_path.name
            shutil.copy2(source_path, dest_path)
        
        # Verify stored artifact
        verification_results = self.verify_artifact(dest_path, platform, artifact_type)
        
        # Create metadata file
        artifact_metadata = {
            'source_path': str(source_path),
            'stored_path': str(dest_path),
            'platform': platform,
            'type': artifact_type,
            'timestamp': timestamp,
            'verification': verification_results,
            'custom_metadata': metadata or {}
        }
        
        metadata_file = storage_dir / f"{source_path.stem}_metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(artifact_metadata, f, indent=2)
        
        print(f"📦 Artifact stored: {dest_path}")
        print(f"📄 Metadata saved: {metadata_file}")
        
        return dest_path
    
    def create_build_manifest(self, build_info: Dict) -> Path:
        """Create a comprehensive build manifest."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        manifest_file = self.artifacts_dir / f"build_manifest_{timestamp}.json"
        
        manifest = {
            'build_info': build_info,
            'timestamp': timestamp,
            'artifacts': [],
            'verification_summary': {
                'total_artifacts': 0,
                'valid_artifacts': 0,
                'failed_artifacts': 0,
                'warnings': 0
            }
        }
        
        # Scan for artifacts
        for platform_dir in self.artifacts_dir.iterdir():
            if platform_dir.is_dir() and platform_dir.name in ['windows', 'macos']:
                for build_dir in platform_dir.iterdir():
                    if build_dir.is_dir():
                        for metadata_file in build_dir.glob('*_metadata.json'):
                            try:
                                with open(metadata_file) as f:
                                    artifact_data = json.load(f)
                                    manifest['artifacts'].append(artifact_data)
                                    
                                    # Update summary
                                    manifest['verification_summary']['total_artifacts'] += 1
                                    if artifact_data['verification']['valid']:
                                        manifest['verification_summary']['valid_artifacts'] += 1
                                    else:
                                        manifest['verification_summary']['failed_artifacts'] += 1
                                    
                                    manifest['verification_summary']['warnings'] += len(
                                        artifact_data['verification']['warnings']
                                    )
                            except Exception as e:
                                print(f"⚠️ Error reading metadata {metadata_file}: {e}")
        
        # Save manifest
        with open(manifest_file, 'w') as f:
            json.dump(manifest, f, indent=2)
        
        print(f"📋 Build manifest created: {manifest_file}")
        return manifest_file
    
    def cleanup_old_artifacts(self, keep_days: int = 30):
        """Clean up old artifacts to save space."""
        cutoff_time = datetime.now().timestamp() - (keep_days * 24 * 60 * 60)
        cleaned_count = 0
        
        for platform_dir in self.artifacts_dir.iterdir():
            if platform_dir.is_dir():
                for build_dir in platform_dir.iterdir():
                    if build_dir.is_dir():
                        try:
                            if build_dir.stat().st_mtime < cutoff_time:
                                shutil.rmtree(build_dir)
                                cleaned_count += 1
                                print(f"🗑️  Cleaned old artifact: {build_dir}")
                        except Exception as e:
                            print(f"⚠️ Error cleaning {build_dir}: {e}")
        
        print(f"🧹 Cleaned {cleaned_count} old artifact directories")


def main():
    """Main function for command-line usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description="CSC-Reach Artifact Manager")
    parser.add_argument('action', choices=['verify', 'store', 'manifest', 'cleanup'],
                       help='Action to perform')
    parser.add_argument('--path', type=Path, help='Path to artifact')
    parser.add_argument('--platform', choices=['windows', 'macos'], help='Platform')
    parser.add_argument('--type', help='Artifact type')
    parser.add_argument('--keep-days', type=int, default=30, help='Days to keep artifacts')
    
    args = parser.parse_args()
    
    # Get project root
    project_root = Path(__file__).parent.parent.parent
    manager = ArtifactManager(project_root)
    
    if args.action == 'verify' and args.path and args.platform and args.type:
        results = manager.verify_artifact(args.path, args.platform, args.type)
        print(json.dumps(results, indent=2))
        return 0 if results['valid'] else 1
    
    elif args.action == 'store' and args.path and args.platform and args.type:
        stored_path = manager.store_artifact(args.path, args.platform, args.type)
        print(f"Stored at: {stored_path}")
        return 0
    
    elif args.action == 'manifest':
        build_info = {'timestamp': datetime.now().isoformat()}
        manifest_path = manager.create_build_manifest(build_info)
        print(f"Manifest created: {manifest_path}")
        return 0
    
    elif args.action == 'cleanup':
        manager.cleanup_old_artifacts(args.keep_days)
        return 0
    
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())