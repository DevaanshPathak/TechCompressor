# Third-Party Notices

TechCompressor uses the following open-source libraries and dependencies. We are grateful to their maintainers and contributors.

## Direct Dependencies

### cryptography

**Version**: >=41.0.0  
**License**: Apache License 2.0 OR BSD-3-Clause  
**Homepage**: https://github.com/pyca/cryptography  
**Purpose**: AES-256-GCM encryption and PBKDF2 key derivation

**License Text**:
```
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
```

**OR**

```
Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice,
   this list of conditions and the following disclaimer.
2. Redistributions in binary form must reproduce the above copyright
   notice, this list of conditions and the following disclaimer in the
   documentation and/or other materials provided with the distribution.
3. Neither the name of the copyright holder nor the names of its
   contributors may be used to endorse or promote products derived from
   this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
ARE DISCLAIMED.
```

**Attribution**: Copyright (c) Individual contributors to pyca/cryptography

### tqdm

**Version**: >=4.65.0  
**License**: MIT License (MIT) AND Mozilla Public License 2.0 (MPL-2.0)  
**Homepage**: https://github.com/tqdm/tqdm  
**Purpose**: Progress bars for CLI operations

**License Text** (MIT):
```
MIT License

Copyright (c) 2013-2023 tqdm developers

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## Development Dependencies

### pytest

**Version**: >=7.0.0 (dev dependency)  
**License**: MIT License  
**Homepage**: https://github.com/pytest-dev/pytest  
**Purpose**: Testing framework

**License Text**:
```
MIT License

Copyright (c) 2004-2023 Holger Krekel and others

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
```

### pytest-cov

**Version**: >=4.0.0 (dev dependency)  
**License**: MIT License  
**Homepage**: https://github.com/pytest-dev/pytest-cov  
**Purpose**: Test coverage reporting

**License**: MIT (same as pytest)

## Transitive Dependencies

TechCompressor's direct dependencies have their own dependencies. Key transitive dependencies include:

- **cffi** (Cryptography dependency): MIT License
- **pycparser** (cffi dependency): BSD-3-Clause License
- **colorama** (tqdm dependency, Windows only): BSD-3-Clause License

For complete dependency tree:
```bash
pip install pipdeptree
pipdeptree -p techcompressor
```

## Standard Library Components

TechCompressor uses the following Python standard library modules (no additional license obligations):

- `tkinter` - GUI framework (Tcl/Tk license, compatible with Python)
- `struct` - Binary data packing
- `heapq` - Priority queue (Huffman tree construction)
- `argparse` - CLI argument parsing
- `pathlib` - Path manipulation
- `logging` - Application logging
- `threading` - Background operations
- `queue` - Thread-safe queues
- `io` - I/O operations
- `os` - Operating system interface
- `tempfile` - Temporary file handling
- `tarfile` - Not used (reserved for future)

## Algorithm References

TechCompressor implements well-known algorithms. No code was directly copied from algorithm references:

### LZW (Lempel-Ziv-Welch)

**Original Papers**:
- Ziv, J.; Lempel, A. (1977). "A Universal Algorithm for Sequential Data Compression". IEEE Transactions on Information Theory.
- Welch, T. (1984). "A Technique for High-Performance Data Compression". IEEE Computer.

**Patent Status**: Original LZW patent (US 4,558,302) expired June 20, 2003. Algorithm is now in public domain.

**Implementation**: Independent clean-room implementation based on algorithm description.

### Huffman Coding

**Original Paper**:
- Huffman, David (1952). "A Method for the Construction of Minimum-Redundancy Codes". Proceedings of the IRE.

**Patent Status**: Public domain (published 1952, never patented).

**Implementation**: Standard textbook algorithm with binary tree construction.

### DEFLATE

**Specification**:
- RFC 1951 - DEFLATE Compressed Data Format Specification version 1.3
- https://datatracker.ietf.org/doc/html/rfc1951

**Patent Status**: Public specification, widely implemented (gzip, zlib, ZIP).

**Implementation**: Independent implementation based on RFC 1951 specification. Not derived from zlib or other implementations.

## Acknowledgments

TechCompressor would not exist without the broader open-source ecosystem:

- **Python Core Developers**: For the Python language and standard library
- **PyCA/Cryptography Team**: For secure, well-tested cryptography
- **tqdm Developers**: For elegant progress bars
- **pytest Team**: For excellent testing framework
- **Open Source Community**: For countless tools, libraries, and knowledge sharing

## License Compatibility

TechCompressor is licensed under the **MIT License**. All direct and transitive dependencies have MIT or similarly permissive licenses (BSD, Apache 2.0, MPL 2.0), ensuring full compatibility.

**No copyleft (GPL/LGPL) dependencies** are used, allowing TechCompressor to be freely used in proprietary software.

## Updating This Notice

This file is updated when dependencies change. Last verified for TechCompressor v1.0.0.

To generate current dependency list:
```bash
pip install techcompressor
pip list --format=columns
```

## Contact

For questions about licenses or third-party components:

- **Email**: devaanshpathak@example.com
- **Issues**: https://github.com/DevaanshPathak/TechCompressor/issues

---

**Last Updated**: October 25, 2025  
**TechCompressor Version**: 1.0.0  
**Document Version**: 1.0
