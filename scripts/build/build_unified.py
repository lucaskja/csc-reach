#!/usr/bin/env python3
"""
Enhanced Unified Build Script for CSC-Reach
Supports building for all platforms with advanced options and error handling.
"""

import sys
import os
import argparse
import subprocess
import shutil
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple


class Colors:
    """ANSI color codes for terminal output."""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'


class BuildManager:
    """Enhanced build manager with comprehensive features."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.scripts_dir = project_root / 'scripts' / 'build'
        self.build_dir = project_root / 'build'
        self.dist_dir = self.build_dir / 'dist'
        self.logs_dir = self.build_dir / 'logs'
        self.start_time = time.time()
        
        # Ensure directories exist
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        
        # Build configuration
        self.build_configs = {
            'macos': {
                'app': {
                    'script': 'build_macos.py',
                    'description': 'Building macOS Application',
                    'output': 'CSC-Reach.app',
                    'emoji': '🍎'
                },
                'dmg': {
                    'script': 'create_dmg.py',
                    'description': 'Creating macOS DMG Installer',
                    'output': 'CSC-Reach-macOS.dmg',
                    'emoji': '📦'
                }
            },
            'windows': {
                'exe': {
                    'script': 'build_windows.py',
                    'description': 'Building Windows Executable',
                    'output': 'CSC-Reach',
                    'emoji': '🪟'
                },
                'zip': {
                    'script': 'create_windows_zip.py',
                    'description': 'Creating Windows ZIP Distribution',
                    'output': 'CSC-Reach-Windows.zip',
                    'emoji': '📦'
                }
            }
        }
    
    def print_header(self, title: str, emoji: str = "🏗️"):
        """Print a formatted header."""
        print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.CYAN}{emoji} {title}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.END}")
    
    def print_step(self, step: str, emoji: str = "🔧"):
        """Print a formatted step."""
        print(f"\n{Colors.BOLD}{Colors.BLUE}{emoji} {step}{Colors.END}")
    
    def print_success(self, message: str, emoji: str = "✅"):
        """Print a success message."""
        print(f"{Colors.GREEN}{emoji} {message}{Colors.END}")
    
    def print_warning(self, message: str, emoji: str = "⚠️"):
        """Print a warning message."""
        print(f"{Colors.YELLOW}{emoji} {message}{Colors.END}")
    
    def print_error(self, message: str, emoji: str = "❌"):
        """Print an error message."""
        print(f"{Colors.RED}{emoji} {message}{Colors.END}")
    
    def clean_build_directory(self, preserve_logs: bool = True):
        """Clean the build directory."""
        self.print_step("Cleaning build directory")
        
        if self.build_dir.exists():
            if preserve_logs and self.logs_dir.exists():
                # Backup logs
                backup_logs = self.project_root / 'logs_backup'
                if backup_logs.exists():
                    shutil.rmtree(backup_logs)
                shutil.copytree(self.logs_dir, backup_logs)
                self.print_success(f"Logs backed up to {backup_logs}")
            
            shutil.rmtree(self.build_dir)
            self.print_success("Build directory cleaned")
            
            if preserve_logs and backup_logs.exists():
                # Restore logs
                self.logs_dir.mkdir(parents=True, exist_ok=True)
                for log_file in backup_logs.iterdir():
                    shutil.copy2(log_file, self.logs_dir)
                shutil.rmtree(backup_logs)
                self.print_success("Logs restored")
        
        # Ensure directories exist
        self.dist_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
    
    def check_prerequisites(self) -> bool:
        """Check if all prerequisites are met."""
        self.print_step("Checking prerequisites")
        
        issues = []
        
        # Check Python version
        if sys.version_info < (3, 8):
            issues.append("Python 3.8+ required")
        else:
            self.print_success(f"Python {sys.version.split()[0]} ✓")
        
        # Check virtual environment
        if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
            self.print_success("Virtual environment active ✓")
        else:
            self.print_warning("Virtual environment not detected")
        
        # Check required packages
        required_packages = ['PySide6', 'pandas', 'PyInstaller', 'yaml', 'chardet']
        for package in required_packages:
            try:
                __import__(package.lower().replace('-', '_'))
                self.print_success(f"{package} installed ✓")
            except ImportError:
                issues.append(f"{package} not installed")
        
        # Check build scripts
        for platform, configs in self.build_configs.items():
            for build_type, config in configs.items():
                script_path = self.scripts_dir / config['script']
                if not script_path.exists():
                    issues.append(f"Missing script: {config['script']}")
                else:
                    self.print_success(f"Script {config['script']} found ✓")
        
        if issues:
            self.print_error("Prerequisites check failed:")
            for issue in issues:
                print(f"  • {issue}")
            return False
        
        self.print_success("All prerequisites met!")
        return True
    
    def run_build_step(self, platform: str, build_type: str, config: dict) -> Tuple[bool, float]:
        """Run a single build step."""
        script_path = self.scripts_dir / config['script']
        description = config['description']
        emoji = config.get('emoji', '🔧')
        
        self.print_step(f"{emoji} {description}")
        
        # Create log file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = self.logs_dir / f"{platform}_{build_type}_{timestamp}.log"
        
        start_time = time.time()
        
        try:
            with open(log_file, 'w') as log:
                log.write(f"=== {description} ===\n")
                log.write(f"Started: {datetime.now().isoformat()}\n")
                log.write(f"Script: {script_path}\n")
                log.write(f"Working Directory: {self.project_root}\n\n")
                
                result = subprocess.run([
                    sys.executable, str(script_path)
                ], 
                cwd=self.project_root,
                capture_output=True, 
                text=True, 
                timeout=1800  # 30 minute timeout
                )
                
                log.write("=== STDOUT ===\n")
                log.write(result.stdout)
                log.write("\n=== STDERR ===\n")
                log.write(result.stderr)
                log.write(f"\n=== Exit Code: {result.returncode} ===\n")
                
                if result.returncode == 0:
                    duration = time.time() - start_time
                    self.print_success(f"{description} completed in {duration:.1f}s")
                    log.write(f"Completed successfully in {duration:.1f}s\n")
                    return True, duration
                else:
                    self.print_error(f"{description} failed with exit code {result.returncode}")
                    log.write(f"Failed with exit code {result.returncode}\n")
                    
                    # Print last few lines of stderr for immediate feedback
                    if result.stderr:
                        stderr_lines = result.stderr.strip().split('\n')[-5:]
                        print(f"{Colors.RED}Last error lines:{Colors.END}")
                        for line in stderr_lines:
                            print(f"  {line}")
                    
                    return False, time.time() - start_time
                    
        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            self.print_error(f"{description} timed out after {duration:.1f}s")
            with open(log_file, 'a') as log:
                log.write(f"\nTIMEOUT after {duration:.1f}s\n")
            return False, duration
            
        except Exception as e:
            duration = time.time() - start_time
            self.print_error(f"{description} failed: {e}")
            with open(log_file, 'a') as log:
                log.write(f"\nEXCEPTION: {e}\n")
            return False, duration
    
    def get_file_size(self, file_path: Path) -> str:
        """Get human-readable file size."""
        if not file_path.exists():
            return "N/A"
        
        size_bytes = file_path.stat().st_size
        
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        
        return f"{size_bytes:.1f} TB"
    
    def verify_outputs(self, platform: str) -> Dict[str, bool]:
        """Verify that build outputs exist."""
        results = {}
        
        for build_type, config in self.build_configs[platform].items():
            output_name = config['output']
            
            # Check multiple possible locations
            possible_paths = [
                self.dist_dir / output_name,
                self.dist_dir / platform / output_name,
                self.project_root / 'dist' / output_name
            ]
            
            found = False
            for path in possible_paths:
                if path.exists():
                    size = self.get_file_size(path)
                    self.print_success(f"{output_name}: {size}")
                    results[build_type] = True
                    found = True
                    break
            
            if not found:
                self.print_error(f"{output_name}: Not found")
                results[build_type] = False
        
        return results
    
    def build_platform(self, platform: str, build_types: Optional[List[str]] = None) -> Dict[str, bool]:
        """Build for a specific platform."""
        if platform not in self.build_configs:
            self.print_error(f"Unknown platform: {platform}")
            return {}
        
        platform_config = self.build_configs[platform]
        if build_types is None:
            build_types = list(platform_config.keys())
        
        results = {}
        total_duration = 0
        
        self.print_header(f"Building for {platform.upper()}", "🚀")
        
        for build_type in build_types:
            if build_type not in platform_config:
                self.print_error(f"Unknown build type for {platform}: {build_type}")
                results[build_type] = False
                continue
            
            config = platform_config[build_type]
            
            # Skip dependent builds if prerequisite failed
            if build_type == 'dmg' and not results.get('app', True):
                self.print_warning("Skipping DMG creation (macOS app build failed)")
                results[build_type] = False
                continue
            
            if build_type == 'zip' and not results.get('exe', True):
                self.print_warning("Skipping ZIP creation (Windows exe build failed)")
                results[build_type] = False
                continue
            
            success, duration = self.run_build_step(platform, build_type, config)
            results[build_type] = success
            total_duration += duration
        
        # Verify outputs
        self.print_step("Verifying build outputs")
        verification_results = self.verify_outputs(platform)
        
        # Update results with verification
        for build_type, verified in verification_results.items():
            if build_type in results:
                results[build_type] = results[build_type] and verified
        
        success_count = sum(1 for success in results.values() if success)
        total_count = len(results)
        
        if success_count == total_count:
            self.print_success(f"{platform.upper()} build completed successfully in {total_duration:.1f}s")
        else:
            self.print_error(f"{platform.upper()} build partially failed ({success_count}/{total_count} successful)")
        
        return results
    
    def generate_build_report(self, all_results: Dict[str, Dict[str, bool]]):
        """Generate a comprehensive build report."""
        self.print_header("BUILD REPORT", "📊")
        
        total_duration = time.time() - self.start_time
        
        print(f"\n{Colors.BOLD}Build Summary:{Colors.END}")
        print(f"Total Duration: {total_duration:.1f}s")
        print(f"Build Directory: {self.build_dir}")
        print(f"Distribution Directory: {self.dist_dir}")
        
        # Platform results
        print(f"\n{Colors.BOLD}Platform Results:{Colors.END}")
        overall_success = True
        
        for platform, results in all_results.items():
            success_count = sum(1 for success in results.values() if success)
            total_count = len(results)
            
            status_emoji = "✅" if success_count == total_count else "❌" if success_count == 0 else "⚠️"
            print(f"{status_emoji} {platform.upper()}: {success_count}/{total_count} successful")
            
            for build_type, success in results.items():
                status = "✅" if success else "❌"
                print(f"   {status} {build_type}")
            
            if success_count != total_count:
                overall_success = False
        
        # Distribution files
        print(f"\n{Colors.BOLD}Distribution Files:{Colors.END}")
        if self.dist_dir.exists():
            dist_files = []
            for item in self.dist_dir.rglob('*'):
                if item.is_file() and item.suffix in ['.dmg', '.zip', '.exe', '.app']:
                    size = self.get_file_size(item)
                    relative_path = item.relative_to(self.dist_dir)
                    dist_files.append((str(relative_path), size))
            
            if dist_files:
                for file_path, size in sorted(dist_files):
                    print(f"📁 {file_path} ({size})")
            else:
                print("No distribution files found")
        else:
            print("Distribution directory not found")
        
        # Log files
        print(f"\n{Colors.BOLD}Log Files:{Colors.END}")
        if self.logs_dir.exists():
            log_files = list(self.logs_dir.glob('*.log'))
            if log_files:
                for log_file in sorted(log_files, key=lambda x: x.stat().st_mtime, reverse=True):
                    size = self.get_file_size(log_file)
                    print(f"📄 {log_file.name} ({size})")
            else:
                print("No log files found")
        
        # Final status
        print(f"\n{Colors.BOLD}Final Status:{Colors.END}")
        if overall_success:
            self.print_success("🎉 ALL BUILDS COMPLETED SUCCESSFULLY!")
            print(f"\n{Colors.GREEN}Ready for distribution!{Colors.END}")
        else:
            self.print_error("⚠️ Some builds failed. Check logs for details.")
            print(f"\n{Colors.YELLOW}Review the logs in {self.logs_dir}{Colors.END}")
        
        return overall_success


def main():
    """Main function with argument parsing."""
    parser = argparse.ArgumentParser(
        description="Enhanced Unified Build Script for CSC-Reach",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                          # Build all platforms
  %(prog)s --platform macos         # Build only macOS
  %(prog)s --platform windows       # Build only Windows
  %(prog)s --macos-only app          # Build only macOS app (no DMG)
  %(prog)s --windows-only exe        # Build only Windows exe (no ZIP)
  %(prog)s --clean                   # Clean build directory first
  %(prog)s --no-prereq-check        # Skip prerequisite checks
        """
    )
    
    parser.add_argument(
        '--platform', 
        choices=['macos', 'windows', 'all'], 
        default='all',
        help='Platform to build for (default: all)'
    )
    
    parser.add_argument(
        '--macos-only',
        nargs='*',
        choices=['app', 'dmg'],
        help='Build only specific macOS components'
    )
    
    parser.add_argument(
        '--windows-only',
        nargs='*',
        choices=['exe', 'zip'],
        help='Build only specific Windows components'
    )
    
    parser.add_argument(
        '--clean',
        action='store_true',
        help='Clean build directory before building'
    )
    
    parser.add_argument(
        '--no-prereq-check',
        action='store_true',
        help='Skip prerequisite checks'
    )
    
    parser.add_argument(
        '--preserve-logs',
        action='store_true',
        default=True,
        help='Preserve existing logs when cleaning (default: True)'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    
    args = parser.parse_args()
    
    # Get project root
    project_root = Path(__file__).parent.parent.parent
    
    # Initialize build manager
    build_manager = BuildManager(project_root)
    
    # Print header
    build_manager.print_header("CSC-REACH ENHANCED UNIFIED BUILD SYSTEM", "🏗️")
    
    print(f"{Colors.BOLD}Configuration:{Colors.END}")
    print(f"Project Root: {project_root}")
    print(f"Platform: {args.platform}")
    print(f"Clean Build: {args.clean}")
    print(f"Skip Prerequisites: {args.no_prereq_check}")
    
    try:
        # Clean build directory if requested
        if args.clean:
            build_manager.clean_build_directory(preserve_logs=args.preserve_logs)
        
        # Check prerequisites
        if not args.no_prereq_check:
            if not build_manager.check_prerequisites():
                build_manager.print_error("Prerequisites check failed. Use --no-prereq-check to skip.")
                return 1
        
        # Determine what to build
        all_results = {}
        
        if args.platform == 'all' or args.platform == 'macos':
            build_types = args.macos_only if args.macos_only is not None else None
            all_results['macos'] = build_manager.build_platform('macos', build_types)
        
        if args.platform == 'all' or args.platform == 'windows':
            build_types = args.windows_only if args.windows_only is not None else None
            all_results['windows'] = build_manager.build_platform('windows', build_types)
        
        # Generate report
        overall_success = build_manager.generate_build_report(all_results)
        
        return 0 if overall_success else 1
        
    except KeyboardInterrupt:
        build_manager.print_error("Build interrupted by user")
        return 130
    except Exception as e:
        build_manager.print_error(f"Unexpected error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
