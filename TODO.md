# TODO: Add Fingerprint Scanner Feature

## 1. Install Dependencies
- [ ] Add pyfingerprint to requirements.txt
- [ ] Install pyfingerprint library

## 2. Update Database Schema
- [ ] Add fingerprint_template column to employees table for storing fingerprint data

## 3. Modify UI for Employee Registration
- [ ] Add fingerprint scanning button in add employee form
- [ ] Implement fingerprint enrollment logic
- [ ] Store fingerprint template in database

## 4. Modify UI for Attendance Marking
- [ ] Replace manual ID entry with fingerprint scanning
- [ ] Implement fingerprint verification logic
- [ ] Match scanned fingerprint against stored templates

## 5. Add Fingerprint Scanner Class
- [ ] Create a new file src/fingerprint_scanner.py
- [ ] Implement FingerprintScanner class with enroll and verify methods

## 6. Update Main UI
- [ ] Remove placeholder comments and integrate real scanner
- [ ] Handle scanner connection errors gracefully

## 7. Testing
- [ ] Test fingerprint enrollment
- [ ] Test fingerprint verification
- [ ] Handle edge cases (no sensor, invalid scans, etc.)
