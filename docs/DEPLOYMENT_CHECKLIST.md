# Production Deployment Checklist

## Pre-Deployment (Complete These First)

### ✅ Code Quality
- [x] All production improvements implemented
- [x] No experimental models (`-exp` removed)
- [x] Structured logging added
- [x] Streaming endpoint created
- [x] Intelligent guardrails implemented
- [ ] Unit tests written for critical paths
- [ ] Golden dataset tests created
- [ ] Code review completed

### ✅ Configuration
- [ ] Environment variables documented
- [ ] Secrets moved to Azure Key Vault
- [ ] Database connection strings secured
- [ ] CORS settings configured for production
- [ ] Rate limiting enabled
- [ ] Logging level set to INFO (not DEBUG)

### ✅ Infrastructure
- [ ] PostgreSQL database provisioned
- [ ] Database backups automated (daily)
- [ ] Redis cache deployed (optional but recommended)
- [ ] SSL/TLS certificate installed
- [ ] Domain name configured
- [ ] CDN configured (if serving static files)

### ✅ Monitoring
- [ ] Application Insights configured
- [ ] Custom metrics endpoint created
- [ ] Error tracking enabled
- [ ] Alert rules configured:
  - [ ] High error rate (>5%)
  - [ ] High latency (>5s avg)
  - [ ] Crisis detection alerts
  - [ ] Database connection failures
  - [ ] High API costs (>$50/day)

### ✅ Security
- [ ] JWT secret rotated from default
- [ ] HTTPS enforced (no HTTP)
- [ ] SQL injection tests passed
- [ ] OWASP Top 10 review completed
- [ ] Rate limiting tested
- [ ] Crisis detection tested with false positives
- [ ] API keys stored securely (not in code)

---

## Deployment Steps

### Step 1: Environment Variables

Create `.env.production` file:

```bash
# Database
DATABASE_URL=postgresql://user:password@prod-db.postgres.database.azure.com:5432/flou_prod
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10

# Redis (Optional but recommended)
REDIS_URL=redis://flou-cache.redis.cache.windows.net:6380?ssl=True&password=YOUR_KEY

# API Keys
GEMINI_API_KEY=your_production_gemini_key
SECRET_KEY=your_super_secret_jwt_key_here  # Generate with: openssl rand -hex 32

# App Config
ENVIRONMENT=production
LOG_LEVEL=INFO
CORS_ORIGINS=["https://yourapp.com", "https://www.yourapp.com"]
MAX_MESSAGE_LENGTH=2000
RATE_LIMIT_PER_MINUTE=20

# Monitoring
APPLICATIONINSIGHTS_CONNECTION_STRING=your_app_insights_connection_string
```

### Step 2: Database Migration

```bash
# Connect to production database
az postgres flexible-server connect \
  --name flou-prod-db \
  --username adminuser

# Run migrations
alembic upgrade head

# Verify tables
psql -d flou_prod -c "\dt"
```

### Step 3: Build and Deploy

```bash
# Option A: Azure App Service (Recommended)
cd motivapp-backend

# Build
docker build -t flou-backend:latest .

# Push to Azure Container Registry
az acr login --name flouregistry
docker tag flou-backend:latest flouregistry.azurecr.io/flou-backend:latest
docker push flouregistry.azurecr.io/flou-backend:latest

# Deploy to App Service
az webapp create \
  --resource-group flou-rg \
  --plan flou-plan \
  --name flou-api \
  --deployment-container-image-name flouregistry.azurecr.io/flou-backend:latest

# Configure environment variables
az webapp config appsettings set \
  --resource-group flou-rg \
  --name flou-api \
  --settings @env-vars.json

# Option B: Manual deployment
git push azure main
```

### Step 4: Health Check

```bash
# Test basic endpoint
curl https://flou-api.azurewebsites.net/health
# Expected: {"status": "healthy", "version": "1.0.0"}

# Test streaming endpoint
curl -X POST https://flou-api.azurewebsites.net/api/v1/chat/send-stream \
  -H "Authorization: Bearer YOUR_TEST_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "Hola"}' \
  --no-buffer

# Expected: SSE stream with data: {...}
```

### Step 5: Smoke Tests

```bash
# Test 1: Authentication
curl -X POST https://flou-api.azurewebsites.net/api/v1/login/access-token \
  -d "username=testuser&password=testpass"
# Expected: {"access_token": "...", "token_type": "bearer"}

# Test 2: Chat message
curl -X POST https://flou-api.azurewebsites.net/api/v1/chat/send \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "Estoy frustrado"}'
# Expected: {"user_message": {...}, "ai_message": {...}}

# Test 3: Crisis detection
curl -X POST https://flou-api.azurewebsites.net/api/v1/chat/send \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"message": "me muero de la risa"}'
# Expected: Normal response (not crisis)

curl -X POST https://flou-api.azurewebsites.net/api/v1/chat/send \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"message": "ya no quiero seguir viviendo"}'
# Expected: Crisis protocol response with 4141 number

# Test 4: Rate limiting (if enabled)
for i in {1..25}; do
  curl -X POST https://flou-api.azurewebsites.net/api/v1/chat/send \
    -H "Authorization: Bearer $TOKEN" \
    -d '{"message": "test"}'
done
# Expected: HTTP 429 after 20 requests
```

---

## Post-Deployment

### Monitoring Setup

1. **Application Insights Dashboard**
   ```bash
   az monitor app-insights component create \
     --app flou-api \
     --location eastus \
     --resource-group flou-rg
   ```

2. **Custom Metrics**
   - Create alert for response time > 5s
   - Create alert for error rate > 5%
   - Create alert for cost > $50/day

3. **Log Analytics Queries**
   ```kusto
   // Find all crisis detections
   traces
   | where message contains "crisis_detected"
   | project timestamp, customDimensions
   
   // Average latency per endpoint
   requests
   | summarize avg(duration) by name
   | order by avg_duration desc
   
   // Error rate
   requests
   | summarize 
       total = count(), 
       errors = countif(resultCode >= 400)
   | extend error_rate = errors * 100.0 / total
   ```

### Gradual Rollout

1. **Week 1: Internal Testing (5% traffic)**
   ```bash
   # Set traffic split
   az webapp traffic-routing set \
     --resource-group flou-rg \
     --name flou-api \
     --distribution production=95 staging=5
   ```

2. **Week 2: Beta Users (25% traffic)**
   - Monitor error rates
   - Collect user feedback
   - Check cost per user

3. **Week 3: General Release (100% traffic)**
   - Enable all users
   - Monitor for 48 hours continuously
   - Prepare rollback plan

### Performance Baseline

After 48 hours of production traffic, record baselines:

```bash
# Query metrics
az monitor metrics list \
  --resource /subscriptions/.../resourceGroups/flou-rg/providers/Microsoft.Web/sites/flou-api \
  --metric "AverageResponseTime" \
  --start-time 2025-11-12T00:00:00Z \
  --end-time 2025-11-14T00:00:00Z
```

| Metric | Target | Alert If |
|--------|--------|----------|
| Avg Response Time | < 2s | > 5s |
| Error Rate | < 1% | > 5% |
| Availability | > 99.5% | < 99% |
| Cost per 1K requests | < $0.10 | > $0.20 |
| Crisis false positives | < 5% | > 10% |

---

## Rollback Plan

If issues detected:

1. **Immediate Rollback (< 5 min)**
   ```bash
   # Revert to previous deployment
   az webapp deployment slot swap \
     --resource-group flou-rg \
     --name flou-api \
     --slot staging \
     --target-slot production
   ```

2. **Database Rollback**
   ```bash
   # If migrations failed
   alembic downgrade -1
   ```

3. **Communication**
   - Notify users via in-app banner
   - Post status on status page
   - Email beta testers

---

## Cost Monitoring

### Daily Check
```bash
# Check Gemini API usage
curl https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent \
  -H "x-goog-api-key: $GEMINI_API_KEY" \
  --request GET

# Check Azure costs
az consumption usage list \
  --start-date 2025-11-01 \
  --end-date 2025-11-14 \
  | jq '.[] | select(.instanceName == "flou-api")'
```

### Budget Alert
```bash
# Create budget alert at $50
az consumption budget create \
  --budget-name flou-monthly-budget \
  --amount 50 \
  --time-grain Monthly \
  --start-date 2025-11-01 \
  --end-date 2026-11-01 \
  --resource-group flou-rg
```

---

## Maintenance Windows

### Weekly (Saturday 2-4 AM UTC)
- Database backup verification
- Log rotation
- Clear old sessions (>30 days)

### Monthly
- Security patches
- Dependency updates
- Performance review

### Quarterly
- Cost optimization review
- Capacity planning
- Feature usage analysis

---

## Documentation Updates

After deployment, update:
- [ ] API documentation with production URLs
- [ ] Frontend integration guide with new endpoints
- [ ] Troubleshooting guide with common issues
- [ ] Runbook for on-call engineers

---

## Success Criteria (First 7 Days)

- [ ] Uptime > 99%
- [ ] Average response time < 3s
- [ ] Zero database connection failures
- [ ] Zero crisis detection false negatives
- [ ] Cost per user < $0.01
- [ ] User satisfaction score > 4/5
- [ ] Zero security incidents

---

## Emergency Contacts

| Role | Name | Contact |
|------|------|---------|
| Backend Engineer | [Your Name] | [Email/Phone] |
| DevOps | [DevOps Lead] | [Email/Phone] |
| Product Owner | [PO Name] | [Email/Phone] |
| Azure Support | Support Portal | portal.azure.com |
| Gemini Support | Google AI | ai.google.dev/support |

---

## Useful Commands

```bash
# View live logs
az webapp log tail --resource-group flou-rg --name flou-api

# Restart app
az webapp restart --resource-group flou-rg --name flou-api

# Scale up
az appservice plan update --resource-group flou-rg --name flou-plan --sku P1V2

# Check database connections
az postgres flexible-server show-connection-string \
  --server-name flou-prod-db \
  --database-name flou_prod \
  --admin-user adminuser

# Export logs for analysis
az monitor activity-log list --resource-group flou-rg \
  --start-time 2025-11-13T00:00:00Z \
  --end-time 2025-11-14T00:00:00Z \
  --output json > logs.json
```

---

## Final Checklist Before Go-Live

- [ ] All smoke tests passed
- [ ] Monitoring dashboards configured
- [ ] Alert rules tested
- [ ] Rollback plan tested
- [ ] Team trained on runbook
- [ ] Backup strategy verified
- [ ] Security scan completed
- [ ] Performance benchmarks recorded
- [ ] Cost alerts configured
- [ ] Documentation updated

---

**Date of Deployment**: _______________  
**Deployed By**: _______________  
**Approved By**: _______________  

**Sign-off**: _______________
