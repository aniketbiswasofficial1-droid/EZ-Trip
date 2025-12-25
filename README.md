# EZ-Trip - Group Expense Splitting & AI Trip Planner

EZ-Trip is a comprehensive travel planning application with AI-powered trip planning, group expense tracking, and settlement management.

## 🚀 Quick Start

### Prerequisites

- **Docker and Docker Compose** installed on your machine
  - [Get Docker Desktop](https://www.docker.com/products/docker-desktop)

### Local Development

1. **Environment Setup**

   Create a `.env` file in the root directory:
   ```bash
   cp .env.example .env
   ```
   
   Fill in the required environment variables (see [Environment Variables](#environment-variables) below).

2. **Start Development Server**

   ```bash
   docker-compose up --build
   ```

   This will start:
   - Frontend (React): http://localhost:3000
   - Backend (FastAPI): http://localhost:8000
   - API Documentation: http://localhost:8000/docs
   - MongoDB: localhost:27017

3. **Hot Reloading**

   Both frontend and backend support hot reloading. Changes to code will automatically refresh the application.

## 🏭 Production Deployment

For production deployment, use the production docker-compose configuration:

```bash
docker-compose -f docker-compose.prod.yml up --build -d
```

**Important Production Steps:**

1. Set `ENVIRONMENT=production` in your `.env` file
2. Configure all required environment variables (see `.env.production.template`)
3. Update `CORS_ORIGINS` and `ALLOWED_ORIGINS` with your production domains
4. Enable HTTPS/TLS for secure communication
5. Consider using MongoDB with authentication

See [DEPLOYMENT.md](DEPLOYMENT.md) for comprehensive production deployment guide.

## 🔐 Environment Variables

### Required Variables

Copy the `.env.example` file and fill in the following required variables:

- **`OPENAI_API_KEY`**: Your OpenAI API key from https://platform.openai.com/api-keys
- **`GOOGLE_CLIENT_ID`**: Google OAuth client ID from https://console.cloud.google.com/apis/credentials
- **`GOOGLE_CLIENT_SECRET`**: Google OAuth client secret
- **`SMTP_USERNAME`**: Email address for sending notifications
- **`SMTP_PASSWORD`**: Email password or app-specific password
- **`REACT_APP_GOOGLE_CLIENT_ID`**: Same as GOOGLE_CLIENT_ID (for frontend)
- **`REACT_APP_BACKEND_URL`**: Backend API URL (e.g., http://localhost:8000)

### Optional Variables

- **`CORS_ORIGINS`**: Comma-separated list of allowed origins
- **`RATE_LIMIT_PER_MINUTE`**: API rate limit per IP (default: 60)
- **`LOG_LEVEL`**: Logging level (DEBUG, INFO, WARNING, ERROR)

See `.env.production.template` for a complete list with documentation.

## 🛠 Development

### Project Structure

```
EZ-Trip/
├── backend/          # Python FastAPI backend
│   ├── server.py     # Main API server
│   ├── trip_planner.py # AI trip planning service
│   ├── email_service.py # Email notifications
│   └── Dockerfile
├── frontend/         # React frontend
│   ├── src/
│   └── Dockerfile
├── docker-compose.yml       # Development configuration
├── docker-compose.prod.yml  # Production configuration
└── .env.example            # Environment variable template
```

### Running Tests

```bash
# Backend tests
cd backend
python -m pytest

# Frontend tests
cd frontend
yarn test
```

## 📚 Features

- **AI Trip Planner**: Generate comprehensive trip itineraries with pricing comparisons
- **Expense Tracking**: Track group expenses with multiple payers and splits
- **Smart Settlements**: Calculate optimal debt settlements
- **Google OAuth**: Secure authentication via Google Sign-In
- **Email Notifications**: Automated trip and expense notifications
- **Multi-Currency Support**: Handle expenses in different currencies
- **Profile Management**: Customizable user profiles with photo upload

## 🔒 Security

- Environment-based security settings (development vs production)
- HTTP-only secure cookies in production
- CORS protection with configurable origins
- Security headers (X-Frame-Options, X-Content-Type-Options, etc.)
- Non-root Docker containers in production
- Input validation and sanitization

See [SECURITY.md](SECURITY.md) for security best practices and vulnerability reporting.

## 📖 API Documentation

Once the backend is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## ⚠️ Important Notes

- **Never commit `.env` files** with real credentials
- Use different credentials for development and production
- Regularly rotate API keys and secrets
- Enable 2FA on all external accounts (Google, email providers)
- Monitor application logs for security issues
