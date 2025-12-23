EZ Trip - Local Development Guide

This project is fully containerized using Docker, allowing you to run the Frontend, Backend, and Database without installing Python, Node.js, or MongoDB locally.
Prerequisites

    Docker and Docker Compose installed on your machine.

        Get Docker Desktop

Quick Start
1. Environment Setup

The backend requires an API key for the LLM service (Emergent/OpenAI). You need to provide this environment variable.

Create a .env file in the root directory (same level as docker-compose.yml) or export the variable in your terminal:
Bash

EMERGENT_LLM_KEY=your_api_key_here

2. Build and Run

Open your terminal in the project root directory and run:
Bash

docker-compose up --build

This command will:

    Pull the MongoDB image.

    Build the Python backend image and install dependencies.

    Build the React frontend image and install dependencies.

    Start all services.

Note: The first run may take a few minutes to download images and install packages.
3. Access the Application

Once the logs show that the services are running:

    Frontend (App): Open http://localhost:3000

    Backend (API Docs): Open http://localhost:8000/docs

    MongoDB: Accessible locally on localhost:27017

Development

The Docker setup is configured for active development:

    Hot Reloading: The source code directories (backend/ and frontend/) are mounted into the containers. Changes you make to the code on your host machine will automatically trigger a reload in the container.

    Persisted Data: Database data is stored in a Docker volume (mongodb_data), so your users and trips will persist even if you restart the containers.