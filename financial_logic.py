import numpy as np
import pandas as pd
from typing import List
from .models import ProjectConfig, FinancialResult

class FinancialCalculator:
    def __init__(self, config: ProjectConfig):
        self.config = config

    def calculate(self) -> List[FinancialResult]:
        # Unpack config
        c = self.config
        
        # Initial Calculations
        monto_deuda_terreno = c.land_value_uf * c.pct_fin_land
        
        # Calculate total other debt
        monto_deuda_otros = sum([e.amount_uf * e.pct_financing for e in c.expenses])
        
        # Rates
        i_uf_mensual = (1 + c.rate_annual_uf/100)**(1/12) - 1
        i_clp_mensual = (1 + c.rate_annual_clp/100)**(1/12) - 1
        inf_mensual = (1 + c.inflation_annual/100)**(1/12) - 1
        
        if (1 + inf_mensual) != 0:
            i_clp_real_mensual = ((1 + i_clp_mensual) / (1 + inf_mensual)) - 1
        else:
            i_clp_real_mensual = i_clp_mensual

        i_ponderada_mensual = (c.pct_mix_uf * i_uf_mensual) + ((1 - c.pct_mix_uf) * i_clp_real_mensual)
        
        # S-Curve for Construction (EEPP)
        meses_obra = np.arange(1, c.duration_months + 1)
        duracion_int = int(c.duration_months)
        curva_lista = []
        acumulado = 0.0
        
        for i in range(duracion_int):
            if i == 0: val = 19.0 # Initial advance
            elif i == duracion_int - 1:
                val = 100.0 - acumulado
                if val < 0: val = 0 
            else:
                val = 3.0 # Linear progress
                if acumulado + val > 100: val = 100.0 - acumulado
            curva_lista.append(val)
            acumulado += val
            
        # Determine Horizon
        max_venta_mes = c.reception_month
        if c.sales_scenario:
            max_venta_mes = max([c.reception_month + s.month_offset for s in c.sales_scenario])
            
        horizonte = max(c.reception_month, max_venta_mes) + 6
        
        # Simulation Loop
        saldo_terreno = 0.0
        saldo_construccion = 0.0
        saldo_otros = 0.0
        
        historia = []
        
        for mes in range(1, horizonte + 1):
            # A. DISBURSEMENTS (GIROS)
            if mes == 1:
                saldo_terreno += monto_deuda_terreno
                saldo_otros += monto_deuda_otros
                
            giro_construccion_banco = 0.0
            monto_eepp_mes = 0.0
            aporte_propio_mes = 0.0
            
            # Check if we are in construction phase
            if mes <= c.duration_months:
                # 0-indexed list access
                avance_pct = curva_lista[mes-1]
                monto_eepp_mes = (avance_pct / 100.0) * c.construction_value_uf
                giro_construccion_banco = monto_eepp_mes * c.pct_fin_construction
                aporte_propio_mes = monto_eepp_mes * (1 - c.pct_fin_construction)
                
            saldo_construccion += giro_construccion_banco
            
            # B. INTERESTS
            int_terreno = saldo_terreno * i_ponderada_mensual
            int_construccion = saldo_construccion * i_ponderada_mensual
            int_otros = saldo_otros * i_ponderada_mensual
            total_int_mes = int_terreno + int_construccion + int_otros
            
            saldo_terreno += int_terreno
            saldo_construccion += int_construccion
            saldo_otros += int_otros
            
            # C. AMORTIZATION (SALES)
            ingreso_venta = 0.0
            for sale in c.sales_scenario:
                sale_month = c.reception_month + sale.month_offset
                if sale_month == mes:
                    ingreso_venta += c.total_sales_value_uf * (sale.pct_sale / 100.0)
            
            disponible = ingreso_venta
            
            # Pay Construction Debt first
            pago_const = min(saldo_construccion, disponible)
            saldo_construccion -= pago_const
            disponible -= pago_const
            
            # Pay Other Debt
            pago_otros = min(saldo_otros, disponible)
            saldo_otros -= pago_otros
            disponible -= pago_otros
            
            # Pay Land Debt
            pago_terr = min(saldo_terreno, disponible)
            saldo_terreno -= pago_terr
            disponible -= pago_terr
            
            historia.append(FinancialResult(
                month=mes,
                eepp_amount=monto_eepp_mes,
                debt_land=saldo_terreno,
                debt_construction=saldo_construccion,
                debt_others=saldo_otros,
                total_debt=saldo_terreno + saldo_construccion + saldo_otros,
                sales_income=ingreso_venta,
                cash_surplus=disponible,
                interest_payment=total_int_mes,
                equity_contribution=aporte_propio_mes
            ))
            
        return historia

    def get_kpis(self, flow: List[FinancialResult]) -> dict:
        df = pd.DataFrame([f.dict() for f in flow])
        
        # Equity Calculation
        equity_terreno = self.config.land_value_uf * (1 - self.config.pct_fin_land)
        equity_otros = sum([e.amount_uf * (1 - e.pct_financing) for e in self.config.expenses])
        
        suma_aporte_equity = df["equity_contribution"].sum() + equity_terreno + equity_otros
        suma_excedente = df["cash_surplus"].sum()
        utilidad_neta = suma_excedente - suma_aporte_equity
        intereses_totales = df["interest_payment"].sum()
        peak_deuda = df["total_debt"].max()
        
        return {
            "net_profit": utilidad_neta,
            "cash_surplus": suma_excedente,
            "financial_cost": intereses_totales,
            "peak_debt": peak_deuda,
            "total_equity": suma_aporte_equity
        }
