from langchain.tools import tool


@tool
def calculate_emi(principal: float, annual_rate: float, tenure_months: int) -> float:
    """Calculate monthly EMI for a loan.

    Args:
        principal: Loan principal amount.
        annual_rate: Annual interest rate in percentage (e.g., 10.5 for 10.5%).
        tenure_months: Loan tenure in months.

    Returns:
        Monthly EMI amount rounded to 2 decimal places.
    """
    if annual_rate == 0:
        return round(principal / tenure_months, 2)

    monthly_rate = annual_rate / (12 * 100)
    emi = principal * monthly_rate * (1 + monthly_rate) ** tenure_months / (
        (1 + monthly_rate) ** tenure_months - 1
    )
    return round(emi, 2)


@tool
def detect_hidden_fees(loan_offer_text: str) -> dict:
    """Detect potential hidden fees in a loan offer description.

    Args:
        loan_offer_text: The text of the loan offer to analyze.

    Returns:
        A dict with keys 'has_fee' (bool) and optionally 'fee_type' and 'estimated_amount'.
    """
    keywords = {
        "processing": "Processing Fee",
        "admin": "Administrative Fee",
        "insurance": "Insurance Fee",
        "late fee": "Late Payment Fee",
    }

    text_lower = loan_offer_text.lower()
    for keyword, fee_type in keywords.items():
        if keyword in text_lower:
            return {
                "has_fee": True,
                "fee_type": fee_type,
                "estimated_amount": "3% of principal",
            }

    return {"has_fee": False}


@tool
def calculate_risk(emi: float, monthly_income: float) -> str:
    """Calculate loan risk level based on EMI-to-income ratio.

    Args:
        emi: Monthly EMI amount.
        monthly_income: Monthly income of the borrower.

    Returns:
        A risk assessment string: HIGH RISK, MEDIUM RISK, or LOW RISK.
    """
    if monthly_income <= 0:
        return "UNDEFINED: Monthly income must be greater than zero."

    ratio = emi / monthly_income

    if ratio > 0.5:
        return "HIGH RISK: EMI exceeds 50% of income"
    elif ratio > 0.3:
        return "MEDIUM RISK: EMI between 30-50%"
    else:
        return "LOW RISK: Safe EMI"


loan_analysis_tools = [calculate_emi, detect_hidden_fees, calculate_risk]