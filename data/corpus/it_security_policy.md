# Section 8.1: Corporate IT Security & Incident Response Protocols

## 1. Password & Access Control Standards
All internal systems require compliance with strict authentication safeguards. Passwords must contain a minimum of 14 characters including uppercase letters, numbers, and symbols. Passwords expire every 90 days and cannot match any of the previous 5 passwords used. Multi-Factor Authentication (MFA) via an approved authenticator app is mandatory on all corporate single sign-on (SSO) portals. SMS-based MFA is strictly prohibited due to SIM-swapping vulnerabilities.

## 2. Workstation Security & Encryption
All employee endpoints must have FileVault (macOS) or BitLocker (Windows) full-disk encryption enabled prior to accessing internal resources. USB storage drives are blocked by administrative group policy unless an exception ticket is authorized by the CISO. Operating system security updates and antivirus definitions are pushed automatically each Tuesday at 02:00 UTC and must not be bypassed or postponed beyond 48 hours.

## 3. Security Incident Classification & Severity Levels
Security incidents are classified into four severity tiers:
- **Severity 1 (Critical)**: Active data breach, ransomware deployment, or unauthorized administrative privilege escalation. Incident Commander must be notified within 15 minutes.
- **Severity 2 (High)**: Compromised employee credential, malware detected on internal host, or unauthenticated API exposure. Response required within 1 hour.
- **Severity 3 (Medium)**: Targeted phishing attempt reported by employee or failed brute-force attempt against internal portal. Response required within 4 business hours.
- **Severity 4 (Low)**: Routine port scanning or spam email delivery. Logged and reviewed during weekly triage.

## 4. Employee Incident Reporting Procedure
If you suspect an active security compromise, credential theft, or phishing email:
1. Immediately disconnect your machine from the network (unplug Ethernet or turn off Wi-Fi).
2. Do not power off or reboot the computer, as volatile RAM evidence must be preserved for forensic analysis.
3. Call the 24/7 IT Security Hotline at extension 4357 (HELP) or alert the `#security-incident` Slack channel using a secondary mobile device.
4. Provide the time of occurrence, observed system symptoms, and suspicious email headers or files involved.

