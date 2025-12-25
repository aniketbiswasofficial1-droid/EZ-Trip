# EZ-Trip Security Policy

## Reporting Security Vulnerabilities

If you discover a security vulnerability, please email us at security@eztrip.com (or your actual security contact email).

**Please do not:**
- Open a public GitHub issue
- Disclose the vulnerability publicly before it has been addressed

**Please include:**
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

We will respond within 48 hours and work with you to address the issue.

## Security Best Practices

### For Developers

1. **Environment Variables**
   - Never commit `.env` files with real credentials
   - Use `.env.example` for templates only
   - Rotate all keys if accidentally committed
   - Use different credentials for development and production

2. **API Keys & Secrets**
   - Store in environment variables, never in code
   - Use strong, randomly generated secrets
   - Rotate keys regularly (at least every 90 days)
   - Enable 2FA on all external accounts (Google, OpenAI, email providers)

3. **Authentication**
   - Passwords must be at least 8 characters with letters, numbers, and special characters
   - Sessions expire after 7 days
   - Cookies are HTTP-only and secure in production
   - Google OAuth is validated with clock skew tolerance

4. **Database Security**
   - Enable MongoDB authentication in production
   - Use connection strings with proper credentials
   - Regular backups of production data
   - Restrict MongoDB access to application network only

5. **Docker Security**
   - Production containers run as non-root users
   - Minimal base images used (alpine, slim)
   - Multi-stage builds to reduce attack surface
   - Regular updates of base images

### For Deployment

1. **HTTPS/TLS**
   - Always use HTTPS in production
   - Configure SSL certificates properly
   - Enable HSTS headers (`Strict-Transport-Security`)
   - Use Let's Encrypt for free SSL certificates

2. **CORS Configuration**
   - Set `CORS_ORIGINS` to only trusted domains
   - Never use `*` (allow all) in production
   - Include both `www` and non-`www` versions if applicable

3. **Rate Limiting**
   - Configure `RATE_LIMIT_PER_MINUTE` appropriately
   - Monitor for unusual traffic patterns
   - Consider using a reverse proxy (nginx/Cloudflare) for additional protection

4. **Monitoring & Logging**
   - Set `LOG_LEVEL=INFO` in production
   - Monitor application logs regularly
   - Set up alerts for errors and security events
   - Use log aggregation tools (ELK stack, Datadog, etc.)

5. **Regular Updates**
   - Keep dependencies updated
   - Monitor for security advisories
   - Test updates in staging before production
   - Subscribe to security mailing lists for used technologies

## Security Checklist

Before deploying to production, ensure:

- [ ] All environment variables are properly configured
- [ ] `.env` files are in `.gitignore` and not committed
- [ ] HTTPS/TLS is enabled and working
- [ ] CORS origins are restricted to trusted domains
- [ ] MongoDB authentication is enabled
- [ ] API keys and secrets are production-specific (not reused from dev)
- [ ] 2FA is enabled on all external accounts
- [ ] Security headers are enabled (check via browser dev tools)
- [ ] Rate limiting is configured
- [ ] Logging is set to appropriate level (INFO)
- [ ] Backups are configured and tested
- [ ] Docker containers run as non-root users
- [ ] Security updates are applied to all dependencies

## Known Security Considerations

1. **Session Management**
   - Sessions expire after 7 days
   - Users need to re-authenticate after expiry
   - Session tokens are stored in HTTP-only cookies

2. **File Uploads**
   - Profile pictures limited to 5MB
   - Only image formats allowed: JPG, JPEG, PNG, GIF, WEBP
   - Files are validated using PIL (Pillow)
   - Uploaded files stored in isolated directory

3. **Password Requirements**
   - Minimum 8 characters
   - Must contain at least one letter
   - Must contain at least one number
   - Must contain at least one special character
   - Passwords are hashed using bcrypt

4. **Input Validation**
   - Email validation using standard patterns
   - Pydantic models validate all API inputs
   - SQL injection not applicable (using MongoDB)
   - XSS protection via security headers

## Credential Rotation Guide

If credentials are compromised or accidentally exposed:

1. **OpenAI API Key**
   - Visit https://platform.openai.com/api-keys
   - Revoke the old key
   - Generate a new key
   - Update `.env` file and restart services

2. **Google OAuth Credentials**
   - Visit https://console.cloud.google.com/apis/credentials
   - Delete the old credentials
   - Create new OAuth 2.0 Client ID
   - Update authorized redirect URIs
   - Update `.env` file with new credentials
   - Restart services

3. **Email SMTP Credentials**
   - For Gmail: Revoke app password and generate a new one
   - For Outlook: Change account password
   - Update `.env` file
   - Restart services

4. **Database Credentials**
   - Create new MongoDB user with strong password
   - Update connection string in `.env`
   - Remove old user
   - Restart services

## Automated Security

Consider implementing:

- **Dependabot** for automated dependency updates
- **SAST tools** (Static Application Security Testing)
- **Container scanning** (Trivy, Snyk)
- **Secret scanning** (git-secrets, trufflehog)
- **WAF** (Web Application Firewall) like Cloudflare

## Compliance

This application handles:
- User authentication data
- Email addresses
- Profile information
- Financial transaction data (expenses)

Ensure compliance with relevant regulations:
- GDPR (if serving EU users)
- CCPA (if serving California users)
- Data retention policies
- Right to deletion requests
