# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Install system dependencies for WeasyPrint
RUN apt-get update && apt-get install -y \
    libgdk-pixbuf2.0-0 \
    libpangocairo-1.0-0 \
    libpangoft2-1.0-0 \
    libcairo2 \
    libffi-dev \
    shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt /app/

# Install the dependencies from the requirements file
RUN pip install --no-cache-dir -r requirements.txt

# Copy the current directory contents into the container at /app
COPY . /app

# Ensure the .env file is present in the container
COPY .env /app/.env

# Set the Groq API key as an environment variable (if not already in .env)
ENV GROQ_API_KEY=${GROQ_API_KEY}

# Expose the port on which the Streamlit app will run
EXPOSE 8501

# Command to run the Streamlit app
CMD ["python3", "-m", "streamlit", "run", "main.py", "--server.port=8501", "--server.address=0.0.0.0"]
