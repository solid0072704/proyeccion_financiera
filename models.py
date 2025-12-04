from pydantic import BaseModel
from typing import List, Optional

class ExpenseItem(BaseModel):
    name: str
    amount_uf: float
    pct_financing: float  # 0.0 to 1.0

class SalesScenario(BaseModel):
    month_offset: int  # Months after reception
    pct_sale: float    # 0.0 to 100.0

class ProjectConfig(BaseModel):
    name: str
    # Land
    land_value_uf: float
    pct_fin_land: float
    
    # Construction
    construction_value_uf: float
    pct_fin_construction: float
    duration_months: int
    reception_month: int
    
    # Other Costs (now granular)
    expenses: List[ExpenseItem]
    
    # Rates
    rate_annual_uf: float
    rate_annual_clp: float
    inflation_annual: float
    pct_mix_uf: float
    
    # Sales
    total_sales_value_uf: float
    sales_scenario: List[SalesScenario]

class FinancialResult(BaseModel):
    month: int
    eepp_amount: float
    debt_land: float
    debt_construction: float
    debt_others: float
    total_debt: float
    sales_income: float
    cash_surplus: float
    interest_payment: float
    equity_contribution: float

class CalculationResponse(BaseModel):
    flow: List[FinancialResult]
    kpis: dict
