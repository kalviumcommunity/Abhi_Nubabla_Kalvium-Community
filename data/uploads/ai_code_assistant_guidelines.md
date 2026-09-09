# Section 8.0: Artificial Intelligence & Automated Code Assistant Policy

## 1. Overview & Authorized Tooling
This policy establishes the compliance, confidentiality, and data safety standards for engineers utilizing Artificial Intelligence (AI) coding tools and Large Language Models. 
All engineering staff must obtain explicit approval from the IT Security Directorate prior to connecting IDE-based code completion plugins to company repositories. 
Authorized tools currently include approved enterprise AI pairing environments configured with strict zero-data-retention (ZDR) agreements.

## 2. Mandatory Sensitive Data Exclusion
Engineers are strictly prohibited from transmitting any of the following artifacts into external AI completion prompts:
- Production database credentials, cryptographic keys, and API tokens.
- Personally Identifiable Information (PII) including customer names, emails, and payroll records.
- Unreleased patent materials and proprietary core algorithmic trade secrets.
All code submitted for completion must utilize mock parameters and sanitized test fixtures.

## 3. Code Verification & Licensing Audits
AI-generated code snippets are not exempt from standard unit testing, linting, and peer code reviews.
Every pull request containing AI-assisted code must be tagged with `#ai-generated` in the pull request description.
Engineers must verify that suggestions do not reproduce copyleft or GPL-licensed third-party intellectual property without proper attribution.
