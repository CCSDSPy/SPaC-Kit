# SPaC-Kit Test Suite

Comprehensive unit tests for the SPaC-Kit package, which provides tools for working with CCSDS Space Packets.

## Test Organization

The test suite is organized by module to mirror the source code structure:

```
tests/
├── __init__.py
├── conftest.py                    # Shared fixtures
├── parser/                        # Tests for spac_kit.parser module
│   ├── __init__.py
│   ├── test_packets.py           # Packet class tests
│   ├── test_parse_ccsds_downlink.py  # CRC and parsing tests
│   ├── test_remove_non_ccsds_headers.py  # Header removal tests
│   ├── test_downlink_to_excel.py # Excel export tests
│   ├── test_util.py              # Utility function tests
│   └── test_test_utils.py        # Test utility tests
└── autodocs/                      # Tests for spac_kit.autodocs module
    ├── __init__.py
    ├── conftest.py               # Autodocs-specific fixtures
    ├── test_formatters.py        # Field formatting tests ✅
    ├── test_node_generation.py   # Docutils node generation tests
    ├── test_stub_generation.py   # Stub file generation tests
    ├── test_packet_loading.py    # Packet loading tests
    ├── test_setup.py             # Sphinx extension setup tests
    └── test_integration.py       # End-to-end integration tests
```

## Running Tests

### Quick Start

```bash
# Install with dev dependencies
pip install -e '.[dev]'

# Run all tests
pytest

# Run tests for a specific module
pytest tests/parser/
pytest tests/autodocs/

# Run with verbose output
pytest -v

# Run with coverage report
pytest --cov=spac_kit --cov-report=html
```

### Test Categories

Tests are organized with pytest markers:

- `unit`: Unit tests for individual components
- `integration`: Integration tests for multiple components
- `slow`: Tests that take a long time to run

```bash
# Run only unit tests
pytest -m unit

# Skip slow tests
pytest -m "not slow"
```

## Test Results

### Parser Module Tests ✅
- **Total:** 94 tests
- **Passing:** 87  ✅
- **Skipped:** 7 (require ccsds.packets plugin)
- **Coverage:** Core functionality of all main modules

### Autodocs Module Tests (In Progress)
- **Formatters:** 18/18 passing ✅
- **Stub Generation:** 10/16 tests working
- **Setup:** 6/8 tests passing
- **Other modules:** Require directive mocking updates

**Note:** Some autodocs tests require refactoring to use the `mock_directive` fixture. See "Known Issues" below.

## Test Details

### Parser Tests (tests/parser/)

#### [test_packets.py](parser/test_packets.py) (10 tests)
Tests for packet class hierarchy:
- `SimpleAPIDPacket` initialization and attributes
- `PreParserAPIDPacket` with decision fields
- `ParserSubAPIDPacket` with sub-APIDs

**Known Bug:** Documents the argument order bug in lines 33 & 45 of [Packets.py](../src/spac_kit/parser/Packets.py)

#### [test_parse_ccsds_downlink.py](parser/test_parse_ccsds_downlink.py) (21 tests)
Tests for CCSDS parsing and CRC:
- `CalculatedChecksum` converter class
- CRC16-CCITT-False for standard packets
- CRC32-MPEG2 for jumbo packets
- Packet distribution and sub-packet handling
- Tab name generation (documents duplicate counter bug)

#### [test_remove_non_ccsds_headers.py](parser/test_remove_non_ccsds_headers.py) (16 tests)
Tests for header stripping:
- MISE marker validation (`start_sequence`)
- BDSEM header removal
- JSON header stripping
- Combined header removal scenarios

#### [test_downlink_to_excel.py](parser/test_downlink_to_excel.py) (16 tests)
Tests for Excel export:
- Command-line argument parser
- DataFrame to Excel conversion
- Nested DataFrame handling
- Workbook management

#### [test_util.py](parser/test_util.py) (8 tests)
Tests for utility functions:
- `default_pkt` packet definition
- Variable-length packet parsing
- Different APID handling

#### [test_test_utils.py](parser/test_test_utils.py) (14 tests)
Tests for test utilities:
- `recursive_compare` function
- Nested DataFrame comparison
- Error reporting

### Autodocs Tests (tests/autodocs/)

#### [test_formatters.py](autodocs/test_formatters.py) (18 tests) ✅
Tests for field formatting methods:
- Data type formatting (uint, int, float, arrays)
- Bit offset calculation (explicit vs running offset)
- Field value formatting
- Format routing

**Status:** All 18 tests passing ✅

#### [test_node_generation.py](autodocs/test_node_generation.py) (18 tests)
Tests for Docutils/Sphinx node generation:
- Name entries with tooltips
- Summary table rows
- Detail section generation
- Table structure creation
- Full content generation

**Status:** Requires `mock_directive` fixture updates

#### [test_stub_generation.py](autodocs/test_stub_generation.py) (16 tests)
Tests for RST stub file generation:
- Stub directory creation (✅)
- Module scanning for packets (✅)
- Toctree file generation (✅)
- Hierarchical grouping (✅)
- CSS/resource copying (partial)

**Status:** 10/16 tests passing

#### [test_packet_loading.py](autodocs/test_packet_loading.py) (12 tests)
Tests for packet loading from modules:
- Module import and packet discovery
- Error handling for missing modules
- Directive execution (`run` method)
- Column definitions

**Status:** Requires `mock_directive` fixture

#### [test_setup.py](autodocs/test_setup.py) (8 tests)
Tests for Sphinx extension setup:
- Extension metadata (✅)
- Directive registration (✅)
- Config value registration (✅)
- Event hook connections

**Status:** 6/8 tests passing

#### [test_integration.py](autodocs/test_integration.py) (9 tests)
End-to-end integration tests:
- Full directive execution
- Complex packet handling
- Multi-mission organization
- Edge cases (empty packets, None values, etc.)

**Status:** Requires `mock_directive` fixture

## Fixtures

### Shared Fixtures ([conftest.py](conftest.py))

- `sample_ccsds_packet`: Binary CCSDS packet for testing
- `sample_ccsds_file_multiple_apids`: File with multiple APIDs
- `sample_bdsem_wrapped_packet`: BDSEM-wrapped packet
- `sample_mise_wrapped_packet`: MISE-wrapped packet
- `sample_json_header_file`: File with JSON header
- `sample_packet_with_crc`: Packet with valid CRC16
- `sample_jumbo_packet_with_crc`: Jumbo packet with valid CRC32

### Autodocs Fixtures ([autodocs/conftest.py](autodocs/conftest.py))

- `mock_packet_field`: Factory for creating mock PacketField objects
- `mock_simple_packet`: Simple packet with 3 fields
- `mock_array_packet`: Packet with array fields
- `mock_packet_with_descriptions`: Packet with field descriptions
- `mock_packet_with_explicit_offsets`: Packet with explicit bit offsets
- `mock_sphinx_app`: Mock Sphinx application object
- `mock_sphinx_config`: Mock Sphinx configuration object
- **`mock_directive`**: Properly initialized SpacDocsDirective instance (✅ KEY FIXTURE)
- `temp_resources_dir`: Temporary directory with test resources
- `temp_test_module`: Temporary Python module for testing

## Known Issues

### Parser Module

1. **Packet Class Constructor Bug** (HIGH Priority)
   - **Location:** [src/spac_kit/parser/Packets.py:33,45](../src/spac_kit/parser/Packets.py)
   - **Issue:** Arguments in wrong order causing name/apid swap
   - **Tests:** Document actual (buggy) behavior
   - **Fix:** Change `super().__init__(fields, apid, name)` to `super().__init__(fields, name, apid)`

2. **Tab Name Duplicate Counter** (MEDIUM Priority)
   - **Location:** [src/spac_kit/parser/parse_ccsds_downlink.py:370-374](../src/spac_kit/parser/parse_ccsds_downlink.py)
   - **Issue:** Appends "(1)" repeatedly instead of incrementing
   - **Tests:** Document actual behavior in test
   - **Fix:** Store base_name and increment counter properly

### Autodocs Module

3. **Sphinx Directive Mocking** (TEST Issue - IN PROGRESS)
   - **Issue:** `SpacDocsDirective` requires proper Sphinx state_machine
   - **Solution:** Use `mock_directive` fixture from conftest
   - **Status:** ✅ Implemented for formatters, needs application to other tests
   - **Pattern:**
     ```python
     # OLD (fails):
     directive = SpacDocsDirective("spacdocs", [], {}, "", 0, 0, "", None, None)

     # NEW (works):
     def test_something(self, mock_directive, mock_packet_field):
         field = mock_packet_field(...)
         result = mock_directive.some_method(field)
     ```

4. **Integration Tests Require Plugin** (EXPECTED)
   - **Issue:** 7 parser tests skipped without ccsds.packets plugin
   - **Status:** Expected behavior, tests will pass with plugin installed
   - **Plugin:** [europa-clipper-ccsds-plugin](https://github.com/nasa-jpl/spac-kit-europa-clipper)

## Test Development Guidelines

### Adding New Tests

1. **Organize by module:** Place tests in the appropriate subdirectory
2. **Use fixtures:** Leverage shared fixtures from conftest.py
3. **Follow naming:** `test_<module>.py` for files, `test_<function>` for tests
4. **Document bugs:** If testing buggy behavior, add clear comments explaining the bug

### Testing Directives (Important!)

When testing Sphinx directives, **always use the `mock_directive` fixture**:

```python
def test_my_feature(self, mock_directive, mock_packet_field):
    """Test description."""
    field = mock_packet_field(name="test", data_type="uint", bit_length=16)
    result = mock_directive._some_method(field)
    assert result == expected
```

**Do NOT** try to instantiate `SpacDocsDirective` directly - it will fail without proper Sphinx internals.

### Testing Stub Generation

For tests that need to create actual files, use `tmp_path` fixture:

```python
def test_creates_files(self, mock_sphinx_app, tmp_path):
    """Test that files are created."""
    mock_sphinx_app.srcdir = str(tmp_path)
    generate_packet_stubs(mock_sphinx_app)

    assert (tmp_path / "_autopackets").exists()
```

### Mocking Module Imports

When testing code that imports modules dynamically:

```python
@patch("spac_kit.autodocs.importlib.import_module")
def test_imports(self, mock_import):
    mock_module = MagicMock()
    mock_module.packet = Mock(spec=_BasePacket)
    mock_import.return_value = mock_module
    # ... test code
```

## Contributing

When adding new features to SPaC-Kit, please:

1. Write tests first (TDD approach recommended)
2. Ensure all existing tests still pass
3. Add integration tests for new features
4. Update this README if adding new test modules
5. Document any known bugs or limitations
6. Use the `mock_directive` fixture for Sphinx directive tests

## CI/CD Integration

The test suite is designed for CI/CD integration. Recommended GitHub Actions workflow:

```yaml
name: Test Suite
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.12'
      - run: pip install -e '.[dev]'
      - run: pytest --cov=spac_kit --cov-report=xml
      - uses: codecov/codecov-action@v2
```

## Next Steps

To complete the autodocs test suite:

1. ✅ **Formatters** - Complete (18/18 tests passing)
2. **Node Generation** - Apply `mock_directive` pattern from formatters
3. **Packet Loading** - Apply `mock_directive` pattern
4. **Integration Tests** - Apply `mock_directive` pattern
5. **Stub Generation** - Fix remaining CSS/resource tests

**Pattern to follow:** See [test_formatters.py](autodocs/test_formatters.py) for the correct approach.

## Resources

- [pytest documentation](https://docs.pytest.org/)
- [pytest-cov documentation](https://pytest-cov.readthedocs.io/)
- [Sphinx extension testing](https://www.sphinx-doc.org/en/master/development/tutorials/extending_build.html)
- [CCSDSPy documentation](https://docs.ccsdspy.org/)
- [SPaC-Kit TODO](../TODO.md) - Known bugs and improvements

---

**Last Updated:** 2026-02-17
**Parser Tests:** 87/94 passing (7 skipped - need plugin) ✅
**Autodocs Tests:** Formatters complete (18/18), others in progress
