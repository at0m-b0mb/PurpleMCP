# PurpleMCP-Bench — guardrail effectiveness

- generated: `2026-06-05T15:54:12+00:00`
- purplemcp: `0.5.0` · python `3.13.12` · macOS-26.6-arm64-arm-64bit-Mach-O
- **guardrail effectiveness: 15/15 (100.0%)** — exploitable on the vulnerable server, blocked on the twin

| # | Attack | OWASP-LLM | CWE | Vulnerable | Hardened | Fixed |
| --- | --- | --- | --- | --- | --- | :---: |
| 03 | Command Injection | LLM05:2025 Improper Output Handling | CWE-78 | EXPLOITED — data leaked | BLOCKED | ✅ |
| 04 | Path Traversal | LLM05:2025 Improper Output Handling | CWE-22 | EXPLOITED — data leaked | BLOCKED | ✅ |
| 05 | Server-Side Request Forgery | LLM06:2025 Excessive Agency | CWE-918 | EXPOSED — no guardrail | BLOCKED | ✅ |
| 06 | Token Theft / Confused Deputy | LLM02:2025 Sensitive Information Disclosure | CWE-522 | EXPLOITED — data leaked | BLOCKED | ✅ |
| 09 | Data Exfiltration | LLM02:2025 Sensitive Information Disclosure | CWE-200 | EXPOSED — no guardrail | BLOCKED | ✅ |
| 10 | SQL Injection | LLM05:2025 Improper Output Handling | CWE-89 | EXPLOITED — data leaked | BLOCKED | ✅ |
| 11 | Template / Format-String Injection | LLM05:2025 Improper Output Handling | CWE-1336 | EXPLOITED — data leaked | BLOCKED | ✅ |
| 13 | Insecure Deserialization | LLM05:2025 Improper Output Handling | CWE-502 | EXPLOITED — data leaked | BLOCKED | ✅ |
| 14 | Broken Access Control (IDOR) | LLM06:2025 Excessive Agency | CWE-639 | EXPLOITED — data leaked | BLOCKED | ✅ |
| 15 | Unrestricted File Write | LLM05:2025 Improper Output Handling | CWE-73 | EXPOSED — no guardrail | BLOCKED | ✅ |
| 17 | Output / Log Injection | LLM05:2025 Improper Output Handling | CWE-117 | EXPLOITED — data leaked | BLOCKED | ✅ |
| 18 | Eval / Expression Injection | LLM05:2025 Improper Output Handling | CWE-95 | EXPLOITED — data leaked | BLOCKED | ✅ |
| 19 | Zip Slip / Archive Traversal | LLM05:2025 Improper Output Handling | CWE-22 | EXPOSED — no guardrail | BLOCKED | ✅ |
| 20 | Mass Assignment / Privilege Escalation | LLM06:2025 Excessive Agency | CWE-915 | EXPLOITED — data leaked | BLOCKED | ✅ |
| 21 | CSV / Formula Injection | LLM05:2025 Improper Output Handling | CWE-1236 | EXPLOITED — data leaked | BLOCKED | ✅ |
