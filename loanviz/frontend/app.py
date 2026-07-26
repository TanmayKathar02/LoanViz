import os
import streamlit as st
import requests
import json

# ---------------------------------------------------------------------------
# Page configuration
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="LoanViz - Education Loan Decision Assistant",
    page_icon="🎓",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Custom CSS for a student-friendly, modern look
# ---------------------------------------------------------------------------
st.markdown(
    """
<style>
/* Main title styling */
.main-title {
    text-align: center;
    font-size: 2.5rem;
    font-weight: 700;
    margin-bottom: 0.25rem;
    color: #1E3A5F;
}
.sub-title {
    text-align: center;
    font-size: 1rem;
    color: #6B7B8D;
    margin-bottom: 2rem;
}

/* Metric cards */
div[data-testid="metric-container"] {
    background: #f8f9fa;
    border-radius: 12px;
    padding: 1.2rem 1rem;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    border: 1px solid #e9ecef;
}
div[data-testid="metric-container"] label {
    font-size: 0.85rem !important;
    font-weight: 600 !important;
    color: #495057 !important;
}
div[data-testid="metric-container"] div[data-testid="metric-value"] {
    font-size: 1.8rem !important;
    font-weight: 700 !important;
}

/* Risk badge styling */
.risk-badge {
    display: inline-block;
    padding: 0.4rem 1.2rem;
    border-radius: 20px;
    font-weight: 700;
    font-size: 1.1rem;
    text-align: center;
}
.risk-low {
    background-color: #d4edda;
    color: #155724;
    border: 1px solid #c3e6cb;
}
.risk-medium {
    background-color: #fff3cd;
    color: #856404;
    border: 1px solid #ffeeba;
}
.risk-high {
    background-color: #f8d7da;
    color: #721c24;
    border: 1px solid #f5c6cb;
}

/* Warning banner */
.warning-banner {
    background: #fff3cd;
    border-left: 5px solid #ffc107;
    padding: 1rem 1.2rem;
    border-radius: 8px;
    margin: 1rem 0;
    font-weight: 500;
}

/* Recommendation box */
.recommendation-box {
    background: linear-gradient(135deg, #e8f4f8 0%, #f0f8ff 100%);
    border: 1px solid #b8d4e3;
    border-radius: 12px;
    padding: 1.5rem;
    margin: 1rem 0;
}

/* Footer */
.footer {
    text-align: center;
    margin-top: 3rem;
    padding-top: 1.5rem;
    border-top: 1px solid #e9ecef;
    color: #6B7B8D;
    font-size: 0.9rem;
}

/* Sidebar styling */
.section-header {
    font-size: 1.1rem;
    font-weight: 600;
    color: #1E3A5F;
    margin-top: 0.5rem;
    margin-bottom: 0.25rem;
}
</style>
""",
    unsafe_allow_html=True,
)

API_BASE_URL = os.getenv("API_URL", "http://localhost:8001").rstrip("/")

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.markdown(
    '<div class="main-title">🎓 LoanViz — Education Loan Decision Assistant</div>',
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="sub-title">Analyse loan offers, detect hidden fees, and get AI-powered recommendations</div>',
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Sidebar – Input fields
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("## 📋 Loan Details")
    st.markdown("Fill in the details below to analyse your education loan offer.")

    principal = st.number_input(
        "💰 Loan Amount (Principal) in ₹",
        min_value=1_000,
        max_value=100_000_000,
        value=500_000,
        step=10_000,
        format="%d",
        help="The total loan amount you are considering.",
    )

    annual_rate = st.number_input(
        "📈 Annual Interest Rate (%)",
        min_value=0.1,
        max_value=50.0,
        value=10.5,
        step=0.1,
        format="%.2f",
        help="The yearly interest rate offered by the bank.",
    )

    tenure_months = st.number_input(
        "📅 Tenure (months)",
        min_value=1,
        max_value=360,
        value=60,
        step=6,
        format="%d",
        help="Loan repayment period in months.",
    )

    monthly_income = st.number_input(
        "💼 Monthly Income (₹)",
        min_value=0,
        max_value=10_000_000,
        value=50_000,
        step=5_000,
        format="%d",
        help="Your expected monthly income (for EMI-to-income ratio).",
    )

    loan_offer_text = st.text_area(
        "📝 Loan Offer Description",
        value="",
        height=150,
        placeholder="Paste the bank's offer details here... e.g. processing fee 1%, prepayment charges, etc.",
        help="Paste the full text of the loan offer from the bank.",
    )

    analyze_clicked = st.button("🔍 Analyze Loan", type="primary", use_container_width=True)

# ---------------------------------------------------------------------------
# Main area – Results
# ---------------------------------------------------------------------------
if analyze_clicked:
    if not loan_offer_text.strip():
        st.error("⚠️ Please paste the loan offer description before analysing.")
    else:
        with st.spinner("🧠 Analysing your loan offer... please wait."):
            try:
                payload = {
                    "principal": principal,
                    "annual_rate": annual_rate,
                    "tenure_months": tenure_months,
                    "monthly_income": monthly_income,
                    "loan_offer_text": loan_offer_text,
                }
                resp = requests.post(
                    f"{API_BASE_URL}/analyze",
                    json=payload,
                    timeout=60,
                )
                resp.raise_for_status()
                data = resp.json()
            except requests.exceptions.ConnectionError:
                st.error(
                    "🚫 Could not connect to the backend. "
                    "Make sure the backend server is running on http://localhost:8001."
                )
                st.stop()
            except requests.exceptions.Timeout:
                st.error("⏱️ The request timed out. Please try again.")
                st.stop()
            except Exception as e:
                st.error(f"❌ An error occurred: {e}")
                st.stop()

        # Check for backend error
        if "error" in data:
            st.error(f"❌ Backend error: {data['error']}")
            st.stop()

        # -------------------------------------------------------------------
        # Results display
        # -------------------------------------------------------------------
        st.markdown("## 📊 Analysis Results")
        st.markdown("---")

        # -- Columns: EMI, Risk Score, Fees --
        col1, col2, col3 = st.columns(3)

        with col1:
            emi = data.get("emi", 0.0)
            st.metric(
                label="📆 Monthly EMI",
                value=f"₹{emi:,.2f}",
                delta=None,
            )

        with col2:
            risk = data.get("risk", "UNKNOWN").upper()
            if risk == "LOW":
                risk_label = "🟢 Low"
                risk_class = "risk-low"
            elif risk == "MEDIUM":
                risk_label = "🟡 Medium"
                risk_class = "risk-medium"
            elif risk == "HIGH":
                risk_label = "🔴 High"
                risk_class = "risk-high"
            else:
                risk_label = risk
                risk_class = "risk-low"

            st.markdown("**⚠️ Risk Score**")
            st.markdown(
                f'<div class="risk-badge {risk_class}">{risk_label}</div>',
                unsafe_allow_html=True,
            )

        with col3:
            fees = data.get("fees", {})
            has_fee = fees.get("has_fee", False) if isinstance(fees, dict) else False
            if has_fee:
                fee_desc = fees.get("description", "Hidden fees detected!")
                st.markdown(
                    f'<div class="warning-banner">🚨 <strong>Hidden Fees Detected!</strong><br>{fee_desc}</div>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    '<div class="risk-badge risk-low">✅ No Hidden Fees</div>',
                    unsafe_allow_html=True,
                )

        # -- Recommendation --
        st.markdown("---")
        recommendation = data.get("recommendation", "")
        if recommendation:
            st.markdown(
                f"""
                <div class="recommendation-box">
                    <h4>🤖 AI Recommendation</h4>
                    <p style="font-size:1.05rem; line-height:1.6;">{recommendation}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.info("ℹ️ No recommendation was provided by the AI.")

        # -- Raw JSON expander (for debugging / transparency) --
        with st.expander("📄 View raw analysis data"):
            st.json(data)

else:
    # Placeholder when no analysis has been run yet
    st.info(
        "👈 Fill in your loan details in the sidebar and click **Analyze Loan** "
        "to get started."
    )

# ---------------------------------------------------------------------------
# Footer – SigNoz attribution
# ---------------------------------------------------------------------------
st.markdown(
    """
    <div class="footer">
        🔍 This analysis was traced and monitored by <strong>SigNoz</strong>
    </div>
    """,
    unsafe_allow_html=True,
)