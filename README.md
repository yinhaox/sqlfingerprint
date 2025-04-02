# SQL Fingerprint
A Python library for generating normalized SQL fingerprints - useful for query identification, logging, and analysis.
## Features
- 🪄 **Query Normalization** - Produces consistent SQL representations
- 🔍 **Literal Replacement** - Safely replaces values with placeholders
- 📏 **Whitespace Normalization** - Removes insignificant spacing
- 🧹 **Syntax Cleaning** - Standardizes SQL keywords and formatting
- ✅ **Select Clause Preservation** - Maintains string literals in SELECT statements
## Installation
```bash
pip install sqlfingerprint
```
## Quick Start
```python
from sqlfingerprint import SQLFingerprinter

fingerprinter = SQLFingerprinter()
# Basic example
query = "SELECT * FROM users WHERE id = 123"
print(fingerprinter.fingerprint(query))
# Output: select * from users where id = ?
# Complex example
complex_sql = """
    SELECT name, 'const' AS const_val FROM users 
    WHERE email LIKE '%@example.com' 
    AND created_at > '2024-01-01' 
    GROUP BY 1 ORDER BY 1 DESC
"""
print(fingerprinter.fingerprint(complex_sql))
# Output: select name, 'const' as const_val from users where email like ? 
#         and created_at > ? group by 1 order by 1 desc
```
## Use Cases
- 🕵️ Query deduplication in database logs
- 📊 SQL performance analysis
- 🔒 Sensitive data obfuscation
- 🔄 Query pattern recognition
- 📈 Query analytics aggregation
## Normalization Rules
The fingerprinting process applies these transformations：
| Original Element       | Normalized Form       |
|-------------------------|-----------------------|
| String literals (WHERE) | ?                     |
| Numeric literals        | ?                     |
| Boolean values          | ?                     |
| IN lists                | IN (?)                |
| SQL keywords            | Lowercase             |
| Whitespace              | Single space          |
| Comments                | Removed               |
| Backticks               | Removed               |
| Parentheses spacing     | Standardized          |
*SELECT clause string literals are preserved for result set identification*
## Limitations
- Primarily tested with SELECT statements
- May require tuning for complex CTE queries
- Performance scales with query complexity
- SQL dialect support limited to standard SQL
## Contributing
Contributions are welcome! Please follow these steps:
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Add tests for your changes
4. Commit your changes (`git commit -am 'Add some feature'`)
5. Push to the branch (`git push origin feature/your-feature`)
6. Open a Pull Request
Run tests with：
```bash
pytest tests/
```
## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
---
**Project Homepage**: [https://github.com/yinhaox/sqlfingerprint](https://github.com/yinhaox/sqlfingerprint)