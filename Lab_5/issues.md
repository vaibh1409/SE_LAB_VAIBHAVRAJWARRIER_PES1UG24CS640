# Issues Found – car_rental.py

Line numbers refer to the original file. Baseline: Pylint 4.94/10, Flake8 25 warnings, Bandit 11 issues (2 High, 4 Medium, 5 Low).

| Issue | Type | Line(s) | Description | Fix Approach |
|---|---|---|---|---|
| Weak SHA1 hash (B324) | Security (High) | 48 | Licence numbers hashed with SHA1, which is cryptographically weak | Switched to SHA-256 |
| Permissive file mode 0o777 (B103) | Security (High) | 67 | Receipt file is readable, writable and executable by everyone | Removed chmod; file made with `NamedTemporaryFile` (private by default) |
| SQL injection in registerCustomer (B608) | Security (Medium) | 23 | Query built with `%` formatting from user input | Parameterized query with `?` placeholders |
| SQL injection in findCustomer (B608) | Security (Medium) | 26 | Name concatenated into the SQL string; `x' OR '1'='1` returned all rows | Parameterized query |
| Use of exec (B102, W0122) | Security (Medium) | 53 | Promo rule string typed by staff was executed as code (arbitrary code execution) | Replaced with a whitelist dictionary of named promo rules |
| Insecure mktemp (B306) | Security (Medium) | 63 | Predictable temp file name allows a race condition | Used `tempfile.NamedTemporaryFile` |
| Unclosed file / no encoding (R1732, W1514) | Quality (Medium) | 64-67 | `open()` without `with` or encoding | Used `with` and `encoding="utf-8"` |
| Hardcoded admin password (B105/B107) | Security (Low) | 70-71 | Password `admin@rent` stored in source and used as a default, so `adminLogin("admin")` always succeeded | Removed default; read `ADMIN_PASSWORD` from environment; compare with `hmac.compare_digest` |
| assert used for validation (B101) | Bug (Low) | 30 | Removed when Python runs with `-O`, disabling the check | Replaced with `raise ValueError` |
| Bare except with pass (B110, W0702, E722) | Bug (Low) | 41-42 | Silently swallowed every error, so returning an unknown car did nothing | Removed try/except; explicit `ValueError` for unknown car |
| Weak random (B311) | Security (Low) | 45 | `random` is predictable for booking codes | Used the `secrets` module |
| Mutable default argument (W0102) | Bug (Medium) | 16 | `features=[]` shared across all cars | Default `None`; new list created inside the function |
| Inconsistent returns (R1710) | Bug (Medium) | 16, 36 | `addCar` and `returnCar` returned a value on some paths and `None` on others | `addCar` raises on invalid input; `returnCar` returns `0` explicitly |
| Double booking (logic) | Bug (High) | 29-34 | `rentCar` never marked the car unavailable, so the same car was rented twice | Check availability and set `available = False` on rental |
| Negative cost from bad dates (logic) | Bug (Medium) | 31 | End date before start date gave a negative price (Innova rental) | Raise `ValueError` if days <= 0 |
| Negative daily rate accepted (logic) | Bug (Medium) | 16-19 | A car could be added with rate -500 | Validate `daily_rate >= 0` |
| Plain-text licence storage (logic) | Security (Medium) | 23 | Licence numbers stored unhashed although `licenceHash` existed unused | Store `licence_hash(licence)` |
| Unvalidated plates / unknown car on rent (logic) | Bug (Low) | 16, 29 | `isValidPlate` was never used; renting an unknown plate raised KeyError | Validate plate in `add_car`; clear error in `rent_car` |
| No main guard (logic) | Quality (Low) | 101 | `main()` ran whenever the module was imported | Added `if __name__ == "__main__":` |
| Unused import (W0611, F401) | Quality (Low) | 2 | `json` imported but never used | Removed |
| Missing docstrings (C0114, C0116) | Quality (Low) | 1, 16-82 | Module and every function lacked a docstring | Added docstrings |
| Non-snake_case names (C0103) | Style (Low) | 16-82 | `addCar`, `rentCar`, `returnCar`, etc. | Renamed to snake_case |
| Simplifiable if/else (R1703, R1705) | Quality (Low) | 57-60 | if/else returning True/False | `return bool(PLATE_PATTERN.match(plate))` |
| Comparison to True (C0121, E712) | Style (Low) | 78 | `== True` | Use truthiness in a list comprehension |
| Dict iteration (C0206) | Quality (Low) | 77 | Looped over keys then indexed | Iterate with `.items()` |
| Old % formatting (C0209) | Style (Low) | 23, 65 | `%` string formatting | f-strings / parameterized SQL |
| Lines too long (E501, C0301) | Style (Low) | 19, 23, 31, 33, 65, 88-90 | Lines over 79 characters | Wrapped lines |
| Blank lines (E302, E305) | Style (Low) | 16-101 | Top-level definitions not separated by two blank lines | Added blank lines |

## Results

| Tool | Before | After |
|---|---|---|
| Bandit | 11 issues (2 High, 4 Medium, 5 Low) | 0 issues |
| Pylint | 4.94/10 | 10.00/10 |
| Flake8 | 25 warnings | 0 warnings |
