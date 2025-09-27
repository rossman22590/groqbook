FROM python:3.9-slim

# Install system dependencies for WeasyPrint
RUN apt-get update && apt-get install -y --no-install-recommends \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["streamlit", "run", "main.py", "--server.port=8000"]# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Install system dependencies for WeasyPrint and GTK
RUN apt-get update && apt-get install -y \
    libgdk-pixbuf2.0-0 \
    libpangocairo-1.0-0 \
    libpangoft2-1.0-0 \
    libcairo2 \
    libffi-dev \
    libgirepository1.0-dev \
    libcairo2-dev \
    pkg-config \
    python3-gi \
    gir1.2-pango-1.0 \
    gir1.2-gtk-3.0 \
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

# Expose the port on which the Streamlit app will run
EXPOSE 8501

# Command to run the Streamlit app
CMD ["python3", "-m", "streamlit", "run", "main.py", "--server.port=8501", "--server.address=0.0.0.0"]
