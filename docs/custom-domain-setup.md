# Custom Domain Setup for RealBreaking.com

This guide explains how to configure `realbreaking.com` to serve your frontend from Google Cloud Storage while keeping the custom domain visible throughout the user experience.

## Architecture

```
User Browser
     ↓
realbreaking.com (DNS)
     ↓
Google Cloud Load Balancer (Static IP)
     ↓ (HTTPS with managed SSL)
Backend Bucket
     ↓
GCS: cms-automation-frontend-476323
```

## Prerequisites

- Domain: `realbreaking.com` (you own this)
- GCP Project: `cmsupload-476323`
- GCS Bucket: `cms-automation-frontend-476323`

## Step 1: Reserve a Static IP Address

```bash
gcloud compute addresses create realbreaking-frontend-ip \
    --network-tier=PREMIUM \
    --ip-version=IPV4 \
    --global \
    --project=cmsupload-476323
```

Get the IP address:
```bash
gcloud compute addresses describe realbreaking-frontend-ip \
    --global \
    --project=cmsupload-476323 \
    --format="get(address)"
```

**Note the IP address** - you'll need it for DNS configuration.

## Step 2: Create SSL Certificate (Google-managed)

```bash
gcloud compute ssl-certificates create realbreaking-ssl-cert \
    --domains=realbreaking.com,www.realbreaking.com \
    --global \
    --project=cmsupload-476323
```

## Step 3: Create Backend Bucket

```bash
gcloud compute backend-buckets create cms-frontend-backend \
    --gcs-bucket-name=cms-automation-frontend-476323 \
    --enable-cdn \
    --project=cmsupload-476323
```

## Step 4: Create URL Map

```bash
gcloud compute url-maps create realbreaking-url-map \
    --default-backend-bucket=cms-frontend-backend \
    --project=cmsupload-476323
```

## Step 5: Create HTTPS Target Proxy

```bash
gcloud compute target-https-proxies create realbreaking-https-proxy \
    --url-map=realbreaking-url-map \
    --ssl-certificates=realbreaking-ssl-cert \
    --project=cmsupload-476323
```

## Step 6: Create Global Forwarding Rule

```bash
gcloud compute forwarding-rules create realbreaking-https-rule \
    --address=realbreaking-frontend-ip \
    --target-https-proxy=realbreaking-https-proxy \
    --global \
    --ports=443 \
    --project=cmsupload-476323
```

## Step 7: Configure DNS

In your domain registrar (where you bought realbreaking.com), add these DNS records:

| Type | Host | Value | TTL |
|------|------|-------|-----|
| A | @ | `<STATIC_IP_FROM_STEP_1>` | 300 |
| A | www | `<STATIC_IP_FROM_STEP_1>` | 300 |

## Step 8: Configure GCS Bucket for Web Hosting

```bash
# Set the main page
gcloud storage buckets update gs://cms-automation-frontend-476323 \
    --web-main-page-suffix=index.html \
    --web-error-page=index.html

# Ensure public access (for CDN)
gcloud storage buckets add-iam-policy-binding gs://cms-automation-frontend-476323 \
    --member=allUsers \
    --role=roles/storage.objectViewer
```

## Step 9: Wait for SSL Certificate Provisioning

SSL certificate provisioning takes 15-60 minutes after DNS is configured. Check status:

```bash
gcloud compute ssl-certificates describe realbreaking-ssl-cert \
    --global \
    --project=cmsupload-476323 \
    --format="get(managed.status)"
```

Status will change from `PROVISIONING` to `ACTIVE`.

## Step 10: (Optional) Add HTTP to HTTPS Redirect

Create HTTP forwarding to redirect to HTTPS:

```bash
# Create URL map for redirect
gcloud compute url-maps import realbreaking-http-redirect \
    --source=/dev/stdin \
    --global \
    --project=cmsupload-476323 << 'EOF'
name: realbreaking-http-redirect
defaultUrlRedirect:
  redirectResponseCode: MOVED_PERMANENTLY_DEFAULT
  httpsRedirect: true
EOF

# Create HTTP target proxy
gcloud compute target-http-proxies create realbreaking-http-proxy \
    --url-map=realbreaking-http-redirect \
    --project=cmsupload-476323

# Create HTTP forwarding rule
gcloud compute forwarding-rules create realbreaking-http-rule \
    --address=realbreaking-frontend-ip \
    --target-http-proxy=realbreaking-http-proxy \
    --global \
    --ports=80 \
    --project=cmsupload-476323
```

## Verification

After DNS propagation (5-60 minutes):

```bash
# Test HTTPS
curl -I https://realbreaking.com

# Check SSL certificate
openssl s_client -connect realbreaking.com:443 -servername realbreaking.com < /dev/null 2>/dev/null | openssl x509 -noout -dates
```

## Estimated Costs

| Resource | Monthly Cost (approx) |
|----------|----------------------|
| Load Balancer | ~$18/month |
| SSL Certificate | Free (Google-managed) |
| Cloud CDN | ~$0.02-0.08/GB egress |
| Static IP | ~$7/month (if not in use) |

**Total: ~$18-25/month** for the load balancer setup.

## Alternative: Firebase Hosting (Simpler, Free for Small Sites)

If you want a simpler solution, Firebase Hosting is free for up to 10GB/month:

```bash
# Install Firebase CLI
npm install -g firebase-tools

# Login and init
firebase login
firebase init hosting

# Deploy
firebase deploy --only hosting

# Add custom domain in Firebase Console
# https://console.firebase.google.com > Hosting > Add custom domain
```

## Troubleshooting

### SSL Certificate stuck in PROVISIONING
- Verify DNS A records point to the Load Balancer IP
- Wait up to 60 minutes
- Check: `dig realbreaking.com A`

### 404 errors
- Ensure GCS bucket has public access
- Check web-main-page-suffix is set to index.html

### CORS errors
- Update backend ALLOWED_ORIGINS to include `https://realbreaking.com`
