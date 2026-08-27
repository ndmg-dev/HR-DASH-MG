"""
Confidential endpoint — GET /api/confidential/employees

Returns individual employee records including names. Exige, além do Bearer JWT
do CRM (global em app/api/router.py), que o e-mail do usuário esteja na
allowlist HR_CONFIDENTIAL_ALLOWLIST — ver app/auth.py.
"""

from fastapi import APIRouter, Depends

from app.auth import require_confidential_access
from app.etl.pipeline import get_dataframe
from app.models.metrics import ConfidentialEmployeeResponse

router = APIRouter(tags=["confidential"])


@router.get("/confidential/employees", response_model=list[ConfidentialEmployeeResponse])
def get_confidential_employees(
    _user: dict = Depends(require_confidential_access),
) -> list[ConfidentialEmployeeResponse]:
    """Return row-level employee data. Restrito a usuários na allowlist."""
    df = get_dataframe()
    
    results = []
    for _, row in df.iterrows():
        # Determine simple risk signal
        risk_signal = None
        if not bool(row["expectativa"]):
            risk_signal = "Risco de Retenção"
            
        results.append(ConfidentialEmployeeResponse(
            func=str(row["func"]),
            cargo=str(row["cargo"]),
            salario=round(float(row["salario"]), 2),
            tenure_years=round(float(row["tenure_years"]), 4),
            expectativa=bool(row["expectativa"]),
            risk_signal=risk_signal
        ))
        
    return results
