# Anime Roast Generator 🔥

A full-stack web application that generates witty, sarcastic roasts for your favorite anime using Google's Gemini AI.

## Features

- **AI-Powered Roasts**: Uses Gemini 2.0 Flash Lite model for fast, creative roasts
- **Security First**: API key hidden on backend, rate limiting, input validation, CORS protection
- **Rate Limiting**: 10 requests per minute per IP to prevent spam
- **Dark Theme**: Clean, anime-inspired design without gradients
- **Mobile Responsive**: Works perfectly on all devices
- **Share Features**: Copy to clipboard and share on X (Twitter)
- **Request Logging**: All requests logged for monitoring

## Tech Stack

### Backend
- **FastAPI**: Modern, fast Python web framework
- **Gemini API**: Google's lightweight AI model
- **SlowAPI**: Rate limiting middleware
- **Pydantic**: Data validation
- **Docker**: Containerization

### Frontend
- **React 18**: Modern React with hooks
- **Vite**: Fast build tool
- **Tailwind CSS**: Utility-first CSS framework
- **Lucide React**: Beautiful icons

## Project Structure

```
anime-roast-generator/
├── backend/
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration management
│   ├── security.py          # Rate limiting & validation
│   ├── models.py            # Pydantic models
│   ├── requirements.txt     # Python dependencies
│   └── Dockerfile           # Backend container
├── frontend/
│   ├── src/
│   │   ├── App.jsx          # Main component
│   │   ├── components/      # React components
│   │   └── styles/          # CSS styles
│   ├── package.json         # Node dependencies
│   ├── Dockerfile           # Frontend container
│   └── nginx.conf           # Nginx configuration
├── docker-compose.yml       # Docker orchestration
└── .env.example             # Environment template
```

## Quick Start

### Prerequisites
- Docker and Docker Compose
- Gemini API key (get one at https://makersuite.google.com/app/apikey)

### 1. Clone and Setup

```bash
git clone https://github.com/oddava/anime-roast-generator
cd anime-roast-generator
```

### 2. Configure Environment

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your Gemini API key
nano .env
```

Edit the `.env` file:
```env
GEMINI_API_KEY=your_actual_api_key_here
```

### 3. Run with Docker

```bash
# Build and start all services
docker-compose up --build

# Or run in background
docker-compose up -d --build
```

### 4. Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

### 5. Stop the Application

```bash
# Stop containers
docker-compose down

# Stop and remove volumes (if using Redis)
docker-compose down -v
```

## Development

### Running Backend Locally

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp ../.env.example .env
# Edit .env with your API key

# Run the server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Running Frontend Locally

```bash
cd frontend

# Install dependencies
npm install

# Create .env file
echo "VITE_API_URL=http://localhost:8000" > .env

# Run development server
npm run dev
```

## API Endpoints

### POST /api/generate-roast
Generate a roast for an anime.

**Request:**
```json
{
  "anime_name": "Naruto"
}
```

**Response:**
```json
{
  "anime_name": "Naruto",
  "roast": "The generated roast text...",
  "success": true
}
```

**Rate Limit:** 10 requests per minute per IP

### GET /health
Health check endpoint.

## Security Features

1. **API Key Protection**: Gemini API key stored in environment variables, never exposed to frontend
2. **Rate Limiting**: 10 requests per minute per IP using SlowAPI
3. **Input Validation**: 
   - Maximum 100 characters for anime names
   - Regex pattern validation
   - SQL injection and XSS prevention
4. **CORS**: Configured to only allow requests from specified frontend origin
5. **Request Logging**: All requests logged with IP, timestamp, and success status
6. **Error Handling**: Graceful error responses without exposing sensitive information

## Customization

### Changing Rate Limits

Edit `.env`:
```env
RATE_LIMIT_PER_MINUTE=20  # Change to your preferred limit
```

### Using a Different Gemini Model

Edit `.env`:
```env
GEMINI_MODEL=gemini-pro  # Or another available model
```

### Adding Redis for Distributed Rate Limiting

Uncomment the Redis service in `docker-compose.yml` and update `config.py` to use Redis.

## Deployment

### Production Considerations

1. **Environment Variables**: Never commit `.env` files to version control
2. **HTTPS**: Use HTTPS in production (configure in nginx.conf)
3. **Rate Limiting**: Consider using Redis for distributed rate limiting across multiple backend instances
4. **Monitoring**: Set up log aggregation and monitoring (e.g., using ELK stack or Datadog)
5. **Scaling**: Use Docker Swarm or Kubernetes for horizontal scaling

### Deploy to Cloud

The application is containerized and can be deployed to any cloud provider:

- **AWS**: Use ECS or EKS
- **Google Cloud**: Use Cloud Run or GKE
- **Azure**: Use Container Instances or AKS
- **Railway/Render**: Direct Docker deployment support

## Troubleshooting

### Backend won't start
- Check that `GEMINI_API_KEY` is set in `.env`
- Verify Docker is running
- Check logs: `docker-compose logs backend`

### Rate limit errors
- Wait 1 minute between requests
- Check `RATE_LIMIT_PER_MINUTE` in `.env`

### CORS errors
- Verify `FRONTEND_URL` in backend `.env` matches actual frontend URL
- Check browser console for detailed error messages

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

MIT License - feel free to use this project for personal or commercial purposes.

## Acknowledgments

- Built with ❤️ for anime fans who can take a joke
- Powered by Google's Gemini AI
- Icons by Lucide
- Fonts by Google Fonts