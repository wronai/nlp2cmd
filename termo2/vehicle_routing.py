"""
Vehicle Routing Problem (VRP) solver.

This module implements a solver for the Vehicle Routing Problem (VRP)
using thermodynamic optimization principles.
"""

import numpy as np
from typing import List, Tuple, Optional, Dict, Any
from dataclasses import dataclass
import math
import random

from termo2.base_solver import BaseSolver


@dataclass
class DeliveryPoint:
    """Represents a delivery location."""
    
    id: str
    x: float
    y: float
    demand: int
    service_time_window: Tuple[int, int] = (8, 18)  # Start and end hours
    
    def distance_to(self, other: 'DeliveryPoint') -> float:
        """Calculate Euclidean distance to another point."""
        return math.sqrt((self.x - other.x)**2 + (self.y - other.y)**2)


@dataclass
class Vehicle:
    """Represents a delivery vehicle."""
    
    id: str
    capacity: int
    speed: float  # km/h
    cost_per_km: float
    max_route_time: int  # minutes


@dataclass
class Route:
    """Represents a delivery route."""
    
    id: str
    vehicle: Vehicle
    points: List[DeliveryPoint]
    total_demand: int
    total_distance: float
    total_time: float
    total_cost: float
    
    def is_feasible(self) -> bool:
        """Check if route is feasible."""
        return (self.total_demand <= self.vehicle.capacity and 
                self.total_time <= self.vehicle.max_route_time)


class VRPSolver(BaseSolver):
    """Vehicle Routing Problem solver using thermodynamic approach."""
    
    def __init__(self, points: List[DeliveryPoint], vehicles: List[Vehicle], 
                 depot: Optional[DeliveryPoint] = None):
        self.points = points
        self.vehicles = vehicles
        self.depot = depot or DeliveryPoint("depot", 0.0, 0.0, 0)
        self.best_solution = None
        self.solution_history = []
    
    def solve(self, n_iterations: int = 100) -> List[Route]:
        """Solve the VRP using thermodynamic optimization."""
        # Initialize with greedy solution
        current_solution = self._create_initial_solution()
        best_solution = current_solution.copy()
        best_energy = self._calculate_solution_energy(current_solution)
        
        temperature = 1.0
        cooling_rate = 0.995
        
        for iteration in range(n_iterations):
            # Generate neighbor solution
            neighbor_solution = self._generate_neighbor(current_solution)
            
            # Calculate energies
            current_energy = self._calculate_solution_energy(current_solution)
            neighbor_energy = self._calculate_solution_energy(neighbor_solution)
            
            # Accept or reject based on Metropolis criterion
            if self._should_accept_solution(current_energy, neighbor_energy, temperature):
                current_solution = neighbor_solution
                
                # Update best solution
                if neighbor_energy < best_energy:
                    best_solution = neighbor_solution.copy()
                    best_energy = neighbor_energy
            
            # Cool down
            temperature *= cooling_rate
            
            # Store in history
            self.solution_history.append({
                'iteration': iteration,
                'energy': current_energy,
                'temperature': temperature,
                'solution': current_solution.copy()
            })
        
        self.best_solution = best_solution
        return best_solution
    
    def _create_initial_solution(self) -> List[Route]:
        """Create initial solution using greedy algorithm."""
        unassigned_points = self.points.copy()
        routes = []
        
        for vehicle in self.vehicles:
            if not unassigned_points:
                break
            
            route = self._create_greedy_route(vehicle, unassigned_points)
            routes.append(route)
            
            # Remove assigned points
            for point in route.points[1:]:  # Skip depot
                if point in unassigned_points:
                    unassigned_points.remove(point)
        
        # Handle remaining points
        while unassigned_points:
            # Find best vehicle for remaining points
            best_vehicle = self._find_best_vehicle_for_points(unassigned_points)
            if not best_vehicle:
                break
            
            route = self._create_greedy_route(best_vehicle, unassigned_points)
            routes.append(route)
            
            # Remove assigned points
            for point in route.points[1:]:  # Skip depot
                if point in unassigned_points:
                    unassigned_points.remove(point)
        
        return routes
    
    def _create_greedy_route(self, vehicle: Vehicle, points: List[DeliveryPoint]) -> Route:
        """Create a greedy route for a vehicle."""
        if not points:
            return Route(
                id=f"route_{vehicle.id}",
                vehicle=vehicle,
                points=[self.depot] + points[:vehicle.capacity],
                total_demand=sum(p.demand for p in points),
                total_distance=self._calculate_route_distance([self.depot] + points[:vehicle.capacity]),
                total_time=self._calculate_route_time([self.depot] + points[:vehicle.capacity], vehicle),
                total_cost=self._calculate_route_cost([self.depot] + points[:vehicle.capacity], vehicle)
            )
        
        # Sort points by some heuristic (e.g., closest to depot first)
        sorted_points = sorted(points, key=lambda p: p.distance_to(self.depot))
        selected_points = [self.depot] + sorted_points[:vehicle.capacity]
        
        return Route(
            id=f"route_{vehicle.id}",
            vehicle=vehicle,
            points=selected_points,
            total_demand=sum(p.demand for p in selected_points),
            total_distance=self._calculate_route_distance(selected_points),
            total_time=self._calculate_route_time(selected_points, vehicle),
            total_cost=self._calculate_route_cost(selected_points, vehicle)
        )
    
    def _find_best_vehicle_for_points(self, points: List[DeliveryPoint]) -> Optional[Vehicle]:
        """Find the best vehicle for a set of points."""
        best_vehicle = None
        best_score = -float('inf')
        
        for vehicle in self.vehicles:
            if len(points) <= vehicle.capacity:
                # Calculate score based on efficiency
                distance = sum(p.distance_to(self.depot) for p in points)
                score = -distance / vehicle.speed  # Negative because we want to minimize
                
                if score > best_score:
                    best_score = score
                    best_vehicle = vehicle
        
        return best_vehicle
    
    def _generate_neighbor(self, current_solution: List[Route]) -> List[Route]:
        """Generate neighbor solution by applying local search operators."""
        new_solution = [route.copy() for route in current_solution]
        
        # Apply random local search operator
        operator = random.choice(['relocate_point', 'swap_points', 'merge_routes', 'split_route'])
        
        if operator == 'relocate_point' and len(new_solution) > 0:
            new_solution = self._relocate_point_operation(new_solution)
        elif operator == 'swap_points' and len(new_solution) > 1:
            new_solution = self._swap_points_operation(new_solution)
        elif operator == 'merge_routes' and len(new_solution) > 1:
            new_solution = self._merge_routes_operation(new_solution)
        elif operator == 'split_route' and len(new_solution) > 0:
            new_solution = self._split_route_operation(new_solution)
        
        return new_solution
    
    def _relocate_point_operation(self, routes: List[Route]) -> List[Route]:
        """Move a point from one route to another."""
        if len(routes) < 2:
            return routes
        
        # Select random routes
        route_idx1, route_idx2 = random.sample(range(len(routes)), 2)
        
        if route_idx1 == route_idx2:
            return routes
        
        route1, route2 = routes[route_idx1], routes[route_idx2]
        
        if len(route1.points) <= 1 or len(route2.points) <= 1:
            return routes
        
        # Select random point from route1
        point_to_move = random.choice(route1.points[1:])  # Skip depot
        new_route1 = Route(
            id=route1.id,
            vehicle=route1.vehicle,
            points=[route1.points[0]] + [p for p in route1.points[1:] if p != point_to_move],
            total_demand=route1.total_demand - point_to_move.demand,
            total_distance=route1.total_distance - self._calculate_point_distance(route1.points[-1], point_to_move),
            total_time=route1.total_time - self._calculate_point_time(route1.points[-1], point_to_move, route1.vehicle),
            total_cost=route1.total_cost - self._calculate_point_cost(route1.points[-1], point_to_move, route1.vehicle)
        )
        
        new_route2 = Route(
            id=route2.id,
            vehicle=route2.vehicle,
            points=route2.points + [point_to_move],
            total_demand=route2.total_demand + point_to_move.demand,
            total_distance=route2.total_distance + self._calculate_point_distance(route2.points[-1], point_to_move),
            total_time=route2.total_time + self._calculate_point_time(route2.points[-1], point_to_move, route2.vehicle),
            total_cost=route2.total_cost + self._calculate_point_cost(route2.points[-1], point_to_move, route2.vehicle)
        )
        
        routes[route_idx1] = new_route1
        routes[route_idx2] = new_route2
        
        return routes
    
    def _swap_points_operation(self, routes: List[Route]) -> List[Route]:
        """Swap points between two routes."""
        if len(routes) < 2:
            return routes
        
        route_idx1, route_idx2 = random.sample(range(len(routes)), 2)
        
        if route_idx1 == route_idx2:
            return routes
        
        route1, route2 = routes[route_idx1], routes[route_idx2]
        
        if len(route1.points) <= 1 or len(route2.points) <= 1:
            return routes
        
        # Select random points to swap
        point1 = random.choice(route1.points[1:])  # Skip depot
        point2 = random.choice(route2.points[1:])  # Skip depot
        
        # Swap points in routes
        new_route1_points = [route1.points[0]]  # Keep depot
        for p in route1.points[1:]:
            if p == point1:
                new_route1_points.append(point2)
            else:
                new_route1_points.append(p)
        
        new_route2_points = [route2.points[0]]  # Keep depot
        for p in route2.points[1:]:
            if p == point2:
                new_route2_points.append(point1)
            else:
                new_route2_points.append(p)
        
        # Update routes
        new_route1 = Route(
            id=route1.id,
            vehicle=route1.vehicle,
            points=new_route1_points,
            total_demand=route1.total_demand,
            total_distance=self._calculate_route_distance(new_route1_points),
            total_time=self._calculate_route_time(new_route1_points, route1.vehicle),
            total_cost=self._calculate_route_cost(new_route1_points, route1.vehicle)
        )
        
        new_route2 = Route(
            id=route2.id,
            vehicle=route2.vehicle,
            points=new_route2_points,
            total_demand=route2.total_demand,
            total_distance=self._calculate_route_distance(new_route2_points),
            total_time=self._calculate_route_time(new_route2_points, route2.vehicle),
            total_cost=self._calculate_route_cost(new_route2_points, route2.vehicle)
        )
        
        routes[route_idx1] = new_route1
        routes[route_idx2] = new_route2
        
        return routes
    
    def _merge_routes_operation(self, routes: List[Route]) -> List[Route]:
        """Merge two routes if feasible."""
        if len(routes) < 2:
            return routes
        
        # Find two routes that can be merged
        for i in range(len(routes)):
            for j in range(i + 1, len(routes)):
                route1, route2 = routes[i], routes[j]
                
                combined_demand = route1.total_demand + route2.total_demand
                
                if combined_demand <= route1.vehicle.capacity:
                    # Merge route2 into route1
                    merged_points = route1.points + route2.points[1:]  # Skip depot of route2
                    
                    new_route1 = Route(
                        id=route1.id,
                        vehicle=route1.vehicle,
                        points=merged_points,
                        total_demand=combined_demand,
                        total_distance=self._calculate_route_distance(merged_points),
                        total_time=self._calculate_route_time(merged_points, route1.vehicle),
                        total_cost=self._calculate_route_cost(merged_points, route1.vehicle)
                    )
                    
                    routes[i] = new_route1
                    routes.pop(j)
                    return routes
        
        return routes
    
    def _split_route_operation(self, routes: List[Route]) -> List[Route]:
        """Split a route if it has too many points."""
        if not routes:
            return routes
        
        # Find a route that can be split
        for i, route in enumerate(routes):
            if len(route.points) > 2 and route.total_demand > route.vehicle.capacity // 2:
                # Split route
                mid_point = len(route.points) // 2
                
                route1_points = route.points[:mid_point + 1]
                route2_points = [self.depot] + route.points[mid_point + 1:]
                
                route1 = Route(
                    id=f"{route.id}_1",
                    vehicle=route.vehicle,
                    points=route1_points,
                    total_demand=sum(p.demand for p in route1_points),
                    total_distance=self._calculate_route_distance(route1_points),
                    total_time=self._calculate_route_time(route1_points, route1.vehicle),
                    total_cost=self._calculate_route_cost(route1_points, route1.vehicle)
                )
                
                route2 = Route(
                    id=f"{route.id}_2",
                    vehicle=Vehicle(
                        id=f"{route.vehicle.id}_2",
                        capacity=route.vehicle.capacity // 2,
                        speed=route.vehicle.speed,
                        cost_per_km=route.vehicle.cost_per_km,
                        max_route_time=route.vehicle.max_route_time
                    ),
                    points=route2_points,
                    total_demand=sum(p.demand for p in route2_points),
                    total_distance=self._calculate_route_distance(route2_points),
                    total_time=self._calculate_route_time(route2_points, route2.vehicle),
                    total_cost=self._calculate_route_cost(route2_points, route2.vehicle)
                )
                
                routes[i] = route1
                routes.insert(i + 1, route2)
                return routes
        
        return routes
    
    def _calculate_solution_energy(self, solution: List[Route]) -> float:
        """Calculate energy of solution (lower is better)."""
        energy = 0.0
        
        # Penalty for unassigned points
        assigned_points = set()
        for route in solution:
            assigned_points.update(route.points)
        
        unassigned_points = set(self.points) - assigned_points
        energy += len(unassigned_points) * 100.0
        
        # Penalty for route violations
        for route in solution:
            if not route.is_feasible():
                energy += 1000.0
            
            # Penalty for long routes
            if route.total_distance > 100:
                energy += route.total_distance * 0.1
            
            # Penalty for underutilized vehicles
            utilization = route.total_demand / route.vehicle.capacity
            if utilization < 0.5:
                energy += (0.5 - utilization) * 50.0
        
        return energy
    
    def _should_accept_solution(self, current_energy: float, new_energy: float, temperature: float) -> bool:
        """Metropolis acceptance criterion."""
        if new_energy < current_energy:
            return True
        
        # Accept with some probability even if worse
        acceptance_prob = np.exp(-(new_energy - current_energy) / temperature)
        return np.random.random() < acceptance_prob
    
    def _calculate_route_distance(self, points: List[DeliveryPoint]) -> float:
        """Calculate total distance of route."""
        distance = 0.0
        for i in range(len(points) - 1):
            distance += points[i].distance_to(points[i + 1])
        return distance
    
    def _calculate_route_time(self, points: List[DeliveryPoint], vehicle: Vehicle) -> float:
        """Calculate total time for route."""
        distance = self._calculate_route_distance(points)
        return distance / vehicle.speed * 60  # Convert to minutes
    
    def _calculate_route_cost(self, points: List[DeliveryPoint], vehicle: Vehicle) -> float:
        """Calculate total cost for route."""
        distance = self._calculate_route_distance(points)
        return distance * vehicle.cost_per_km
    
    def _calculate_point_distance(self, point1: DeliveryPoint, point2: DeliveryPoint) -> float:
        """Calculate distance between two points."""
        return point1.distance_to(point2)
    
    def _calculate_point_time(self, point1: DeliveryPoint, point2: DeliveryPoint, vehicle: Vehicle) -> float:
        """Calculate time between two points."""
        distance = point1.distance_to(point2)
        return distance / vehicle.speed * 60  # Convert to minutes
    
    def _calculate_point_cost(self, point1: DeliveryPoint, point2: DeliveryPoint, vehicle: Vehicle) -> float:
        """Calculate cost between two points."""
        distance = point1.distance_to(point2)
        return distance * vehicle.cost_per_km


def demo_vehicle_routing():
    """Demonstrate vehicle routing optimization."""
    print("=== Vehicle Routing Demo ===")
    
    # Create delivery points
    points = [
        DeliveryPoint("p1", 10, 20, 5),
        DeliveryPoint("p2", 30, 15, 8),
        DeliveryPoint("p3", 50, 40, 3),
        DeliveryPoint("p4", 20, 50, 6),
        DeliveryPoint("p5", 60, 30, 4),
        DeliveryPoint("p6", 40, 10, 7),
        DeliveryPoint("p7", 70, 45, 2),
        DeliveryPoint("p8", 25, 35, 9),
    ]
    
    # Create vehicles
    vehicles = [
        Vehicle("v1", 20, 40, 0.5, 480),  # 20 capacity, 40 km/h, $0.5/km, 8 hours
        Vehicle("v2", 15, 50, 0.6, 360),  # 15 capacity, 50 km/h, $0.6/km, 6 hours
        Vehicle("v3", 25, 35, 0.4, 420),  # 25 capacity, 35 km/h, $0.4/km, 7 hours
    ]
    
    # Create solver
    solver = VRPSolver(points, vehicles)
    
    # Solve
    print("Solving vehicle routing problem...")
    solution = solver.solve(n_iterations=100)
    
    if solution:
        print(f"\nSolution found with {len(solution)} routes:")
        total_distance = sum(route.total_distance for route in solution)
        total_cost = sum(route.total_cost for route in solution)
        total_demand = sum(route.total_demand for route in solution)
        
        for route in solution:
            print(f"\n  Route {route.id}:")
            print(f"    Vehicle: {route.vehicle.id}")
            print(f"    Points: {len(route.points)}")
            print(f"    Demand: {route.total_demand}/{route.vehicle.capacity}")
            print(f"    Distance: {route.total_distance:.1f} km")
            print(f"    Time: {route.total_time:.1f} min")
            print(f"    Cost: ${route.total_cost:.2f}")
        
        print(f"\nTotal:")
        print(f"  Distance: {total_distance:.1f} km")
        print(f"  Cost: ${total_cost:.2f}")
        print(f"  Demand served: {total_demand}/{sum(v.capacity for v in vehicles)}")
        print(f"  Energy: {solver._calculate_solution_energy(solution):.2f}")
    else:
        print("No feasible solution found")


if __name__ == "__main__":
    demo_vehicle_routing()
