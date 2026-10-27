# Issues Found and Fixed

| Issue | Type | Line(s) | Description | Fix Approach |
|-------|------|---------|-------------|--------------|
| CGIHandler (httpoxy) | Security (Bandit B412, High) | 6, 92 | CGIHandler can be tricked via the HTTP_PROXY header (httpoxy attack) | Remove HTTP_PROXY from the environment before running the handler; reviewed and marked with `# nosec B412` |
| Insecure ECB cipher mode | Security (Bandit B305, Medium) | 77 | ECB encrypts identical PANs to identical ciphertext, leaking patterns; fixed 16-byte padding with spaces | Replaced with AES-GCM using a random nonce per encryption |
| Hardcoded encryption key | Security | PAN_KEY constant | Key `0123456789abcdef` was hardcoded in source | Load key from `PAN_KEY_HEX` environment variable, otherwise generate a random 256-bit key |
| Weak RSA key | Security (Bandit B505, Medium) | 83 | 1024-bit RSA keys are considered breakable | Increased key size to 2048 |
| Unsafe XML parsing | Security (Bandit B318 Medium, B408 Low) | 5, 86 | minidom is vulnerable to XML attacks (entity expansion) on untrusted Form-16 input | Switched to `defusedxml.minidom` |
| Inverted regime comparison | Logic bug | 63-67 (`betterRegime`) | Returned "new" when new tax was higher (3,58,800 vs 2,79,240) | Return "new" only when new tax is lower than old tax |
| Flat rate on whole income | Logic bug | 18-31, 34-40 (`slabRate`, `newRegimeTax`) | One slab rate applied to all income instead of marginal slabs; 18L gave 3,58,800 instead of 1,50,800 | Replaced with a shared `slab_tax` function that applies each rate only to its band |
| Rebate boundary and cess order | Logic bug | 38-41 (`newRegimeTax`) | `<` excluded income exactly at the 12L limit, and cess was computed before the rebate zeroed the tax | Use `<=` and apply cess after the rebate |
| Basic exemption at age 80 | Logic bug | 44-47 (`basicExemption`) | `age > 80` meant age 80 got 2,50,000 instead of 5,00,000 | Changed to `age >= 80` |
| PAN validation accepts extra characters | Logic bug | 73 | `re.match` has no end anchor, so `ABCDE1234FXYZ` passed | Use `re.fullmatch` and catch `TypeError` |
| Leftover debug print | Code quality | 60 (`oldRegimeTax`) | Printed "Last slab rate applied" on every call | Removed |
| Bare except | Quality (Pylint W0702, Flake8 E722) | 73 | Catches every exception, hiding real errors | Catch only `TypeError` |
| Unused imports, variables, arguments | Quality (Pylint W0611/W0612/W0613, Flake8 F401/F841) | 2-4, 36, 85, 91 | `sys`, `json`, `bracket`, `checked`, `strict`, `debug` never used | Removed |
| camelCase names | Style (Pylint C0103) | many | Function and variable names did not follow snake_case | Renamed all to snake_case |
| Missing docstrings | Style (Pylint C0114/C0116) | 1 and every function | No module or function documentation | Added docstrings |
| Formatting | Style (Flake8 E302/E305/E501/E702) | many | Missing blank lines, long lines, semicolon statement | Fixed layout and split long lines |

**Results:** Bandit 6 issues to 0, Pylint 4.57 to 10.00, Flake8 23 messages to 0.