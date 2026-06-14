Markdown
# NetBox & MikroTik Infrastructure Automation Toolkit

A Python-based automation pipeline designed to manage, secure, and standardize MikroTik RouterOS devices. This script integrates with NetBox as a Source of Truth (SoT) to dynamically discover active network infrastructure, perform state preservation (backups), and actively remediate security vulnerabilities.

##  Key Features

* **NetBox Integration:** Dynamically queries your NetBox API for devices with the `router` role and `active` status, ensuring the automation pipeline only targets currently deployed hardware.
* **State Preservation (Automated Backups):** Connects via SSH to generate and download timestamped `.rsc` configuration backups locally before any changes are made.
* **Active Security Remediation:** Audits running services and automatically disables insecure management protocols (Telnet, FTP) if they are found active.
* **Baseline Standardization:** Detects configuration drift and enforces global standards for core infrastructure services (DNS and NTP).
* **Secure Credential Management:** Utilizes environment variables (`.env`) to ensure API tokens and SSH passwords are never hardcoded or tracked in version control.

## Prerequisites

* Python 3.8 or higher
* Network access to the NetBox API and SSH access (Port 22) to the target routers.
* A NetBox API Token with read permissions.

##  Installation

1. **Clone the repository:**
```bash
   git clone [https://github.com/yourusername/your-repo-name.git](https://github.com/yourusername/your-repo-name.git)
   cd your-repo-name
```
2. **Create a virtual environment (Recommended):**

```bash
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
```
3. **Install required dependencies:**

```bash
pip install pynetbox netmiko python-dotenv
```
##  Configuration
This project uses python-dotenv to manage secrets. Do not commit your .env file to version control.

Create a file named .env in the root directory of the project.

Add your environmental variables as follows:
```bash
Code snippet
NETBOX_URL="[https://netbox.yourdomain.com](https://netbox.yourdomain.com)"
NETBOX_TOKEN="your_netbox_api_token"
ROUTER_USER="your_admin_username"
ROUTER_PASSWORD="your_secure_password"
```


## Usage
Once your environment variables are configured, run the pipeline execution script:

```bash
python main.py
```

**Expected Output Process:**
1. Discovery: Connects to NetBox and compiles a list of active targets.

2. Authentication: Establishes an SSH connection to each target via Netmiko.

3. Backup: Generates a timestamped config file in the local ./router_backups/ directory.

4. Audit: Checks for and disables Telnet/FTP.

5. Standardization: Validates and corrects DNS (1.1.1.1,8.8.8.8) and NTP (pool.ntp.org) settings.

## Project Structure
```text
.
├── main.py               # Core automation script
├── .env                  # Environment variables (DO NOT COMMIT)
├── .gitignore            # Git ignore definitions
├── README.md             # Project documentation
└── router_backups/       # Auto-generated directory for config backups
```
## ⚠️ Disclaimer
This script performs active configuration changes on network equipment. It is highly recommended to run and test this code in a staging environment before deploying it against production infrastructure.
