class Truck:
    def __init__(self, truck_id, location=0, mileage=0.0, packages=None):
        self.id = truck_id
        self.location = location  # using address ID to track location
        self.mileage = mileage
        self.packages = set(packages) if packages else set()  # store package IDs on this truck

    def add_package(self, package_id):
        # Add a package to this truck's load
        self.packages.add(package_id)

    def __str__(self):
        # Nicely format truck info for printing/debugging
        return f"Truck {self.id}: Location {self.location}, Mileage {self.mileage:.2f}, Packages {sorted(self.packages)}"
