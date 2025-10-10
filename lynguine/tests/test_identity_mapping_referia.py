"""
Test for identity mapping override bug found in referia.

This test reproduces the bug where identity mappings (column -> column) created by
_augment_column_names in __init__ conflict with explicit vstack mappings like
jobTitle: job_title.

The bug only appears when using referia's CustomDataFrame which calls
_augment_column_names in __init__ (line 180 in referia/assess/data.py).
"""

import pytest
import tempfile
import os
import shutil
import lynguine.config.interface
import lynguine.assess.data


def test_identity_mapping_override_with_vstack():
    """
    Test that lynguine is strict and does not allow overriding auto-generated identity mappings.
    
    This reproduces the scenario where:
    1. referia's CustomDataFrame.__init__ calls _augment_column_names, creating job_title -> job_title
    2. Later, vstack mapping tries to apply jobTitle: job_title
    3. lynguine should raise ValueError about conflicting mappings (strict behavior)
    """
    
    # Patch lynguine's CustomDataFrame to mimic referia's behavior
    orig_init = lynguine.assess.data.CustomDataFrame.__init__
    def patched_init(self, *args, **kwargs):
        orig_init(self, *args, **kwargs)
        # This is what referia does in its __init__ (lines 178-180 in referia/assess/data.py)
        for typ in self._d:
            self._augment_column_names(self._d[typ])
    lynguine.assess.data.CustomDataFrame.__init__ = patched_init
    
    try:
        tmpdir = tempfile.mkdtemp()
        
        # Create minimal markdown files with job_title field
        people_dir = f"{tmpdir}/_people"
        os.makedirs(people_dir)
        
        with open(f"{people_dir}/john_smith.md", 'w') as f:
            f.write("---\ngiven: John\nfamily: Smith\njob_title: Professor\n---\n")
        
        with open(f"{tmpdir}/_referia.yml", 'w') as f:
            f.write(f"""input:
  type: vstack
  index: Name
  mapping:
    jobTitle: job_title
  specifications:
  - type: markdown_directory
    compute:
      field: Name
      function: render_liquid
      args:
        template: "{{{{ family }}}}_{{{{ given }}}}"
      row_args:
        given: given
        family: family
    source:
    - glob: "*.md"
      directory: {people_dir}/
""")
        
        interface = lynguine.config.interface.Interface.from_file(
            user_file="_referia.yml", 
            directory=tmpdir
        )
        
        # This SHOULD raise ValueError because lynguine is strict
        with pytest.raises(ValueError, match="Column.*already exists in the name-column map"):
            data = lynguine.assess.data.CustomDataFrame.from_flow(interface)
        
    finally:
        # Restore original __init__
        lynguine.assess.data.CustomDataFrame.__init__ = orig_init
        # Cleanup
        shutil.rmtree(tmpdir, ignore_errors=True)
