# Security Policy

## Security Features

### Authentication & Authorization
- Bearer token authentication (development mode)
- Role-based permissions (read/write)
- Rate limiting with Redis backend

### Data Protection
- Environment variable configuration for secrets
- No hardcoded credentials in source code
- Parameterized SQL queries to prevent injection
- Input validation with Pydantic models

### Network Security
- CORS configuration with allowed origins
- Request size limits
- Secure headers implementation

### Database Security
- Connection pooling with error handling
- Prepared statements for all queries
- Data validation before database operations

## Environment Variables

Required secure environment variables:

```bash
# Required - No defaults provided
SECRET_KEY=your-secure-secret-key-minimum-32-characters
REDDIT_CLIENT_ID=your-reddit-client-id
REDDIT_CLIENT_SECRET=your-reddit-client-secret

# Optional
API_KEY=your-api-key-for-additional-auth
REDIS_PASSWORD=your-redis-password
```

## Production Security Checklist

- [ ] Set strong SECRET_KEY (32+ characters)
- [ ] Configure REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET
- [ ] Set up HTTPS with valid SSL certificates
- [ ] Configure firewall rules
- [ ] Enable database encryption at rest
- [ ] Set up log monitoring and alerting
- [ ] Regular security updates
- [ ] Backup encryption

## Reporting Security Issues

Please report security vulnerabilities responsibly by emailing the project maintainers directly rather than opening public issues.

## Security Updates

This project follows semantic versioning with security patches released as patch versions.