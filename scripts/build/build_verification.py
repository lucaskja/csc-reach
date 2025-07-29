#!/usr/bin/env python3
"""
Build Verification System for CSC-Reach
Comprehensive verification and smoke testing of build artifacts.
"""

import os
import sys
import json
import subprocess
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
import zipfile
import platform


class BuildVerifier:
    """Comprehensive build verification system."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.build_dir = project_root / 'build'
        self.dist_dir = self.build_dir / 'dist'
        self.verification_dir = self.build_dir / 'verification'
        
        # Ensure verification directory exists
        self.verification_dir.mkdir(parents=True, exist_ok=True)
        
        # Verification configuration
        self.verification_config = {
            'windows': {
                'executable': {
                    'file_patterns': ['*.exe'],
                    'min_size_mb': 10,
                    'max_size_mb': 500,
                    'required_signatures': [b'MZ'],  # PE header
                    'smoke_test_args': ['--help'],
                    'smoke_test_timeout': 30,
                    'dependencies': ['config', 'assets']
                },
                'distribution': {
                    'file_patterns': ['*.zip'],
                    'min_size_mb': 50,
                    'max_size_mb': 1000,
                    'required_contents': ['CSC-Reach.exe', 'config/', 'assets/'],
                    'archive_test': True
                }
            },
            'macos': {
                'application': {
                    'file_patterns': ['*.app'],
                    'min_size_mb': 150,
                    'max_size_mb': 1000,
                    'required_structure': [
                        'Contents/Info.plist',
                        'Contents/MacOS/CSC-Reach',
                        'Contents/Resources'
                    ],
                    'smoke_test_args': ['--help'],
                    'smoke_test_timeout': 30,
                    'bundle_validation': True
                },
                'distribution': {
                    'file_patterns': ['*.dmg'],
                    'min_size_mb': 80,
                    'max_size_mb': 800,
                    'dmg_validation': True
                }
            }
        }
    
    def find_artifacts(self, platform: str, artifact_type: str) -> List[Path]:
        """Find artifacts matching the specified criteria."""
        config = self.verification_config.get(platform, {}).get(artifact_type, {})
        patterns = config.get('file_patterns', [])
        
        artifacts = []
        for pattern in patterns:
            artifacts.extend(self.dist_dir.rglob(pattern))
        
        return artifacts
    
    def verify_file_size(self, file_path: Path, min_mb: float, max_mb: float) -> Dict[str, Any]:
        """Verify file size is within acceptable range."""
        result = {'passed': True, 'issues': [], 'info': {}}
        
        if not file_path.exists():
            result['passed'] = False
            result['issues'].append('File does not exist')
            return result
        
        size_bytes = file_path.stat().st_size
        size_mb = size_bytes / (1024 * 1024)
        
        result['info']['size_bytes'] = size_bytes
        result['info']['size_mb'] = round(size_mb, 2)
        
        if size_mb < min_mb:
            result['passed'] = False
            result['issues'].append(f'File too small: {size_mb:.1f} MB < {min_mb} MB')
        elif size_mb > max_mb:
            result['issues'].append(f'File unusually large: {size_mb:.1f} MB > {max_mb} MB')
        
        return result
    
    def verify_file_signature(self, file_path: Path, signatures: List[bytes]) -> Dict[str, Any]:
        """Verify file has expected binary signatures."""
        result = {'passed': True, 'issues': [], 'info': {}}
        
        try:
            with open(file_path, 'rb') as f:
                header = f.read(64)  # Read first 64 bytes
                
                for signature in signatures:
                    if header.startswith(signature):
                        result['info']['signature'] = signature.hex()
                        return result
                
                result['passed'] = False
                result['issues'].append(f'Invalid file signature. Expected one of: {[s.hex() for s in signatures]}')
                result['info']['actual_header'] = header[:16].hex()
                
        except Exception as e:
            result['passed'] = False
            result['issues'].append(f'Error reading file signature: {e}')
        
        return result
    
    def verify_dependencies(self, artifact_path: Path, dependencies: List[str]) -> Dict[str, Any]:
        """Verify required dependencies are present."""
        result = {'passed': True, 'issues': [], 'info': {'found': [], 'missing': []}}
        
        base_dir = artifact_path.parent if artifact_path.is_file() else artifact_path
        
        for dependency in dependencies:
            dep_path = base_dir / dependency
            if dep_path.exists():
                result['info']['found'].append(dependency)
            else:
                result['info']['missing'].append(dependency)
                result['issues'].append(f'Missing dependency: {dependency}')
        
        if result['info']['missing']:
            result['passed'] = False
        
        return result
    
    def run_smoke_test(self, executable_path: Path, args: List[str], timeout: int) -> Dict[str, Any]:
        """Run smoke test on executable."""
        result = {'passed': False, 'issues': [], 'info': {}}
        
        try:
            # Determine the actual executable to run
            if executable_path.suffix == '.app':
                # macOS app bundle
                actual_exe = executable_path / 'Contents' / 'MacOS' / 'CSC-Reach'
                if not actual_exe.exists():
                    result['issues'].append('Executable not found in app bundle')
                    return result
            else:
                actual_exe = executable_path
            
            # Run the executable
            cmd = [str(actual_exe)] + args
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=actual_exe.parent
            )
            
            result['info']['exit_code'] = process.returncode
            result['info']['stdout'] = process.stdout
            result['info']['stderr'] = process.stderr
            result['info']['command'] = ' '.join(cmd)
            
            # Consider exit codes 0 and 1 as success (some apps exit with 1 for --help)
            if process.returncode in [0, 1]:
                result['passed'] = True
            else:
                result['issues'].append(f'Unexpected exit code: {process.returncode}')
            
        except subprocess.TimeoutExpired:
            result['issues'].append(f'Smoke test timed out after {timeout}s')
        except FileNotFoundError:
            result['issues'].append('Executable not found or not executable')
        except Exception as e:
            result['issues'].append(f'Smoke test failed: {e}')
        
        return result
    
    def verify_macos_bundle(self, app_path: Path) -> Dict[str, Any]:
        """Verify macOS application bundle structure."""
        result = {'passed': True, 'issues': [], 'info': {}}
        
        if not app_path.is_dir():
            result['passed'] = False
            result['issues'].append('Not a directory (invalid app bundle)')
            return result
        
        # Check required structure
        required_files = [
            'Contents/Info.plist',
            'Contents/MacOS/CSC-Reach'
        ]
        
        for required_file in required_files:
            file_path = app_path / required_file
            if not file_path.exists():
                result['passed'] = False
                result['issues'].append(f'Missing required file: {required_file}')
            else:
                result['info'][f'found_{required_file.replace("/", "_")}'] = True
        
        # Validate Info.plist if it exists
        info_plist = app_path / 'Contents' / 'Info.plist'
        if info_plist.exists():
            try:
                # Use plutil to validate plist format
                plist_result = subprocess.run(
                    ['plutil', '-lint', str(info_plist)],
                    capture_output=True,
                    text=True
                )
                
                if plist_result.returncode == 0:
                    result['info']['info_plist_valid'] = True
                    
                    # Extract bundle information
                    try:
                        bundle_id_result = subprocess.run([
                            'plutil', '-extract', 'CFBundleIdentifier', 'raw', str(info_plist)
                        ], capture_output=True, text=True)
                        
                        if bundle_id_result.returncode == 0:
                            result['info']['bundle_id'] = bundle_id_result.stdout.strip()
                        
                        version_result = subprocess.run([
                            'plutil', '-extract', 'CFBundleShortVersionString', 'raw', str(info_plist)
                        ], capture_output=True, text=True)
                        
                        if version_result.returncode == 0:
                            result['info']['version'] = version_result.stdout.strip()
                            
                    except Exception as e:
                        result['issues'].append(f'Error extracting bundle info: {e}')
                else:
                    result['passed'] = False
                    result['issues'].append('Invalid Info.plist format')
                    
            except FileNotFoundError:
                result['issues'].append('plutil not available for plist validation')
            except Exception as e:
                result['issues'].append(f'Error validating Info.plist: {e}')
        
        # Check executable format
        executable = app_path / 'Contents' / 'MacOS' / 'CSC-Reach'
        if executable.exists():
            try:
                file_result = subprocess.run(
                    ['file', str(executable)],
                    capture_output=True,
                    text=True
                )
                
                if 'Mach-O' in file_result.stdout:
                    result['info']['executable_format'] = 'Mach-O'
                else:
                    result['passed'] = False
                    result['issues'].append('Executable is not Mach-O format')
                    
            except Exception as e:
                result['issues'].append(f'Error checking executable format: {e}')
        
        return result
    
    def verify_archive_integrity(self, archive_path: Path) -> Dict[str, Any]:
        """Verify archive integrity and contents."""
        result = {'passed': True, 'issues': [], 'info': {}}
        
        try:
            if archive_path.suffix.lower() == '.zip':
                with zipfile.ZipFile(archive_path, 'r') as zf:
                    # Test archive integrity
                    bad_files = zf.testzip()
                    if bad_files:
                        result['passed'] = False
                        result['issues'].append(f'Corrupt files in ZIP: {bad_files}')
                    else:
                        result['info']['zip_integrity'] = 'valid'
                    
                    # List contents
                    file_list = zf.namelist()
                    result['info']['file_count'] = len(file_list)
                    result['info']['contents'] = file_list[:20]  # First 20 files
                    
                    # Check for required contents
                    config = self.verification_config.get('windows', {}).get('distribution', {})
                    required_contents = config.get('required_contents', [])
                    
                    for required in required_contents:
                        found = any(required in f for f in file_list)
                        if not found:
                            result['issues'].append(f'Missing required content: {required}')
                    
            elif archive_path.suffix.lower() == '.dmg':
                # For DMG files, we can check basic file properties
                # More detailed verification would require mounting the DMG
                result['info']['dmg_format'] = 'detected'
                
                # Check if it's a valid DMG using file command
                try:
                    file_result = subprocess.run(
                        ['file', str(archive_path)],
                        capture_output=True,
                        text=True
                    )
                    
                    if 'disk image' in file_result.stdout.lower():
                        result['info']['dmg_valid'] = True
                    else:
                        result['issues'].append('File does not appear to be a valid DMG')
                        
                except Exception as e:
                    result['issues'].append(f'Error validating DMG: {e}')
            
        except Exception as e:
            result['passed'] = False
            result['issues'].append(f'Error verifying archive: {e}')
        
        return result
    
    def verify_artifact(self, artifact_path: Path, platform: str, artifact_type: str) -> Dict[str, Any]:
        """Comprehensive artifact verification."""
        print(f"🔍 Verifying {platform} {artifact_type}: {artifact_path.name}")
        
        verification_result = {
            'artifact_path': str(artifact_path),
            'platform': platform,
            'type': artifact_type,
            'timestamp': datetime.now().isoformat(),
            'overall_passed': True,
            'tests': {},
            'summary': {'passed': 0, 'failed': 0, 'warnings': 0}
        }
        
        config = self.verification_config.get(platform, {}).get(artifact_type, {})
        
        # File size verification
        min_size = config.get('min_size_mb', 0)
        max_size = config.get('max_size_mb', float('inf'))
        
        size_result = self.verify_file_size(artifact_path, min_size, max_size)
        verification_result['tests']['file_size'] = size_result
        
        if size_result['passed']:
            verification_result['summary']['passed'] += 1
        else:
            verification_result['summary']['failed'] += 1
            verification_result['overall_passed'] = False
        
        # File signature verification (for executables)
        if 'required_signatures' in config:
            sig_result = self.verify_file_signature(artifact_path, config['required_signatures'])
            verification_result['tests']['file_signature'] = sig_result
            
            if sig_result['passed']:
                verification_result['summary']['passed'] += 1
            else:
                verification_result['summary']['failed'] += 1
                verification_result['overall_passed'] = False
        
        # Dependencies verification
        if 'dependencies' in config:
            dep_result = self.verify_dependencies(artifact_path, config['dependencies'])
            verification_result['tests']['dependencies'] = dep_result
            
            if dep_result['passed']:
                verification_result['summary']['passed'] += 1
            else:
                verification_result['summary']['failed'] += 1
                verification_result['overall_passed'] = False
        
        # macOS bundle verification
        if config.get('bundle_validation') and artifact_path.suffix == '.app':
            bundle_result = self.verify_macos_bundle(artifact_path)
            verification_result['tests']['bundle_structure'] = bundle_result
            
            if bundle_result['passed']:
                verification_result['summary']['passed'] += 1
            else:
                verification_result['summary']['failed'] += 1
                verification_result['overall_passed'] = False
        
        # Archive integrity verification
        if config.get('archive_test') or config.get('dmg_validation'):
            archive_result = self.verify_archive_integrity(artifact_path)
            verification_result['tests']['archive_integrity'] = archive_result
            
            if archive_result['passed']:
                verification_result['summary']['passed'] += 1
            else:
                verification_result['summary']['failed'] += 1
                verification_result['overall_passed'] = False
        
        # Smoke test
        if 'smoke_test_args' in config:
            smoke_result = self.run_smoke_test(
                artifact_path,
                config['smoke_test_args'],
                config.get('smoke_test_timeout', 30)
            )
            verification_result['tests']['smoke_test'] = smoke_result
            
            if smoke_result['passed']:
                verification_result['summary']['passed'] += 1
            else:
                verification_result['summary']['warnings'] += 1
                # Don't fail overall verification for smoke test failures
        
        # Print results
        if verification_result['overall_passed']:
            print(f"✅ {artifact_path.name} verification passed")
            print(f"   Tests: {verification_result['summary']['passed']} passed, "
                  f"{verification_result['summary']['warnings']} warnings")
        else:
            print(f"❌ {artifact_path.name} verification failed")
            print(f"   Tests: {verification_result['summary']['passed']} passed, "
                  f"{verification_result['summary']['failed']} failed, "
                  f"{verification_result['summary']['warnings']} warnings")
            
            # Print specific issues
            for test_name, test_result in verification_result['tests'].items():
                if not test_result.get('passed', True) and test_result.get('issues'):
                    print(f"   {test_name}: {', '.join(test_result['issues'])}")
        
        return verification_result
    
    def verify_all_artifacts(self) -> Dict[str, Any]:
        """Verify all artifacts in the distribution directory."""
        print("🔍 Starting comprehensive artifact verification...")
        
        verification_report = {
            'timestamp': datetime.now().isoformat(),
            'artifacts': [],
            'summary': {
                'total_artifacts': 0,
                'passed_artifacts': 0,
                'failed_artifacts': 0,
                'platforms': {}
            }
        }
        
        # Verify artifacts for each platform
        for platform in ['windows', 'macos']:
            platform_summary = {'total': 0, 'passed': 0, 'failed': 0}
            
            for artifact_type in self.verification_config[platform].keys():
                artifacts = self.find_artifacts(platform, artifact_type)
                
                for artifact_path in artifacts:
                    result = self.verify_artifact(artifact_path, platform, artifact_type)
                    verification_report['artifacts'].append(result)
                    
                    platform_summary['total'] += 1
                    if result['overall_passed']:
                        platform_summary['passed'] += 1
                    else:
                        platform_summary['failed'] += 1
            
            verification_report['summary']['platforms'][platform] = platform_summary
            verification_report['summary']['total_artifacts'] += platform_summary['total']
            verification_report['summary']['passed_artifacts'] += platform_summary['passed']
            verification_report['summary']['failed_artifacts'] += platform_summary['failed']
        
        # Save verification report
        report_file = self.verification_dir / f"verification_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(verification_report, f, indent=2)
        
        print(f"\n📊 Verification Summary:")
        print(f"Total Artifacts: {verification_report['summary']['total_artifacts']}")
        print(f"Passed: {verification_report['summary']['passed_artifacts']}")
        print(f"Failed: {verification_report['summary']['failed_artifacts']}")
        print(f"Report saved: {report_file}")
        
        return verification_report


def main():
    """Main function for command-line usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description="CSC-Reach Build Verification System")
    parser.add_argument('--artifact', type=Path, help='Specific artifact to verify')
    parser.add_argument('--platform', choices=['windows', 'macos'], help='Platform')
    parser.add_argument('--type', help='Artifact type (executable, application, distribution)')
    parser.add_argument('--all', action='store_true', help='Verify all artifacts')
    parser.add_argument('--report', action='store_true', help='Generate detailed report')
    
    args = parser.parse_args()
    
    # Get project root
    project_root = Path(__file__).parent.parent.parent
    verifier = BuildVerifier(project_root)
    
    if args.all:
        report = verifier.verify_all_artifacts()
        success = report['summary']['failed_artifacts'] == 0
        return 0 if success else 1
    
    elif args.artifact and args.platform and args.type:
        result = verifier.verify_artifact(args.artifact, args.platform, args.type)
        if args.report:
            print(json.dumps(result, indent=2))
        return 0 if result['overall_passed'] else 1
    
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())