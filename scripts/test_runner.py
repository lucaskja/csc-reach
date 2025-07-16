#!/usr/bin/env python3
"""
Comprehensive Test Runner for CSC-Reach
Provides advanced testing capabilities with detailed reporting and analysis.
"""

import os
import sys
import argparse
import subprocess
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
import xml.etree.ElementTree as ET


class TestRunner:
    """Advanced test runner with comprehensive reporting and analysis."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.test_dir = project_root / "tests"
        self.reports_dir = project_root / "test-reports"
        self.coverage_dir = project_root / "htmlcov"
        
        # Ensure directories exist
        self.reports_dir.mkdir(exist_ok=True)
        
        # Test configuration
        self.test_config = {
            "unit": {
                "path": "tests/unit",
                "markers": ["unit"],
                "timeout": 300,
                "parallel": True
            },
            "integration": {
                "path": "tests/integration",
                "markers": ["integration"],
                "timeout": 600,
                "parallel": False
            },
            "gui": {
                "path": "tests/gui",
                "markers": ["gui"],
                "timeout": 900,
                "parallel": False,
                "requires_display": True
            },
            "performance": {
                "path": "tests/performance",
                "markers": ["performance", "slow"],
                "timeout": 1800,
                "parallel": False
            },
            "security": {
                "path": "tests/security",
                "markers": ["security"],
                "timeout": 600,
                "parallel": False
            }
        }
    
    def run_quality_checks(self) -> Dict[str, Any]:
        """Run comprehensive code quality checks."""
        print("🔍 Running code quality checks...")
        
        quality_results = {
            "timestamp": datetime.now().isoformat(),
            "checks": {},
            "overall_passed": True
        }
        
        # Code formatting with Black
        print("  📝 Checking code formatting...")
        black_result = self._run_command([
            sys.executable, "-m", "black", "--check", "--diff",
            "src/", "tests/", "scripts/"
        ])
        quality_results["checks"]["formatting"] = {
            "passed": black_result["returncode"] == 0,
            "output": black_result["stdout"],
            "errors": black_result["stderr"]
        }
        
        # Linting with flake8
        print("  🔍 Running linting checks...")
        flake8_result = self._run_command([
            sys.executable, "-m", "flake8",
            "src/", "tests/", "scripts/",
            "--statistics", "--tee", "--output-file=flake8-report.txt"
        ])
        quality_results["checks"]["linting"] = {
            "passed": flake8_result["returncode"] == 0,
            "output": flake8_result["stdout"],
            "errors": flake8_result["stderr"]
        }
        
        # Type checking with mypy
        print("  🔬 Running type checks...")
        mypy_result = self._run_command([
            sys.executable, "-m", "mypy",
            "src/", "--show-error-codes", "--no-error-summary"
        ])
        quality_results["checks"]["type_checking"] = {
            "passed": mypy_result["returncode"] == 0,
            "output": mypy_result["stdout"],
            "errors": mypy_result["stderr"]
        }
        
        # Security checks with bandit
        print("  🔒 Running security checks...")
        bandit_result = self._run_command([
            sys.executable, "-m", "bandit",
            "-r", "src/", "-f", "json", "-o", "bandit-report.json"
        ])
        quality_results["checks"]["security"] = {
            "passed": bandit_result["returncode"] == 0,
            "output": bandit_result["stdout"],
            "errors": bandit_result["stderr"]
        }
        
        # Import sorting with isort
        print("  📦 Checking import sorting...")
        isort_result = self._run_command([
            sys.executable, "-m", "isort",
            "--check-only", "--diff", "src/", "tests/", "scripts/"
        ])
        quality_results["checks"]["import_sorting"] = {
            "passed": isort_result["returncode"] == 0,
            "output": isort_result["stdout"],
            "errors": isort_result["stderr"]
        }
        
        # Update overall status
        quality_results["overall_passed"] = all(
            check["passed"] for check in quality_results["checks"].values()
        )
        
        # Save quality report
        quality_report_file = self.reports_dir / "quality-report.json"
        with open(quality_report_file, "w") as f:
            json.dump(quality_results, f, indent=2)
        
        print(f"  📊 Quality report saved: {quality_report_file}")
        return quality_results
    
    def run_test_suite(self, test_type: str, **kwargs) -> Dict[str, Any]:
        """Run a specific test suite with comprehensive reporting."""
        if test_type not in self.test_config:
            raise ValueError(f"Unknown test type: {test_type}")
        
        config = self.test_config[test_type]
        print(f"🧪 Running {test_type} tests...")
        
        # Check if test path exists
        test_path = self.project_root / config["path"]
        if not test_path.exists():
            print(f"  ⚠️ Test path not found: {test_path}")
            return {
                "test_type": test_type,
                "skipped": True,
                "reason": "Test path not found"
            }
        
        # Build pytest command
        pytest_cmd = [
            sys.executable, "-m", "pytest",
            str(test_path),
            "-v",
            "--tb=short",
            f"--timeout={config['timeout']}",
            f"--junit-xml={self.reports_dir}/{test_type}-results.xml",
            f"--html={self.reports_dir}/{test_type}-report.html",
            "--self-contained-html",
            f"--json-report-file={self.reports_dir}/{test_type}-report.json"
        ]
        
        # Add coverage for unit tests
        if test_type == "unit":
            pytest_cmd.extend([
                "--cov=src/multichannel_messaging",
                f"--cov-report=html:{self.coverage_dir}",
                f"--cov-report=xml:{self.reports_dir}/coverage.xml",
                "--cov-report=term-missing",
                "--cov-branch"
            ])
        
        # Add markers
        for marker in config["markers"]:
            pytest_cmd.extend(["-m", marker])
        
        # Add parallel execution if supported
        if config.get("parallel") and kwargs.get("parallel", True):
            pytest_cmd.extend(["-n", "auto"])
        
        # Set environment variables
        env = os.environ.copy()
        env["TESTING"] = "1"
        
        if config.get("requires_display"):
            # For GUI tests, ensure display is available
            if not os.environ.get("DISPLAY") and sys.platform.startswith("linux"):
                pytest_cmd.insert(-1, "--xvfb")
        
        # Run tests
        start_time = time.time()
        result = self._run_command(pytest_cmd, env=env)
        end_time = time.time()
        
        # Parse results
        test_results = {
            "test_type": test_type,
            "duration": end_time - start_time,
            "returncode": result["returncode"],
            "passed": result["returncode"] == 0,
            "stdout": result["stdout"],
            "stderr": result["stderr"],
            "timestamp": datetime.now().isoformat()
        }
        
        # Parse JUnit XML if available
        junit_file = self.reports_dir / f"{test_type}-results.xml"
        if junit_file.exists():
            test_results["junit_summary"] = self._parse_junit_xml(junit_file)
        
        # Parse JSON report if available
        json_report_file = self.reports_dir / f"{test_type}-report.json"
        if json_report_file.exists():
            try:
                with open(json_report_file) as f:
                    json_report = json.load(f)
                    test_results["detailed_summary"] = json_report.get("summary", {})
            except Exception as e:
                print(f"  ⚠️ Error parsing JSON report: {e}")
        
        print(f"  ✅ {test_type} tests completed in {test_results['duration']:.2f}s")
        return test_results
    
    def run_all_tests(self, **kwargs) -> Dict[str, Any]:
        """Run all available test suites."""
        print("🚀 Running comprehensive test suite...")
        
        overall_results = {
            "timestamp": datetime.now().isoformat(),
            "test_suites": {},
            "quality_checks": {},
            "summary": {}
        }
        
        # Run quality checks first
        if not kwargs.get("skip_quality", False):
            overall_results["quality_checks"] = self.run_quality_checks()
        
        # Run test suites
        total_duration = 0
        total_tests = 0
        total_passed = 0
        total_failed = 0
        total_skipped = 0
        
        for test_type in self.test_config.keys():
            if kwargs.get(f"skip_{test_type}", False):
                print(f"  ⏭️ Skipping {test_type} tests")
                continue
            
            try:
                test_results = self.run_test_suite(test_type, **kwargs)
                overall_results["test_suites"][test_type] = test_results
                
                if not test_results.get("skipped", False):
                    total_duration += test_results["duration"]
                    
                    if "junit_summary" in test_results:
                        summary = test_results["junit_summary"]
                        total_tests += summary.get("tests", 0)
                        total_passed += summary.get("passed", 0)
                        total_failed += summary.get("failures", 0) + summary.get("errors", 0)
                        total_skipped += summary.get("skipped", 0)
                
            except Exception as e:
                print(f"  ❌ Error running {test_type} tests: {e}")
                overall_results["test_suites"][test_type] = {
                    "test_type": test_type,
                    "error": str(e),
                    "passed": False
                }
        
        # Generate summary
        overall_results["summary"] = {
            "total_duration": total_duration,
            "total_tests": total_tests,
            "total_passed": total_passed,
            "total_failed": total_failed,
            "total_skipped": total_skipped,
            "success_rate": (total_passed / total_tests * 100) if total_tests > 0 else 0,
            "overall_passed": total_failed == 0 and overall_results["quality_checks"].get("overall_passed", True)
        }
        
        # Save comprehensive report
        report_file = self.reports_dir / f"comprehensive-test-report-{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, "w") as f:
            json.dump(overall_results, f, indent=2)
        
        # Generate summary report
        self._generate_summary_report(overall_results)
        
        print(f"\n📊 Test Summary:")
        print(f"  Total Tests: {total_tests}")
        print(f"  Passed: {total_passed}")
        print(f"  Failed: {total_failed}")
        print(f"  Skipped: {total_skipped}")
        print(f"  Success Rate: {overall_results['summary']['success_rate']:.1f}%")
        print(f"  Duration: {total_duration:.2f}s")
        print(f"  Report: {report_file}")
        
        return overall_results
    
    def _run_command(self, cmd: List[str], env: Optional[Dict] = None) -> Dict[str, Any]:
        """Run a command and capture output."""
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                env=env or os.environ,
                cwd=self.project_root
            )
            
            return {
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
        except Exception as e:
            return {
                "returncode": -1,
                "stdout": "",
                "stderr": str(e)
            }
    
    def _parse_junit_xml(self, junit_file: Path) -> Dict[str, Any]:
        """Parse JUnit XML file and extract summary information."""
        try:
            tree = ET.parse(junit_file)
            root = tree.getroot()
            
            # Handle both testsuite and testsuites root elements
            if root.tag == "testsuites":
                # Multiple test suites
                summary = {
                    "tests": int(root.get("tests", 0)),
                    "failures": int(root.get("failures", 0)),
                    "errors": int(root.get("errors", 0)),
                    "skipped": int(root.get("skipped", 0)),
                    "time": float(root.get("time", 0))
                }
            else:
                # Single test suite
                summary = {
                    "tests": int(root.get("tests", 0)),
                    "failures": int(root.get("failures", 0)),
                    "errors": int(root.get("errors", 0)),
                    "skipped": int(root.get("skipped", 0)),
                    "time": float(root.get("time", 0))
                }
            
            summary["passed"] = summary["tests"] - summary["failures"] - summary["errors"] - summary["skipped"]
            return summary
            
        except Exception as e:
            print(f"  ⚠️ Error parsing JUnit XML: {e}")
            return {}
    
    def _generate_summary_report(self, results: Dict[str, Any]):
        """Generate a human-readable summary report."""
        summary_file = self.reports_dir / "test-summary.md"
        
        with open(summary_file, "w") as f:
            f.write("# CSC-Reach Test Execution Summary\n\n")
            f.write(f"**Generated:** {results['timestamp']}\n\n")
            
            # Overall summary
            summary = results["summary"]
            f.write("## Overall Results\n\n")
            f.write(f"- **Total Tests:** {summary['total_tests']}\n")
            f.write(f"- **Passed:** {summary['total_passed']} ✅\n")
            f.write(f"- **Failed:** {summary['total_failed']} ❌\n")
            f.write(f"- **Skipped:** {summary['total_skipped']} ⏭️\n")
            f.write(f"- **Success Rate:** {summary['success_rate']:.1f}%\n")
            f.write(f"- **Total Duration:** {summary['total_duration']:.2f}s\n")
            f.write(f"- **Overall Status:** {'✅ PASSED' if summary['overall_passed'] else '❌ FAILED'}\n\n")
            
            # Quality checks
            if "quality_checks" in results:
                f.write("## Code Quality Checks\n\n")
                quality = results["quality_checks"]
                f.write(f"**Overall Quality:** {'✅ PASSED' if quality['overall_passed'] else '❌ FAILED'}\n\n")
                
                for check_name, check_result in quality["checks"].items():
                    status = "✅ PASSED" if check_result["passed"] else "❌ FAILED"
                    f.write(f"- **{check_name.replace('_', ' ').title()}:** {status}\n")
                f.write("\n")
            
            # Test suites
            f.write("## Test Suite Results\n\n")
            for test_type, test_result in results["test_suites"].items():
                if test_result.get("skipped"):
                    f.write(f"### {test_type.title()} Tests - ⏭️ SKIPPED\n")
                    f.write(f"Reason: {test_result.get('reason', 'Unknown')}\n\n")
                    continue
                
                status = "✅ PASSED" if test_result["passed"] else "❌ FAILED"
                f.write(f"### {test_type.title()} Tests - {status}\n")
                f.write(f"- **Duration:** {test_result['duration']:.2f}s\n")
                
                if "junit_summary" in test_result:
                    junit = test_result["junit_summary"]
                    f.write(f"- **Tests:** {junit.get('tests', 0)}\n")
                    f.write(f"- **Passed:** {junit.get('passed', 0)}\n")
                    f.write(f"- **Failed:** {junit.get('failures', 0) + junit.get('errors', 0)}\n")
                    f.write(f"- **Skipped:** {junit.get('skipped', 0)}\n")
                
                f.write("\n")
            
            # Coverage information
            coverage_file = self.reports_dir / "coverage.xml"
            if coverage_file.exists():
                f.write("## Code Coverage\n\n")
                f.write(f"Detailed coverage report available in: `{self.coverage_dir}/index.html`\n\n")
            
            # Reports and artifacts
            f.write("## Generated Reports\n\n")
            f.write("- **HTML Reports:** Available in `test-reports/` directory\n")
            f.write("- **Coverage Report:** Available in `htmlcov/index.html`\n")
            f.write("- **JUnit XML:** Available in `test-reports/*-results.xml`\n")
            f.write("- **JSON Reports:** Available in `test-reports/*-report.json`\n")
        
        print(f"  📄 Summary report generated: {summary_file}")


def main():
    """Main function for command-line usage."""
    parser = argparse.ArgumentParser(description="CSC-Reach Comprehensive Test Runner")
    parser.add_argument("--test-type", choices=["unit", "integration", "gui", "performance", "security", "all"],
                       default="all", help="Type of tests to run")
    parser.add_argument("--skip-quality", action="store_true", help="Skip code quality checks")
    parser.add_argument("--skip-unit", action="store_true", help="Skip unit tests")
    parser.add_argument("--skip-integration", action="store_true", help="Skip integration tests")
    parser.add_argument("--skip-gui", action="store_true", help="Skip GUI tests")
    parser.add_argument("--skip-performance", action="store_true", help="Skip performance tests")
    parser.add_argument("--skip-security", action="store_true", help="Skip security tests")
    parser.add_argument("--no-parallel", action="store_true", help="Disable parallel test execution")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    
    args = parser.parse_args()
    
    # Get project root
    project_root = Path(__file__).parent.parent
    
    # Initialize test runner
    test_runner = TestRunner(project_root)
    
    try:
        if args.test_type == "all":
            # Run all tests
            results = test_runner.run_all_tests(
                skip_quality=args.skip_quality,
                skip_unit=args.skip_unit,
                skip_integration=args.skip_integration,
                skip_gui=args.skip_gui,
                skip_performance=args.skip_performance,
                skip_security=args.skip_security,
                parallel=not args.no_parallel
            )
            
            return 0 if results["summary"]["overall_passed"] else 1
        else:
            # Run specific test type
            if args.test_type in ["unit", "integration", "gui", "performance", "security"]:
                results = test_runner.run_test_suite(args.test_type, parallel=not args.no_parallel)
                return 0 if results["passed"] else 1
            else:
                print(f"❌ Unknown test type: {args.test_type}")
                return 1
                
    except KeyboardInterrupt:
        print("\n❌ Test execution interrupted by user")
        return 130
    except Exception as e:
        print(f"❌ Test execution failed: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())