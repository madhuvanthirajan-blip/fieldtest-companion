import json
import uuid
from datetime import datetime
from pathlib import Path

import streamlit as st

from cv_engine import analyze_image
from pdf_report import create_pdf_report

try:
    from streamlit_geolocation import streamlit_geolocation
except Exception:
    streamlit_geolocation = None


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

/* ==========================================================
   MAIN APP
   ========================================================== */

.stApp {
    background: #07111f;
    color: #eef6ff;
}

.block-container {
    max-width: 760px;
    padding: 1rem 1rem 3rem;
}


/* ==========================================================
   HERO
   ========================================================== */

.hero {
    padding: 22px;
    border-radius: 24px;
    background: linear-gradient(
        145deg,
        #10243a,
        #091827
    );
    border: 1px solid #1f405d;
    margin-bottom: 14px;
}

.hero h1 {
    margin: 0;
    font-size: 2rem;
}

.hero p {
    color: #a9c0d6;
    margin-bottom: 0;
}


/* ==========================================================
   RESULT CARD
   ========================================================== */

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

.positive {
    color: #ff5d8f;
}

.negative {
    color: #b7e34b;
}

.inconclusive {
    color: #ffc857;
}

.small {
    color: #91a9bf;
    font-size: 0.88rem;
}

.pill {
    display: inline-block;
    padding: 6px 12px;
    border-radius: 999px;
    background: #132d43;
    color: #9edbff;
    font-size: 0.82rem;
    margin-right: 5px;
}


/* ==========================================================
   METRICS
   ========================================================== */

div[data-testid="stMetric"] {
    background: #0d1b2a;
    border: 1px solid #203d56;
    padding: 12px;
    border-radius: 16px;
}


/* ==========================================================
   CAMERA CONTAINER
   ========================================================== */

div[data-testid="stCameraInput"] {
    background: #050d17;
    border-radius: 22px;
    padding: 8px;
    border: 1px solid #1d3a52;
    overflow: hidden;
}


/* ==========================================================
   HIDE CAMERA LABEL
   ========================================================== */

div[data-testid="stCameraInput"] label {
    color: transparent !important;
    height: 0 !important;
    min-height: 0 !important;
    margin: 0 !important;
    padding: 0 !important;
    overflow: hidden !important;
}


/* ==========================================================
   CAMERA BUTTON
   ========================================================== */

/*
   Streamlit normally displays:

   Take Photo

   We turn it into a circular camera/shutter button.
*/

div[data-testid="stCameraInput"] button {
    width: 72px !important;
    height: 72px !important;

    min-width: 72px !important;
    min-height: 72px !important;

    border-radius: 50% !important;

    background: #ffffff !important;

    border: 6px solid #c9d1d9 !important;

    box-shadow:
        0 0 0 3px rgba(255,255,255,0.18),
        0 8px 25px rgba(0,0,0,0.45) !important;

    padding: 0 !important;

    font-size: 0 !important;

    position: relative;

    margin: 12px auto !important;

    display: flex !important;

    align-items: center !important;

    justify-content: center !important;
}


/* ==========================================================
   CAMERA ICON
   ========================================================== */

div[data-testid="stCameraInput"] button::after {
    content: "📷";

    font-size: 28px !important;

    line-height: 1 !important;

    position: absolute;

    left: 50%;
    top: 50%;

    transform: translate(-50%, -50%);
}


/* ==========================================================
   CAMERA BUTTON HOVER
   ========================================================== */

div[data-testid="stCameraInput"] button:hover {
    background: #f3f6f8 !important;
    border-color: #ffffff !important;
}


/* ==========================================================
   CAMERA BUTTON PRESS
   ========================================================== */

div[data-testid="stCameraInput"] button:active {
    transform: scale(0.92);
}


/* ==========================================================
   GEOLOCATION COMPONENT
   ========================================================== */

/*
   streamlit-geolocation creates a white box with a
   location/crosshair button.

   We don't want that visible in the UI.

   The component is therefore made visually invisible,
   while the Python call still requests the location.
*/

div[data-testid="stCustomComponentV1"] {
    background: transparent !important;

    border: none !important;

    padding: 0 !important;

    margin: 0 !important;

    min-height: 0 !important;
}


/* Hide geolocation iframe */

div[data-testid="stCustomComponentV1"] iframe {
    height: 1px !important;

    min-height: 1px !important;

    opacity: 0 !important;

    pointer-events: none !important;
}


/* ==========================================================
   LOCATION SUCCESS
   ========================================================== */

.location-success {
    text-align: center;

    color: #75d99a;

    font-size: 0.82rem;

    margin: 6px 0 10px;
}


/* ==========================================================
   INSTRUCTION CARD
   ========================================================== */

.instruction-card {
    background: #0d1b2a;

    border: 1px solid #203d56;

    border-radius: 16px;

    padding: 12px 15px;

    margin-bottom: 12px;
}

.instruction-title {
    font-weight: 700;

    color: #eef6ff;
}

.instruction-text {
    color: #91a9bf;

    font-size: 0.86rem;

    line-height: 1.5;
}


/* ==========================================================
   DISCLAIMER
   ========================================================== */

.disclaimer {
    background: #241d0b;

    border: 1px solid #67511c;

    border-radius: 14px;

    padding: 12px 14px;

    color: #eadca8;

    font-size: 0.84rem;
}


/* ==========================================================
   MOBILE IMPROVEMENTS
   ========================================================== */

@media (max-width: 600px) {

    .block-container {
        padding-left: 0.7rem;
        padding-right: 0.7rem;
    }

    .hero {
        padding: 18px;
        border-radius: 20px;
    }

    .hero h1 {
        font-size: 1.6rem;
    }

    .result {
        font-size: 1.9rem;
    }

    div[data-testid="stCameraInput"] {
        border-radius: 18px;
    }

}

</style>
""",
    unsafe_allow_html=True,
)


# ============================================================
# STORAGE FUNCTIONS
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

    if streamlit_geolocation is None:
        return None

    try:

        location = streamlit_geolocation()

        if (
            location
            and location.get("latitude") is not None
            and location.get("longitude") is not None
        ):

            return {
                "latitude": float(
                    location["latitude"]
                ),

                "longitude": float(
                    location["longitude"]
                ),

                "accuracy": location.get(
                    "accuracy"
                ),
            }

    except Exception:

        pass

    return None


# ============================================================
# RESET TEST
# ============================================================

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


# ============================================================
# LOAD HISTORY
# ============================================================

history = load_history()


# ============================================================
# HEADER
# ============================================================

st.markdown(
    """
<div class="hero">

    <div class="pill">
        FIELD TEST PROTOTYPE
    </div>

    <h1>
        🧪 FieldTest Companion
    </h1>

    <p>
        Capture → Calibrate → Classify → Generate Report
    </p>

</div>
""",
    unsafe_allow_html=True
)


# ============================================================
# NAVIGATION TABS
# ============================================================

tab_capture, tab_history, tab_about = st.tabs(
    [
        "📷 New Test",
        "🗂 History",
        "ℹ️ About"
    ]
)


# ============================================================
# NEW TEST TAB
# ============================================================

with tab_capture:

    st.subheader(
        "1. Test information"
    )


    # --------------------------------------------------------
    # OPERATOR INFORMATION
    # --------------------------------------------------------

    c1, c2 = st.columns(2)

    with c1:

        operator_id = st.text_input(
            "Operator ID",
            value="OP-001"
        )

    with c2:

        kit_profile = st.selectbox(
            "Demo kit profile",
            [
                "Demo Colorimetric Kit"
            ]
        )


    # --------------------------------------------------------
    # CAMERA
    # --------------------------------------------------------

    st.markdown(
        "### 2. Capture the test"
    )


    # Instruction card

    st.markdown(
        """
        <div class="instruction-card">

            <div class="instruction-title">
                📋 Position the test
            </div>

            <div class="instruction-text">

                Place the reference card on the
                <b>left</b> and the test strip on
                the <b>right</b>.

                Keep both completely visible
                and avoid glare.

            </div>

        </div>
        """,
        unsafe_allow_html=True
    )


    # Camera instruction

    st.markdown(
        """
        <div style="
            text-align:center;
            color:#91a9bf;
            font-size:0.9rem;
            margin-bottom:8px;
        ">
            📷 Capture the reference card and test strip together
        </div>
        """,
        unsafe_allow_html=True
    )


    # --------------------------------------------------------
    # CAMERA INPUT
    # --------------------------------------------------------

    photo = st.camera_input(
        "Camera",
        key="field_camera",
        label_visibility="collapsed"
    )


    # --------------------------------------------------------
    # GPS
    # --------------------------------------------------------

    location = get_location()


    # Show only a small status message.
    # The actual geolocation component remains hidden.

    if location:

        st.markdown(
            """
            <div class="location-success">

                ● Location captured

            </div>
            """,
            unsafe_allow_html=True
        )


    # --------------------------------------------------------
    # CAPTURED IMAGE
    # --------------------------------------------------------

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
        # COMPUTER VISION
        # ----------------------------------------------------

        st.markdown(
            "### 3. Computer vision analysis"
        )


        if st.button(
            "🔬 Analyze Test",
            type="primary",
            use_container_width=True
        ):

            with st.spinner(
                "Calibrating lighting and analyzing test color..."
            ):

                try:

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
                    # CREATE RECORD
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
                    # SAVE HISTORY
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


        st.markdown("---")


        st.subheader(
            "4. Presumptive result"
        )


        # ----------------------------------------------------
        # RESULT COLOR
        # ----------------------------------------------------

        css_class = {

            "POSITIVE":
                "positive",

            "NEGATIVE":
                "negative",

            "INCONCLUSIVE":
                "inconclusive",

        }.get(
            result["classification"],
            "inconclusive"
        )


        # ----------------------------------------------------
        # RESULT CARD
        # ----------------------------------------------------

        st.markdown(
            f"""
            <div class="result-card">

                <div class="small">
                    COLORIMETRIC CLASSIFICATION
                </div>

                <div class="result {css_class}">
                    {result["classification"]}
                </div>

                <div>
                    Confidence:
                    <b>
                        {result["confidence"]:.1f}%
                    </b>
                </div>

            </div>
            """,
            unsafe_allow_html=True
        )


        # ----------------------------------------------------
        # CONFIDENCE
        # ----------------------------------------------------

        st.progress(
            min(
                result["confidence"] / 100.0,
                1.0
            )
        )


        # ----------------------------------------------------
        # ANALYSIS METRICS
        # ----------------------------------------------------

        a, b = st.columns(2)

        with a:

            st.metric(
                "Calibration",
                result["calibration"]
            )

        with b:

            st.metric(
                "Test color distance",
                f'{result["distance"]:.1f}'
            )


        # ----------------------------------------------------
        # CV DETAILS
        # ----------------------------------------------------

        with st.expander(
            "🔬 CV analysis details"
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
        # DIGITAL REPORT
        # ====================================================

        if record:

            st.markdown(
                "### 5. Digital report"
            )


            st.write(
                f"""
**Test ID:** {record["test_id"]}

**Operator:** {record["operator_id"]}

**Time:** {record["timestamp_display"]}
"""
            )


            if (
                record["latitude"]
                is not None
            ):

                st.write(
                    f"""
**GPS:** {record["latitude"]:.6f},
{record["longitude"]:.6f}
"""
                )


            # ------------------------------------------------
            # GENERATE PDF
            # ------------------------------------------------

            if st.button(
                "📄 Generate PDF Report",
                use_container_width=True
            ):

                pdf_path = create_pdf_report(

                    record=record,

                    image_path=(
                        APP_DIR
                        / record["image_path"]
                    )
                )


                st.session_state[
                    "pdf_path"
                ] = str(pdf_path)


                st.success(
                    "PDF report created."
                )


            # ------------------------------------------------
            # DOWNLOAD PDF
            # ------------------------------------------------

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

                    "⬇️ Save PDF",

                    data=pdf_bytes,

                    file_name=(
                        f'{record["test_id"]}'
                        '_report.pdf'
                    ),

                    mime="application/pdf",

                    use_container_width=True
                )


                st.info(
                    "On your phone, save the PDF and "
                    "use the phone's Share option to "
                    "send it through WhatsApp, Gmail, "
                    "Drive, etc."
                )


            # ------------------------------------------------
            # NEW TEST
            # ------------------------------------------------

            if st.button(
                "➕ Start New Test",
                use_container_width=True
            ):

                reset_test()

                st.rerun()


    # ========================================================
    # DISCLAIMER
    # ========================================================

    st.markdown(
        """
        <div class="disclaimer">

        ⚠️ <b>Presumptive field-test result only.</b>

        This prototype does not replace
        laboratory confirmatory testing.

        </div>
        """,
        unsafe_allow_html=True
    )


# ============================================================
# HISTORY TAB
# ============================================================

with tab_history:

    st.subheader(
        "Test history"
    )


    if not history:

        st.info(
            "No tests have been saved yet."
        )


    else:

        # ----------------------------------------------------
        # SEARCH
        # ----------------------------------------------------

        query = st.text_input(

            "Search by test ID, operator, or result",

            placeholder=(
                "e.g. FT-1234 or OP-001 or POSITIVE"
            )

        ).strip().lower()


        # ----------------------------------------------------
        # FILTER
        # ----------------------------------------------------

        filtered = [

            record

            for record in history

            if (

                not query

                or query
                in record[
                    "test_id"
                ].lower()

                or query
                in record[
                    "operator_id"
                ].lower()

                or query
                in record[
                    "classification"
                ].lower()

            )

        ]


        # ----------------------------------------------------
        # HISTORY METRICS
        # ----------------------------------------------------

        p, n, i = st.columns(3)


        with p:

            st.metric(
                "Total",
                len(history)
            )


        with n:

            st.metric(
                "Positive",
                sum(
                    record[
                        "classification"
                    ]
                    == "POSITIVE"

                    for record
                    in history
                )
            )


        with i:

            st.metric(
                "Other",
                sum(
                    record[
                        "classification"
                    ]
                    != "POSITIVE"

                    for record
                    in history
                )
            )


        # ----------------------------------------------------
        # HISTORY ITEMS
        # ----------------------------------------------------

        for record in filtered:

            label = (
                f'{record["classification"]}'
                f' · '
                f'{record["test_id"]}'
            )


            with st.expander(
                label
            ):

                st.write(
                    f'**Operator:** '
                    f'{record["operator_id"]}'
                )

                st.write(
                    f'**Time:** '
                    f'{record["timestamp_display"]}'
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


                st.write(
                    f'**Confidence:** '
                    f'{record["confidence"]:.1f}%'
                )


                # --------------------------------------------
                # IMAGE
                # --------------------------------------------

                img = (
                    APP_DIR
                    / record["image_path"]
                )


                if img.exists():

                    st.image(
                        img,
                        use_container_width=True
                    )


                # --------------------------------------------
                # PDF
                # --------------------------------------------

                if st.button(

                    f'📄 Generate PDF — '
                    f'{record["test_id"]}',

                    key=(
                        f'pdf_'
                        f'{record["test_id"]}'
                    ),

                    use_container_width=True

                ):

                    pdf = create_pdf_report(

                        record,

                        img

                    )


                    st.download_button(

                        "⬇️ Download report",

                        data=pdf.read_bytes(),

                        file_name=(
                            f'{record["test_id"]}'
                            '_report.pdf'
                        ),

                        mime="application/pdf",

                        key=(
                            f'download_'
                            f'{record["test_id"]}'
                        ),

                        use_container_width=True
                    )


# ============================================================
# ABOUT TAB
# ============================================================

with tab_about:

    st.subheader(
        "How the prototype works"
    )


    st.markdown(
        """
### 📷 Step 1 — Image Capture

The phone camera captures the existing
colorimetric field-test strip together
with a reference colour card.

### 🎨 Step 2 — Lighting Calibration

The reference card is used as an
illumination reference so the test
colour can be normalized.

### 🔬 Step 3 — Computer Vision

The calibrated test colour is analyzed
and classified as:

- POSITIVE
- NEGATIVE
- INCONCLUSIVE

### 📍 Step 4 — Digital Record

The prototype records:

- Operator ID
- Timestamp
- GPS location
- Test ID
- Classification
- Confidence
- Captured image

### 📄 Step 5 — PDF Report

A digital report is generated containing
the captured image and test information.

### 📤 Step 6 — Sharing

The PDF can be downloaded and shared
through the phone's normal sharing system.

---

### ⚠️ Important

This is a prototype.

The positive and negative colour
profiles are **demo profiles** and are
not a validated narcotics-testing model.

The output is a **presumptive field-test
result** and does not replace laboratory
confirmatory testing.
"""
    )
