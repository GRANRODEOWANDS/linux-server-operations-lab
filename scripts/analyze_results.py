import subprocess
import re

inventory = "/home/controller/linux-server-operations-lab/inventory/hosts_generated.ini"

# Disk check
disk_result = subprocess.run(
    [
        "ansible",
        "servers",
        "-i",
        inventory,
        "-a",
        "df -P /"
    ],
    capture_output=True,
    text=True
)

disk_status = {}
current_host = None

for line in disk_result.stdout.splitlines():
    host_match = re.match(r"^(\S+) \|", line)

    if host_match:
        current_host = host_match.group(1)

        if "UNREACHABLE" in line:
            disk_status[current_host] = {
                "percent": None,
                "status": "UNREACHABLE"
            }

        elif "FAILED" in line:
            disk_status[current_host] = {
                "percent": None,
                "status": "FAILED"
            }

    disk_match = re.search(r"(\d+)%\s+/$", line)

    if disk_match and current_host:
        disk_percent = int(disk_match.group(1))

        if disk_percent >= 80:
            status = "WARNING"
        else:
            status = "OK"

        disk_status[current_host] = {
            "percent": disk_percent,
            "status": status
        }

# nginx check
nginx_result = subprocess.run(
    [
        "ansible",
        "servers",
        "-i",
        inventory,
        "-a",
        "systemctl is-active nginx"
    ],
    capture_output=True,
    text=True
)

nginx_status = {}
current_host = None

for line in nginx_result.stdout.splitlines():
    host_match = re.match(r"^(\S+) \|", line)

    if host_match:
        current_host = host_match.group(1)

        if "UNREACHABLE" in line:
            nginx_status[current_host] = "UNREACHABLE"

        elif "FAILED" in line:
            nginx_status[current_host] = "FAILED"

    if line.strip() == "active" and current_host:
        nginx_status[current_host] = "OK"

# Final result
hosts = set(disk_status.keys()) | set(nginx_status.keys())

for host in sorted(hosts):
    disk = disk_status.get(
        host,
        {"percent": None, "status": "FAILED"}
    )

    nginx = nginx_status.get(host, "FAILED")

    if disk["status"] == "UNREACHABLE" or nginx == "UNREACHABLE":
        final = "UNREACHABLE"

    elif disk["status"] == "FAILED" or nginx == "FAILED":
        final = "FAILED"

    elif disk["status"] == "WARNING":
        final = "WARNING"

    else:
        final = "OK"

    disk_display = (
        f'{disk["percent"]}%'
        if disk["percent"] is not None
        else "-"
    )

    print(
        f"{host} "
        f"Disk={disk_display} "
        f"nginx={nginx} "
        f"Result={final}"
    )
