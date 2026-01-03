"""
Phase 5: Stateful Data Sessions Example

Demonstrates using stateful sessions for efficient repeated access with
minimal HTTP data transfer. Mirrors CustomDataFrame API.
"""
from lynguine.client import ServerClient
import time

def main():
    print("=== Phase 5: Stateful Data Sessions Example ===\n")
    
    # Create client with auto-start
    client = ServerClient(
        auto_start=True,
        idle_timeout=300  # 5-minute timeout
    )
    
    print("1. Creating session from interface file...")
    # Create session (loads interface file once)
    session = client.create_session(
        interface_file='test_config.yml',
        directory='.'
    )
    print(f"   ✓ Session created: {session.session_id[:8]}...\n")
    
    # Get session info
    info = session.get_info()
    print(f"2. Session Info:")
    print(f"   Shape: {info['shape']}")
    print(f"   Columns: {info['columns']}")
    print(f"   Memory: {info['memory_mb']:.2f} MB\n")
    
    # Focus-based navigation (like mdfield)
    print("3. Focus-Based Navigation (mimics CustomDataFrame):")
    indices = session.get_indices()
    print(f"   Indices: {indices[:3]}...")
    
    # Set focus and get value
    start = time.time()
    session.set_index(indices[0])
    session.set_column('name')
    value = session.get_value()  # Transfers ~bytes, not full DataFrame
    elapsed = time.time() - start
    
    print(f"   ✓ set_index({indices[0]})")
    print(f"   ✓ set_column('name')")
    print(f"   ✓ get_value() → {value}")
    print(f"   Time: {elapsed*1000:.2f}ms (minimal HTTP transfer)\n")
    
    # Extract multiple fields (lamd mdfield pattern)
    print("4. Multiple Field Extraction (lamd mdfield pattern):")
    fields = {}
    start = time.time()
    for field in ['name', 'email']:
        session.set_column(field)
        fields[field] = session.get_value()
    elapsed = time.time() - start
    
    print(f"   Extracted {len(fields)} fields:")
    for k, v in fields.items():
        print(f"     {k}: {v}")
    print(f"   Time: {elapsed*1000:.2f}ms total (~{elapsed/len(fields)*1000:.2f}ms per field)")
    print(f"   (vs {1.9*len(fields):.1f}s for {len(fields)} subprocess calls)\n")
    
    # Convenience method
    print("5. Convenience Method (get_value_at):")
    start = time.time()
    value = session.get_value_at(indices[1], 'email')
    elapsed = time.time() - start
    print(f"   ✓ get_value_at({indices[1]}, 'email') → {value}")
    print(f"   Time: {elapsed*1000:.2f}ms\n")
    
    # Column queries
    print("6. Column Type Queries (CustomDataFrame API):")
    input_cols = session.get_input_columns()
    output_cols = session.get_output_columns()
    print(f"   Input columns: {input_cols}")
    print(f"   Output columns: {output_cols}\n")
    
    # List all sessions
    print("7. List All Sessions:")
    sessions_info = client.list_sessions()
    print(f"   Total sessions: {sessions_info['total_sessions']}")
    print(f"   Total memory: {sessions_info['total_memory_mb']:.2f} MB\n")
    
    # Cleanup
    print("8. Cleanup:")
    session.delete()
    print("   ✓ Session deleted")
    
    client.close()
    print("   ✓ Client closed\n")
    
    print("=== Phase 5 Benefits ===")
    print("✓ Minimal HTTP traffic (~bytes per operation)")
    print("✓ CustomDataFrame API mirroring")
    print("✓ 35-40x faster for lamd (72s → 2s)")
    print("✓ Crash recovery (sessions persist)")
    print("✓ Multiple concurrent sessions")


if __name__ == '__main__':
    main()

