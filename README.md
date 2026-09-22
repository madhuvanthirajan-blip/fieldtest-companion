# FieldTest Companion — Streamlit Prototype

A mobile-friendly Streamlit prototype for the "Digital Companion for Field Drug Testing" problem statement.

## Scope

Included:
- Mobile/browser camera capture
- Reference-card + test-strip workflow
- RGB lighting calibration
- Prototype color classification
- POSITIVE / NEGATIVE / INCONCLUSIVE
- Confidence score
- Operator ID
- Timestamp
- Browser GPS when permission is granted
- Local test history
- Search/filter
- PDF report generation
- PDF download for sharing

Not included:
- SHA-256 security core
- Central database
- Streamlit admin dashboard
- Laboratory-grade drug identification

## Important

The positive and negative color profiles are DEMO values for a prototype. They must not be presented as a validated narcotics-testing model.

The app is intended to demonstrate the engineering workflow:
Capture -> Calibrate -> Classify -> Record -> PDF -> Share.

## Windows setup

```powershell
cd fieldtest_streamlit_app

python -m venv venv
venv\Scripts\activate

python -m pip install --upgrade pip
pip install -r requirements.txt

streamlit run app.py
```

Open the URL shown by Streamlit.

For phone testing on the same Wi-Fi:

```powershell
streamlit run app.py --server.address 0.0.0.0
```

Then open the displayed Network URL from the phone.

## Phone camera

When opened in a mobile browser, `st.camera_input()` requests camera permission. Allow it.

## GPS

The app uses `streamlit-geolocation` and asks the browser for location permission. GPS may be unavailable on desktop or when browser permissions are blocked.

## Demo workflow

1. Print the provided demo card.
2. Put REFERENCE CARD on the left.
3. Put a dummy strip on the right.
4. Open New Test.
5. Enter Operator ID.
6. Capture.
7. Analyze Test.
8. Show the result.
9. Generate PDF.
10. Save/download PDF and share it using the phone's share UI.
11. Open History and search the test.

## Demo profiles

Positive:
- magenta/pink

Negative:
- yellow/green

The CV code is deliberately simple and deterministic for the prototype. A production version should use automatic reference-card detection, perspective correction, HSV/LAB features, kit-specific calibration, and a validated dataset.
