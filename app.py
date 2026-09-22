import json
import uuid
from datetime import datetime
from pathlib import Path

import streamlit as st
from PIL import Image

from cv_engine import analyze_image
from pdf_report import create_pdf_report

try:
    from streamlit_geolocation import streamlit_geolocation
except Exception:
    streamlit_geolocation = None

APP_DIR = Path(__file__).resolve().parent
DATA_DIR = APP_DIR / "data"
IMAGE_DIR = DATA_DIR / "images"
HISTORY_FILE = DATA_DIR / "history.json"
IMAGE_DIR.mkdir(parents=True, exist_ok=True)

st.set_page_config(
    page_title="FieldTest Companion",
    page_icon="🧪",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ---------- Styling ----------
st.markdown("""
<style>
    .stApp {
        background: #07111f;
        color: #eef6ff;
    }
    .block-container {
        max-width: 760px;
        padding: 1rem 1rem 3rem;
    }
    .hero {
        padding: 22px;
        border-radius: 24px;
        background: linear-gradient(145deg, #10243a, #091827);
        border: 1px solid #1f405d;
        margin-bottom: 14px;
    }
    .hero h1 { margin: 0; font-size: 2rem; }
    .hero p { color: #a9c0d6; margin-bottom: 0; }
    .result-card {
        padding: 24px;
        border-radius: 24px;
        background: #0d1b2a;
        border: 1px solid #24435d;
        text-align: center;
    }
    .result {
        font-size: 2.2rem;
        font-weight: 800;
        letter-spacing: 1px;
    }
    .positive { color: #ff5d8f; }
    .negative { color: #b7e34b; }
    .inconclusive { color: #ffc857; }
    .small {
        color: #91a9bf;
        font-size: .88rem;
    }
    .pill {
        display: inline-block;
        padding: 6px 12px;
        border-radius: 999px;
        background: #132d43;
        color: #9edbff;
        font-size: .82rem;
        margin-right: 5px;
    }
    div[data-testid="stMetric"] {
        background: #0d1b2a;
        border: 1px solid #203d56;
        padding: 12px;
        border-radius: 16px;
    }
    .disclaimer {
        background: #241d0b;
        border: 1px solid #67511c;
        border-radius: 14px;
        padding: 12px 14px;
        color: #eadca8;
        font-size: .84rem;
    }
</style>
""", unsafe_allow_html=True)

# ---------- Storage ----------
def load_history():
    if not HISTORY_FILE.exists():
        return []
    try:
        return json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []

def save_history(history):
    HISTORY_FILE.write_text(
        json.dumps(history, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

def get_location():
    if streamlit_geolocation is None:
        return None
    try:
        loc = streamlit_geolocation()
        if loc and loc.get("latitude") is not None and loc.get("longitude") is not None:
            return {
                "latitude": float(loc["latitude"]),
                "longitude": float(loc["longitude"]),
                "accuracy": loc.get("accuracy"),
            }
    except Exception:
        pass
    return None

def reset_test():
    for key in ["capture_bytes", "analysis", "last_record", "pdf_path"]:
        st.session_state.pop(key, None)

# ---------- Header ----------
st.markdown("""
<div class="hero">
  <div class="pill">FIELD TEST PROTOTYPE</div>
  <h1>🧪 FieldTest Companion</h1>
  <p>Capture → Calibrate → Classify → Generate Report</p>
</div>
""", unsafe_allow_html=True)

history = load_history()

# ---------- Navigation ----------
tab_capture, tab_history, tab_about = st.tabs(["📷 New Test", "🗂 History", "ℹ️ About"])

with tab_capture:
    st.subheader("1. Test information")

    c1, c2 = st.columns(2)
    with c1:
        operator_id = st.text_input("Operator ID", value="OP-001")
    with c2:
        kit_profile = st.selectbox(
            "Demo kit profile",
            ["Demo Colorimetric Kit"]
        )

    st.markdown("### 2. Capture the test")
    st.caption(
        "Place the printed reference card on the LEFT and one dummy test strip "
        "on the RIGHT. Keep both inside the camera frame."
    )

    # Camera input works in mobile browsers and asks for camera permission.
    photo = st.camera_input(
        "Open camera / capture image",
        key="field_camera"
    )

    location = get_location()
    if location:
        st.success(
            f"GPS detected: {location['latitude']:.6f}, "
            f"{location['longitude']:.6f}"
        )
    else:
        st.info(
            "GPS is not available yet. Allow browser location permission and "
            "refresh/reopen this section. GPS is optional for the local demo."
        )

    if photo:
        st.session_state["capture_bytes"] = photo.getvalue()

        st.image(
            st.session_state["capture_bytes"],
            caption="Captured field-test image",
            use_container_width=True
        )

        st.markdown("### 3. Computer vision analysis")

        if st.button("🔬 Analyze Test", type="primary", use_container_width=True):
            with st.spinner("Calibrating lighting and analyzing test color..."):
                try:
                    result = analyze_image(st.session_state["capture_bytes"])
                    st.session_state["analysis"] = result

                    now = datetime.now()
                    test_id = "FT-" + uuid.uuid4().hex[:8].upper()

                    image_path = IMAGE_DIR / f"{test_id}.jpg"
                    image_path.write_bytes(st.session_state["capture_bytes"])

                    record = {
                        "test_id": test_id,
                        "operator_id": operator_id.strip() or "OP-001",
                        "kit_profile": kit_profile,
                        "timestamp": now.isoformat(timespec="seconds"),
                        "timestamp_display": now.strftime("%d %b %Y, %I:%M %p"),
                        "latitude": location["latitude"] if location else None,
                        "longitude": location["longitude"] if location else None,
                        "gps_accuracy": location.get("accuracy") if location else None,
                        "classification": result["classification"],
                        "confidence": result["confidence"],
                        "calibration": result["calibration"],
                        "reference_rgb": result["reference_rgb"],
                        "test_rgb_raw": result["test_rgb_raw"],
                        "test_rgb_calibrated": result["test_rgb_calibrated"],
                        "reason": result["reason"],
                        "image_path": str(image_path.relative_to(APP_DIR)),
                    }

                    history.insert(0, record)
                    save_history(history)
                    st.session_state["last_record"] = record

                except Exception as e:
                    st.error(f"Analysis failed: {e}")

    if "analysis" in st.session_state:
        result = st.session_state["analysis"]
        record = st.session_state.get("last_record")

        st.markdown("---")
        st.subheader("4. Presumptive result")

        css_class = {
            "POSITIVE": "positive",
            "NEGATIVE": "negative",
            "INCONCLUSIVE": "inconclusive",
        }.get(result["classification"], "inconclusive")

        st.markdown(
            f"""
            <div class="result-card">
              <div class="small">COLORIMETRIC CLASSIFICATION</div>
              <div class="result {css_class}">
                {result["classification"]}
              </div>
              <div>Confidence: <b>{result["confidence"]:.1f}%</b></div>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.progress(min(result["confidence"] / 100.0, 1.0))

        a, b = st.columns(2)
        with a:
            st.metric("Calibration", result["calibration"])
        with b:
            st.metric("Test color distance", f"{result['distance']:.1f}")

        with st.expander("CV analysis details"):
            st.write(result["reason"])
            st.write("Reference RGB:", result["reference_rgb"])
            st.write("Raw test RGB:", result["test_rgb_raw"])
            st.write("Calibrated test RGB:", result["test_rgb_calibrated"])

        if record:
            st.markdown("### 5. Digital report")

            st.write(
                f"**Test ID:** {record['test_id']}  \n"
                f"**Operator:** {record['operator_id']}  \n"
                f"**Time:** {record['timestamp_display']}"
            )

            if record["latitude"] is not None:
                st.write(
                    f"**GPS:** {record['latitude']:.6f}, "
                    f"{record['longitude']:.6f}"
                )

            if st.button(
                "📄 Generate PDF Report",
                use_container_width=True
            ):
                pdf_path = create_pdf_report(
                    record=record,
                    image_path=APP_DIR / record["image_path"]
                )
                st.session_state["pdf_path"] = str(pdf_path)
                st.success("PDF report created.")

            pdf_path = st.session_state.get("pdf_path")
            if pdf_path and Path(pdf_path).exists():
                pdf_bytes = Path(pdf_path).read_bytes()

                st.download_button(
                    "⬇️ Save PDF",
                    data=pdf_bytes,
                    file_name=f"{record['test_id']}_report.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )

                # Streamlit cannot force the phone's native share sheet by itself.
                # The downloaded PDF can be shared using the phone's file/share UI.
                st.info(
                    "On a phone: tap Save PDF, then open the downloaded PDF and "
                    "use Android/iOS Share to send it through WhatsApp, Gmail, Drive, etc."
                )

            if st.button("➕ Start New Test", use_container_width=True):
                reset_test()
                st.rerun()

    st.markdown(
        '<div class="disclaimer">⚠️ Presumptive field-test result only. '
        'This prototype does not replace laboratory confirmatory testing.</div>',
        unsafe_allow_html=True
    )

with tab_history:
    st.subheader("Test history")

    if not history:
        st.info("No tests have been saved yet.")
    else:
        query = st.text_input(
            "Search by test ID, operator, or result",
            placeholder="e.g. FT-1234 or OP-001 or POSITIVE"
        ).strip().lower()

        filtered = [
            r for r in history
            if not query
            or query in r["test_id"].lower()
            or query in r["operator_id"].lower()
            or query in r["classification"].lower()
        ]

        p, n, i = st.columns(3)
        with p:
            st.metric("Total", len(history))
        with n:
            st.metric("Positive", sum(r["classification"] == "POSITIVE" for r in history))
        with i:
            st.metric("Other", sum(r["classification"] != "POSITIVE" for r in history))

        for r in filtered:
            label = f"{r['classification']} · {r['test_id']}"
            with st.expander(label):
                st.write(f"**Operator:** {r['operator_id']}")
                st.write(f"**Time:** {r['timestamp_display']}")
                if r["latitude"] is not None:
                    st.write(
                        f"**GPS:** {r['latitude']:.6f}, "
                        f"{r['longitude']:.6f}"
                    )
                st.write(f"**Confidence:** {r['confidence']:.1f}%")

                img = APP_DIR / r["image_path"]
                if img.exists():
                    st.image(img, use_container_width=True)

                if st.button(
                    f"Generate PDF — {r['test_id']}",
                    key=f"pdf_{r['test_id']}",
                    use_container_width=True
                ):
                    pdf = create_pdf_report(r, img)
                    st.download_button(
                        "⬇️ Download report",
                        data=pdf.read_bytes(),
                        file_name=f"{r['test_id']}_report.pdf",
                        mime="application/pdf",
                        key=f"download_{r['test_id']}",
                        use_container_width=True
                    )

with tab_about:
    st.subheader("How the prototype works")

    st.markdown("""
**Step 1 — Image Capture**

The phone browser opens the device camera using Streamlit's camera input.
The reference card and dummy test strip are captured in the same image.

**Step 2 — Lighting Calibration**

The CV engine uses the reference-card patch to estimate scene brightness
and normalize the test-region color.

**Step 3 — Classification**

The calibrated RGB color is compared with the prototype's positive and
negative color profiles. A distance-based confidence is calculated.

**Step 4 — Record**

The app stores the result locally with operator ID, timestamp, GPS when
available, and the captured image.

**Step 5 — PDF**

A report is generated containing the captured image, result, confidence,
timestamp, operator ID and location.

**Step 6 — Sharing**

The PDF can be downloaded on the phone and shared using the phone's normal
share system.
""")

    st.info(
        "This Streamlit version is a prototype. The demo color profiles are "
        "not a validated narcotics-testing model."
    )
