# Paul Miller
# 011466892
# 06/9/2025

import logging
from visualizations import (
    ensure_output_dir,
    TruckVizData,
    save_mileage_by_truck,
    save_route_progress_line,
    save_baseline_vs_optimized,
)
import csv
from datetime import time, datetime
from truck import Truck
from package import Package
from packagehashtable import ChainingHashTable

# --- Constants ---
STATUS_AT_HUB = "at the hub"
STATUS_EN_ROUTE = "en route"
STATUS_DELIVERED = "delivered"
STATUS_DELAYED_NOTE = "Delayed - En Route from 09:05 AM"

# --- Optimization Toggle ---
USE_TWO_OPT = True
TWO_OPT_APPLIED = False

# --- Data Storage ---
pHash = ChainingHashTable()
address_list = []
distance_list = []

# Initialize trucks with package IDs
truck1 = Truck(1, packages=[14, 15, 16, 34, 20, 21, 13, 39, 4, 40, 19, 27, 35, 12, 23, 11])
truck2 = Truck(2, packages=[6, 31, 32, 25, 26, 3, 18, 36, 38, 28, 9, 10, 2, 33, 17, 22])
truck3 = Truck(3, packages=[37, 5, 30, 8, 7, 29, 1, 24])

# Truck departure times (HH:MM)
truck_departure_times = {
    1: time(8, 0),
    2: time(9, 15),
    3: time(8, 0),
}

# Global flag to ensure routes and delivery times are computed once before reporting
routes_computed = False

# --- Load CSV Data ---
def load_addresses(filename):
    with open(filename) as f:
        reader = csv.reader(f)
        next(reader)
        for row in reader:
            address_list.append(row)

def load_distances(filename):
    with open(filename) as f:
        reader = csv.reader(f)
        next(reader)
        for row in reader:
            distance_list.append(row)

def load_packages(filename):
    with open(filename) as f:
        reader = csv.reader(f)
        next(reader)
        for row in reader:
            corrected_addr = "410 S State St" if int(row[0]) == 9 else None
            pkg = Package(
                PackageID=int(row[0]),
                Address=row[1],
                City=row[2],
                State=row[3],
                Zip=row[4],
                Deadline=row[5],
                Weight=row[6],
                Notes=row[7],
                Status=STATUS_AT_HUB,
                Time=None,  # Use None instead of "N/A"
                corrected_address=corrected_addr,
            )
            pHash.insert(pkg.PackageID, pkg)

# --- Address and Distance Helpers ---
def get_address_id_from_package_id(pkg_id):
    pkg = pHash.search(pkg_id)
    if not pkg:
        return None
    # Compare lowercase, strip spaces
    pkg_addr = pkg.Address.strip().lower()
    for addr in address_list:
        if addr[2].strip().lower() == pkg_addr:
            return int(addr[0])
    return None

def get_distance(a, b):
    try:
        dist = distance_list[a][b]
        if dist != '':
            return float(dist)
        else:
            return float(distance_list[b][a])
    except (IndexError, ValueError):
        return 0.0
def route_total_distance(route):
    """
    Total miles for a route of package IDs.
    Starts at HUB (0), visits each package destination in order, and returns to HUB.
    """
    if not route:
        return 0.0

    total = 0.0
    current = 0  # HUB address id
    for pkg_id in route:
        nxt = get_address_id_from_package_id(pkg_id)
        total += get_distance(current, nxt)
        current = nxt

    # return to HUB
    total += get_distance(current, 0)
    return total


def two_opt(route, max_passes=3):
    #2-opt improvement with a small pass limit to keep runtime fast.

    best = route[:]
    best_dist = route_total_distance(best)

    passes = 0
    improved = True

    while improved and passes < max_passes:
        improved = False
        passes += 1

        for i in range(0, len(best) - 1):
            for k in range(i + 1, len(best)):
                new_route = best[:]
                new_route[i:k + 1] = reversed(new_route[i:k + 1])

                new_dist = route_total_distance(new_route)
                if new_dist < best_dist:
                    best = new_route
                    best_dist = new_dist
                    improved = True

        # continue for another pass if we found improvements
    return best


# --- Route Planning ---
def nearest_neighbor_route(pkg_ids):
    remaining = pkg_ids.copy()
    route = []
    current_loc = 0
    while remaining:
        nearest = min(
            remaining,
            key=lambda pid: get_distance(current_loc, get_address_id_from_package_id(pid))
        )
        route.append(nearest)
        current_loc = get_address_id_from_package_id(nearest)
        remaining.remove(nearest)
    return route

def compute_route_data(truck, departure_minutes):
    global TWO_OPT_APPLIED

    route = nearest_neighbor_route(list(truck.packages))

    if USE_TWO_OPT:
        nn_dist = route_total_distance(route)
        candidate = two_opt(route)
        cand_dist = route_total_distance(candidate)

        if cand_dist < nn_dist:
            route = candidate
            TWO_OPT_APPLIED = True

    truck.route = route

    mileage_list, delivery_times = [], []
    total_m, location = 0.0, 0

    for pid in route:
        dest = get_address_id_from_package_id(pid)
        d = get_distance(location, dest)
        total_m += d
        mileage_list.append(total_m)
        location = dest

    last_m, current_min = 0.0, departure_minutes
    for m in mileage_list:
        travel_time = (m - last_m) / 0.3
        current_min += int(round(travel_time))
        h, mi = divmod(current_min, 60)
        delivery_times.append(f"{h:02}:{mi:02}")
        last_m = m

    truck.mileage = total_m
    return route, delivery_times

def toggle_two_opt():
    global USE_TWO_OPT, routes_computed
    USE_TWO_OPT = not USE_TWO_OPT
    routes_computed = False

    state = "ON" if USE_TWO_OPT else "OFF"
    print(f"\n2-opt optimization is now {state}. Routes will be recalculated.\n")

    logging.info("2-opt toggled %s", state)


def assign_times(truck, delivery_times):
    for pid, t_str in zip(truck.route, delivery_times):
        pkg = pHash.search(pid)
        if pkg:
            # Convert "HH:MM" string to time object
            try:
                t_obj = datetime.strptime(t_str, "%H:%M").time()
            except Exception:
                t_obj = None
            pkg.update_time(t_obj)

# --- Package Status Update ---
def update_package_status(pkg, now):
    delayed_packages = {6, 25, 28, 32}
    available_time = time(9, 5)  # Delayed packages ready at 9:05

    # Find truck departure time for package
    truck_depart = None
    for truck in [truck1, truck2, truck3]:
        if pkg.PackageID in truck.packages:
            truck_depart = truck_departure_times[truck.id]
            break
    if truck_depart is None:
        truck_depart = time(8, 0)

    delivery_time = pkg.Time if isinstance(pkg.Time, time) else None

    # Delayed package logic
    if pkg.PackageID in delayed_packages:
        if now < available_time:
            pkg.update_status(STATUS_DELAYED_NOTE)
            return
        elif now < truck_depart:
            pkg.update_status(STATUS_AT_HUB)
            return
        elif delivery_time and now < delivery_time:
            pkg.update_status(STATUS_EN_ROUTE)
            return
        elif delivery_time and now >= delivery_time:
            pkg.update_status(STATUS_DELIVERED)
            return

    # Regular package logic
    if now < truck_depart:
        pkg.update_status(STATUS_AT_HUB)
        pkg.update_time(None)
    elif delivery_time and now < delivery_time:
        pkg.update_status(STATUS_EN_ROUTE)
    elif delivery_time and now >= delivery_time:
        pkg.update_status(STATUS_DELIVERED)
    else:
        # No delivery time, assume en route after departure
        if now >= truck_depart:
            pkg.update_status(STATUS_EN_ROUTE)
        else:
            pkg.update_status(STATUS_AT_HUB)

# --- Display helpers ---
def print_package_details(pkg, current_time=None):
    print(pkg.__str__(current_time))

# --- Reporting ---
def compute_total_mileage():
    t3_last_dest = get_address_id_from_package_id(truck3.route[-1]) if truck3.route else 0
    return (
        truck1.mileage +
        truck2.mileage +
        truck3.mileage + get_distance(t3_last_dest, 0)
    )

def compute_baseline_total_mileage():
    def route_mileage_in_order(truck):
        total_m = 0.0
        loc = 0
        for pid in sorted(list(truck.packages)):
            dest = get_address_id_from_package_id(pid)
            d = get_distance(loc, dest)
            total_m += d
            loc = dest
        total_m += get_distance(loc, 0)
        return total_m

    return (
        route_mileage_in_order(truck1) +
        route_mileage_in_order(truck2) +
        route_mileage_in_order(truck3)
    )


def show_dashboard():
    global routes_computed
    if not routes_computed:
        compute_all_routes_and_times()

    total = compute_total_mileage()
    baseline = compute_baseline_total_mileage()

    print("\n=== WGUPS Routing Dashboard ===")
    algo = "Nearest Neighbor + 2-opt" if USE_TWO_OPT else "Nearest Neighbor only"
    applied = "YES" if TWO_OPT_APPLIED else "NO"
    print(f"2-opt improvement applied: {applied}")
    print(f"Routing algorithm: {algo}")
    print(f"Optimized total mileage: {total:.1f} miles")
    print(f"Baseline total mileage:  {baseline:.1f} miles")

    improvement = baseline - total
    if baseline > 0:
        pct = (improvement / baseline) * 100
        print(f"Improvement: {improvement:.1f} miles ({pct:.1f}%)")
    else:
        print("Improvement: N/A")

    print("\nPer-truck mileage:")
    show_truck_mileages()
    print("\nAccuracy metric used: total miles traveled (lower is better).")
    print("A typical efficiency target is <= 120 total miles for this dataset.\n")

    logging.info("Dashboard viewed: optimized=%.1f baseline=%.1f", total, baseline)

def compute_all_routes_and_times():
    global routes_computed, TWO_OPT_APPLIED
    TWO_OPT_APPLIED = False # reset once

    for truck in [truck1, truck2, truck3]:
        departure_minutes = (
            truck_departure_times[truck.id].hour * 60
            + truck_departure_times[truck.id].minute
        )
        route, times = compute_route_data(truck, departure_minutes)
        assign_times(truck, times)

    routes_computed = True


def show_all_statuses():
    global routes_computed
    # Ensure delivery times/routes are computed before showing statuses
    if not routes_computed:
        compute_all_routes_and_times()

    end_of_day = time(23, 59)
    print("ID | Address | Deadline | Status | Delivery Time | Notes | Weight")
    for pid in range(1, 41):
        pkg = pHash.search(pid)
        if pkg:
            update_package_status(pkg, end_of_day)
            print_package_details(pkg, end_of_day)
    print(f"\nTotal mileage: {compute_total_mileage():.1f} miles\n")

def show_single_package():
    try:
        pkg_id = int(input("Package ID: "))
        now = time.fromisoformat(input("Time (HH:MM): ") + ":00")
    except Exception:
        print("Invalid input.")
        return
    pkg = pHash.search(pkg_id)
    if pkg:
        update_package_status(pkg, now)
        print_package_details(pkg, now)
    else:
        print("Package not found.")

def show_statuses_in_window():
    try:
        start_str = input("Start time (HH:MM): ")
        end_str = input("End time (HH:MM): ")
        start_time = time.fromisoformat(start_str + ":00")
        end_time = time.fromisoformat(end_str + ":00")
    except Exception:
        print("Invalid time format.")
        return

    # Use midpoint for snapshot time to check statuses
    start_minutes = start_time.hour * 60 + start_time.minute
    end_minutes = end_time.hour * 60 + end_time.minute
    mid_minutes = (start_minutes + end_minutes) // 2
    mid_hour, mid_minute = divmod(mid_minutes, 60)
    snapshot_time = time(mid_hour, mid_minute)

    for truck in [truck1, truck2, truck3]:
        print(f"\n--- Truck {truck.id} package statuses at {snapshot_time.strftime('%H:%M')} ---")
        print("ID | Address | Deadline | Status | Delivery Time | Notes | Weight")
        for pid in truck.packages:
            pkg = pHash.search(pid)
            if pkg:
                update_package_status(pkg, snapshot_time)
                print_package_details(pkg, snapshot_time)
        print()

logging.basicConfig(
    filename="app.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)

def show_truck_mileages():
    global routes_computed

    if not routes_computed:
        compute_all_routes_and_times()
    t3_last = get_address_id_from_package_id(truck3.route[-1]) if truck3.route else 0
    print(f"Truck 1: {truck1.mileage:.1f} mi")
    print(f"Truck 2: {truck2.mileage:.1f} mi")
    print(f"Truck 3: {truck3.mileage + get_distance(t3_last, 0):.1f} mi")

def generate_visualizations():
    global routes_computed
    if not routes_computed:
        compute_all_routes_and_times()

    out_dir = ensure_output_dir("output")

    t3_last = get_address_id_from_package_id(truck3.route[-1]) if truck3.route else 0
    truck_totals = {
        1: truck1.mileage,
        2: truck2.mileage,
        3: truck3.mileage + get_distance(t3_last, 0),
    }

    # Visualization 1
    p1 = save_mileage_by_truck(truck_totals, out_dir)

    # Visualization 2
    def cumulative_from_route(truck):
        cum = []
        total_m = 0.0
        loc = 0
        for pid in truck.route:
            dest = get_address_id_from_package_id(pid)
            total_m += get_distance(loc, dest)
            cum.append(total_m)
            loc = dest
        return cum

    truck1_viz = TruckVizData(
        truck_id=1,
        route_package_ids=list(truck1.route),
        cumulative_miles=cumulative_from_route(truck1),
        total_miles=truck_totals[1],
    )
    p2 = save_route_progress_line(truck1_viz, out_dir)

    # Visualization 3
    baseline = compute_baseline_total_mileage()
    optimized = compute_total_mileage()
    p3 = save_baseline_vs_optimized(baseline, optimized, out_dir)

    print("\nVisualizations created:")
    print(f"- {p1}")
    print(f"- {p2}")
    print(f"- {p3}\n")

    logging.info("Visualizations generated: %s, %s, %s", p1, p2, p3)


# --- Main Menu ---
def menu():
    while True:
        print("\n1) All packages & mileage")
        print("2) Single package status")
        print("3) Package statuses on each truck at a time window")
        print("4) Truck mileages")
        print("5) Dashboard (summary + accuracy)")
        print("6) Generate visualizations (creates 3 PNG files)")
        print("7) Toggle 2-opt optimization ON/OFF")
        print("8) Exit")

        choice = input("Choice: ").strip()

        if choice == "1":
            show_all_statuses()
        elif choice == "2":
            show_single_package()
        elif choice == "3":
            show_statuses_in_window()
        elif choice == "4":
            show_truck_mileages()
        elif choice == "5":
            show_dashboard()
        elif choice == "6":
            generate_visualizations()
        elif choice == "7":
            toggle_two_opt()
        elif choice == "8":
            print("Goodbye!")
            break

    else:
            print("Invalid input. Try 1-8.")


# --- Initialization ---
load_addresses('addresses.csv')
load_distances('distances.csv')
load_packages('packages.csv')


if __name__ == "__main__":
    menu()
