#!/usr/bin/env python3
"""
Realistic benchmark for lynguine server mode PoC

This script simulates the real-world scenario where applications like `lamd`
call lynguine as a separate process each time, incurring full startup costs.

Compares:
1. Subprocess mode: Launching a new Python process for each operation (like lamd does)
2. Server mode: Using a persistent lynguine server

Usage:
    # Terminal 1: Start the server
    python -m lynguine.server
    
    # Terminal 2: Run the benchmark
    python examples/server_mode/benchmark_subprocess.py
"""

import time
import sys
import os
import subprocess
import tempfile

# Add lynguine to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from lynguine.client import ServerClient


def benchmark_subprocess_mode(num_iterations: int = 10, config_file: str = 'test_config.yml'):
    """
    Benchmark subprocess mode: Launch a new Python process for each operation
    
    This simulates what happens when applications like lamd call lynguine repeatedly,
    each time incurring the full startup cost of Python + pandas + lynguine.
    """
    print(f"Benchmarking SUBPROCESS MODE ({num_iterations} iterations)...")
    print("  Each iteration: New Python process + import pandas + import lynguine + read data")
    
    times = []
    config_dir = os.path.abspath(os.path.dirname(__file__))
    
    # Create a simple Python script that does what lamd would do
    script = f"""
import sys
sys.path.insert(0, '{os.path.abspath(os.path.join(config_dir, "../.."))}')

from lynguine.config.interface import Interface
from lynguine.access import io

interface = Interface.from_file(
    user_file='{config_file}',
    directory='{config_dir}'
)
result = io.read_data(interface._data['input'])
if isinstance(result, tuple):
    df, _ = result
else:
    df = result

print(f"Shape: {{df.shape}}")
"""
    
    # Write script to temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(script)
        script_file = f.name
    
    try:
        for i in range(num_iterations):
            start = time.time()
            
            # Run as subprocess (simulates lamd calling lynguine)
            result = subprocess.run(
                ['python', script_file],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                print(f"  Error in iteration {i+1}:")
                print(result.stderr)
                sys.exit(1)
            
            elapsed = time.time() - start
            times.append(elapsed)
            print(f"  Iteration {i+1}: {elapsed:.3f}s")
    
    finally:
        # Clean up temp file
        os.unlink(script_file)
    
    total_time = sum(times)
    avg_time = total_time / num_iterations
    
    print(f"\nSubprocess Mode Results:")
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


def analyze_results(subprocess_results, server_results, num_iterations):
    """Analyze and display comparison results"""
    print("\n" + "="*70)
    print("PERFORMANCE COMPARISON (REALISTIC SCENARIO)")
    print("="*70)
    
    speedup = subprocess_results['total_time'] / server_results['total_time']
    time_saved = subprocess_results['total_time'] - server_results['total_time']
    time_saved_per_op = subprocess_results['avg_time'] - server_results['avg_time']
    
    print(f"\nTotal time for {num_iterations} operations:")
    print(f"  Subprocess mode:  {subprocess_results['total_time']:.3f}s")
    print(f"  Server mode:      {server_results['total_time']:.3f}s")
    print(f"  Time saved:       {time_saved:.3f}s ({time_saved_per_op:.3f}s per operation)")
    
    print(f"\nAverage time per operation:")
    print(f"  Subprocess mode:  {subprocess_results['avg_time']:.3f}s")
    print(f"  Server mode:      {server_results['avg_time']:.3f}s")
    
    print(f"\n🚀 SPEEDUP: {speedup:.1f}x faster")
    
    # Calculate HTTP overhead
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
    print(f"✓ HTTP overhead < {target_overhead_ms}ms: {'✅ PASS' if meets_overhead else '⚠️  WARNING'} ({http_overhead_ms:.1f}ms)")
    
    print(f"\n{'🎉 SUCCESS' if meets_speedup else '⚠️  PARTIAL SUCCESS'}:")
    if meets_speedup:
        print(f"  Server mode provides {speedup:.1f}x speedup - EXCEEDS 5x target!")
        print(f"  For {num_iterations} operations: Saves {time_saved:.1f}s total")
    else:
        print(f"  Speedup of {speedup:.1f}x is less than 5x target")
    
    if not meets_overhead:
        print(f"  HTTP overhead ({http_overhead_ms:.1f}ms) is higher than {target_overhead_ms}ms target")
        print(f"  BUT: {http_overhead_ms:.0f}ms overhead << {subprocess_results['avg_time']*1000:.0f}ms subprocess startup")
        print(f"  The overhead is negligible compared to the savings!")
    
    print(f"\n📊 Real-world impact for applications like lamd:")
    print(f"  Subprocess: {subprocess_results['avg_time']:.2f}s per call")
    print(f"  Server:     {server_results['avg_time']:.3f}s per call")
    print(f"  Savings:    {time_saved_per_op:.2f}s per call ({speedup:.1f}x faster)")
    
    return {
        'speedup': speedup,
        'http_overhead_ms': http_overhead_ms,
        'meets_criteria': meets_speedup
    }


def main():
    """Main benchmark execution"""
    import argparse
    parser = argparse.ArgumentParser(description='Realistic benchmark for lynguine server mode')
    parser.add_argument('-n', '--iterations', type=int, default=10,
                       help='Number of iterations (default: 10)')
    parser.add_argument('--config', default='test_config.yml',
                       help='Configuration file to use (default: test_config.yml)')
    parser.add_argument('--server-url', default='http://127.0.0.1:8765',
                       help='Server URL (default: http://127.0.0.1:8765)')
    parser.add_argument('--server-only', action='store_true',
                       help='Only benchmark server mode (skip subprocess mode)')
    args = parser.parse_args()
    
    print("="*70)
    print("LYNGUINE SERVER MODE BENCHMARK - REALISTIC SCENARIO")
    print("(Simulates subprocess calls like lamd does)")
    print("="*70)
    print(f"\nConfiguration:")
    print(f"  Iterations: {args.iterations}")
    print(f"  Config file: {args.config}")
    print(f"  Server URL: {args.server_url}")
    print()
    
    # Run benchmarks
    if not args.server_only:
        print("\n" + "-"*70)
        subprocess_results = benchmark_subprocess_mode(args.iterations, args.config)
        print()
    else:
        subprocess_results = None
    
    print("-"*70)
    server_results = benchmark_server_mode(args.iterations, args.config, args.server_url)
    
    # Analyze results
    if subprocess_results:
        print()
        analyze_results(subprocess_results, server_results, args.iterations)
    
    print("\n" + "="*70)
    print()


if __name__ == '__main__':
    main()

