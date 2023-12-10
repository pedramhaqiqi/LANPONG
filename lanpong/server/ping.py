import subprocess
import re

class Ping:
    # Maximum size for the ping result cache
    MAX_CACHE_SIZE = 100

    def __init__(self, ip) -> None:
        """
        Initialize a Ping object with an IP address and an empty cache.

        Parameters:
        - ip: IP address to ping.
        """
        self._cache = []  # List to store ping results
        self.ip = ip  # IP address to ping

    def get(self):
        """
        Get the average ping time for the specified IP address.

        Returns:
        - Average ping time rounded to 3 decimal places.
        """
        self.get_ping(self.ip)
        average = sum(self._cache) / len(self._cache)
        return round(average, 3)

    def get_ping(self, ip_address):
        """
        Perform a single ping to the specified IP address and update the cache.

        Parameters:
        - ip_address: IP address to ping.
        """
        command = ["ping", "-c", "1", ip_address]
        process = subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        stdout, stderr = process.communicate()

        if process.returncode == 0:
            # Regex to extract the time from the output
            match = re.search(r"time=(\d+\.?\d*)\s*ms", stdout.decode())
            if match:
                if len(self._cache) > self.MAX_CACHE_SIZE:
                    # If the cache exceeds the maximum size, remove the oldest entry
                    self._cache.pop(0)
                # Add the ping time to the cache
                self._cache.append(float(match.group(1)))
        else:
            # Print an error message if the ping was not successful
            print(f"Error pinging {ip_address}: {stderr}")
            return None

