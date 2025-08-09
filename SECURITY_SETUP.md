# LTMC Security Setup Guide

## Redis Authentication Setup

**IMPORTANT**: Redis passwords are now environment-based for security.

### Environment Configuration

1. **Set Redis Password Environment Variable**:
```bash
export REDIS_PASSWORD="your_secure_password_here"
```

2. **Add to your shell profile** (`.bashrc`, `.zshrc`, etc.):
```bash
echo 'export REDIS_PASSWORD="your_secure_password_here"' >> ~/.bashrc
source ~/.bashrc
```

### Starting Redis Services

All Redis scripts now use the `REDIS_PASSWORD` environment variable:

```bash
# Start Redis with environment password
./redis_control.sh start

# Check status
./redis_control.sh status

# Connect to Redis
./redis_control.sh connect
```

### Development vs Production

**Development** (no env var set):
- Automatically generates random password: `ltmc_dev_<random>`
- Password shown in startup logs

**Production** (env var set):
- Uses your specified secure password
- Password never logged or displayed

### Security Best Practices

1. **Never commit passwords**: All config files with passwords are now gitignored
2. **Use strong passwords**: Minimum 16 characters with mixed case, numbers, symbols
3. **Environment isolation**: Use different passwords for dev/staging/production
4. **Regular rotation**: Change passwords regularly

### Migration from Hardcoded Passwords

If you were using the old hardcoded password `ltmc_cache_2025`:

1. **Stop existing Redis**:
```bash
./redis_control.sh stop
```

2. **Set new secure password**:
```bash
export REDIS_PASSWORD="your_new_secure_password"
```

3. **Restart with new password**:
```bash
./redis_control.sh start
```

### Troubleshooting

**Connection errors**: Ensure `REDIS_PASSWORD` environment variable matches your Redis configuration.

**Permission denied**: Check that your password is properly exported in the current shell session.

**Generated passwords**: If no env var is set, check the startup logs for the generated password.