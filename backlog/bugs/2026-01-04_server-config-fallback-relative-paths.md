---
id: "2026-01-04_server-config-fallback-relative-paths"
title: "Server Config File Fallback Doesn't Handle Relative Paths Correctly"
status: "Proposed"
priority: "Low"
created: "2026-01-04"
last_updated: "2026-01-04"
category: "bug"
related_cips: []
owner: ""
dependencies: []
---

# Bug: Server Config File Fallback Doesn't Handle Relative Paths Correctly

## Description

When the lynguine server's `extract_talk_field()` endpoint falls back to config files (`_lamd.yml`, `_config.yml`), it uses `directory='.'` which refers to the server's working directory, not the markdown file's directory.

This causes config fallback to fail when the markdown file is in a different directory than where the server was started.

**Discovered in**: lamd CIP-0008 Phase 2.5 testing (shell client `mdfield-server`)

## Steps to Reproduce

```bash
# Start server from directory A
cd /some/directory
python -m lynguine.server &

# Create files in directory B
cd /tmp/test
cat > _lamd.yml << EOF
test_field: "Test Value"
EOF

cat > test.md << EOF
---
title: "Test"
---
EOF

# Try to extract field that's only in config file
curl -X POST http://127.0.0.1:8765/api/talk/field \
  -H "Content-Type: application/json" \
  -d '{"markdown_file": "/tmp/test/test.md", "field": "test_field", "config_files": ["_lamd.yml"]}'

# Result: field not found (empty value)
# Expected: field found from _lamd.yml in /tmp/test/
```

## Current Behavior

- Server looks for `_lamd.yml` in its own working directory (where it was started)
- Does NOT look in the markdown file's directory
- Config fallback fails for markdown files in different directories

## Expected Behavior

- Server should look for config files relative to the markdown file's location
- Should extract the directory from the markdown file path
- Should pass that directory to `Interface.from_file()` for config fallback

## Root Cause

In `lynguine/server_interface_handlers.py`, line ~138:

```python
iface = Interface.from_file(user_file=config_files, directory='.')
#                                                    ^^^^^^^^^^^
#                                              Hard-coded to current dir
```

Should be:

```python
# Extract directory from markdown file path
markdown_dir = os.path.dirname(markdown_file) or '.'
iface = Interface.from_file(user_file=config_files, directory=markdown_dir)
```

## Impact

**Severity**: Low

**Affected users**:
- Users relying on config file fallback (rare - most markdown files have complete frontmatter)
- lamd shell client (`mdfield-server`) when extracting fields not in frontmatter

**Workaround**:
- Ensure markdown files have complete frontmatter (best practice anyway)
- Start server from the same directory as markdown files
- Use Python `mdfield` directly for config-dependent extractions

## Testing

Test case already exists in lamd:
- `tests/test_mdfield_server.py::TestConfigFallback::test_config_fallback`
- Currently marked as `@pytest.mark.skip` with this issue as the reason

## Acceptance Criteria

- [ ] Server extracts directory from markdown file path
- [ ] Config files looked up relative to markdown file's directory
- [ ] Test case in lamd passes without skip marker
- [ ] No regression in existing functionality

## Related

- **lamd CIP**: CIP-0008 (Integrate Lynguine Server Mode for Fast Builds)
- **lamd Backlog**: backlog/features/2026-01-04_deploy-shell-mdfield-client.md

## Progress Updates

### 2026-01-04

Bug discovered during lamd CIP-0008 Phase 2.5 shell client testing. Marked as low priority since:
- Real-world markdown files (talks, CVs) have complete frontmatter
- Config fallback is rarely needed in practice
- Workarounds available
- Not a blocker for lamd shell client deployment

