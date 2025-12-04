from financial_logic import FinancialCalculator
from models import ProjectConfig, ExpenseItem, SalesScenario
import json

def test_calculation():
    config = ProjectConfig(
        name="Test Project",
        land_value_uf=30000,
        pct_fin_land=0.6,
        construction_value_uf=70000,
        pct_fin_construction=0.8,
        duration_months=18,
        reception_month=22,
        expenses=[
            ExpenseItem(name="Arch", amount_uf=2000, pct_financing=0.5)
        ],
        rate_annual_uf=6.5,
        rate_annual_clp=11.0,
        inflation_annual=3.0,
        pct_mix_uf=1.0,
        total_sales_value_uf=140000,
        sales_scenario=[
            SalesScenario(month_offset=1, pct_sale=20)
        ]
    )
    
    calc = FinancialCalculator(config)
    flow = calc.calculate()
    kpis = calc.get_kpis(flow)
    
    print("KPIs:", json.dumps(kpis, indent=2))
    assert kpis['net_profit'] is not None
    assert len(flow) > 22
    print("Test Passed!")

if __name__ == "__main__":
    test_calculation()
