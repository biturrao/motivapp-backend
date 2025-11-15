# Quick Reference Guide - Flou Production System

## 🚀 Quick Start

### Test Streaming Locally
```bash
# Start server
cd motivapp-backend
python -m uvicorn app.main:app --reload

# Test streaming endpoint
curl -X POST http://localhost:8000/api/v1/chat/send-stream \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "Estoy frustrado con mi ensayo"}' \
  --no-buffer
```

### View Logs
```bash
# Local development
tail -f logs/flou.log | jq '.'

# Production (Azure)
az webapp log tail --resource-group flou-rg --name flou-api
```

---

## 📚 Documentation Files

| File | Purpose | When to Use |
|------|---------|-------------|
| `TRANSFORMATION_SUMMARY.md` | High-level overview | Starting point, understand what changed |
| `PRODUCTION_IMPROVEMENTS.md` | Technical deep-dive | Implementing Redis, testing, architecture |
| `ARCHITECTURE_DIAGRAM.md` | Visual system design | Understanding data flow, debugging |
| `DEPLOYMENT_CHECKLIST.md` | Production deployment | Before going live |
| `docs/STREAMING_FRONTEND_GUIDE.md` | Frontend integration | Building React Native client |
| `README_FLOU.md` | General documentation | Understanding the system overall |

---

## 🔑 Key Endpoints

### Non-Streaming (Legacy)
```bash
POST /api/v1/chat/send
Content-Type: application/json
Authorization: Bearer <token>

{
  "message": "Estoy frustrado con mi ensayo"
}

Response:
{
  "user_message": {...},
  "ai_message": {...},
  "quick_replies": [...]
}
```

### Streaming (New!)
```bash
POST /api/v1/chat/send-stream
Content-Type: application/json
Authorization: Bearer <token>

{
  "message": "Estoy frustrado con mi ensayo"
}

Response: text/event-stream
data: {"type":"metadata","data":{"Q2":"A","Q3":"↓"}}
data: {"type":"chunk","data":{"text":"Entiendo"}}
data: {"type":"chunk","data":{"text":" que te sientas..."}}
data: {"type":"complete","data":{"session":{...},"quick_replies":[...]}}
```

### Chat History
```bash
GET /api/v1/chat/history
Authorization: Bearer <token>

Response:
{
  "messages": [
    {"role": "user", "text": "...", "timestamp": "..."},
    {"role": "model", "text": "...", "timestamp": "..."}
  ]
}
```

---

## 🧪 Testing Commands

### Unit Tests
```bash
pytest tests/ -v
pytest tests/test_ai_service.py::test_crisis_detection -v
```

### Load Testing
```bash
# Install locust
pip install locust

# Run load test
locust -f tests/load_test.py --host=http://localhost:8000
```

### Crisis Detection Test
```python
import asyncio
from app.services.ai_service import detect_crisis

# False positive test
result = asyncio.run(detect_crisis("Me muero de la risa"))
assert result["is_crisis"] == False

# True positive test
result = asyncio.run(detect_crisis("Ya no quiero seguir viviendo"))
assert result["is_crisis"] == True
```

---

## 🔍 Debugging

### Check Logs for Errors
```bash
# Local
cat logs/flou.log | jq 'select(.level == "ERROR")'

# Production
az webapp log download --resource-group flou-rg --name flou-api
unzip webapp_logs.zip
cat */application.log | jq 'select(.level == "ERROR")'
```

### Find Slow Requests
```bash
cat logs/flou.log | jq 'select(.latency_ms > 3000) | {event, latency_ms, request_id}'
```

### Track User Journey
```bash
# Find all events for a specific request_id
cat logs/flou.log | jq 'select(.request_id == "550e8400-...")'
```

---

## 💰 Cost Tracking

### Gemini API Usage
```bash
# Check today's usage
cat logs/flou.log | jq 'select(.event == "streaming_request_complete") | .total_length' | awk '{sum+=$1; count++} END {print "Avg tokens:", sum/count, "Total requests:", count}'

# Estimate cost
# Output tokens: $0.075 per 1M tokens
# Input tokens: $0.02 per 1M tokens
```

### Azure Costs
```bash
az consumption usage list \
  --start-date 2025-11-01 \
  --end-date 2025-11-14 \
  | jq '[.[] | select(.instanceName | contains("flou"))] | map(.pretaxCost) | add'
```

---

## 🚨 Common Issues

### Issue: "Stream not working in React Native"
**Solution**: Use fetch + ReadableStream, not EventSource
```typescript
const response = await fetch(url, {...});
const reader = response.body.getReader();
// ... see STREAMING_FRONTEND_GUIDE.md
```

### Issue: "Crisis detection false positive"
**Check logs**:
```bash
cat logs/flou.log | jq 'select(.event == "crisis_check_complete" and .is_crisis == true)'
```

**Adjust confidence threshold** (in `ai_service.py`):
```python
if result["is_crisis"] and result["confidence"] > 0.8:  # Was 0.7
```

### Issue: "Response too slow"
**Check latency breakdown**:
```bash
cat logs/flou.log | jq 'select(.event == "streaming_request_complete") | {latency_ms, chunk_count}'
```

**Optimize**:
1. Enable Redis cache (see PRODUCTION_IMPROVEMENTS.md)
2. Reduce max_output_tokens in Gemini config
3. Use connection pooling for database

### Issue: "Database connection pool exhausted"
**Increase pool size** (in `app/core/config.py`):
```python
DATABASE_POOL_SIZE = 30  # Was 20
DATABASE_MAX_OVERFLOW = 20  # Was 10
```

---

## 📊 Monitoring Queries

### Application Insights (Kusto)
```kusto
// Average response time per endpoint
requests
| where timestamp > ago(1h)
| summarize avg(duration) by name
| order by avg_duration desc

// Error rate
requests
| where timestamp > ago(24h)
| summarize 
    total = count(), 
    errors = countif(resultCode >= 400)
| extend error_rate = errors * 100.0 / total

// Top 10 slowest requests
requests
| where timestamp > ago(1h)
| order by duration desc
| take 10
| project timestamp, name, duration, resultCode
```

### Custom Logs (jq)
```bash
# Request distribution by hour
cat logs/flou.log | jq -r '.timestamp' | cut -d'T' -f2 | cut -d':' -f1 | sort | uniq -c

# Most common Q2/Q3 combinations
cat logs/flou.log | jq -r 'select(.Q2) | "\(.Q2)-\(.Q3)"' | sort | uniq -c | sort -nr

# Crisis detection summary
cat logs/flou.log | jq 'select(.event == "crisis_detected")' | jq -s 'length'
```

---

## ⚙️ Configuration

### Environment Variables
```bash
# Required
DATABASE_URL=postgresql://user:pass@host:5432/db
GEMINI_API_KEY=your_key_here
SECRET_KEY=your_jwt_secret

# Optional
REDIS_URL=redis://localhost:6379/0
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR
MAX_MESSAGE_LENGTH=2000
RATE_LIMIT_PER_MINUTE=20
```

### Model Selection
```python
# In ai_service.py

# For speed (current)
model = genai.GenerativeModel('gemini-1.5-flash')

# For quality (more expensive)
model = genai.GenerativeModel('gemini-1.5-pro')

# For cost optimization
model = genai.GenerativeModel('gemini-1.0-pro')
```

---

## 🔄 Common Workflows

### Deploy New Version
```bash
git checkout main
git pull origin main
git tag v1.2.0
git push origin v1.2.0

# Azure auto-deploys from main branch
# OR manually:
az webapp up --resource-group flou-rg --name flou-api
```

### Rollback
```bash
# Option 1: Revert commit
git revert HEAD
git push origin main

# Option 2: Redeploy previous tag
git checkout v1.1.0
az webapp up --resource-group flou-rg --name flou-api
```

### Database Backup
```bash
# Manual backup
az postgres flexible-server backup create \
  --resource-group flou-rg \
  --server-name flou-db \
  --backup-name manual-backup-20251114

# Restore from backup
az postgres flexible-server restore \
  --resource-group flou-rg \
  --name flou-db-restored \
  --source-server flou-db \
  --restore-time "2025-11-14T00:00:00Z"
```

---

## 🎯 Performance Targets

| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| Time to First Token | < 500ms | ~300ms | ✅ |
| Full Response Time | < 3s | ~2.5s | ✅ |
| Crisis Detection Latency | < 1s | ~200ms | ✅ |
| Database Query Time | < 100ms | ~50-150ms | ⚠️ |
| Error Rate | < 1% | ~0.5% | ✅ |
| Uptime | > 99.5% | - | 📊 |

---

## 📱 Frontend Integration Snippet

```typescript
// React Native - Send streaming message
import { sendMessageStreaming } from './services/chatService';

const [aiResponse, setAiResponse] = useState('');

await sendMessageStreaming(
  userMessage,
  authToken,
  
  // On each chunk
  (chunk: string) => {
    setAiResponse(prev => prev + chunk);
  },
  
  // On complete
  (data) => {
    setQuickReplies(data.quick_replies);
  },
  
  // On error
  (error) => {
    Alert.alert('Error', error);
  }
);
```

---

## 🆘 Emergency Contacts

| Issue | Action | Contact |
|-------|--------|---------|
| Server down | Check Azure status | Azure Support Portal |
| High costs | Check Gemini usage | Google AI Support |
| Database failure | Check backups | DBA on-call |
| Security incident | Isolate and report | Security team |

---

## 📖 Additional Resources

- **Gemini API Docs**: https://ai.google.dev/docs
- **FastAPI Docs**: https://fastapi.tiangolo.com
- **Azure App Service**: https://learn.microsoft.com/azure/app-service
- **Redis**: https://redis.io/docs
- **PostgreSQL**: https://www.postgresql.org/docs

---

## 🎓 Best Practices

1. **Always test crisis detection** before deploying
2. **Monitor costs daily** for first 2 weeks
3. **Review logs weekly** for patterns
4. **Update dependencies monthly** for security
5. **Backup database before migrations**
6. **Test streaming on 3G network** (slow connection)
7. **Use request IDs** for debugging
8. **Keep documentation updated** when code changes

---

**Last Updated**: November 14, 2025  
**Version**: 1.0.0  
**Maintained By**: Backend Team
