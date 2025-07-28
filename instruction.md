# Docker Setup for Persona-Based Document Intelligence

This document provides instructions for running the application using Docker.

## Quick Start

### Using Docker Compose (Recommended)

1. **Build and run the application:**
   ```bash
   docker-compose up --build
   ```

2. **Access the application:**
   - Open your browser and go to `http://localhost:8000`
   - The API will be available at `http://localhost:8000/process/`

3. **Stop the application:**
   ```bash
   docker-compose down
   ```

### Using Docker directly

1. **Build the image:**
   ```bash
   docker build -t persona-doc-intelligence .
   ```

2. **Run the container:**
   ```bash
   docker run -p 8000:8000 persona-doc-intelligence
   ```

## Docker Image

The application uses a single Dockerfile that:
- Based on `python:3.11-slim`
- Includes all necessary system dependencies for PDF processing and AI models
- Suitable for both development and production
- Includes health checks and proper environment setup

## Environment Variables

The following environment variables can be configured:

- `PYTHONUNBUFFERED=1`: Ensures Python output is sent straight to terminal
- `PYTHONDONTWRITEBYTECODE=1`: Prevents Python from writing .pyc files
- `DEBIAN_FRONTEND=noninteractive`: Prevents interactive prompts during package installation

## Health Checks

The application includes health checks that:
- Check if the application is responding on port 8000
- Run every 30 seconds
- Have a 30-second timeout
- Retry 3 times before marking as unhealthy

## Volumes

When using Docker Compose, the following volumes are mounted:
- `./templates:/app/templates:ro`: Templates directory (read-only)
- `./processing:/app/processing:ro`: Processing modules (read-only)

## Troubleshooting

### Common Issues

1. **Port already in use:**
   ```bash
   # Check what's using port 8000
   lsof -i :8000
   # Or use a different port
   docker run -p 8001:8000 persona-doc-intelligence
   ```

2. **Permission issues:**
   ```bash
   # Make sure the start script is executable
   chmod +x start.sh
   ```

3. **Memory issues with large PDFs:**
   ```bash
   # Increase memory limit
   docker run -p 8000:8000 --memory=4g persona-doc-intelligence
   ```

### Logs

View application logs:
```bash
docker-compose logs -f


docker logs <container_id>
```

## Security Considerations

- Only necessary system dependencies are installed
- Health checks help monitor application status
- Proper environment variable configuration
- Clean build process with .dockerignore

## Performance Optimization

- Consider using Docker volumes for persistent data
- Monitor memory usage when processing large PDFs
- Use appropriate resource limits in production
- The image includes all necessary dependencies for optimal performance 