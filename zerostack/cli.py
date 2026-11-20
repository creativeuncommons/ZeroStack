"""
ZeroStack Unified Command Line Interface
========================================
Enterprise CLI commands:
- `zerostack doctor`: Runs 10-point host environment pre-flight audit.
- `zerostack check`: Executes full 30-test conformance and drift gate.
- `zerostack stress`: Executes Phase 6 high-concurrency stress suite.
- `zerostack version`: Displays package version and member package manifest.

Zero external dependencies: 100% Python standard library.
"""

import sys
import os
import argparse
import unittest
from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parent
REPO_ROOT = PACKAGE_DIR.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from zerostack.doctor import run_doctor_audit


def main():
    parser = argparse.ArgumentParser(
        prog="zerostack",
        description="ZeroStack: Zero-Dependency Enterprise Agent Infrastructure"
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # doctor
    subparsers.add_parser("doctor", help="Run 10-point enterprise pre-flight environment audit")

    # check
    check_parser = subparsers.add_parser("check", help="Run full 30-test conformance and drift gate")
    check_parser.add_argument("--verbose", action="store_true", help="Verbose test output")

    # stress
    stress_parser = subparsers.add_parser("stress", help="Execute Phase 6 high-concurrency stress test")
    stress_parser.add_argument("--verbose", action="store_true", help="Verbose stress output")

    # version
    subparsers.add_parser("version", help="Show ZeroStack version and package manifest")

    args = parser.parse_args()

    if args.command == "doctor" or args.command is None:
        if args.command is None and len(sys.argv) > 1:
            parser.print_help()
            sys.exit(1)
        res = run_doctor_audit()
        sys.exit(0 if res["all_passed"] else 1)

    elif args.command == "check":
        import subprocess
        check_script = REPO_ROOT / "scripts" / "zerostack-check"
        cmd = [sys.executable, str(check_script)]
        if args.verbose:
            cmd.append("--verbose")
        ret = subprocess.run(cmd).returncode
        sys.exit(ret)

    elif args.command == "stress":
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromName("tests.test_phase6_stress_and_load.TestPhase6StressAndLoad")
        runner = unittest.TextTestRunner(verbosity=2 if args.verbose else 1)
        res = runner.run(suite)
        sys.exit(0 if res.wasSuccessful() else 1)

    elif args.command == "version":
        print("ZeroStack v1.0.0 (Enterprise Production Release)")
        print("Governing Ecosystem Packages:")
        print("  - ZeroMCP    v1.0.0-rc1 (MCP 2024-11-05 Fast-Path JSON-RPC 2.0)")
        print("  - ZeroLeak   v1.0.0-rc1 (Sub-millisecond PII Tokenization Vault)")
        print("  - ZeroLoop   v1.0.0-rc1 (Crash-Proof Durable SQLite WAL State Machine)")
        print("  - HyperGate  v0.1.0     (BM25 Tool Pruner & Circuit Breaker Gateway)")
        print("  - AgentTrace v1.0.0-rc1 (W3C Distributed Tracing & OTLP Sinks)")
        print("Runtime Dependencies: 0 (100% Python Standard Library)")
        sys.exit(0)


if __name__ == "__main__":
    main()
