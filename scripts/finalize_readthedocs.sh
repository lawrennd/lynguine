#!/bin/bash
# Script to finalize ReadTheDocs integration after manual registration
# Run this AFTER completing the ReadTheDocs registration steps

set -e  # Exit on error

echo "================================"
echo "ReadTheDocs Finalization Script"
echo "================================"
echo ""
echo "This script will:"
echo "  1. Add ReadTheDocs badge to README.md"
echo "  2. Update documentation links"
echo "  3. Update backlog item status"
echo "  4. Commit changes"
echo ""

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ] || [ ! -d "docs" ]; then
    echo "❌ Error: Must be run from the lynguine project root directory"
    exit 1
fi

# Verify ReadTheDocs is actually working
echo "Checking if ReadTheDocs site is accessible..."
if curl -s --head https://lynguine.readthedocs.io/ | grep "200 OK" > /dev/null; then
    echo "✅ ReadTheDocs site is accessible"
else
    echo "⚠️  Warning: Could not verify ReadTheDocs site is accessible"
    echo "   Make sure https://lynguine.readthedocs.io/ is working before proceeding"
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo ""
echo "📝 Updating README.md..."

# Add ReadTheDocs badge after the Documentation badge
if grep -q "readthedocs.org/projects/lynguine/badge" README.md; then
    echo "   Badge already exists, skipping..."
else
    # Insert after line 5 (after the Documentation badge)
    sed -i.bak '5a\
[![ReadTheDocs](https://readthedocs.org/projects/lynguine/badge/?version=latest)](https://lynguine.readthedocs.io/en/latest/)
' README.md
    echo "   ✅ Added ReadTheDocs badge"
fi

# Update Quick Links section
if grep -q "https://lynguine.readthedocs.io/" README.md; then
    echo "   Links already updated, skipping..."
else
    # Update the documentation link
    sed -i.bak 's|- \[Documentation\](https://lawrennd.github.io/lynguine/)|- [Documentation](https://lynguine.readthedocs.io/)\n- [GitHub Pages (Mirror)](https://lawrennd.github.io/lynguine/)|' README.md
    
    # Update security documentation link
    sed -i.bak 's|- \[Security Documentation\](docs/security/)|- [Security Documentation](https://lynguine.readthedocs.io/en/latest/security/)|' README.md
    
    echo "   ✅ Updated documentation links"
fi

# Remove backup files
rm -f README.md.bak

echo ""
echo "📝 Updating backlog item..."

BACKLOG_FILE="backlog/documentation/2025-05-05_readthedocs-setup.md"
TODAY=$(date +%Y-%m-%d)

# Update status to completed
sed -i.bak 's/^status: "Ready"/status: "completed"/' "$BACKLOG_FILE"

# Mark all acceptance criteria as done
sed -i.bak 's/^- \[ \]/- [x]/' "$BACKLOG_FILE"

# Add completion note
cat >> "$BACKLOG_FILE" << EOF

### $TODAY

**ReadTheDocs Registration Completed**

Successfully registered lynguine project on ReadTheDocs platform:

1. ✅ Project registered at https://lynguine.readthedocs.io/
2. ✅ GitHub repository connected with automatic webhook
3. ✅ Documentation builds successfully on ReadTheDocs
4. ✅ ReadTheDocs badge added to README.md
5. ✅ Documentation links updated to point to ReadTheDocs
6. ✅ Security section verified and accessible

**Documentation now available at**:
- Latest: https://lynguine.readthedocs.io/en/latest/
- Security: https://lynguine.readthedocs.io/en/latest/security/

**Status**: Fully operational. Documentation automatically rebuilds on every commit to main branch.
EOF

rm -f "$BACKLOG_FILE.bak"

echo "   ✅ Updated backlog item"

echo ""
echo "📝 Staging changes for commit..."

git add README.md "$BACKLOG_FILE"

echo ""
echo "✅ All updates complete!"
echo ""
echo "Next steps:"
echo "  1. Review the changes: git diff --staged"
echo "  2. Commit: git commit -m 'Complete ReadTheDocs integration'"
echo "  3. Push: git push"
echo ""
echo "Your documentation is now live at: https://lynguine.readthedocs.io/"

