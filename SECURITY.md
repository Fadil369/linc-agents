Security Policy
Supported Versions
We regularly maintain and update the main branch. Please ensure you are using the latest release for security updates and bug fixes.

Version	Supported
main	✔️
others	❌
Reporting a Vulnerability
If you discover a security vulnerability in this repository, please follow these steps:

Do not create public issues or pull requests that detail the vulnerability.
Contact us privately at [security@brainsait.io] or via GitHub Security Advisories.
Include as much detail as possible:
Type of vulnerability (e.g., authentication, data leak, etc.)
Steps to reproduce
Potential impact
Suggested remediation, if possible
We will respond within 5 business days and work with you to resolve the issue promptly.

Security Best Practices
No hardcoded secrets: All credentials and sensitive information must be stored in environment variables (.env).
Dependencies: We use Dependabot for automated dependency updates.
Code review: All code is reviewed for security risks, especially access control and data handling.
Data protection: Sensitive data is encrypted when stored or transmitted.
FastAPI: Security middleware and authentication (e.g., OAuth2) are enabled for all APIs.
Disclosure Policy
Please report vulnerabilities privately as described above.
We will acknowledge your report and keep you informed of progress.
Once resolved, users will be notified via release notes.
Additional Resources
CONTRIBUTING.md
GitHub Security Advisories
