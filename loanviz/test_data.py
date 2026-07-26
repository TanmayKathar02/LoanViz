#!/usr/bin/env python3
"""
test_data.py – Send 3 sample loan scenarios to the LoanViz backend
and print the results.

Usage:
    python test_data.py

Requires the backend to be running on http://localhost:8000.
"""

import json
import sys
import requests

BACKEND_URL = "http://localhost:8000/analyze"


def send_scenario(name: str, payload: dict) -> None:
    """Send a single loan scenario to the backend and print the result."""
    print(f"\n{'='*70}")
    print(f"  📌 Scenario: {name}")
    print(f"{'='*70}")
    print(f"  Input: {json.dumps(payload, indent=2)}")
    print()

    try:
        resp = requests.post(BACKEND_URL, json=payload, timeout=60)
        resp.raise_for_status()
        data = resp.json()
    except requests.exceptions.ConnectionError:
        print("  ❌ ERROR: Could not connect to the backend.")
        print("     Make sure it's running on http://localhost:8000")
        return
    except Exception as e:
        print(f"  ❌ ERROR: {e}")
        return

    if "error" in data:
        print(f"  ❌ Backend error: {data['error']}")
        return

    emi = data.get("emi", 0.0)
    risk = data.get("risk", "UNKNOWN")
    fees = data.get("fees", {})
    recommendation = data.get("recommendation", "")

    print(f"  📆 EMI:            ₹{emi:,.2f}")
    print(f"  ⚠️  Risk Score:     {risk}")

    if isinstance(fees, dict):
        if fees.get("has_fee", False):
            print(f"  🚨 Hidden Fees:    YES — {fees.get('description', '')}")
        else:
            print(f"  ✅ Hidden Fees:    None detected")
    else:
        print(f"  ℹ️  Fees:           {fees}")

    if recommendation:
        print(f"  🤖 Recommendation: {recommendation[:200]}...")
    else:
        print(f"  ℹ️  No recommendation provided.")

    print()


def main():
    # ------------------------------------------------------------------
    # Scenario A: "Good Loan" – low rate, no fees, good income
    # ------------------------------------------------------------------
    good_loan = {
        "principal": 300_000,
        "annual_rate": 6.5,
        "tenure_months": 48,
        "monthly_income": 80_000,
        "loan_offer_text": (
            "Education loan of ₹3,00,000 at 6.5% p.a. for 48 months. "
            "No processing fee. No prepayment charges. "
            "Simple interest with monthly reducing balance."
        ),
    }
    send_scenario("A) Good Loan (low rate, no fees, good income)", good_loan)

    # ------------------------------------------------------------------
    # Scenario B: "Hidden Fee Loan" – high rate, processing fee detected
    # ------------------------------------------------------------------
    hidden_fee_loan = {
        "principal": 1_000_000,
        "annual_rate": 14.5,
        "tenure_months": 60,
        "monthly_income": 60_000,
        "loan_offer_text": (
            "Education loan of ₹10,00,000 at 14.5% p.a. for 60 months. "
            "Processing fee of 2.5% of the loan amount. "
            "Prepayment penalty of 3% if closed before 24 months. "
            "Annual maintenance fee of ₹1,500. "
            "Late payment fee of ₹750 per occurrence."
        ),
    }
    send_scenario("B) Hidden Fee Loan (high rate, processing fee detected)", hidden_fee_loan)

    # ------------------------------------------------------------------
    # Scenario C: "High Risk Loan" – EMI > 50% of income
    # ------------------------------------------------------------------
    high_risk_loan = {
        "principal": 2_500_000,
        "annual_rate": 18.0,
        "tenure_months": 24,
        "monthly_income": 25_000,
        "loan_offer_text": (
            "Education loan of ₹25,00,000 at 18% p.a. for 24 months. "
            "Processing fee 1%. No prepayment charges. "
            "Interest calculated on daily reducing balance."
        ),
    }
    send_scenario("C) High Risk Loan (EMI > 50% of income)", high_risk_loan)

    print(f"{'='*70}")
    print("  ✅ All scenarios sent. Check the output above.")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()