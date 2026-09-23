import json
import uuid
from datetime import datetime
from pathlib import Path

import streamlit as st

from cv_engine import analyze_image
from pdf_report import create_pdf_report

# New GPS method
try:
    from streamlit_js_eval import get_geolocation
except Exception:
    get_geolocation = None


# ============================================================
# PATHS
# ============================================================

APP_DIR = Path(__file__).resolve().parent

DATA_DIR = APP_DIR / "data"
IMAGE_DIR = DATA_DIR / "images"
HISTORY_FILE = DATA_DIR / "history.json"

IMAGE_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="FieldTest Companion",
    page_icon="🧪",
    layout="centered",
    initial_sidebar_state="collapsed",
)


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
    <style>

    /* ======================================================
       MAIN APP
       ====================================================== */

    .stApp {
        background-color: #07111f;
        color: #eef6ff;
    }

    .block-container {
        max-width: 760px;
        padding-top: 1rem;
        padding-bottom: 3rem;
    }


    /* ======================================================
       HEADINGS
       ====================================================== */

    h1 {
        color: #eef6ff !important;
        font-weight: 800 !important;
    }

    h2, h3 {
        color: #eef6ff !important;
    }


    /* ======================================================
       CAMERA AREA
       ====================================================== */

    div[data-testid="stCameraInput"] {
        background: #050d17 !important;
        border: 1px solid #24435d !important;
        border-radius: 22px !important;
        padding: 8px !important;
        overflow: hidden !important;
    }


    /* Hide camera label */

    div[data-testid="stCameraInput"] label {
        display: none !important;
    }


    /* ======================================================
       CAMERA BUTTON
       ====================================================== */

    div[data-testid="stCameraInput"] button {
        width: 76px !important;
        height: 76px !important;

        min-width: 76px !important;
        min-height: 76px !important;

        border-radius: 50% !important;

        background: #ffffff !important;

        border: 6px solid #c8d0d8 !important;

        box-shadow:
            0 0 0 3px rgba(255,255,255,0.15),
            0 8px 25px rgba(0,0,0,0.5) !important;

        padding: 0 !important;

        font-size: 0 !important;

        margin: 14px auto !important;

        display: flex !important;

        align-items: center !important;

        justify-content: center !important;
    }


    /* Camera icon */

    div[data-testid="stCameraInput"] button::after {
        content: "📷";

        font-size: 30px !important;

        line-height: 1 !important;

        position: absolute;

        left: 50%;
        top: 50%;

        transform: translate(-50%, -50%);
    }


    /* Button hover */

    div[data-testid="stCameraInput"] button:hover {
        background: #f5f7f9 !important;
        border-color: #ffffff !important;
    }


    /* Button press */

    div[data-testid="stCameraInput"] button:active {
        transform: scale(0.92);
    }


    /* ======================================================
       INPUTS
       ====================================================== */

    input {
        border-radius: 12px !important;
    }


    /* ======================================================
       BUTTONS
       ====================================================== */

    .stButton > button {
        border-radius: 12px !important;
        min-height: 46px !important;
        font-weight: 600 !important;
    }


    /* ======================================================
       RESULT CARD
       ====================================================== */

    .result-box {
        background-color: #0d1b2a;
        border: 1px solid #294963;
        border-radius: 20px;
        padding: 25px;
        text-align: center;
        margin-top: 10px;
        margin-bottom: 15px;
    }


    /* ======================================================
       DISCLAIMER
       ====================================================== */

    .warning-box {
        background-color: #241d0b;
        border: 1px solid #67511c;
        border-radius: 14px;
        padding: 15px;
        color: #eadca8;
        margin-top: 20px;
    }


    /* ======================================================
       MOBILE
       ====================================================== */

    @media (max-width: 600px) {

        .block-container {
            padding-left: 0.7rem;
            padding-right: 0.7rem;
        }

        div[data-testid="stCameraInput"] {
            border-radius: 18px !important;
        }

    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# STORAGE
# ============================================================

def load_history():

    if not HISTORY_FILE.exists():
        return []

    try:

        return json.loads(
            HISTORY_FILE.read_text(
                encoding="utf-8"
            )
        )

    except Exception:

        return []


def save_history(history):

    HISTORY_FILE.write_text(
        json.dumps(
            history,
            indent=2,
            ensure_ascii=False
        ),
        encoding="utf-8"
    )


# ============================================================
# GPS
# ============================================================

def get_location():

    if get_geolocation is None:
        return None

    try:

        location = get_geolocation()

        if not location:
            return None

        if "error" in location:
            return None

        coords = location.get("coords")

        if not coords:
            return None

        latitude = coords.get("latitude")
        longitude = coords.get("longitude")

        if latitude is None or longitude is None:
            return None

        return {
            "latitude": float(latitude),
            "longitude": float(longitude),
            "accuracy": coords.get("accuracy"),
        }

    except Exception:

        return None


# ============================================================
# RESET
# ============================================================

def reset_test():

    keys = [
        "capture_bytes",
        "analysis",
        "last_record",
        "pdf_path",
    ]

    for key in keys:

        if key in st.session_state:
            del st.session_state[key]


# ============================================================
# LOAD HISTORY
# ============================================================

history = load_history()


# ============================================================
# HEADER
# ============================================================

st.title("🧪 FieldTest Companion")

st.caption(
    "Capture → Calibrate → Classify → Generate Report"
)

st.divider()


# ============================================================
# TABS
# ============================================================

tab_new, tab_history, tab_about = st.tabs(
    [
        "📷 New Test",
        "🗂 History",
        "ℹ️ About"
    ]
)


# ============================================================
# NEW TEST
# ============================================================

with tab_new:

    # --------------------------------------------------------
    # TEST INFORMATION
    # --------------------------------------------------------

    st.header("1. Test information")

    col1, col2 = st.columns(2)

    with col1:

        operator_id = st.text_input(
            "Operator ID",
            value="OP-001"
        )

    with col2:

        kit_profile = st.selectbox(
            "Test kit",
            [
                "Demo Colorimetric Kit"
            ]
        )


    # --------------------------------------------------------
    # CAMERA
    # --------------------------------------------------------

    st.header("2. Capture the test")

    st.info(
        "📋 Place the reference colour card on the "
        "LEFT and the test strip on the RIGHT. "
        "Keep both completely visible and avoid glare."
    )

    st.caption(
        "📷 Tap the camera button below to capture the test."
    )


    # ========================================================
    # CAMERA INPUT
    # ========================================================

    photo = st.camera_input(
        "Camera",
        key="field_camera"
    )


    # ========================================================
    # GPS
    # ========================================================

    location = get_location()


    # Only show a small status if GPS was successfully obtained.

    if location:

        st.caption(
            "📍 GPS location captured"
        )


    # ========================================================
    # AFTER PHOTO
    # ========================================================

    if photo:

        st.session_state[
            "capture_bytes"
        ] = photo.getvalue()


        st.image(
            st.session_state[
                "capture_bytes"
            ],
            caption="Captured field-test image",
            use_container_width=True
        )


        # ----------------------------------------------------
        # ANALYZE
        # ----------------------------------------------------

        st.header(
            "3. Computer vision analysis"
        )


        analyze_clicked = st.button(
            "🔬 Analyze Test",
            type="primary",
            use_container_width=True
        )


        if analyze_clicked:

            with st.spinner(
                "Analyzing image and calibrating colour..."
            ):

                try:

                    # ----------------------------------------
                    # RUN CV
                    # ----------------------------------------

                    result = analyze_image(
                        st.session_state[
                            "capture_bytes"
                        ]
                    )


                    st.session_state[
                        "analysis"
                    ] = result


                    # ----------------------------------------
                    # TEST ID
                    # ----------------------------------------

                    now = datetime.now()

                    test_id = (
                        "FT-"
                        + uuid.uuid4()
                        .hex[:8]
                        .upper()
                    )


                    # ----------------------------------------
                    # SAVE IMAGE
                    # ----------------------------------------

                    image_path = (
                        IMAGE_DIR
                        / f"{test_id}.jpg"
                    )


                    image_path.write_bytes(
                        st.session_state[
                            "capture_bytes"
                        ]
                    )


                    # ----------------------------------------
                    # RECORD
                    # ----------------------------------------

                    record = {

                        "test_id":
                            test_id,

                        "operator_id":
                            operator_id.strip()
                            or "OP-001",

                        "kit_profile":
                            kit_profile,

                        "timestamp":
                            now.isoformat(
                                timespec="seconds"
                            ),

                        "timestamp_display":
                            now.strftime(
                                "%d %b %Y, %I:%M %p"
                            ),

                        "latitude":
                            (
                                location["latitude"]
                                if location
                                else None
                            ),

                        "longitude":
                            (
                                location["longitude"]
                                if location
                                else None
                            ),

                        "gps_accuracy":
                            (
                                location.get(
                                    "accuracy"
                                )
                                if location
                                else None
                            ),

                        "classification":
                            result[
                                "classification"
                            ],

                        "confidence":
                            result[
                                "confidence"
                            ],

                        "calibration":
                            result[
                                "calibration"
                            ],

                        "reference_rgb":
                            result[
                                "reference_rgb"
                            ],

                        "test_rgb_raw":
                            result[
                                "test_rgb_raw"
                            ],

                        "test_rgb_calibrated":
                            result[
                                "test_rgb_calibrated"
                            ],

                        "reason":
                            result[
                                "reason"
                            ],

                        "image_path":
                            str(
                                image_path.relative_to(
                                    APP_DIR
                                )
                            ),
                    }


                    # ----------------------------------------
                    # SAVE
                    # ----------------------------------------

                    history.insert(
                        0,
                        record
                    )

                    save_history(
                        history
                    )


                    st.session_state[
                        "last_record"
                    ] = record


                    st.success(
                        "Image analyzed successfully."
                    )


                except Exception as e:

                    st.error(
                        f"Analysis failed: {e}"
                    )


    # ========================================================
    # RESULT
    # ========================================================

    if "analysis" in st.session_state:

        result = st.session_state[
            "analysis"
        ]

        record = st.session_state.get(
            "last_record"
        )


        st.divider()

        st.header(
            "4. Presumptive result"
        )


        classification = result[
            "classification"
        ]


        # ----------------------------------------------------
        # RESULT
        # ----------------------------------------------------

        if classification == "POSITIVE":

            st.error(
                f"🔴 {classification}"
            )

        elif classification == "NEGATIVE":

            st.success(
                f"🟢 {classification}"
            )

        else:

            st.warning(
                f"🟡 {classification}"
            )


        # ----------------------------------------------------
        # CONFIDENCE
        # ----------------------------------------------------

        st.metric(
            "Confidence",
            f'{result["confidence"]:.1f}%'
        )


        st.progress(
            min(
                result["confidence"] / 100,
                1.0
            )
        )


        # ----------------------------------------------------
        # ANALYSIS METRICS
        # ----------------------------------------------------

        col1, col2 = st.columns(2)

        with col1:

            st.metric(
                "Calibration",
                result["calibration"]
            )

        with col2:

            st.metric(
                "Colour distance",
                f'{result["distance"]:.1f}'
            )


        # ----------------------------------------------------
        # DETAILS
        # ----------------------------------------------------

        with st.expander(
            "🔬 View CV analysis details"
        ):

            st.write(
                result["reason"]
            )

            st.write(
                "Reference RGB:",
                result["reference_rgb"]
            )

            st.write(
                "Raw test RGB:",
                result["test_rgb_raw"]
            )

            st.write(
                "Calibrated test RGB:",
                result[
                    "test_rgb_calibrated"
                ]
            )


        # ====================================================
        # DIGITAL RECORD
        # ====================================================

        if record:

            st.header(
                "5. Digital record"
            )


            st.write(
                f'**Test ID:** {record["test_id"]}'
            )

            st.write(
                f'**Operator:** {record["operator_id"]}'
            )

            st.write(
                f'**Time:** {record["timestamp_display"]}'
            )


            if (
                record["latitude"]
                is not None
            ):

                st.write(
                    f'**GPS:** '
                    f'{record["latitude"]:.6f}, '
                    f'{record["longitude"]:.6f}'
                )

            else:

                st.caption(
                    "📍 GPS location was not available."
                )


            # =================================================
            # PDF
            # =================================================

            st.header(
                "6. PDF report"
            )


            if st.button(
                "📄 Generate PDF Report",
                use_container_width=True
            ):

                try:

                    pdf_path = create_pdf_report(

                        record=record,

                        image_path=(
                            APP_DIR
                            / record[
                                "image_path"
                            ]
                        )
                    )


                    st.session_state[
                        "pdf_path"
                    ] = str(pdf_path)


                    st.success(
                        "PDF report generated successfully."
                    )


                except Exception as e:

                    st.error(
                        f"PDF generation failed: {e}"
                    )


            # -------------------------------------------------
            # DOWNLOAD
            # -------------------------------------------------

            pdf_path = st.session_state.get(
                "pdf_path"
            )


            if (
                pdf_path
                and Path(pdf_path).exists()
            ):

                pdf_bytes = Path(
                    pdf_path
                ).read_bytes()


                st.download_button(

                    label="⬇️ Save PDF",

                    data=pdf_bytes,

                    file_name=(
                        f'{record["test_id"]}'
                        '_report.pdf'
                    ),

                    mime="application/pdf",

                    use_container_width=True
                )


                st.info(
                    "📤 After saving the PDF on your phone, "
                    "open it and use the phone's Share option "
                    "to send it through WhatsApp, Gmail, Drive, etc."
                )


            # -------------------------------------------------
            # NEW TEST
            # -------------------------------------------------

            if st.button(
                "➕ Start New Test",
                use_container_width=True
            ):

                reset_test()

                st.rerun()


    # ========================================================
    # DISCLAIMER
    # ========================================================

    st.warning(
        "⚠️ Presumptive field-test result only. "
        "This prototype does not replace laboratory "
        "confirmatory testing."
    )


# ============================================================
# HISTORY
# ============================================================

with tab_history:

    st.header(
        "🗂 Test history"
    )


    if not history:

        st.info(
            "No tests have been recorded yet."
        )

    else:

        # ----------------------------------------------------
        # SEARCH
        # ----------------------------------------------------

        search = st.text_input(
            "Search tests",
            placeholder=(
                "Test ID, operator or result"
            )
        ).strip().lower()


        filtered = []

        for record in history:

            if not search:

                filtered.append(
                    record
                )

                continue


            if (
                search
                in record[
                    "test_id"
                ].lower()

                or search
                in record[
                    "operator_id"
                ].lower()

                or search
                in record[
                    "classification"
                ].lower()
            ):

                filtered.append(
                    record
                )


        # ----------------------------------------------------
        # METRICS
        # ----------------------------------------------------

        c1, c2, c3 = st.columns(3)

        with c1:

            st.metric(
                "Total",
                len(history)
            )

        with c2:

            st.metric(
                "Positive",
                sum(
                    r[
                        "classification"
                    ] == "POSITIVE"

                    for r in history
                )
            )

        with c3:

            st.metric(
                "Other",
                sum(
                    r[
                        "classification"
                    ] != "POSITIVE"

                    for r in history
                )
            )


        # ----------------------------------------------------
        # RECORDS
        # ----------------------------------------------------

        for record in filtered:

            title = (
                f'{record["classification"]}'
                f' — '
                f'{record["test_id"]}'
            )


            with st.expander(
                title
            ):

                st.write(
                    f'**Operator:** '
                    f'{record["operator_id"]}'
                )

                st.write(
                    f'**Time:** '
                    f'{record["timestamp_display"]}'
                )

                st.write(
                    f'**Confidence:** '
                    f'{record["confidence"]:.1f}%'
                )


                if (
                    record["latitude"]
                    is not None
                ):

                    st.write(
                        f'**GPS:** '
                        f'{record["latitude"]:.6f}, '
                        f'{record["longitude"]:.6f}'
                    )


                image_file = (
                    APP_DIR
                    / record[
                        "image_path"
                    ]
                )


                if image_file.exists():

                    st.image(
                        image_file,
                        use_container_width=True
                    )


                # ------------------------------------------------
                # GENERATE HISTORY PDF
                # ------------------------------------------------

                if st.button(

                    "📄 Generate PDF",

                    key=(
                        "generate_"
                        + record[
                            "test_id"
                        ]
                    ),

                    use_container_width=True

                ):

                    try:

                        pdf = create_pdf_report(

                            record,

                            image_file
                        )


                        st.download_button(

                            "⬇️ Download PDF",

                            data=pdf.read_bytes(),

                            file_name=(
                                f'{record["test_id"]}'
                                '_report.pdf'
                            ),

                            mime="application/pdf",

                            key=(
                                "download_"
                                + record[
                                    "test_id"
                                ]
                            ),

                            use_container_width=True
                        )


                    except Exception as e:

                        st.error(
                            f"PDF generation failed: {e}"
                        )


# ============================================================
# ABOUT
# ============================================================

with tab_about:

    st.header(
        "ℹ️ About FieldTest Companion"
    )


    st.markdown(
        """
### 📷 Image Capture

The application captures the existing
colorimetric field-test strip together
with a reference colour card.

### 🎨 Lighting Calibration

The reference card is used to compensate
for differences in scene brightness.

### 🔬 Computer Vision

The captured test region is analyzed and
classified into:

- POSITIVE
- NEGATIVE
- INCONCLUSIVE

### 📍 Digital Information

The prototype records:

- Operator ID
- Timestamp
- GPS location
- Test ID
- Classification
- Confidence
- Captured image

### 📄 PDF Report

A report containing the test image and
result information can be generated and
saved.

### 📤 Sharing

The saved PDF can be shared using the
phone's normal sharing system.

---

### ⚠️ Prototype limitation

The current colour profiles are
**demonstration profiles only**.

They are not validated narcotics-testing
thresholds.

The application produces a
**presumptive field-test result** and
does not replace laboratory confirmatory
testing.
"""
    )