from datetime import time, datetime

# Status constants for consistency
STATUS_AT_HUB = "at the hub"
STATUS_EN_ROUTE = "en route"
STATUS_DELIVERED = "delivered"
STATUS_DELAYED = "Delayed - En Route from 09:05 AM"


class Package:
    def __init__(
        self,
        PackageID,
        Address,
        City,
        State,
        Zip,
        Deadline,
        Weight,
        Notes,
        Status=STATUS_AT_HUB,
        Time=None,  # Use None instead of "N/A"
        corrected_address=None,
    ):
        self.PackageID = PackageID
        self.Address = Address
        self.City = City
        self.State = State
        self.Zip = Zip
        self.Deadline = Deadline
        self.Weight = Weight
        self.Notes = Notes
        self.Status = Status
        self.Time = Time  # datetime.time object or None
        self.corrected_address = corrected_address  # For special cases like package 9

    def update_time(self, new_time):
        # Accepts either a datetime.time or a string "HH:MM", or None
        if isinstance(new_time, str):
            try:
                self.Time = datetime.strptime(new_time, "%H:%M").time()
            except Exception:
                self.Time = None
        elif isinstance(new_time, time) or new_time is None:
            self.Time = new_time
        else:
            self.Time = None

    def update_status(self, new_status):
        self.Status = new_status

    def get_current_address(self, current_time):
        # Return corrected address if after 10:20 AM and package 9
        if self.PackageID == 9 and self.corrected_address:
            cutoff = time(10, 20)
            if current_time >= cutoff:
                return self.corrected_address
        return self.Address

    def __str__(self, current_time=None):
        display_address = self.Address
        if current_time:
            display_address = self.get_current_address(current_time)

        # Format Time nicely or show "N/A"
        if self.Time is None:
            time_str = "N/A"
        else:
            time_str = self.Time.strftime("%H:%M")

        if self.Status == STATUS_DELIVERED:
            status_time_str = f"Delivered at: {time_str}"
        elif self.Status in (STATUS_EN_ROUTE, STATUS_DELAYED):
            status_time_str = f"Scheduled for: {time_str}"
        else:
            status_time_str = "Time: N/A"

        return (
            f"ID: {self.PackageID} | Address: {display_address} | City: {self.City} | State: {self.State} | Zip: {self.Zip} | "
            f"Deadline: {self.Deadline} | Status: {self.Status} | {status_time_str} | Notes: {self.Notes} | Weight: {self.Weight}"
        )

    def print_details(self, current_time=None):
        print(self.__str__(current_time))
