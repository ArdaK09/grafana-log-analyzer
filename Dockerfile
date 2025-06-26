# Use official Python 3.9 image
FROM python:3.9-slim

# Set the working directory inside the container
WORKDIR /app

COPY requirements.txt .

# Install Python dependencies
RUN python3 -m pip install --no-cache-dir -r requirements.txt

# Copy the source code and resources into the container
COPY src/ ./src/
COPY resources/ ./resources/
COPY out/ ./out/
COPY templates/ ./src/templates/
COPY static ./src/static/

# Command to run the Flask app
CMD ["python3", "./src/app.py"]
