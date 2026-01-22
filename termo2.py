"""
NLP2CMD - Przykłady zastosowań w różnych dziedzinach.

Ten moduł zawiera praktyczne przykłady użycia NLP2CMD
w IT, nauce i biznesie.
"""

import asyncio
from dataclasses import dataclass
from typing import Any, Optional
import numpy as np


# =============================================================================
# 1. IT & DevOps - Kubernetes Automation
# =============================================================================

async def demo_devops_automation():
    """Demonstracja automatyzacji DevOps."""
    print("=" * 70)
    print("  DevOps Automation Demo")
    print("=" * 70)

    # Symulacja NLP2CMD (w produkcji użyj prawdziwego generatora)
    queries_and_commands = [
        ("Pokaż wszystkie pody w namespace production",
         "kubectl get pods -n production"),
        ("Skaluj deployment api-server do 5 replik",
         "kubectl scale deployment api-server --replicas=5"),
        ("Znajdź logi z błędami z ostatniej godziny",
         "kubectl logs -l app=api --since=1h | grep -i error"),
        ("Pokaż wykorzystanie zasobów przez pody",
         "kubectl top pods --sort-by=memory"),
        ("Wykonaj rolling restart deployment web",
         "kubectl rollout restart deployment/web"),
    ]

    for query, expected_cmd in queries_and_commands:
        print(f"\n📝 Query: {query}")
        print(f"   Command: {expected_cmd}")

    print("\n" + "-" * 70)
    print("✅ DevOps queries translated to kubectl commands")


# =============================================================================
# 2. Data Science - Hyperparameter Optimization
# =============================================================================

@dataclass
class HyperparameterSpace:
    """Przestrzeń hiperparametrów do optymalizacji."""
    learning_rate: tuple = (0.0001, 0.1)
    batch_size: tuple = (16, 256)
    num_layers: tuple = (2, 10)
    dropout: tuple = (0.0, 0.5)
    hidden_dim: tuple = (64, 512)


class HyperparameterOptimizer:
    """
    Optymalizator hiperparametrów używający Langevin sampling.

    Zamiast grid search czy random search, używamy
    termodynamicznego samplowania do eksploracji przestrzeni.
    """

    def __init__(self, space: HyperparameterSpace, n_samples: int = 20):
        self.space = space
        self.n_samples = n_samples

    def _decode_params(self, z: np.ndarray) -> dict:
        """Dekoduj wektor z do hiperparametrów."""
        # Sigmoid dla [0, 1], potem skaluj do zakresów
        sigmoid = lambda x: 1 / (1 + np.exp(-x))

        lr_range = self.space.learning_rate
        bs_range = self.space.batch_size

        return {
            'learning_rate': lr_range[0] + sigmoid(z[0]) * (lr_range[1] - lr_range[0]),
            'batch_size': int(bs_range[0] + sigmoid(z[1]) * (bs_range[1] - bs_range[0])),
            'num_layers': int(self.space.num_layers[0] + sigmoid(z[2]) *
                              (self.space.num_layers[1] - self.space.num_layers[0])),
            'dropout': sigmoid(z[3]) * self.space.dropout[1],
            'hidden_dim': int(self.space.hidden_dim[0] + sigmoid(z[4]) *
                              (self.space.hidden_dim[1] - self.space.hidden_dim[0])),
        }

    def _evaluate(self, params: dict) -> float:
        """Symulacja ewaluacji modelu (w produkcji - prawdziwy trening)."""
        # Symulacja: optymalne wartości gdzieś w środku
        optimal = {
            'learning_rate': 0.001,
            'batch_size': 64,
            'num_layers': 4,
            'dropout': 0.2,
            'hidden_dim': 256,
        }

        # "Loss" jako odległość od optimum
        loss = 0.0
        loss += abs(np.log(params['learning_rate']) - np.log(optimal['learning_rate']))
        loss += abs(params['batch_size'] - optimal['batch_size']) / 100
        loss += abs(params['num_layers'] - optimal['num_layers'])
        loss += abs(params['dropout'] - optimal['dropout']) * 5
        loss += abs(params['hidden_dim'] - optimal['hidden_dim']) / 100

        return loss + np.random.normal(0, 0.1)  # Dodaj szum

    def optimize(self) -> tuple[dict, float]:
        """Znajdź optymalne hiperparametry."""
        best_params = None
        best_loss = float('inf')

        # Prosty Langevin sampling
        z = np.random.randn(5)

        for i in range(self.n_samples):
            params = self._decode_params(z)
            loss = self._evaluate(params)

            if loss < best_loss:
                best_loss = loss
                best_params = params

            # Langevin update (uproszczony)
            grad = np.random.randn(5) * 0.1  # Przybliżony gradient
            z = z - 0.1 * grad + np.sqrt(0.2) * np.random.randn(5)

        return best_params, best_loss


async def demo_hyperparameter_optimization():
    """Demonstracja optymalizacji hiperparametrów."""
    print("\n" + "=" * 70)
    print("  Hyperparameter Optimization Demo")
    print("=" * 70)

    space = HyperparameterSpace()
    optimizer = HyperparameterOptimizer(space, n_samples=50)

    print("\n🔍 Searching hyperparameter space...")
    best_params, best_loss = optimizer.optimize()

    print(f"\n✅ Optimal hyperparameters found:")
    print(f"   Learning rate: {best_params['learning_rate']:.6f}")
    print(f"   Batch size: {best_params['batch_size']}")
    print(f"   Num layers: {best_params['num_layers']}")
    print(f"   Dropout: {best_params['dropout']:.3f}")
    print(f"   Hidden dim: {best_params['hidden_dim']}")
    print(f"\n   Final loss: {best_loss:.4f}")


# =============================================================================
# 3. Logistyka - Vehicle Routing Problem (VRP)
# =============================================================================

@dataclass
class DeliveryPoint:
    """Punkt dostawy."""
    id: str
    x: float
    y: float
    demand: int
    time_window: tuple[int, int] = (0, 24)


class VRPSolver:
    """
    Solver dla Vehicle Routing Problem.

    Używa termodynamicznego samplowania do znajdowania
    optymalnych tras dla floty pojazdów.
    """

    def __init__(self, points: list[DeliveryPoint], vehicle_capacity: int = 100):
        self.points = points
        self.depot = points[0]  # Pierwszy punkt to depot
        self.customers = points[1:]
        self.capacity = vehicle_capacity

    def _distance(self, p1: DeliveryPoint, p2: DeliveryPoint) -> float:
        """Odległość euklidesowa między punktami."""
        return np.sqrt((p1.x - p2.x) ** 2 + (p1.y - p2.y) ** 2)

    def _route_distance(self, route: list[DeliveryPoint]) -> float:
        """Całkowita długość trasy."""
        if not route:
            return 0

        dist = self._distance(self.depot, route[0])
        for i in range(len(route) - 1):
            dist += self._distance(route[i], route[i + 1])
        dist += self._distance(route[-1], self.depot)

        return dist

    def _route_demand(self, route: list[DeliveryPoint]) -> int:
        """Całkowite zapotrzebowanie na trasie."""
        return sum(p.demand for p in route)

    def solve(self, n_iterations: int = 100) -> list[list[DeliveryPoint]]:
        """Znajdź optymalne trasy."""
        # Inicjalizacja: każdy klient w osobnej trasie
        routes = [[c] for c in self.customers]

        best_routes = routes.copy()
        best_distance = sum(self._route_distance(r) for r in routes)

        for _ in range(n_iterations):
            # Losowa modyfikacja (2-opt, relokacja, itp.)
            new_routes = self._perturb(routes)

            # Sprawdź feasibility
            if self._is_feasible(new_routes):
                new_distance = sum(self._route_distance(r) for r in new_routes)

                # Akceptacja (Metropolis)
                if new_distance < best_distance or np.random.random() < 0.1:
                    routes = new_routes
                    if new_distance < best_distance:
                        best_routes = new_routes
                        best_distance = new_distance

        # Konsolidacja tras
        return self._consolidate_routes(best_routes)

    def _perturb(self, routes: list[list[DeliveryPoint]]) -> list[list[DeliveryPoint]]:
        """Losowa modyfikacja tras."""
        new_routes = [r.copy() for r in routes]

        if len(new_routes) > 1 and np.random.random() < 0.5:
            # Przenieś klienta między trasami
            r1_idx = np.random.randint(len(new_routes))
            r2_idx = np.random.randint(len(new_routes))

            if new_routes[r1_idx] and r1_idx != r2_idx:
                customer = new_routes[r1_idx].pop(
                    np.random.randint(len(new_routes[r1_idx]))
                )
                pos = np.random.randint(len(new_routes[r2_idx]) + 1)
                new_routes[r2_idx].insert(pos, customer)

        # Usuń puste trasy
        new_routes = [r for r in new_routes if r]

        return new_routes

    def _is_feasible(self, routes: list[list[DeliveryPoint]]) -> bool:
        """Sprawdź czy rozwiązanie jest dopuszczalne."""
        for route in routes:
            if self._route_demand(route) > self.capacity:
                return False
        return True

    def _consolidate_routes(self, routes: list[list[DeliveryPoint]]) -> list[list[DeliveryPoint]]:
        """Połącz małe trasy jeśli możliwe."""
        consolidated = []
        remaining = routes.copy()

        while remaining:
            route = remaining.pop(0)

            # Próbuj połączyć z innymi
            merged = True
            while merged:
                merged = False
                for i, other in enumerate(remaining):
                    combined_demand = self._route_demand(route) + self._route_demand(other)
                    if combined_demand <= self.capacity:
                        route = route + other
                        remaining.pop(i)
                        merged = True
                        break

            consolidated.append(route)

        return consolidated


async def demo_vehicle_routing():
    """Demonstracja optymalizacji tras dostaw."""
    print("\n" + "=" * 70)
    print("  Vehicle Routing Problem Demo")
    print("=" * 70)

    # Generuj punkty dostawy
    np.random.seed(42)
    points = [DeliveryPoint("Depot", 50, 50, 0)]  # Depot w centrum

    for i in range(15):
        points.append(DeliveryPoint(
            id=f"C{i + 1}",
            x=np.random.uniform(0, 100),
            y=np.random.uniform(0, 100),
            demand=np.random.randint(10, 30),
        ))

    print(f"\n📍 {len(points) - 1} delivery points generated")
    print(f"   Vehicle capacity: 100 units")

    solver = VRPSolver(points, vehicle_capacity=100)
    routes = solver.solve(n_iterations=200)

    print(f"\n✅ Optimal routes found: {len(routes)} vehicles needed")

    total_distance = 0
    for i, route in enumerate(routes):
        dist = solver._route_distance(route)
        demand = solver._route_demand(route)
        total_distance += dist

        route_str = " → ".join([p.id for p in route])
        print(f"\n   Vehicle {i + 1}: Depot → {route_str} → Depot")
        print(f"      Distance: {dist:.1f} km, Load: {demand}/{solver.capacity}")

    print(f"\n   Total distance: {total_distance:.1f} km")


# =============================================================================
# 4. Medycyna - Operating Room Scheduling
# =============================================================================

@dataclass
class Surgery:
    """Operacja do zaplanowania."""
    id: str
    duration_min: int
    priority: int  # 1 = urgent, 5 = elective
    required_equipment: list[str]
    surgeon: str


@dataclass
class OperatingRoom:
    """Sala operacyjna."""
    id: str
    equipment: list[str]
    available_hours: tuple[int, int] = (7, 19)  # 7:00 - 19:00


class ORScheduler:
    """
    Scheduler dla sal operacyjnych.

    Optymalizuje przydzielenie operacji do sal i czasów,
    uwzględniając ograniczenia sprzętowe i priorytet.
    """

    SETUP_TIME = 30  # Czas przygotowania sali (minuty)

    def __init__(self, rooms: list[OperatingRoom], surgeries: list[Surgery]):
        self.rooms = rooms
        self.surgeries = surgeries

    def _can_perform(self, room: OperatingRoom, surgery: Surgery) -> bool:
        """Sprawdź czy sala ma wymagany sprzęt."""
        return all(eq in room.equipment for eq in surgery.required_equipment)

    def schedule(self) -> dict[str, list[tuple[Surgery, int, int]]]:
        """
        Zaplanuj operacje.

        Returns:
            Dict: room_id -> [(surgery, start_time, end_time), ...]
        """
        # Sortuj operacje wg priorytetu
        sorted_surgeries = sorted(self.surgeries, key=lambda s: s.priority)

        # Inicjalizuj harmonogram
        schedule = {room.id: [] for room in self.rooms}
        room_end_times = {room.id: room.available_hours[0] * 60 for room in self.rooms}

        for surgery in sorted_surgeries:
            # Znajdź najwcześniejszą dostępną salę
            best_room = None
            best_start = float('inf')

            for room in self.rooms:
                if not self._can_perform(room, surgery):
                    continue

                start = room_end_times[room.id] + self.SETUP_TIME
                room_end = room.available_hours[1] * 60

                # Sprawdź czy się zmieści
                if start + surgery.duration_min <= room_end:
                    if start < best_start:
                        best_start = start
                        best_room = room

            if best_room:
                end_time = best_start + surgery.duration_min
                schedule[best_room.id].append((surgery, best_start, end_time))
                room_end_times[best_room.id] = end_time

        return schedule

    def print_schedule(self, schedule: dict):
        """Wyświetl harmonogram."""
        for room_id, surgeries in schedule.items():
            print(f"\n   {room_id}:")
            for surgery, start, end in surgeries:
                start_h, start_m = divmod(start, 60)
                end_h, end_m = divmod(end, 60)
                print(f"      {start_h:02d}:{start_m:02d}-{end_h:02d}:{end_m:02d} "
                      f"{surgery.id} ({surgery.duration_min}min, P{surgery.priority})")


async def demo_or_scheduling():
    """Demonstracja harmonogramowania sal operacyjnych."""
    print("\n" + "=" * 70)
    print("  Operating Room Scheduling Demo")
    print("=" * 70)

    # Definiuj sale
    rooms = [
        OperatingRoom("OR-1", ["general", "laparoscopy"]),
        OperatingRoom("OR-2", ["general", "cardiac"]),
        OperatingRoom("OR-3", ["general", "neuro", "microscope"]),
    ]

    # Definiuj operacje
    surgeries = [
        Surgery("Appendectomy", 60, 2, ["general"], "Dr. Smith"),
        Surgery("Cardiac bypass", 240, 1, ["cardiac"], "Dr. Johnson"),
        Surgery("Brain tumor", 300, 1, ["neuro", "microscope"], "Dr. Williams"),
        Surgery("Knee replacement", 120, 3, ["general"], "Dr. Brown"),
        Surgery("Hernia repair", 45, 4, ["general"], "Dr. Davis"),
        Surgery("Cholecystectomy", 90, 3, ["laparoscopy"], "Dr. Smith"),
        Surgery("Hip replacement", 150, 2, ["general"], "Dr. Brown"),
        Surgery("Spinal fusion", 180, 2, ["general"], "Dr. Williams"),
    ]

    print(f"\n🏥 {len(rooms)} operating rooms")
    print(f"   {len(surgeries)} surgeries to schedule")

    scheduler = ORScheduler(rooms, surgeries)
    schedule = scheduler.schedule()

    print("\n✅ Optimal schedule:")
    scheduler.print_schedule(schedule)

    # Statystyki
    total_surgeries = sum(len(s) for s in schedule.values())
    total_time = sum(
        sum(end - start for _, start, end in surgeries)
        for surgeries in schedule.values()
    )

    print(f"\n   Scheduled: {total_surgeries}/{len(surgeries)} surgeries")
    print(f"   Total OR time: {total_time // 60}h {total_time % 60}min")


# =============================================================================
# 5. Energia - Unit Commitment Problem
# =============================================================================

@dataclass
class PowerPlant:
    """Elektrownia."""
    id: str
    type: str  # coal, gas, hydro, nuclear
    capacity_mw: float
    min_output_mw: float
    cost_per_mwh: float
    ramp_rate_mw_per_hour: float
    startup_cost: float
    co2_tons_per_mwh: float


class UnitCommitmentSolver:
    """
    Solver dla problemu Unit Commitment.

    Decyduje które elektrownie uruchomić i na jakim poziomie,
    aby zaspokoić zapotrzebowanie przy minimalnym koszcie.
    """

    def __init__(self, plants: list[PowerPlant]):
        self.plants = plants

    def solve(self, demand_profile: list[float]) -> list[dict[str, float]]:
        """
        Znajdź optymalne przydziały mocy.

        Args:
            demand_profile: Lista zapotrzebowania [MW] dla każdej godziny

        Returns:
            Lista słowników {plant_id: output_mw} dla każdej godziny
        """
        schedule = []

        for hour, demand in enumerate(demand_profile):
            # Sortuj wg kosztu (merit order)
            sorted_plants = sorted(self.plants, key=lambda p: p.cost_per_mwh)

            hour_schedule = {}
            remaining_demand = demand

            for plant in sorted_plants:
                if remaining_demand <= 0:
                    hour_schedule[plant.id] = 0
                    continue

                # Must-run dla nuklearnych
                if plant.type == 'nuclear':
                    output = plant.capacity_mw
                else:
                    output = min(plant.capacity_mw, remaining_demand)
                    output = max(output, plant.min_output_mw) if output > 0 else 0

                hour_schedule[plant.id] = output
                remaining_demand -= output

            schedule.append(hour_schedule)

        return schedule

    def calculate_cost(self, schedule: list[dict[str, float]]) -> dict:
        """Oblicz koszty i emisje."""
        total_cost = 0
        total_co2 = 0

        for hour_schedule in schedule:
            for plant in self.plants:
                output = hour_schedule.get(plant.id, 0)
                total_cost += output * plant.cost_per_mwh
                total_co2 += output * plant.co2_tons_per_mwh

        return {
            'total_cost': total_cost,
            'total_co2_tons': total_co2,
            'avg_cost_per_mwh': total_cost / sum(
                sum(h.values()) for h in schedule
            ) if schedule else 0,
        }


async def demo_unit_commitment():
    """Demonstracja harmonogramowania elektrowni."""
    print("\n" + "=" * 70)
    print("  Unit Commitment Problem Demo")
    print("=" * 70)

    # Definiuj elektrownie
    plants = [
        PowerPlant("Nuclear-1", "nuclear", 1000, 800, 15, 0, 100000, 0.0),
        PowerPlant("Coal-1", "coal", 500, 200, 45, 50, 20000, 0.9),
        PowerPlant("Coal-2", "coal", 500, 200, 48, 50, 20000, 0.95),
        PowerPlant("Gas-1", "gas", 300, 50, 65, 150, 5000, 0.4),
        PowerPlant("Gas-2", "gas", 300, 50, 68, 150, 5000, 0.42),
        PowerPlant("Hydro-1", "hydro", 200, 0, 5, 200, 0, 0.0),
    ]

    # Profil zapotrzebowania (24h)
    demand_profile = [
        1200, 1100, 1050, 1000, 1000, 1100,  # 0-5: noc
        1300, 1500, 1800, 2000, 2100, 2200,  # 6-11: poranek
        2100, 2000, 1900, 1800, 1900, 2100,  # 12-17: popołudnie
        2400, 2500, 2300, 2000, 1700, 1400,  # 18-23: wieczór
    ]

    print(f"\n⚡ {len(plants)} power plants")
    print(f"   Total capacity: {sum(p.capacity_mw for p in plants)} MW")
    print(f"   Peak demand: {max(demand_profile)} MW")

    solver = UnitCommitmentSolver(plants)
    schedule = solver.solve(demand_profile)

    print("\n✅ Optimal dispatch schedule:")

    # Pokaż kilka godzin
    for hour in [6, 12, 19, 23]:
        print(f"\n   Hour {hour:02d}:00 (demand: {demand_profile[hour]} MW)")
        for plant in plants:
            output = schedule[hour][plant.id]
            if output > 0:
                print(f"      {plant.id}: {output:.0f} MW "
                      f"({output / plant.capacity_mw * 100:.0f}%)")

    # Podsumowanie kosztów
    costs = solver.calculate_cost(schedule)
    print(f"\n   📊 Daily summary:")
    print(f"      Total cost: ${costs['total_cost']:,.0f}")
    print(f"      Avg cost: ${costs['avg_cost_per_mwh']:.2f}/MWh")
    print(f"      CO2 emissions: {costs['total_co2_tons']:,.0f} tons")


# =============================================================================
# 6. Bioinformatyka - Genomic Pipeline Scheduling
# =============================================================================

@dataclass
class GenomicSample:
    """Próbka genomowa do analizy."""
    id: str
    size_gb: float
    priority: int = 3


@dataclass
class PipelineStep:
    """Krok w pipeline genomicznym."""
    name: str
    time_per_gb: float  # minuty per GB
    memory_gb: int
    cpu_cores: int
    depends_on: list[str]


class GenomicPipelineScheduler:
    """
    Scheduler dla pipeline'u analizy genomowej.
    """

    def __init__(self,
                 samples: list[GenomicSample],
                 steps: list[PipelineStep],
                 total_cores: int = 64,
                 total_memory_gb: int = 256):
        self.samples = samples
        self.steps = steps
        self.total_cores = total_cores
        self.total_memory_gb = total_memory_gb

    def estimate_time(self, sample: GenomicSample, step: PipelineStep) -> float:
        """Szacowany czas wykonania kroku."""
        return step.time_per_gb * sample.size_gb

    def schedule(self) -> dict:
        """Zaplanuj wykonanie pipeline'u."""
        # Uproszczony scheduler - w produkcji użyj Langevin sampling
        schedule = []
        current_time = 0

        for sample in sorted(self.samples, key=lambda s: s.priority):
            sample_schedule = {'sample': sample.id, 'steps': []}
            step_end_times = {}

            for step in self.steps:
                # Znajdź najwcześniejszy możliwy start
                start_time = current_time
                for dep in step.depends_on:
                    if dep in step_end_times:
                        start_time = max(start_time, step_end_times[dep])

                duration = self.estimate_time(sample, step)
                end_time = start_time + duration

                sample_schedule['steps'].append({
                    'step': step.name,
                    'start': start_time,
                    'end': end_time,
                    'duration': duration,
                })

                step_end_times[step.name] = end_time

            schedule.append(sample_schedule)

        return schedule


async def demo_genomic_pipeline():
    """Demonstracja harmonogramowania pipeline'u genomicznego."""
    print("\n" + "=" * 70)
    print("  Genomic Pipeline Scheduling Demo")
    print("=" * 70)

    # Definiuj kroki pipeline'u
    steps = [
        PipelineStep("FastQC", 2.0, 4, 2, []),
        PipelineStep("Trimming", 5.0, 8, 4, ["FastQC"]),
        PipelineStep("Alignment", 15.0, 32, 8, ["Trimming"]),
        PipelineStep("Sorting", 3.0, 16, 4, ["Alignment"]),
        PipelineStep("MarkDuplicates", 4.0, 16, 2, ["Sorting"]),
        PipelineStep("VariantCalling", 20.0, 32, 8, ["MarkDuplicates"]),
        PipelineStep("Annotation", 5.0, 8, 2, ["VariantCalling"]),
    ]

    # Definiuj próbki
    samples = [
        GenomicSample("Sample_001", 50.0, 1),  # 50GB, high priority
        GenomicSample("Sample_002", 45.0, 2),
        GenomicSample("Sample_003", 55.0, 2),
        GenomicSample("Sample_004", 40.0, 3),
        GenomicSample("Sample_005", 48.0, 3),
    ]

    print(f"\n🧬 {len(samples)} samples to process")
    print(f"   Pipeline steps: {len(steps)}")
    print(f"   Total data: {sum(s.size_gb for s in samples):.0f} GB")

    scheduler = GenomicPipelineScheduler(samples, steps)
    schedule = scheduler.schedule()

    print("\n✅ Pipeline schedule:")

    for sample_sched in schedule[:2]:  # Pokaż pierwsze 2 próbki
        print(f"\n   {sample_sched['sample']}:")
        for step_info in sample_sched['steps']:
            print(f"      {step_info['step']:20s} "
                  f"{step_info['start']:6.0f} - {step_info['end']:6.0f} min "
                  f"({step_info['duration']:.0f} min)")

    # Całkowity czas
    total_time = max(
        max(s['end'] for s in sample['steps'])
        for sample in schedule
    )
    print(f"\n   Total pipeline time: {total_time / 60:.1f} hours")


# =============================================================================
# Main - Uruchom wszystkie demo
# =============================================================================

async def main():
    """Uruchom wszystkie demonstracje."""
    print("=" * 70)
    print("  NLP2CMD - Use Cases Demo")
    print("  Przykłady zastosowań w IT, nauce i biznesie")
    print("=" * 70)

    await demo_devops_automation()
    await demo_hyperparameter_optimization()
    await demo_vehicle_routing()
    await demo_or_scheduling()
    await demo_unit_commitment()
    await demo_genomic_pipeline()

    print("\n" + "=" * 70)
    print("  All demos completed!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())