# Security Advisory

## Overview

This document outlines security vulnerabilities identified in the project dependencies and the remediation steps taken to address them.

## Vulnerabilities and Fixes

### Critical Severity

1. **python-jose algorithm confusion with OpenSSH ECDSA keys** (CVE-2023-48124)
   - **Affected Version**: python-jose 3.3.0
   - **Description**: Vulnerability in the ECDSA key handling that could lead to signature verification bypass.
   - **Mitigation**: While we've kept python-jose for now, we recommend migrating to PyJWT in the future. Added additional cryptography dependency with a secure version.

### High Severity

1. **Denial of service (DoS) via deformation `multipart/form-data` boundary** (CVE-2023-46136)
   - **Affected Version**: python-multipart 0.0.6
   - **Description**: Vulnerability that allows attackers to cause denial of service by manipulating form data boundaries.
   - **Mitigation**: Updated to python-multipart 0.0.7 which includes the fix.

2. **Starlette Denial of service (DoS) via multipart/form-data** (CVE-2023-45803)
   - **Affected Version**: starlette 0.26.1
   - **Description**: Vulnerability in multipart form data handling that could lead to denial of service.
   - **Mitigation**: Updated to starlette 0.36.3 which includes the fix.

3. **python-multipart vulnerable to Content-Type Header ReDoS** (CVE-2023-24816)
   - **Affected Version**: python-multipart 0.0.6
   - **Description**: Regular expression denial of service vulnerability in Content-Type header parsing.
   - **Mitigation**: Updated to python-multipart 0.0.7 which includes the fix.

### Moderate Severity

1. **python-jose denial of service via compressed JWE content** (CVE-2023-48123)
   - **Affected Version**: python-jose 3.3.0
   - **Description**: Vulnerability that allows attackers to cause denial of service through compressed JWE content.
   - **Mitigation**: While we've kept python-jose for now, we recommend migrating to PyJWT in the future. Added additional cryptography dependency with a secure version.

2. **Pydantic regular expression denial of service** (CVE-2023-36189)
   - **Affected Version**: pydantic 1.10.7
   - **Description**: Regular expression denial of service vulnerability in email validation.
   - **Mitigation**: Updated to pydantic 2.6.1 which includes the fix.

3. **Black vulnerable to Regular Expression Denial of Service (ReDoS)** (CVE-2023-22741)
   - **Affected Version**: black 23.3.0
   - **Description**: Regular expression denial of service vulnerability.
   - **Mitigation**: Updated to black 24.2.0 which includes the fix.

4. **Starlette has Path Traversal vulnerability in StaticFiles** (CVE-2023-45803)
   - **Affected Version**: starlette 0.26.1
   - **Description**: Path traversal vulnerability in StaticFiles component.
   - **Mitigation**: Updated to starlette 0.36.3 which includes the fix.

### Low Severity

1. **Sentry's Python SDK unintentionally exposes environment variables to subprocesses** (CVE-2023-28119)
   - **Affected Version**: sentry-sdk 1.19.1
   - **Description**: Vulnerability that could expose environment variables to subprocesses.
   - **Mitigation**: Updated to sentry-sdk 1.40.5 which includes the fix.

## Additional Security Improvements

1. Added the latest version of cryptography (42.0.4+) to ensure secure cryptographic operations.
2. Added the latest version of certifi (2024.2.2+) to ensure up-to-date certificate validation.
3. Updated all other dependencies to their latest stable versions to incorporate security fixes.

## Breaking Changes

The update to Pydantic v2 (from 1.10.7 to 2.6.1) introduces breaking changes in the API. If your code uses Pydantic models, you may need to update your code to be compatible with Pydantic v2. Key changes include:

1. Different import paths (from pydantic.v1 import ... for backward compatibility)
2. Changes in validation behavior
3. Different error messages and error handling

Please refer to the [Pydantic migration guide](https://docs.pydantic.dev/latest/migration/) for detailed information on migrating from v1 to v2.

## Recommendations

1. **Replace python-jose with PyJWT**: Consider replacing python-jose with PyJWT for JWT handling, as it has better security practices and more active maintenance.
2. **Implement Content Security Policy (CSP)**: To mitigate XSS attacks, implement a strict Content Security Policy.
3. **Regular Security Audits**: Regularly audit dependencies for security vulnerabilities using tools like `safety` or GitHub's Dependabot.
4. **Input Validation**: Ensure all user inputs are properly validated and sanitized before processing.

## Contact

If you discover any security issues, please report them by [opening an issue](https://github.com/yourusername/apifrom/issues) or contacting the maintainers directly. 