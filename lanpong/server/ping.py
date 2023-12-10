import subprocess
import re


class Ping:
    def __init__(self, ip) -> None:
        self._cache = []
        self.ip = ip

    def get(self):
        self.get_ping(self.ip)
        average = sum(self._cache) / len(self._cache)
        return round(average, 3)

    def get_ping(self, ip_address):
        command = ["ping", "-c", "1", ip_address]
        process = subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        stdout, stderr = process.communicate()
        if process.returncode == 0:
            # Regex to extract the time from the output
            match = re.search(r"time=(\d+\.?\d*)\s*ms", stdout.decode())
            if match:
                if len(self._cache) > 100:
                    self._cache.pop(0)
                self._cache.append(float(match.group(1)))

        else:
            print(f"Error pinging {ip_address}: {stderr}")
            return None
