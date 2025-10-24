# TechCompressor AI Coding Assistant Instructions

## Project Overview

TechCompressor is a modular Python compression framework currently in **Phase 1** (completed setup). The project follows a phased development roadmap with future implementations of LZW, Huffman, Arithmetic coding, DEFLATE, AES encryption, archiving, GUI (Tkinter), and CLI interfaces.

## Architecture & Design Principles

### Modular Structure
The codebase is organized into distinct modules with clear separation of concerns:
- `core.py` - Main compression/decompression API (currently placeholder)
- `archiver.py` - Multi-file and folder handling (Phase 7)
- `crypto.py` - AES encryption for compressed data (Phase 6)
- `cli.py` - argparse-based command-line interface (Phase 9)
- `gui.py` - Tkinter GUI implementation (Phase 8)
- `utils.py` - Shared utilities and logging helpers

### Key Patterns
1. **Phased Development**: The project follows a 10-phase roadmap. Most modules are stubs with `pass` statements awaiting future implementation. Check README.md roadmap before implementing features.

2. **Type Hints**: Use modern Python type hints (PEP 604 unions with `|` syntax). Example from `core.py`:
   ```python
   def compress(data: bytes, algo: str = "LZW", password: str | None = None) -> bytes:
   ```

3. **Logging Pattern**: Use the standardized logger from `utils.get_logger()`:
   ```python
   from techcompressor.utils import get_logger
   logger = get_logger(__name__)
   ```
   Format: `"[%(levelname)s] %(name)s: %(message)s"` with INFO level default.

## Development Workflow

### Environment Setup
```bash
pip install -r requirements.txt  # Installs: cryptography, tqdm, pytest
```

### Testing
```bash
pytest  # Run all tests from project root
```
Current test suite: `tests/test_sanity.py` validates basic imports only.

### Code Standards
- **Python Version**: Requires Python >= 3.10
- **Style**: PEP 8 compliance expected
- **Build System**: Uses modern `pyproject.toml` with setuptools backend
- **Package Version**: Defined in both `pyproject.toml` and `techcompressor/__init__.py` (currently 0.1.0)

## Critical Implementation Notes

### Current State (Phase 1)
- Most modules are intentional stubs - don't treat empty files as bugs
- `core.compress()` and `core.decompress()` raise `NotImplementedError` by design
- Framework is ready for algorithm implementations (Phases 2-5)

### Future Integration Points
- **Algorithms** (Phases 2-5): Will be implemented in `core.py` with `algo` parameter routing
- **Encryption** (Phase 6): `password` parameter in `core.py` will trigger `crypto.py` wrapper
- **Archiving** (Phase 7): `archiver.py` will handle metadata and multi-file TAR-like structures
- **UIs** (Phases 8-9): Both CLI and GUI will consume the `core` module API

### Dependencies
- `cryptography` - Future AES encryption (Phase 6)
- `tqdm` - Progress bars for CLI/GUI operations
- `pytest` - Testing framework

## When Adding Features

1. **Check the roadmap phase** - Ensure you're working on the correct phase sequence
2. **Maintain API consistency** - Keep `compress()` and `decompress()` signatures stable
3. **Update version** - Coordinate changes to `__version__` in both `__init__.py` and `pyproject.toml`
4. **Add tests** - Follow the pattern in `tests/test_sanity.py` with descriptive docstrings
5. **Document algorithm choices** - Compression algorithms should be well-commented for educational purposes

## Project-Specific Conventions

- **Module docstrings** include phase targets (e.g., `"(Phase 6 target)"`)
- **Placeholder modules** use `pass` rather than empty files
- **Error handling**: Use `NotImplementedError` for unimplemented features, not `TODO` comments
- **Imports**: Prefer absolute imports (`from techcompressor.utils import ...`)

## License
MIT License - Copyright (c) 2025 Devaansh Pathak
