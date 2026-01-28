"""
Finanse i Trading - Optymalizacja portfela i wykonanie zleceń

Demonstruje użycie NLP2CMD do optymalizacji finansowej
i zarządzania ryzykiem.
"""

import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from _demo_helpers import print_metrics, print_separator, run_thermo_demo
from nlp2cmd.generation.thermodynamic import ThermodynamicGenerator


async def demo_portfolio_optimization():
    """Optymalizacja portfela inwestycyjnego (Markowitz)."""
    # Optymalizacja portfela
    result = await run_thermo_demo(
        "Finanse - Portfolio Optimization",
        """
        Zoptymalizuj portfel 20 akcji:
        - Budżet: 1,000,000 PLN
        - Max 15% w jednej akcji
        - Min 5% w każdej wybranej akcji
        - Docelowe ryzyko (std): 12% rocznie
        
        Maksymalizuj oczekiwany zwrot przy zadanym ryzyku.
    """,
    )
    
    print("Optimal Portfolio:")
    # Symulacja wyników
    portfolio = {
        'PKO BP': {'weight': 0.15, 'expected_return': 0.08},
        'PZU': {'weight': 0.12, 'expected_return': 0.10},
        'KGHM': {'weight': 0.10, 'expected_return': 0.15},
        'PGE': {'weight': 0.08, 'expected_return': 0.12},
        'ORLEN': {'weight': 0.14, 'expected_return': 0.09},
        'MBank': {'weight': 0.11, 'expected_return': 0.11},
        'ING': {'weight': 0.09, 'expected_return': 0.07},
        'Santander': {'weight': 0.07, 'expected_return': 0.06},
        'Alior': {'weight': 0.06, 'expected_return': 0.13},
        'Millennium': {'weight': 0.08, 'expected_return': 0.10}
    }
    
    for asset, data in portfolio.items():
        print(f"  {asset}: {data['weight']:.1%}")
    
    total_return = sum(data['weight'] * data['expected_return'] for data in portfolio.values())
    print(f"\nExpected return: {total_return:.1%}")
    print(f"Risk (std): 12.0%")
    print(f"Sharpe ratio: {total_return/0.12:.2f}")
    
    print(f"\n📊 Optimization result:")
    print(f"   {result.decoded_output}")
    print_metrics(result, energy=True)


async def demo_trade_execution():
    """Optymalizacja wykonania dużego zlecenia (TWAP/VWAP)."""
    # Optymalizacja wykonania zlecenia
    result = await run_thermo_demo(
        "Finanse - Trade Execution Scheduling",
        """
        Wykonaj zlecenie kupna 100,000 akcji XYZ:
        - Horyzont: 4 godziny
        - Minimalizuj market impact
        - Max 5% dziennego wolumenu w każdym interwale
        - Uwzględnij historyczny profil wolumenu
    """,
        leading_newline=True,
    )
    
    print(f"\n📈 Execution schedule:")
    print(f"   {result.decoded_output}")
    print_metrics(result, latency=True)


async def demo_risk_allocation():
    """Alokacja limitów ryzyka między deskami tradingowymi."""
    # Alokacja limitów ryzyka
    result = await run_thermo_demo(
        "Finanse - Risk Limit Allocation",
        """
        Przydziel limity VaR (100M PLN łącznie) do 5 desków:
        - Equity: historyczny Sharpe 1.2
        - Fixed Income: Sharpe 0.8
        - FX: Sharpe 1.5
        - Commodities: Sharpe 0.6
        - Derivatives: Sharpe 1.8
        
        Maksymalizuj oczekiwany P&L przy całkowitym VaR ≤ 100M.
    """,
        leading_newline=True,
    )
    
    print(f"\n⚠️ Risk allocation:")
    print(f"   {result.decoded_output}")
    print_metrics(result, solution_feasible=True)


async def demo_arbitrage_detection():
    """Wykrywanie i optymalizacja arbitrażu."""
    # Optymalizacja arbitrażu
    result = await run_thermo_demo(
        "Finanse - Arbitrage Optimization",
        """
        Zidentyfikuj i zoptymalizuj arbitraż na 10 parach walut:
        - EUR/PLN, USD/PLN, GBP/PLN, CHF/PLN, JPY/PLN
        - Koszty transakcyjne: 0.1% per trade
        - Max exposure: 10M PLN
        - Minimalny spread: 0.05%
        
        Maksymalizuj oczekiwany zysk przy kontrolowanym ryzyku.
    """,
        leading_newline=True,
    )
    
    print(f"\n💱 Arbitrage opportunities:")
    print(f"   {result.decoded_output}")
    print_metrics(result, energy_estimate=True, energy_estimate_label="Energy savings")


async def demo_options_strategy():
    """Optymalizacja strategii opcji."""
    # Optymalizacja strategii opcji
    result = await run_thermo_demo(
        "Finanse - Options Strategy Optimization",
        """
        Zaprojektuj strategię opcji na indeks WIG20:
        - Horyzont: 3 miesiące
        - Początkowa kapitalizacja: 100,000 PLN
        - Max tolerowana strata: 15%
        - Preferowany scenariusz: umiarkowana hossa
        
        Optymalizuj payoff przy ograniczonym ryzyku.
    """,
        leading_newline=True,
    )
    
    print(f"\n📊 Options strategy:")
    print(f"   {result.decoded_output}")
    print_metrics(result, sampler_steps=True)


async def demo_credit_scoring():
    """Optymalizacja modeli credit scoring."""
    # Optymalizacja modeli scoringowych
    result = await run_thermo_demo(
        "Finanse - Credit Scoring Model Optimization",
        """
        Zoptymalizuj model credit scoring dla 1000 aplikacji:
        - Cechy: dochód, wiek, historia kredytowa, zatrudnienie
        - Cel: minimalizacja false negatives (default)
        - Ograniczenie: max 10% false positives
        - Waga: default koszt = 10x koszt odrzucenia
        
        Znajdź optymalny próg scoringowy.
    """,
        leading_newline=True,
    )
    
    print(f"\n💳 Credit scoring model:")
    print(f"   {result.decoded_output}")
    print_metrics(result, solution_quality=True)


async def main():
    """Uruchom wszystkie demonstracje finansowe."""
    await demo_portfolio_optimization()
    await demo_trade_execution()
    await demo_risk_allocation()
    await demo_arbitrage_detection()
    await demo_options_strategy()
    await demo_credit_scoring()

    print_separator("Finance demos completed!", leading_newline=True, width=70)


if __name__ == "__main__":
    asyncio.run(main())
