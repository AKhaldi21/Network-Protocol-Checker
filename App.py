import os
import sys
import datetime
import pynetbox
from netmiko import ConnectHandler
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

# --- CONFIGURATION BASELINES ---
NETBOX_URL = os.getenv("NETBOX_URL")
NETBOX_TOKEN = os.getenv("NETBOX_TOKEN")
ROUTER_USER = os.getenv("ROUTER_USER")
ROUTER_PASSWORD = os.getenv("ROUTER_PASSWORD")
BACKUP_DIR = "router_backups"

STANDARD_DNS = "1.1.1.1,8.8.8.8"
STANDARD_NTP = "pool.ntp.org"

# Ensure all critical credentials are loaded before proceeding
if not all([NETBOX_URL, NETBOX_TOKEN, ROUTER_USER, ROUTER_PASSWORD]):
    print("[ERROR] Missing required credentials. Please check your .env file.")
    sys.exit(1)

if not os.path.exists(BACKUP_DIR):
    os.makedirs(BACKUP_DIR)

print("Step 1: Querying NetBox for active routers...\n")
try:
    nb = pynetbox.api(NETBOX_URL, token=NETBOX_TOKEN)
    devices = nb.dcim.devices.filter(role="router", status="active")
except Exception as e:
    print(f"[ERROR] Critical Error connecting to NetBox API: {e}")
    sys.exit(1)

if not devices:
    print("No active routers found in NetBox.")
    sys.exit(0)

# --- AUTOMATION PIPELINE LOOP ---
for device in devices:
    device_name = device.name
    mgmt_ip = str(device.primary_ip4).split('/')[0] if device.primary_ip4 else None
    
    if not mgmt_ip:
        print(f"[WARNING] Skipping {device_name}: No Primary IPv4 address assigned in NetBox.")
        continue

    print(f"Target: {device_name} ({mgmt_ip})")

    device_params = {
        "device_type": "mikrotik_routeros",
        "host": mgmt_ip,
        "username": ROUTER_USER,
        "password": ROUTER_PASSWORD,
        "port": 22,
        "fast_cli": False,
    }

    try:
        ssh = ConnectHandler(**device_params)
        print(f"  SSH Authentication successful for {device_name}!")

        # --- PHASE 1: STATE PRESERVATION (BACKUP) ---
        print("  Generating configuration backup...")
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"{BACKUP_DIR}/{device_name}_{timestamp}.rsc"
        
        raw_config = ssh.send_command("/export")
        with open(backup_filename, "w") as backup_file:
            backup_file.write(raw_config)
        print(f"  Backup saved to {backup_filename}")

        # --- PHASE 2: ACTIVE SECURITY REMEDIATION ---
        print("  Running security compliance audit...")
        
        telnet_active = ssh.send_command('/ip service print count-only where name="telnet" disabled=no')
        if "1" in telnet_active:
            print("    [AUDIT WARNING] Insecure service [Telnet] is actively running!")
            print("    [REMEDIATION] Disabling Telnet service via explicit selector...")
            ssh.send_command('/ip service disable [find name="telnet"]')
        else:
            print("    [OK] Telnet service is fully disabled.")

        ftp_active = ssh.send_command('/ip service print count-only where name="ftp" disabled=no')
        if "1" in ftp_active:
            print("    [AUDIT WARNING] Insecure service [FTP] is actively running!")
            print("    [REMEDIATION] Disabling FTP service via explicit selector...")
            ssh.send_command('/ip service disable [find name="ftp"]')
        else:
            print("    [OK] FTP service is fully disabled.")

        # --- PHASE 3: GLOBAL BASELINE STANDARDIZATION ---
        print("  Running System Baseline Standardization...")
        
        dns_output = ssh.send_command("/ip dns print")
        if any(server in dns_output for server in STANDARD_DNS.split(',')):
            print("    [OK] DNS Compliance: Primary servers match structural targets.")
        else:
            print(f"    [DRIFT] DNS Configuration Drift: Aligning servers to {STANDARD_DNS}...")
            ssh.send_command(f"/ip dns set servers={STANDARD_DNS}")

        ntp_output = ssh.send_command("/system ntp client print")
        if "enabled: yes" in ntp_output or "enabled: true" in ntp_output:
            print("    [OK] NTP Compliance: Network Time Protocol daemon is operational.")
        else:
            print(f"    [DRIFT] NTP Configuration Drift: Enabling network clock synchronization via {STANDARD_NTP}...")
            ssh.send_command("/system ntp client set enabled=yes")
            ssh.send_command(f"/system ntp client servers add address={STANDARD_NTP}")

        ssh.disconnect()
        print("-" * 50)

    except Exception as e:
        print(f"[ERROR] Automation Error for {device_name}: {e}")
        print("-" * 50)
        continue

print("\nAll automation pipelines completed successfully!")