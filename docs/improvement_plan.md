# Lynguine Documentation and Test Coverage Improvement Plan

## Documentation Improvements

### 1. Fix Documentation Build System
- [x] Add Sphinx and related dependencies to the poetry dev dependencies
- [x] Correct module names from ndlpy to lynguine throughout documentation
- [x] Ensure conf.py correctly identifies the project

### 2. Enhance Module Documentation
- [x] Update .rst files to provide meaningful module overviews
- [ ] Add examples and usage patterns to module documentation
- [ ] Include architecture diagrams to explain data flow
- [x] Create proper index.rst that accurately reflects the project

### 3. Improve Code Docstrings
- [x] Reviewed lynguine/assess/compute.py and confirmed it has comprehensive docstrings
- [x] Improved docstrings in lynguine/config/interface.py with more detailed explanations
- [ ] Improve docstrings in lynguine/assess/data.py (next target)
- [ ] Ensure consistency in docstring format across all modules
- [ ] Add more examples within docstrings for complex functions

### 4. Documentation Generation
- [x] Successfully build documentation with sphinx-build
- [x] Created GitHub Actions workflow for documentation generation
- [ ] Consider using Read the Docs for hosting

## Test Coverage Improvements

### 1. Target Low-Coverage Areas
- [ ] Add tests for lynguine/assess/compute.py (49% coverage)
- [ ] Add tests for lynguine/config/interface.py (56% coverage)
- [ ] Improve coverage for lynguine/assess/data.py (64% coverage)

### 2. Add Tests for Uncovered Scripts
- [ ] Create tests for utility scripts at 0% coverage:
  - [ ] lynguine/clone_or_pull.py
  - [ ] lynguine/convert.py
  - [ ] lynguine/ndlappointment.py
  - [ ] lynguine/ndlcal.py
  - [ ] lynguine/ndlconvert.py
  - [ ] lynguine/ndlexpenses.py
  - [ ] lynguine/ndlimage.py
  - [ ] lynguine/ndlmarkdown.py
  - [ ] lynguine/ndlstrutil.py
  - [ ] lynguine/ndltext.py
  - [ ] lynguine/old_data.py

### 3. Integration Tests
- [ ] Add more integration tests to ensure components work together
- [ ] Test data flow from input through processing to output

### 4. Test Automation
- [x] Created GitHub Actions workflow for test coverage reporting
- [ ] Enforce minimum coverage requirements in CI/CD

## Implementation Timeline

### Phase 1: Setup and Foundation (Week 1-2)
- ✅ Fix documentation build system
- ✅ Created documentation GitHub action
- ✅ Created test coverage GitHub action
- ❌ Attempted to improve docstrings in lynguine/assess/compute.py (encountered errors)

### Phase 2: Core Coverage (Week 3-4)
- [ ] Complete module documentation updates
- [ ] Add tests for lynguine/config/interface.py
- [ ] Add tests for 3-5 utility scripts

### Phase 3: Completion and Integration (Week 5-6)
- [ ] Finish remaining docstrings
- [ ] Complete tests for remaining utility scripts
- [ ] Add integration tests
- [ ] Set up documentation generation in CI/CD

## Progress Tracking

### 2024-11-01
- Added Sphinx and related dependencies to poetry dev-dependencies
- Updated conf.py to use Read the Docs theme and fix project identification
- Created appropriate module documentation files for lynguine.access, lynguine.assess, lynguine.config, and lynguine.util
- Fixed index.rst to reflect the current project structure
- Successfully built documentation using sphinx-build
- Created GitHub Actions workflow for documentation and test coverage

### 2024-11-02
- Reviewed lynguine/assess/compute.py and confirmed it already has comprehensive docstrings
- Improved docstrings in lynguine/config/interface.py, enhancing:
  - Class-level docstring with better explanation of hierarchical inheritance
  - Method docstrings for from_file, __init__, and _process_parent
  - Parameter descriptions for improved clarity
- Fixed a bug in lynguine/assess/compute.py related to python-liquid compatibility
  - Updated to use liquid.Mode.LAX instead of deprecated constants
  - Ensured all tests pass successfully

### Next Steps
- Focus on improving test coverage for modules with low coverage
- Add example code snippets to module documentation
- Improve docstrings in remaining modules 