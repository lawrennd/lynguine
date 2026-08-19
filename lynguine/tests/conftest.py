"""Pytest hooks for lynguine tests."""


def pytest_collection_modifyitems(config, items):
    """Run server-mode tests before the rest of the suite.

    On macOS, ``subprocess.Popen`` / fork after a long pytest process (numpy,
    pandas, and other extension modules loaded) can SIGSEGV in
    ``_execute_child``. Server-mode tests start HTTP servers that way, so they
    need to run while the process can still spawn children. Linux CI is
    unaffected; this only changes order.
    """
    server_items = []
    other_items = []
    for item in items:
        if "test_server_mode" in item.nodeid:
            server_items.append(item)
        else:
            other_items.append(item)
    items[:] = server_items + other_items
