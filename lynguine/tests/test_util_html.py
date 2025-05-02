import pytest
import os
import tempfile
from unittest.mock import mock_open, patch
from lynguine.util.html import write_to_file, md_write_to_file, get_reference

def test_write_to_file_basic():
    # Use tempfile to avoid writing to the actual filesystem
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = os.path.join(tmpdir, "test.html")
        test_content = "<p>Test content</p>"
        
        # Call the function
        write_to_file(test_file, test_content)
        
        # Verify the file was written correctly
        with open(test_file, 'r') as f:
            content = f.read()
            
        # Check that our content is in the file
        assert test_content in content
        
        # Check that the HTML structure is correct
        assert "<html>" in content
        assert "<body>" in content
        assert "</body>" not in content  # Not added by the function
        assert "</html>" in content
        assert "This document last modified" in content

def test_write_to_file_with_title():
    # Use tempfile to avoid writing to the actual filesystem
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = os.path.join(tmpdir, "test.html")
        test_content = "<p>Test content</p>"
        test_title = "Test Title"
        
        # Call the function with a title
        write_to_file(test_file, test_content, title=test_title)
        
        # Verify the file was written correctly
        with open(test_file, 'r') as f:
            content = f.read()
            
        # Check that the title is in the file
        assert f"<title>{test_title}</title>" in content

def test_write_to_file_with_navigation_header_footer():
    # Use tempfile to avoid writing to the actual filesystem
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = os.path.join(tmpdir, "test.html")
        test_content = "<p>Test content</p>"
        test_header = "<header>Test Header</header>"
        test_footer = "<footer>Test Footer</footer>"
        test_nav = "<nav>Test Navigation</nav>"
        
        # Call the function with header, footer, and navigation
        write_to_file(
            test_file, 
            test_content,
            header=test_header,
            footer=test_footer,
            navigation=test_nav
        )
        
        # Verify the file was written correctly
        with open(test_file, 'r') as f:
            content = f.read()
            
        # Check that our elements are in the file
        assert test_header in content
        assert test_footer in content
        assert test_nav in content

def test_md_write_to_file_basic():
    # Use tempfile to avoid writing to the actual filesystem
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = os.path.join(tmpdir, "test.md")
        test_content = "# Test content"
        
        # Call the function
        md_write_to_file(test_file, test_content)
        
        # Verify the file was written correctly
        with open(test_file, 'r') as f:
            content = f.read()
            
        # Check that our content is in the file
        assert test_content in content
        
        # Check that the front matter is correct
        assert "---" in content
        assert "layout: default" in content

def test_md_write_to_file_with_title():
    # Use tempfile to avoid writing to the actual filesystem
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = os.path.join(tmpdir, "test.md")
        test_content = "# Test content"
        test_title = "Test Title"
        
        # Call the function with a title
        md_write_to_file(test_file, test_content, title=test_title)
        
        # Verify the file was written correctly
        with open(test_file, 'r') as f:
            content = f.read()
            
        # Check that the title is in the front matter
        assert f'title: "{test_title}"' in content

def test_md_write_to_file_with_navigation_footer():
    # Use tempfile to avoid writing to the actual filesystem
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = os.path.join(tmpdir, "test.md")
        test_content = "# Test content"
        test_footer = "Test Footer"
        test_nav = "Test Navigation"
        
        # Call the function with footer and navigation
        md_write_to_file(
            test_file, 
            test_content,
            footer=test_footer,
            navigation=test_nav
        )
        
        # Verify the file was written correctly
        with open(test_file, 'r') as f:
            content = f.read()
            
        # Check that our elements are in the file
        assert test_footer in content
        assert test_nav in content

def test_get_reference():
    # This function returns an empty string as it's no longer implemented
    assert get_reference("test_key") == "" 