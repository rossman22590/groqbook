# Use an official Python runtime as a parent image
FROM python:3.8-slim

# Set non-interactive installation
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies for WeasyPrint
RUN apt-get update && apt-get install -y \
    libgirepository1.0-dev \
    gcc \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    shared-mime-info \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Set the working directory to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Make port 8501 available to the world outside this container
EXPOSE 8501

# Define environment variable for Groq API Key
ENV GROQ_API_KEY=your_groq_api_key_here

# Run streamlit when the container launches
CMD ["streamlit", "run", "main.py"]
