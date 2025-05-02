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
- [x] Improved docstrings in lynguine/config/interface.py, enhancing:
  - Class-level docstring with better explanation of the hierarchical interface concept
  - Method-level docstrings for from_file, __init__, and _process_parent
- [ ] Target remaining modules for docstring improvements based on test coverage results

## Test Coverage Improvements

### 1. Fix Immediate Test Issues
- [ ] Fix the failures in lynguine/assess/data.py tests related to NumPy compatibility issues with _NoValueType
- [ ] Prioritize fixing CustomDataFrame implementation to work with current pandas/numpy versions

### 2. Add Tests for Modules with Low Coverage
- [ ] lynguine/util/html.py (29% coverage)
- [ ] lynguine/assess/compute.py (51% coverage)
- [ ] lynguine/config/interface.py (56% coverage)
- [ ] lynguine/util/yaml.py (61% coverage)

### 3. Create Tests for Modules with No Coverage
- [ ] Create basic test scaffolding for the following modules:
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

### 4. Improve Code Quality
- [ ] Refactor code to make it more testable where necessary
- [ ] Remove or update deprecated code that relies on old versions of dependencies

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
  - Class-level docstring with better explanation of the hierarchical interface concept
  - Method-level docstrings including from_file, __init__, and _process_parent
- Fixed liquid environment initialization in compute.py (Mode.LAX instead of deprecated constants)
- Analyzed test coverage to identify priority modules for improvement
- Identified NumPy/Pandas compatibility issues breaking tests in lynguine/assess/data.py

### 2024-11-03
- Fixed compatibility issues with newer versions of NumPy and Pandas:
  - Updated liquid environment initialization in compute.py to use Mode.LAX instead of deprecated constants
  - Fixed data.py to use DataFrame.loc indexing instead of direct [] indexing to avoid _NoValueType errors
  - Updated util/dataframe.py functions (reorder_dataframe, ascending, descending) to avoid NumPy _NoValueType issues

### Next Steps
1. Fix the compatibility issue with CustomDataFrame in data.py breaking tests
2. Create basic tests for lynguine/util/html.py to improve its low coverage
3. Write tests for remaining no-coverage modules in order of importance/usage 