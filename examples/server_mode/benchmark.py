#!/usr/bin/env python3
"""
Benchmark script for lynguine server mode PoC

This script compares performance between:
1. Direct mode: Loading lynguine for each operation (baseline)
2. Server mode: Using a persistent lynguine server

Usage:
    # Terminal 1: Start the server
    python -m lynguine.server
    
    # Terminal 2: Run the benchmark
    python examples/server_mode/benchmark.py
"""

import time
import sys
import os

# Add lynguine to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from lynguine.config.interface import Interface
from lynguine.access import io
from lynguine.client import ServerClient


def benchmark_direct_mode(num_iterations: int = 10, config_file: str = 'test_config.yml'):
    """
    Benchmark direct mode: Load lynguine for each operation
    
    This simulates the current behavior where applications like lamd
    call lynguine repeatedly, each time incurring the full startup cost.
    """
    print(f"Benchmarking DIRECT MODE ({num_iterations} iterations)...")
    print("  Each iteration: Import lynguine + load config + read data")
    
    times = []
    config_dir = os.path.dirname(__file__)
    
    for i in range(num_iterations):
        start = time.time()
        
        # Simulate what happens in each call: load interface, read data
        interface = Interface.from_file(
            user_file=config_file,
            directory=config_dir
        )
        df = io.read_data(interface._data['input'])
        
        elapsed = time.time() - start
        times.append(elapsed)
        print(f"  Iteration {i+1}: {elapsed:.3f}s")
    
    total_time = sum(times)
    avg_time = total_time / num_iterations
    
    print(f"\nDirect Mode Results:")
    print(f"  Total time: {total_time:.3f}s")
    print(f"  Average per operation: {avg_time:.3f}s")
    print(f"  Operations/second: {1.0/avg_time:.2f}")
    
    return {
        'total_time': total_time,
        'avg_time': avg_time,
        'times': times
    }


def benchmark_server_mode(num_iterations: int = 10, config_file: str = 'test_config.yml', server_url: str = 'http://127.0.0.1:8765'):
    """
    Benchmark server mode: Use persistent lynguine server
    
    This demonstrates the improved performance when lynguine stays loaded.
    """
    print(f"Benchmarking SERVER MODE ({num_iterations} iterations)...")
    print("  Server is already running with lynguine loaded")
    
    # Test server connectivity
    client = ServerClient(server_url=server_url)
    if not client.ping():
        print(f"\n❌ ERROR: Cannot connect to server at {server_url}")
        print("  Make sure the server is running:")
        print("    python -m lynguine.server")
        sys.exit(1)
    
    health = client.health_check()
    print(f"  Connected to: {health.get('server', 'unknown')}")
    
    times = []
    config_dir = os.path.dirname(__file__)
    
    for i in range(num_iterations):
        start = time.time()
        
        # Make request to server
        df = client.read_data(
            interface_file=config_file,
            directory=config_dir
        )
        
        elapsed = time.time() - start
        times.append(elapsed)
        print(f"  Iteration {i+1}: {elapsed:.3f}s")
    
    total_time = sum(times)
    avg_time = total_time / num_iterations
    
    print(f"\nServer Mode Results:")
    print(f"  Total time: {total_time:.3f}s")
    print(f"  Average per operation: {avg_time:.3f}s")
    print(f"  Operations/second: {1.0/avg_time:.2f}")
    
    client.close()
    
    return {
        'total_time': total_time,
        'avg_time': avg_time,
        'times': times
    }


def analyze_results(direct_results, server_results, num_iterations):
    """Analyze and display comparison results"""
    print("\n" + "="*70)
    print("PERFORMANCE COMPARISON")
    print("="*70)
    
    speedup = direct_results['total_time'] / server_results['total_time']
    time_saved = direct_results['total_time'] - server_results['total_time']
    
    print(f"\nTotal time for {num_iterations} operations:")
    print(f"  Direct mode:  {direct_results['total_time']:.3f}s")
    print(f"  Server mode:  {server_results['total_time']:.3f}s")
    print(f"  Time saved:   {time_saved:.3f}s")
    
    print(f"\nAverage time per operation:")
    print(f"  Direct mode:  {direct_results['avg_time']:.3f}s")
    print(f"  Server mode:  {server_results['avg_time']:.3f}s")
    
    print(f"\n🚀 SPEEDUP: {speedup:.1f}x faster")
    
    # Calculate estimated HTTP overhead
    # This is the server mode time minus the theoretical minimum (near-zero for fake data)
    http_overhead_ms = server_results['avg_time'] * 1000
    print(f"   HTTP overhead: ~{http_overhead_ms:.1f}ms per request")
    
    # Success criteria from CIP-0008
    print(f"\n" + "="*70)
    print("SUCCESS CRITERIA (from CIP-0008)")
    print("="*70)
    
    target_speedup = 5.0
    target_overhead_ms = 5.0
    
    meets_speedup = speedup >= target_speedup
    meets_overhead = http_overhead_ms <= target_overhead_ms
    
    print(f"\n✓ Speedup > {target_speedup}x:        {'✅ PASS' if meets_speedup else '❌ FAIL'} ({speedup:.1f}x)")
    print(f"✓ HTTP overhead < {target_overhead_ms}ms: {'✅ PASS' if meets_overhead else '❌ FAIL'} ({http_overhead_ms:.1f}ms)")
    
    if meets_speedup and meets_overhead:
        print(f"\n🎉 SUCCESS: All criteria met! Proceed to Phase 2.")
    else:
        print(f"\n⚠️  REVIEW: Not all criteria met. Review approach before Phase 2.")
    
    return {
        'speedup': speedup,
        'http_overhead_ms': http_overhead_ms,
        'meets_criteria': meets_speedup and meets_overhead
    }


def main():
    """Main benchmark execution"""
    import argparse
    parser = argparse.ArgumentParser(description='Benchmark lynguine server mode')
    parser.add_argument('-n', '--iterations', type=int, default=10,
                       help='Number of iterations (default: 10)')
    parser.add_argument('--config', default='test_config.yml',
                       help='Configuration file to use (default: test_config.yml)')
    parser.add_argument('--server-url', default='http://127.0.0.1:8765',
                       help='Server URL (default: http://127.0.0.1:8765)')
    parser.add_argument('--server-only', action='store_true',
                       help='Only benchmark server mode (skip direct mode)')
    args = parser.parse_args()
    
    print("="*70)
    print("LYNGUINE SERVER MODE BENCHMARK (Phase 1 PoC)")
    print("="*70)
    print(f"\nConfiguration:")
    print(f"  Iterations: {args.iterations}")
    print(f"  Config file: {args.config}")
    print(f"  Server URL: {args.server_url}")
    print()
    
    # Run benchmarks
    if not args.server_only:
        print("\n" + "-"*70)
        direct_results = benchmark_direct_mode(args.iterations, args.config)
        print()
    else:
        direct_results = None
    
    print("-"*70)
    server_results = benchmark_server_mode(args.iterations, args.config, args.server_url)
    
    # Analyze results
    if direct_results:
        print()
        analyze_results(direct_results, server_results, args.iterations)
    
    print("\n" + "="*70)
    print()


if __name__ == '__main__':
    main()

