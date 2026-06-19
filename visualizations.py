# visualizations.py
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import List, Dict, Tuple

import matplotlib.pyplot as plt


@dataclass
class TruckVizData:
    truck_id: int
    route_package_ids: List[int]
    cumulative_miles: List[float]
    total_miles: float


def ensure_output_dir(path: str = "output") -> str:
    os.makedirs(path, exist_ok=True)
    return path


def save_mileage_by_truck(truck_totals: Dict[int, float], out_dir: str) -> str:
    # Visualization 1: Bar chart (Mileage per truck)
    truck_ids = list(truck_totals.keys())
    miles = [truck_totals[t] for t in truck_ids]

    plt.figure()
    plt.bar(truck_ids, miles)
    plt.title("Mileage by Truck")
    plt.xlabel("Truck ID")
    plt.ylabel("Miles Traveled")
    out_path = os.path.join(out_dir, "viz_mileage_by_truck.png")
    plt.savefig(out_path, bbox_inches="tight")
    plt.close()
    return out_path


def save_route_progress_line(viz: TruckVizData, out_dir: str) -> str:
    # Visualization 2: Line plot (Cumulative miles over delivery stops)
    stops = list(range(1, len(viz.cumulative_miles) + 1))

    plt.figure()
    plt.plot(stops, viz.cumulative_miles, marker="o")
    plt.title(f"Truck {viz.truck_id} Route Progress (Cumulative Miles)")
    plt.xlabel("Stop Number")
    plt.ylabel("Cumulative Miles")
    out_path = os.path.join(out_dir, f"viz_truck_{viz.truck_id}_route_progress.png")
    plt.savefig(out_path, bbox_inches="tight")
    plt.close()
    return out_path


def save_baseline_vs_optimized(baseline_total: float, optimized_total: float, out_dir: str) -> str:
    # Visualization 3: Comparison chart (Baseline vs Optimized)
    labels = ["Baseline", "Optimized"]
    values = [baseline_total, optimized_total]

    plt.figure()
    plt.bar(labels, values)
    plt.title("Baseline vs Optimized Total Mileage")
    plt.xlabel("Routing Approach")
    plt.ylabel("Total Miles")
    out_path = os.path.join(out_dir, "viz_baseline_vs_optimized.png")
    plt.savefig(out_path, bbox_inches="tight")
    plt.close()
    return out_path
