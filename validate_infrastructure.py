#!/usr/bin/env python3
"""
Infrastructure Validation Test - Task 0.1
Validates that the Warnet economic node infrastructure works end-to-end

Tests:
1. Network deployment with economic nodes
2. Economic weight accessibility via metadata
3. Fork detection capabilities
4. Data logging correctness
"""

import subprocess
import json
import time
import sys
from pathlib import Path
from datetime import datetime

class Colors:
    GREEN = '\033[0;32m'
    RED = '\033[0;31m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'

def print_header(text):
    print(f"\n{Colors.BLUE}{'='*80}{Colors.NC}")
    print(f"{Colors.BLUE}{text.center(80)}{Colors.NC}")
    print(f"{Colors.BLUE}{'='*80}{Colors.NC}\n")

def print_success(text):
    print(f"{Colors.GREEN}✓ {text}{Colors.NC}")

def print_error(text):
    print(f"{Colors.RED}✗ {text}{Colors.NC}")

def print_info(text):
    print(f"{Colors.YELLOW}→ {text}{Colors.NC}")

def run_command(cmd, capture=True, timeout=30):
    """Run a shell command and return output"""
    try:
        if capture:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return result.returncode == 0, result.stdout, result.stderr
        else:
            result = subprocess.run(cmd, shell=True, timeout=timeout)
            return result.returncode == 0, "", ""
    except subprocess.TimeoutExpired:
        return False, "", "Command timed out"
    except Exception as e:
        return False, "", str(e)

def check_warnet_installed():
    """Test 1: Check if Warnet is installed"""
    print_header("TEST 1: Warnet Installation Check")

    success, stdout, stderr = run_command("which warnet")
    if success:
        print_success("Warnet CLI found")
        success, version, _ = run_command("warnet --version")
        if success:
            print_info(f"Version: {version.strip()}")
        return True
    else:
        print_error("Warnet CLI not found in PATH")
        return False

def check_network_status():
    """Test 2: Check if any Warnet network is running"""
    print_header("TEST 2: Network Status Check")

    print_info("Checking for running pods...")
    success, stdout, stderr = run_command("kubectl get pods -n warnet --field-selector=status.phase=Running 2>/dev/null | wc -l")

    if success:
        try:
            pod_count = int(stdout.strip()) - 1  # Subtract header line
            if pod_count > 0:
                print_success(f"Found {pod_count} running pods in warnet namespace")
                return True, pod_count
            else:
                # Try default namespace
                success2, stdout2, _ = run_command("kubectl get pods --field-selector=status.phase=Running 2>/dev/null | grep tank | wc -l")
                if success2:
                    default_count = int(stdout2.strip())
                    if default_count > 0:
                        print_success(f"Found {default_count} running pods in default namespace")
                        return True, default_count

                print_error("No running Warnet pods found")
                print_info("You may need to deploy a network first")
                return False, 0
        except ValueError:
            print_error("Failed to parse pod count")
            return False, 0
    else:
        print_error("Failed to query Kubernetes")
        print_info("Is kubectl configured correctly?")
        return False, 0

def get_node_list():
    """Get list of running nodes"""
    success, stdout, _ = run_command("kubectl get pods -n warnet -o name 2>/dev/null | grep tank")
    if not success or not stdout.strip():
        success, stdout, _ = run_command("kubectl get pods -o name 2>/dev/null | grep tank")

    if success and stdout.strip():
        nodes = [line.replace('pod/', '').strip() for line in stdout.strip().split('\n')]
        return nodes
    return []

def test_economic_weight_access():
    """Test 3: Verify economic weight metadata is accessible"""
    print_header("TEST 3: Economic Weight Accessibility")

    # Check if economic network config exists
    economic_config = Path("warnet-economic-implementation/warnet-economic-examples/networks/economic-30-nodes.yaml")

    if economic_config.exists():
        print_success(f"Economic config found: {economic_config}")

        # Parse the config to extract weights
        import yaml
        try:
            with open(economic_config, 'r') as f:
                config = yaml.safe_load(f)

            # Handle both formats: top-level 'nodes' or 'network.nodes'
            nodes = config.get('nodes', config.get('network', {}).get('nodes', []))
            economic_nodes = [n for n in nodes if 'economic_node' in n.get('tags', [])]

            total_weight = sum(n.get('metadata', {}).get('weight', 0) for n in nodes)
            economic_weight = sum(n.get('metadata', {}).get('weight', 0) for n in economic_nodes)

            print_success(f"Found {len(economic_nodes)} economic nodes in config")
            print_info(f"Total network weight: {total_weight}")
            print_info(f"Economic node weight: {economic_weight}")
            if total_weight > 0:
                print_info(f"Economic weight percentage: {economic_weight/total_weight*100:.1f}%")
            else:
                print_info("Economic weight percentage: N/A (no weights defined in current network)")

            # Show distribution
            print_info("\nEconomic Node Types:")
            for node in economic_nodes:
                name = node['name']
                weight = node.get('metadata', {}).get('weight', 0)
                node_type = node.get('metadata', {}).get('node_type', 'unknown')
                print(f"    {name:30s} weight={weight:2d} type={node_type}")

            return True
        except Exception as e:
            print_error(f"Failed to parse economic config: {e}")
            return False
    else:
        print_error(f"Economic config not found at {economic_config}")
        return False

def test_fork_detection():
    """Test 4: Verify fork detection capability"""
    print_header("TEST 4: Fork Detection Capability")

    nodes = get_node_list()

    if not nodes:
        print_error("No nodes available for testing")
        print_info("Fork detection requires running network")
        return False

    print_success(f"Found {len(nodes)} nodes to test")

    # Query each node for its chain tip
    tips = {}
    heights = {}

    print_info("Querying node chain tips...")
    for node in nodes[:8]:  # Test first 8 nodes
        success, stdout, stderr = run_command(f"warnet bitcoin rpc {node} getbestblockhash", timeout=10)
        if success and stdout.strip():
            tip = stdout.strip().strip('"')
            tips[node] = tip

            # Get height
            success2, height_out, _ = run_command(f"warnet bitcoin rpc {node} getblockcount", timeout=10)
            if success2 and height_out.strip():
                try:
                    heights[node] = int(height_out.strip())
                    print(f"    {node}: height={heights[node]} tip={tip[:16]}...")
                except ValueError:
                    pass

    if not tips:
        print_error("Failed to query any nodes")
        return False

    # Analyze tips
    unique_tips = set(tips.values())

    if len(unique_tips) == 1:
        print_success(f"Network is synchronized - all {len(tips)} nodes on same tip")
        print_info(f"Common tip: {list(unique_tips)[0][:16]}...")
        fork_detected = False
    else:
        print_error(f"FORK DETECTED! {len(unique_tips)} different tips across {len(tips)} nodes")
        for tip in unique_tips:
            nodes_on_tip = [n for n, t in tips.items() if t == tip]
            print_info(f"Tip {tip[:16]}...: {len(nodes_on_tip)} nodes")
        fork_detected = True

    # Check height variance
    if heights:
        min_height = min(heights.values())
        max_height = max(heights.values())
        height_diff = max_height - min_height

        if height_diff > 1:
            print_error(f"Height variance detected: {min_height} - {max_height} (diff: {height_diff})")
        else:
            print_success(f"Height consensus: {min_height} - {max_height} (diff: {height_diff})")

    print_success("Fork detection mechanism is functional")
    return True

def test_data_logging():
    """Test 5: Verify data logging infrastructure"""
    print_header("TEST 5: Data Logging Infrastructure")

    # Check if monitoring tools exist
    monitor_script = Path("warnetScenarioDiscovery/tools/persistent_monitor.sh")
    test_framework = Path("warnetScenarioDiscovery/warnet_test_framework.py")

    checks = [
        (monitor_script, "Persistent monitoring script"),
        (test_framework, "Test framework"),
    ]

    all_exist = True
    for path, name in checks:
        if path.exists():
            print_success(f"{name} found: {path}")
        else:
            print_error(f"{name} not found: {path}")
            all_exist = False

    # Check if output directories can be created
    test_output = Path("test_results/validation_test")
    try:
        test_output.mkdir(parents=True, exist_ok=True)
        print_success(f"Output directory accessible: {test_output}")

        # Create a test log file
        test_log = test_output / f"validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        test_data = {
            "timestamp": datetime.now().isoformat(),
            "test": "infrastructure_validation",
            "status": "success"
        }
        with open(test_log, 'w') as f:
            json.dump(test_data, f, indent=2)

        print_success(f"Test log created: {test_log}")
        return True
    except Exception as e:
        print_error(f"Failed to create output directory: {e}")
        return False

def test_rpc_connectivity():
    """Test 6: Basic RPC connectivity"""
    print_header("TEST 6: RPC Connectivity Test")

    nodes = get_node_list()

    if not nodes:
        print_error("No nodes available for RPC testing")
        return False

    test_node = nodes[0]
    print_info(f"Testing RPC on node: {test_node}")

    # Test multiple RPC commands
    rpc_tests = [
        ("getblockcount", "Get block height"),
        ("getbestblockhash", "Get best block hash"),
        ("getblockchaininfo", "Get blockchain info"),
        ("getnetworkinfo", "Get network info"),
        ("getpeerinfo", "Get peer info"),
    ]

    passed = 0
    for command, description in rpc_tests:
        success, stdout, stderr = run_command(f"warnet bitcoin rpc {test_node} {command}", timeout=10)
        if success:
            print_success(f"{description}: {command}")
            passed += 1
        else:
            print_error(f"{description}: {command} - {stderr[:100]}")

    print_info(f"RPC tests passed: {passed}/{len(rpc_tests)}")
    return passed >= 3  # At least 3 commands should work

def generate_summary_report(results):
    """Generate final validation report"""
    print_header("VALIDATION SUMMARY")

    total_tests = len(results)
    passed_tests = sum(1 for r in results.values() if r)

    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    print(f"Success Rate: {passed_tests/total_tests*100:.1f}%\n")

    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        color = Colors.GREEN if result else Colors.RED
        print(f"{color}{status}{Colors.NC} - {test_name}")

    print()

    if passed_tests == total_tests:
        print_success("ALL VALIDATION TESTS PASSED!")
        print_info("Infrastructure is ready for Task 0.1 completion")
        return True
    else:
        print_error(f"{total_tests - passed_tests} tests failed")
        print_info("Please address failures before proceeding")
        return False

def main():
    print_header("WARNET INFRASTRUCTURE VALIDATION - Task 0.1")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    results = {}

    # Run all validation tests
    results["Warnet Installation"] = check_warnet_installed()

    network_ok, pod_count = check_network_status()
    results["Network Running"] = network_ok

    results["Economic Weight Access"] = test_economic_weight_access()
    results["Fork Detection"] = test_fork_detection()
    results["Data Logging"] = test_data_logging()
    results["RPC Connectivity"] = test_rpc_connectivity()

    # Generate final report
    success = generate_summary_report(results)

    # Return appropriate exit code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
