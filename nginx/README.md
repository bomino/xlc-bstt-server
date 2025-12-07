# Nginx Production Configuration

This directory contains production Nginx configuration for the BSTT Compliance Dashboard.

## Files

- `nginx.prod.conf` - Production Nginx configuration with SSL support
- `ssl/` - Directory for SSL certificates (not committed to git)

## SSL Certificate Setup

### Option A: Let's Encrypt (Recommended for Public Servers)

```bash
# Install certbot
sudo apt install certbot

# Stop nginx temporarily if running
docker-compose -f docker-compose.prod.yml down

# Get certificate
sudo certbot certonly --standalone -d your-domain.com

# Copy certificates
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem nginx/ssl/
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem nginx/ssl/

# Set permissions
sudo chmod 644 nginx/ssl/fullchain.pem
sudo chmod 600 nginx/ssl/privkey.pem

# Start containers
docker-compose -f docker-compose.prod.yml --env-file .env.production up -d
```

### Option B: Self-Signed Certificate (For Internal/Testing)

```bash
# Create self-signed certificate (valid for 365 days)
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout nginx/ssl/privkey.pem \
  -out nginx/ssl/fullchain.pem \
  -subj "/CN=bstt.local"
```

### Option C: Corporate/Internal CA

If your organization has an internal Certificate Authority:

1. Request a certificate for your domain
2. Place the certificate chain in `nginx/ssl/fullchain.pem`
3. Place the private key in `nginx/ssl/privkey.pem`

## Certificate Renewal (Let's Encrypt)

Let's Encrypt certificates expire every 90 days. Set up auto-renewal:

```bash
# Test renewal
sudo certbot renew --dry-run

# Add to crontab for automatic renewal
# Run daily at 2am
0 2 * * * /usr/bin/certbot renew --quiet && docker-compose -f /path/to/docker-compose.prod.yml restart frontend
```

## Security Notes

1. **Never commit SSL certificates to git** - They are in `.gitignore`
2. **Use strong passwords** for private keys if passphrase-protected
3. **Regularly update** certificates before expiration
4. **Monitor** SSL/TLS configuration at https://www.ssllabs.com/ssltest/

## Testing SSL Configuration

After deployment, test your SSL configuration:

```bash
# Check certificate details
openssl s_client -connect your-domain.com:443 -servername your-domain.com

# Test with curl
curl -v https://your-domain.com/health
```

## Troubleshooting

### Certificate not found
```
nginx: [emerg] cannot load certificate "/etc/nginx/ssl/fullchain.pem"
```
Solution: Ensure SSL certificates exist in `nginx/ssl/` directory

### Permission denied
```
nginx: [emerg] BIO_new_file("/etc/nginx/ssl/privkey.pem") failed
```
Solution: Check file permissions (should be readable by nginx user)

### Certificate chain issues
```
curl: (60) SSL certificate problem: unable to get local issuer certificate
```
Solution: Ensure `fullchain.pem` contains the full certificate chain (certificate + intermediates)
