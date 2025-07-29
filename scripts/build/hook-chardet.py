#!/usr/bin/env python3
"""
PyInstaller hook for chardet module.
Ensures all chardet submodules are properly included in the bundle.
"""

from PyInstaller.utils.hooks import collect_all

# Collect all chardet modules and data
datas, binaries, hiddenimports = collect_all('chardet')

# Ensure specific chardet modules are included
hiddenimports += [
    'chardet.charsetprober',
    'chardet.universaldetector',
    'chardet.charsetgroupprober',
    'chardet.enums',
    'chardet.escprober',
    'chardet.latin1prober',
    'chardet.mbcharsetprober',
    'chardet.sbcharsetprober',
    'chardet.utf8prober',
    'chardet.chardetng',
]