# Security Policy

## Quest and Crossfire™ | Aethelgard Academy™

---

## 🔒 Repository Security

This is a **PRIVATE REPOSITORY** with proprietary code.

### Access Control

- ✅ Repository is set to **PRIVATE**
- ✅ Access restricted to authorized personnel only
- ✅ Two-factor authentication (2FA) required for all collaborators
- ✅ Branch protection enabled on `main` branch

---

## 🔐 Security Measures

### 1. **Secrets Management**

**NEVER commit these to the repository:**
- ❌ API keys (OpenAI, Tavily, LangSmith, Honeycomb)
- ❌ Database credentials
- ❌ Redis URLs with passwords
- ❌ Authentication passwords or hashes
- ❌ Any `.env` files with real values

**Use environment variables or GitHub Secrets instead.**

### 2. **Files Excluded from Git**

The `.gitignore` file excludes:
- `config/settings.env` (actual secrets)
- `.env` files
- `*.log` files
- `__pycache__/`
- Virtual environments
- Test files with sensitive data

### 3. **Authentication**

- Default credentials (`admin`/`aethelgard2024`) are for **DEVELOPMENT ONLY**
- **MUST** be changed before production deployment
- Use strong passwords (16+ characters, mixed case, numbers, symbols)
- Password hashes use SHA-256

### 4. **API Security**

- CORS configured to allow only authorized frontend URLs
- API keys encrypted in Redis
- Session-based authentication
- Rate limiting recommended for production

---

## 🚨 Reporting Security Issues

If you discover a security vulnerability:

1. **DO NOT** open a public issue
2. Email: security@questandcrossfire.com
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

---

## ✅ Security Checklist for Deployment

Before deploying to production:

- [ ] Change default authentication credentials
- [ ] Set strong `AUTH_PASSWORD_HASH`
- [ ] Verify all API keys are in environment variables (not code)
- [ ] Enable HTTPS on both frontend and backend
- [ ] Configure CORS to allow only your frontend URL
- [ ] Enable database backups
- [ ] Set up monitoring and alerts
- [ ] Review and rotate API keys regularly
- [ ] Enable 2FA for all admin accounts
- [ ] Implement rate limiting
- [ ] Set up WAF (Web Application Firewall) if possible
- [ ] Regular security audits

---

## 🔄 Security Updates

- Dependencies are managed via Poetry (backend) and requirements.txt (frontend)
- Regular updates recommended for security patches
- Monitor GitHub Security Advisories
- Review LangChain/OpenAI security bulletins

---

## 📋 Compliance

This software handles:
- Educational content (non-sensitive)
- User authentication data (passwords hashed)
- API keys (encrypted in Redis)
- Generated curriculum content

**No PII (Personally Identifiable Information) is stored.**

---

## 🛡️ Best Practices

### For Developers:

1. **Never commit secrets**
   ```bash
   # Check before committing
   git diff
   git status
   ```

2. **Use environment variables**
   ```python
   # Good
   api_key = os.getenv("OPENAI_API_KEY")
   
   # Bad
   api_key = "sk-1234567890"
   ```

3. **Rotate credentials regularly**
   - API keys: Every 90 days
   - Passwords: Every 180 days
   - Database passwords: Every 180 days

4. **Review pull requests carefully**
   - Check for exposed secrets
   - Verify security implications
   - Test authentication flows

---

## 📞 Security Contact

**Quest and Crossfire™ Security Team**
- Email: security@questandcrossfire.com
- Response time: 24-48 hours for critical issues

---

## 📜 Security Audit Log

| Date | Action | Status |
|------|--------|--------|
| 2025-11-08 | Initial security setup | ✅ Complete |
| 2025-11-08 | Authentication implemented | ✅ Complete |
| 2025-11-08 | `.gitignore` configured | ✅ Complete |
| TBD | First security audit | ⏳ Pending |

---

**Last Updated**: November 8, 2025  
**Version**: 2.0  
**Classification**: PROPRIETARY & CONFIDENTIAL



