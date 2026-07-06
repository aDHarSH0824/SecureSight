# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies needed for OpenCV, dlib, and PostgreSQL adapter
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    libopenblas-dev \
    liblapack-dev \
    libx11-dev \
    libgtk-3-dev \
    libgl1 \
    libglib2.0-0 \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Set up a new user named "user" with UID 1000
RUN useradd -m -u 1000 user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

# Set work directory
WORKDIR $HOME/app

# Prevent compiler OOM during dlib build by limiting to 1 thread
ENV CMAKE_BUILD_PARALLEL_LEVEL=1
ENV MAKEFLAGS="-j1"

# Install python dependencies
COPY requirements.txt $HOME/app/
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r $HOME/app/requirements.txt

# Copy project files and change ownership to user
COPY --chown=user:user . $HOME/app

# Ensure the non-root user owns the app directory and all its files
RUN chown -R user:user $HOME/app

# Switch to the non-root user
USER user

# Pre-initialize the database and folder structures at build time to prevent Gunicorn process race conditions
RUN python scripts/db_setup.py

# Expose Flask web application ports
EXPOSE 7860
EXPOSE 5000

# Start Flask web interface via Gunicorn in production mode on both ports
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:7860", "-b", "0.0.0.0:5000", "--access-logfile", "-", "src.web.app:app"]
