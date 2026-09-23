import json
import uuid
from datetime import datetime
from pathlib import Path

import streamlit as st

from cv_engine import analyze_image
from pdf_report import create_pdf_report


# =========================================================
# OPTIONAL GPS
# =========================================================

try:
    from streamlit_js_eval import get_geolocation
except Exception:
    get_geolocation = None


# =========================================================
# PROJECT PATHS
# =========================================================

APP_DIR = Path(__file__).resolve().parent

DATA_DIR = APP_DIR / "data"
IMAGE_DIR = DATA_DIR / "images"
REPORT_DIR = DATA_DIR / "reports"
HISTORY_FILE = DATA_DIR / "history.json"

IMAGE_DIR.mkdir(parents=True, exist_ok=True)
REPORT_DIR.mkdir(parents=True, exist_ok=True)


# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="FieldTest Companion",
    page_icon="🧪",
    layout="centered",
    initial_sidebar_state="collapsed",
)


# =========================================================
# CUSTOM CSS
# =========================================================

st.markdown(
    """
    <style>

    /* =====================================================
       MAIN APP
       ===================================================== */

    .stApp {
        background-color: #07111f;
        color: #eef6ff;
    }

    .block-container {
        max-width: 760px;
        padding-top: 1rem;
        padding-bottom: 4rem;
        padding-left: 1rem;
        padding-right: 1rem;
    }


    /* =====================================================
       HEADINGS
       ===================================================== */

    h1 {
        color: #f4f8ff !important;
        font-size: 2.2rem !important;
        font-weight: 800 !important;
        letter-spacing: -0.5px;
    }

    h2 {
        color: #f4f8ff !important;
        font-size: 1.65rem !important;
        font-weight: 750 !important;
        margin-top: 1.5rem !important;
    }

    h3 {
        color: #f4f8ff !important;
        font-weight: 700 !important;
    }


    /* =====================================================
       NORMAL TEXT
       ===================================================== */

    .stMarkdown p {
        color: #c8d6e5;
    }

    .stCaption {
        color: #9fb2c5 !important;
    }


    /* =====================================================
       INPUT FIELDS
       ===================================================== */

    input,
    textarea {
        border-radius: 12px !important;
    }

    div[data-baseweb="select"] {
        border-radius: 12px !important;
    }


    /* =====================================================
       NORMAL BUTTONS
       ===================================================== */

    .stButton > button {
        min-height: 48px !important;
        border-radius: 14px !important;
        font-size: 1rem !important;
        font-weight: 700 !important;
        border: 1px solid #294b66 !important;
    }

    .stButton > button:hover {
        border-color: #6c9fc8 !important;
    }


    /* =====================================================
       CAMERA WIDGET CONTAINER
       ===================================================== */

    div[data-testid="stCameraInput"] {
        background: #081522 !important;
        border: 1px solid #294d68 !important;
        border-radius: 22px !important;
        padding: 8px !important;
        overflow: hidden !important;
        box-shadow: 0 12px 30px rgba(0, 0, 0, 0.30) !important;
    }


    /* Hide default camera label */

    div[data-testid="stCameraInput"] label {
        display: none !important;
    }


    /* =====================================================
       CAMERA PREVIEW
       ===================================================== */

    div[data-testid="stCameraInput"] video {
        width: 100% !important;
        max-width: 100% !important;
        border-radius: 16px !important;
        object-fit: cover !important;
    }


    /* =====================================================
       CAMERA CAPTURE BUTTON
       
       We intentionally DON'T style every button inside
       the camera widget.
       
       This prevents the camera-switch button from becoming
       a giant button.
       ===================================================== */

    div[data-testid="stCameraInput"]
    button[aria-label="Take a picture"] {

        width: 72px !important;
        height: 72px !important;

        min-width: 72px !important;
        min-height: 72px !important;

        border-radius: 50% !important;

        background: #ffffff !important;

        border: 5px solid #cbd5df !important;

        box-shadow:
            0 0 0 3px rgba(255,255,255,0.12),
            0 8px 22px rgba(0,0,0,0.45) !important;

        margin: 14px auto !important;

        padding: 0 !important;

        position: relative !important;

        color: transparent !important;
    }


    /* Camera icon */

    div[data-testid="stCameraInput"]
    button[aria-label="Take a picture"]::after {

        content: "📷";

        position: absolute !important;

        left: 50% !important;
        top: 50% !important;

        transform: translate(-50%, -50%) !important;

        font-size: 28px !important;

        line-height: 1 !important;
    }


    /* Capture hover */

    div[data-testid="stCameraInput"]
    button[aria-label="Take a picture"]:hover {

        background: #f7f9fb !important;

        border-color: #ffffff !important;
    }


    /* Capture press */

    div[data-testid="stCameraInput"]
    button[aria-label="Take a picture"]:active {

        transform: scale(0.94) !important;
    }


    /* =====================================================
       SWITCH CAMERA BUTTON
       ===================================================== */

    div[data-testid="stCameraInput"]
    button[aria-label="Switch camera"] {

        width: 46px !important;
        height: 46px !important;

        min-width: 46px !important;
        min-height: 46px !important;

        border-radius: 50% !important;

        background: rgba(8, 17, 29, 0.82) !important;

        border: 1px solid rgba(255,255,255,0.35) !important;

        color: white !important;

        margin: 8px !important;

        padding: 0 !important;

        box-shadow:
            0 5px 15px rgba(0,0,0,0.40) !important;
    }


    div[data-testid="stCameraInput"]
    button[aria-label="Switch camera"]:hover {

        background: rgba(24, 42, 60, 0.95) !important;

        border-color: rgba(255,255,255,0.70) !important;
    }


    /* =====================================================
       ALERTS / INFO
       ===================================================== */

    div[data-testid="stAlert"] {
        border-radius: 14px !important;
    }


    /* =====================================================
       METRIC CARDS
       ===================================================== */

    div[data-testid="stMetric"] {
        background: #0c1b2a;
        border: 1px solid #294b66;
        border-radius: 16px;
        padding: 15px;
    }


    /* =====================================================
       MOBILE
       ===================================================== */

    @media (max-width: 600px) {

        .block-container {
            padding-left: 0.7rem;
            padding-right: 0.7rem;
            padding-top: 0.7rem;
        }

        h1 {
            font-size: 1.85rem !important;
        }

        h2 {
            font-size: 1.45rem !important;
        }

        div[data-testid="stCameraInput"] {
            border-radius: 18px !important;
            padding: 6px !important;
        }

        div[data-testid="stCameraInput"]
        button[aria-label="Take a picture"] {

            width: 68px !important;
            height: 68px !important;

            min-width: 68px !important;
            min-height: 68px !important;
        }

        div[data-testid="stCameraInput"]
        button[aria-label="Switch camera"] {

            width: 44px !important;
            height: 44px !important;

            min-width: 44px !important;
            min-height: 44px !important;
        }
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# LOAD HISTORY
# =========================================================

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


# =========================================================
# SAVE HISTORY
# =========================================================

def save_history(history):

    HISTORY_FILE.write_text(
        json.dumps(
            history,
            indent=2,
            ensure_ascii=False
        ),
        encoding="utf-8"
    )


# =========================================================
# GET GPS
# =========================================================

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


# =========================================================
# RESET TEST
# =========================================================

def reset_test():

    keys = [
        "capture_bytes",
        "analysis",
        "last_record",
        "pdf_path",
    ]

    for key in keys:

        st.session_state.pop(
            key,
            None
        )


# =========================================================
# INITIAL DATA
# =========================================================

history = load_history()


# =========================================================
# HEADER
# =========================================================

st.title("🧪 FieldTest Companion")

st.caption(
    "Capture → Calibrate → Classify → Generate Report"
)

st.divider()


# =========================================================
# TABS
# =========================================================

tab_new, tab_history, tab_about = st.tabs(
    [
        "📷 New Test",
        "🗂 History",
        "ℹ️ About",
    ]
)


# =========================================================
# NEW TEST
# =========================================================

with tab_new:

    # =====================================================
    # STEP 1
    # =====================================================

    st.header("1. Test information")

    col1, col2 = st.columns(
        2,
        gap="medium"
    )

    with col1:

        operator_id = st.text_input(
            "Operator ID",
            value="OP-001",
            key="operator_id"
        )

    with col2:

        kit_profile = st.selectbox(
            "Test kit",
            [
                "Demo Colorimetric Kit"
            ],
            key="kit_profile"
        )


    # =====================================================
    # STEP 2
    # =====================================================

    st.header("2. Capture the test")

    st.info(
        "📋 Position the reference colour card on the "
        "LEFT and the test strip on the RIGHT. "
        "Keep both completely visible and avoid glare."
    )

    st.caption(
        "📷 Use the camera below to capture both "
        "the reference card and test strip."
    )


    # =====================================================
    # CAMERA
    #
    # IMPORTANT:
    # No 'resolution' argument.
    # =====================================================

    photo = st.camera_input(
        "Field test camera",
        key="field_camera",
        label_visibility="collapsed",
    )


    # =====================================================
    # GPS
    # =====================================================

    location = get_location()

    if location:

        st.success(
            "📍 GPS location captured"
        )

    else:

        st.caption(
            "📍 GPS location is unavailable. "
            "Allow browser location permission "
            "if GPS recording is required."
        )


    # =====================================================
    # IMAGE CAPTURED
    # =====================================================

    if photo:

        image_bytes = photo.getvalue()

        st.session_state[
            "capture_bytes"
        ] = image_bytes


        st.image(
            image_bytes,
            caption="Captured field-test image",
            use_container_width=True
        )


        # =================================================
        # STEP 3
        # =================================================

        st.header(
            "3. Computer vision analysis"
        )

        st.caption(
            "The captured image is processed using "
            "the colour calibration and classification engine."
        )


        analyze_clicked = st.button(
            "🔬 Analyze Test",
            type="primary",
            use_container_width=True,
            key="analyze_test",
        )


        # =================================================
        # ANALYSIS
        # =================================================

        if analyze_clicked:

            with st.spinner(
                "Analyzing image and calibrating colour..."
            ):

                try:

                    result = analyze_image(
                        image_bytes
                    )

                    st.session_state[
                        "analysis"
                    ] = result


                    # -------------------------------------
                    # TEST ID
                    # -------------------------------------

                    now = datetime.now()

                    test_id = (
                        "FT-"
                        + uuid.uuid4()
                        .hex[:8]
                        .upper()
                    )


                    # -------------------------------------
                    # SAVE IMAGE
                    # -------------------------------------

                    image_path = (
                        IMAGE_DIR
                        / f"{test_id}.jpg"
                    )

                    image_path.write_bytes(
                        image_bytes
                    )


                    # -------------------------------------
                    # CREATE RECORD
                    # -------------------------------------

                    record = {

                        "test_id":
                            test_id,

                        "operator_id":
                            (
                                operator_id.strip()
                                or "OP-001"
                            ),

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


                    # -------------------------------------
                    # SAVE RECORD
                    # -------------------------------------

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


    # =====================================================
    # RESULT
    # =====================================================

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


        # =================================================
        # CLASSIFICATION
        # =================================================

        classification = (
            result["classification"]
        )


        if classification == "POSITIVE":

            st.error(
                "🔴 POSITIVE"
            )

        elif classification == "NEGATIVE":

            st.success(
                "🟢 NEGATIVE"
            )

        else:

            st.warning(
                "🟡 INCONCLUSIVE"
            )


        # =================================================
        # CONFIDENCE
        # =================================================

        confidence = float(
            result["confidence"]
        )

        st.metric(
            "Confidence",
            f"{confidence:.1f}%"
        )

        st.progress(
            max(
                0.0,
                min(
                    confidence / 100.0,
                    1.0
                )
            )
        )


        # =================================================
        # CV METRICS
        # =================================================

        col1, col2 = st.columns(2)

        with col1:

            st.metric(
                "Calibration",
                str(
                    result[
                        "calibration"
                    ]
                )
            )

        with col2:

            st.metric(
                "Colour distance",
                f'{float(result["distance"]):.1f}'
            )


        # =================================================
        # CV DETAILS
        # =================================================

        with st.expander(
            "🔬 View CV analysis details"
        ):

            st.write(
                result["reason"]
            )

            st.write(
                "Reference RGB:",
                result[
                    "reference_rgb"
                ]
            )

            st.write(
                "Raw test RGB:",
                result[
                    "test_rgb_raw"
                ]
            )

            st.write(
                "Calibrated test RGB:",
                result[
                    "test_rgb_calibrated"
                ]
            )


        # =================================================
        # DIGITAL RECORD
        # =================================================

        if record:

            st.header(
                "5. Digital record"
            )


            col1, col2 = st.columns(2)

            with col1:

                st.write(
                    "**Test ID**"
                )

                st.code(
                    record[
                        "test_id"
                    ],
                    language=None
                )


            with col2:

                st.write(
                    "**Operator**"
                )

                st.code(
                    record[
                        "operator_id"
                    ],
                    language=None
                )


            st.write(
                f'**Time:** '
                f'{record["timestamp_display"]}'
            )


            # =================================================
            # GPS
            # =================================================

            if record[
                "latitude"
            ] is not None:

                st.write(
                    f'**GPS:** '
                    f'{record["latitude"]:.6f}, '
                    f'{record["longitude"]:.6f}'
                )

                if record[
                    "gps_accuracy"
                ] is not None:

                    st.caption(
                        "GPS accuracy: "
                        f'{float(record["gps_accuracy"]):.1f} m'
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


            generate_pdf = st.button(
                "📄 Generate PDF Report",
                use_container_width=True,
                key="generate_current_pdf",
            )


            if generate_pdf:

                try:

                    pdf_path = (
                        create_pdf_report(
                            record=record,
                            image_path=(
                                APP_DIR
                                / record[
                                    "image_path"
                                ]
                            )
                        )
                    )


                    st.session_state[
                        "pdf_path"
                    ] = str(
                        pdf_path
                    )


                    st.success(
                        "PDF report generated successfully."
                    )


                except Exception as e:

                    st.error(
                        f"PDF generation failed: {e}"
                    )


            # =================================================
            # DOWNLOAD PDF
            # =================================================

            pdf_path = (
                st.session_state.get(
                    "pdf_path"
                )
            )


            if (
                pdf_path
                and Path(
                    pdf_path
                ).exists()
            ):

                pdf_bytes = (
                    Path(
                        pdf_path
                    ).read_bytes()
                )


                st.download_button(
                    label="⬇️ Save PDF",
                    data=pdf_bytes,
                    file_name=(
                        f'{record["test_id"]}'
                        "_report.pdf"
                    ),
                    mime="application/pdf",
                    use_container_width=True,
                    key="save_current_pdf",
                )


                st.info(
                    "📤 After saving the PDF, "
                    "use your phone's Share option "
                    "to send it through WhatsApp, "
                    "Gmail, Drive, or another app."
                )


            # =================================================
            # NEW TEST
            # =================================================

            if st.button(
                "➕ Start New Test",
                use_container_width=True,
                key="new_test",
            ):

                reset_test()

                st.rerun()


    # =====================================================
    # DISCLAIMER
    # =====================================================

    st.warning(
        "⚠️ Presumptive field-test result only. "
        "This prototype does not replace laboratory "
        "confirmatory testing."
    )


# =========================================================
# HISTORY TAB
# =========================================================

with tab_history:

    st.header(
        "🗂 Test history"
    )


    if not history:

        st.info(
            "No tests have been recorded yet."
        )


    else:

        search = st.text_input(
            "Search tests",
            placeholder=(
                "Test ID, operator or result"
            ),
            key="history_search",
        ).strip().lower()


        filtered = []


        for record in history:

            if not search:

                filtered.append(
                    record
                )

            else:

                if (
                    search
                    in record[
                        "test_id"
                    ].lower()
                    or
                    search
                    in record[
                        "operator_id"
                    ].lower()
                    or
                    search
                    in record[
                        "classification"
                    ].lower()
                ):

                    filtered.append(
                        record
                    )


        # =================================================
        # STATISTICS
        # =================================================

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


        # =================================================
        # HISTORY RECORDS
        # =================================================

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
                    f'{float(record["confidence"]):.1f}%'
                )


                if record[
                    "latitude"
                ] is not None:

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


                if st.button(
                    "📄 Generate PDF",
                    key=(
                        "history_pdf_"
                        + record[
                            "test_id"
                        ]
                    ),
                    use_container_width=True,
                ):

                    try:

                        pdf = (
                            create_pdf_report(
                                record,
                                image_file
                            )
                        )


                        st.download_button(
                            "⬇️ Download PDF",
                            data=(
                                pdf.read_bytes()
                            ),
                            file_name=(
                                f'{record["test_id"]}'
                                "_report.pdf"
                            ),
                            mime="application/pdf",
                            key=(
                                "download_pdf_"
                                + record[
                                    "test_id"
                                ]
                            ),
                            use_container_width=True,
                        )


                    except Exception as e:

                        st.error(
                            f"PDF generation failed: {e}"
                        )


# =========================================================
# ABOUT TAB
# =========================================================

with tab_about:

    st.header(
        "ℹ️ About FieldTest Companion"
    )


    # -----------------------------------------------------
    # IMAGE CAPTURE
    # -----------------------------------------------------

    st.subheader(
        "📷 Image Capture"
    )

    st.write(
        "The application captures the existing "
        "colorimetric field-test strip together "
        "with a reference colour card."
    )


    # -----------------------------------------------------
    # CALIBRATION
    # -----------------------------------------------------

    st.subheader(
        "🎨 Lighting Calibration"
    )

    st.write(
        "The reference card is used to compensate "
        "for differences in scene brightness."
    )


    # -----------------------------------------------------
    # COMPUTER VISION
    # -----------------------------------------------------

    st.subheader(
        "🔬 Computer Vision"
    )

    st.write(
        "The captured image is analyzed and "
        "classified into:"
    )

    st.markdown(
        """
        - 🔴 POSITIVE
        - 🟢 NEGATIVE
        - 🟡 INCONCLUSIVE
        """
    )


    # -----------------------------------------------------
    # DIGITAL INFORMATION
    # -----------------------------------------------------

    st.subheader(
        "📍 Digital Information"
    )

    st.markdown(
        """
        - Operator ID
        - Timestamp
        - GPS location
        - Test ID
        - Classification
        - Confidence
        - Captured image
        """
    )


    # -----------------------------------------------------
    # PDF
    # -----------------------------------------------------

    st.subheader(
        "📄 PDF Report"
    )

    st.write(
        "A digital PDF report containing the "
        "test information, image and result "
        "can be generated."
    )


    # -----------------------------------------------------
    # LIMITATION
    # -----------------------------------------------------

    st.subheader(
        "⚠️ Prototype limitation"
    )

    st.warning(
        "The current colour profiles are "
        "demonstration profiles only. They are "
        "not validated narcotics-testing thresholds."
    )

    st.write(
        "The application produces a presumptive "
        "field-test result and does not replace "
        "laboratory confirmatory testing."
    )