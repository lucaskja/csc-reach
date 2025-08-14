# Chardet Module Fix for Windows Build

## Problem
The Windows application was failing with the error: "Failed to analyze CSV file: No module named 'chardet'"

## Root Cause
The `chardet` module was being imported inside a method (`detect_encoding`) rather than at the module level, which can cause PyInstaller to miss the dependency during runtime bundling, even though it was listed in `hiddenimports`.

## Solution Implemented

### 1. Fixed Import Structure
- **File**: `src/multichannel_messaging/core/csv_processor.py`
- **Change**: Moved `chardet` import from inside the `detect_encoding` method to the top of the file
- **Added**: Conditional import with fallback handling:
  ```python
  try:
      import chardet
  except ImportError:
      chardet = None
  ```

### 2. Enhanced Error Handling
- **Added**: Robust fallback mechanism when `chardet` is not available
- **Fallback Strategy**: Try common encodings (utf-8, latin-1, cp1252, iso-8859-1) in order
- **Logging**: Added appropriate warning messages when fallback is used

### 3. Improved PyInstaller Configuration
- **File**: `scripts/build/build_windows.spec`
- **Added**: Additional chardet submodules to `hiddenimports`:
  - `chardet.charsetprober`
  - `chardet.universaldetector`
- **Added**: Custom PyInstaller hook path

### 4. Created PyInstaller Hook
- **File**: `scripts/build/hook-chardet.py`
- **Purpose**: Ensures all chardet submodules are properly included in the bundle
- **Method**: Uses `collect_all('chardet')` to gather all related modules

### 5. Applied to Both Platforms
- **Updated**: Both Windows and macOS spec files for consistency
- **Ensures**: Cross-platform compatibility

## Testing
Created comprehensive tests to verify:
1. **Normal Operation**: `test_chardet.py` - Tests chardet import and functionality
2. **Fallback Mechanism**: `test_chardet_fallback.py` - Tests behavior when chardet is unavailable

## Files Modified
1. `src/multichannel_messaging/core/csv_processor.py` - Fixed import and added fallback
2. `scripts/build/build_windows.spec` - Enhanced hiddenimports and hook path
3. `scripts/build/build_macos.spec` - Added hook path for consistency
4. `scripts/build/hook-chardet.py` - New PyInstaller hook file

## Result
- ✅ Windows build should now properly include chardet module
- ✅ Robust fallback mechanism if chardet is still missing
- ✅ Better error messages and logging
- ✅ Cross-platform consistency maintained

## Next Steps
1. Rebuild the Windows executable using the updated configuration
2. Test the built executable with CSV files to verify the fix
3. Consider adding chardet availability check to the application startup diagnostics