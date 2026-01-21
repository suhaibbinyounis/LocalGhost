# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Security Model

LocalGhost is designed with security as a core principle:

- **Localhost only**: Binds to `127.0.0.1` by default
- **User consent**: Protected endpoints require explicit user approval
- **Encrypted tokens**: Fernet symmetric encryption
- **Scoped permissions**: Tokens are tied to specific endpoints
- **Audit logging**: All grants/revokes logged to SQLite

## Reporting a Vulnerability

If you discover a security vulnerability:

1. **Do NOT open a public issue**
2. Email the maintainers directly with:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
3. Allow up to 48 hours for initial response
4. Work with us on a fix before public disclosure

## Best Practices

When using LocalGhost:

- Keep the service updated
- Review granted permissions regularly (`localghost permissions`)
- Revoke unused permissions (`localghost revoke <client_id>`)
- Use `LOCALGHOST_NO_AUTOSTART=1` if you don't want auto-registration
