"""
Finanse i Trading - Optymalizacja portfela i wykonanie zleceń

Demonstruje użycie NLP2CMD do optymalizacji finansowej
i zarządzania ryzykiem.
"""

import asyncio
import time
from nlp2cmd.generation.thermodynamic import ThermodynamicGenerator


async def demo_portfolio_optimization():
    start_time = time.time()
    """Optymalizacja portfela inwestycyjnego (Markowitz)."""
    print("=" * 70)
    print("  Finanse - Portfolio Optimization")
    print("=" * 70)
    
    thermo = ThermodynamicGenerator()
    
    # Optymalizacja portfela
    result = await thermo.generate("""
        Zoptymalizuj portfel 20 akcji:
        - Budżet: 1,000,000 PLN
        - Max 15% w jednej akcji
        - Min 5% w każdej wybranej akcji
        - Docelowe ryzyko (std): 12% rocznie
        
        Maksymalizuj oczekiwany zwrot przy zadanym ryzyku.
    """)
    
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
    print(f"   Energy: {result.energy:.4f}")


async def demo_trade_execution():
    start_time = time.time()
    """Optymalizacja wykonania dużego zlecenia (TWAP/VWAP)."""
    print("\n" + "=" * 70)
    print("  Finanse - Trade Execution Scheduling")
    print("=" * 70)
    
    thermo = ThermodynamicGenerator()
    
    # Optymalizacja wykonania zlecenia
    result = await thermo.generate("""
        Wykonaj zlecenie kupna 100,000 akcji XYZ:
        - Horyzont: 4 godziny
        - Minimalizuj market impact
        - Max 5% dziennego wolumenu w każdym interwale
        - Uwzględnij historyczny profil wolumenu
    """)
    
    print(f"\n📈 Execution schedule:")
    print(f"   {result.decoded_output}")
    print(f"   Latency: {result.latency_ms:.1f}ms")


async def demo_risk_allocation():
    start_time = time.time()
    """Alokacja limitów ryzyka między deskami tradingowymi."""
    print("\n" + "=" * 70)
    print("  Finanse - Risk Limit Allocation")
    print("=" * 70)
    
    thermo = ThermodynamicGenerator()
    
    # Alokacja limitów ryzyka
    result = await thermo.generate("""
        Przydziel limity VaR (100M PLN łącznie) do 5 desków:
        - Equity: historyczny Sharpe 1.2
        - Fixed Income: Sharpe 0.8
        - FX: Sharpe 1.5
        - Commodities: Sharpe 0.6
        - Derivatives: Sharpe 1.8
        
        Maksymalizuj oczekiwany P&L przy całkowitym VaR ≤ 100M.
    """)
    
    print(f"\n⚠️ Risk allocation:")
    print(f"   {result.decoded_output}")
    print(f"   Solution feasible: {result.solution_quality.is_feasible}")


async def demo_arbitrage_detection():
    start_time = time.time()
    """Wykrywanie i optymalizacja arbitrażu."""
    print("\n" + "=" * 70)
    print("  Finanse - Arbitrage Optimization")
    print("=" * 70)
    
    thermo = ThermodynamicGenerator()
    
    # Optymalizacja arbitrażu
    result = await thermo.generate("""
        Zidentyfikuj i zoptymalizuj arbitraż na 10 parach walut:
        - EUR/PLN, USD/PLN, GBP/PLN, CHF/PLN, JPY/PLN
        - Koszty transakcyjne: 0.1% per trade
        - Max exposure: 10M PLN
        - Minimalny spread: 0.05%
        
        Maksymalizuj oczekiwany zysk przy kontrolowanym ryzyku.
    """)
    
    print(f"\n💱 Arbitrage opportunities:")
    print(f"   {result.decoded_output}")
    print(f"   Energy savings: {result.energy_estimate.get('savings_digital_percent', 0):.1f}%")


async def demo_options_strategy():
    start_time = time.time()
    """Optymalizacja strategii opcji."""
    print("\n" + "=" * 70)
    print("  Finanse - Options Strategy Optimization")
    print("=" * 70)
    
    thermo = ThermodynamicGenerator()
    
    # Optymalizacja strategii opcji
    result = await thermo.generate("""
        Zaprojektuj strategię opcji na indeks WIG20:
        - Horyzont: 3 miesiące
        - Początkowa kapitalizacja: 100,000 PLN
        - Max tolerowana strata: 15%
        - Preferowany scenariusz: umiarkowana hossa
        
        Optymalizuj payoff przy ograniczonym ryzyku.
    """)
    
    print(f"\n📊 Options strategy:")
    print(f"   {result.decoded_output}")
    print(f"   Sampler steps: {result.sampler_steps}")


async def demo_credit_scoring():
    start_time = time.time()
    """Optymalizacja modeli credit scoring."""
    print("\n" + "=" * 70)
    print("  Finanse - Credit Scoring Model Optimization")
    print("=" * 70)
    
    thermo = ThermodynamicGenerator()
    
    # Optymalizacja modeli scoringowych
    result = await thermo.generate("""
        Zoptymalizuj model credit scoring dla 1000 aplikacji:
        - Cechy: dochód, wiek, historia kredytowa, zatrudnienie
        - Cel: minimalizacja false negatives (default)
        - Ograniczenie: max 10% false positives
        - Waga: default koszt = 10x koszt odrzucenia
        
        Znajdź optymalny próg scoringowy.
    """)
    
    print(f"\n💳 Credit scoring model:")
    start_time = time.time()
    print(f"   {result.decoded_output}")
    print(f"   Solution quality: {result.solution_quality.explanation}")


async def main():
    """Uruchom wszystkie demonstracje finansowe."""
    await demo_portfolio_optimization()
    await demo_trade_execution()
    await demo_risk_allocation()
    await demo_arbitrage_detection()
    await demo_options_strategy()
    await demo_credit_scoring()
    
    print("\n" + "=" * 70)
    print("  Finance demos completed!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
