# Delivery Route Optimizer

A delivery route optimization system that uses greedy nearest-neighbor and 2-opt algorithms to minimize total mileage across multiple delivery trucks while meeting package deadlines and constraints.

## Features
- Greedy nearest-neighbor routing algorithm for initial route generation
- 2-opt local search optimization to further reduce total mileage
- Custom chaining hash table implementation for O(1) average package lookups
- Real-time package status tracking (at hub, en route, delivered)
- Special constraint handling (deadlines, delayed packages, address corrections)
- Interactive dashboard showing optimized vs baseline mileage
- Data visualizations (mileage by truck, route progress, baseline vs optimized comparison)
- Logging system for tracking dashboard activity

## Results
- Baseline total mileage: 216.1 miles
- Optimized total mileage: 88.0 miles
- Mileage reduction: ~59%

## Tech Stack
- Python
- matplotlib (data visualizations)
- CSV data handling

## Project Structure

```
delivery_route_optimizer/
├── main.py                 # Main application - routing logic and dashboard
├── package.py              # Package class with status tracking
├── packagehashtable.py     # Custom chaining hash table implementation
├── truck.py                # Truck class
├── visualizations.py       # Matplotlib chart generation
├── packages.csv            # Package data
├── addresses.csv           # Address data
└── distances.csv           # Distance matrix
```

## Algorithms
- **Nearest Neighbor (Greedy)** — builds an initial route by always delivering to the closest unvisited address
- **2-opt** — improves the route by swapping pairs of edges to eliminate crossings and reduce total distance
