FROM jrottenberg/ffmpeg:4.4-ubuntu2004

# Install Python and pip
RUN apt-get update && \
    apt-get install -y python3-pip python3.11 && \
    ln -s /usr/bin/python3 /usr/bin/python && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Create necessary directories
RUN mkdir -p uploads outputs

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 10000

# Command to run the application
CMD ["gunicorn", "--bind", "0.0.0.0:10000", "app:app"]
