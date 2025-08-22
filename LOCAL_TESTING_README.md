# 🏠 quanBuy Local Testing Guide

Test the entire quanBuy platform locally without any cloud services or costs!

## 🚀 Quick Start

### Prerequisites
- **Docker Desktop** installed ([Download here](https://www.docker.com/products/docker-desktop))
- **Optional**: Gemini API key (for real AI features)

### Run Everything with One Command

```bash
# Start all services locally
./run-local.sh
```

That's it! The script will:
- Start Redis for caching
- Launch the Gemini AI service
- Serve the quanBuy UI
- Set up networking between services

## 📱 Access Your Local quanBuy

Once running, access:

| Service | URL | Description |
|---------|-----|-------------|
| **quanBuy UI** | http://localhost:8000/quanbuy.html | Beautiful infinite scroll interface |
| **Gemini API** | http://localhost:8081 | AI service endpoints |
| **API Docs** | http://localhost:8081/docs | Interactive API documentation |

## 🧪 Test AI Features

### Without Gemini API Key (Mock Mode)
The service will return realistic fallback responses - perfect for testing!

### With Gemini API Key (Real AI)
```bash
# Set your API key
export GEMINI_API_KEY="your-api-key-here"

# Then run
./run-local.sh
```

Get a free API key at: https://makersuite.google.com/app/apikey

## 🎮 Try the AI Features

### 1. Mystery Search
Discover surprising products based on search patterns:

```bash
curl -X POST http://localhost:8081/mystery-search \
  -H 'Content-Type: application/json' \
  -d '{
    "user_id": "test123",
    "search_history": ["vintage", "bohemian", "handmade"]
  }'
```

### 2. Oracle Mode (Search by Feeling)
Find products based on emotions:

```bash
curl -X POST http://localhost:8081/oracle-search \
  -H 'Content-Type: application/json' \
  -d '{
    "user_id": "test123",
    "feeling": "anxious"
  }'
```

### 3. Discovery Story
Generate a poetic narrative of your search journey:

```bash
curl -X POST http://localhost:8081/discovery-story \
  -H 'Content-Type: application/json' \
  -d '{
    "user_id": "test123",
    "searches": ["candles", "crystals", "incense"],
    "products_viewed": ["Sage Bundle", "Rose Quartz", "Meditation Cushion"],
    "duration_minutes": 15
  }'
```

### 4. Search DNA
Analyze search patterns to create visual DNA:

```bash
curl -X POST http://localhost:8081/search-dna \
  -H 'Content-Type: application/json' \
  -d '{
    "user_id": "test123",
    "search_history": ["vintage", "antique", "retro", "classic", "timeless"],
    "timeframe_days": 30
  }'
```

## 📊 Monitor Services

### View Logs
```bash
# All services
docker-compose logs -f

# Just Gemini service
docker-compose logs -f geminiservice

# Just Redis
docker-compose logs -f redis
```

### Check Service Health
```bash
# Gemini service health
curl http://localhost:8081/health

# Redis health
docker-compose exec redis redis-cli ping
```

## 🛠️ Development Mode

### Hot Reload for Python
The Gemini service supports hot reload. Edit `src/geminiservice/main.py` and changes apply automatically!

### Modify the UI
Edit `quanbuy.html` and refresh your browser to see changes instantly.

## 🛑 Stop Everything

```bash
# Stop all services
docker-compose down

# Stop and remove all data
docker-compose down -v
```

## 🐛 Troubleshooting

### Port Already in Use
If you get port conflicts:
```bash
# Check what's using the ports
lsof -i :8000
lsof -i :8081
lsof -i :6379

# Kill the process or change ports in docker-compose.yml
```

### Docker Not Starting
```bash
# Make sure Docker Desktop is running
open -a Docker  # macOS
# or start Docker Desktop manually

# Reset Docker
docker-compose down -v
docker system prune -a
```

### Service Not Responding
```bash
# Restart specific service
docker-compose restart geminiservice

# Check service logs
docker-compose logs geminiservice
```

## 🎯 What's Working Locally

✅ **Full UI** - Beautiful infinite scroll interface  
✅ **Redis Caching** - Fast response times  
✅ **Gemini AI** - All AI features (with API key)  
✅ **Mock Mode** - Realistic responses without API key  
✅ **API Documentation** - Interactive Swagger UI  

## 🚫 What's Disabled Locally

❌ **Firestore** - No persistence (uses Redis only)  
❌ **Pub/Sub** - Events logged but not published  
❌ **Cloud CDN** - Not needed locally  
❌ **Load Balancing** - Single instance only  

## 💡 Tips

1. **First Time?** Just run `./run-local.sh` - it handles everything!

2. **Want Real AI?** Get a free Gemini API key:
   - Visit: https://makersuite.google.com/app/apikey
   - Create key
   - Export: `export GEMINI_API_KEY="your-key"`

3. **Testing the UI?** Open multiple browser tabs to simulate multiple users

4. **Building Features?** The mock mode returns consistent data - perfect for UI development

## 📈 Next Steps

Once you're happy with local testing:

1. **Get Google Cloud credits** (new accounts get $300 free)
2. **Deploy to GKE** using `./deploy-to-gke.sh`
3. **Scale globally** with Cloud CDN and multiple regions

---

**Happy Testing! 🎉** No cloud costs, no setup hassle, just pure development joy!
