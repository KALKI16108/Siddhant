File Name: requirements.txt
```text
fastapi
uvicorn
sqlalchemy
psycopg2-binary
pydantic
httpx
google-generativeai
GitPython
```

File Name: Dockerfile
```dockerfile
# Use a clean, lightweight base image for production
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file first to leverage Docker's layer caching
# This allows rebuilding dependencies only when requirements.txt changes
COPY requirements.txt .

# Install the required production dependencies
# --no-cache-dir prevents pip from storing cache, reducing image size
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
# Assuming the application's root directory (where Dockerfile resides)
# contains the main app files, including app.py
COPY . .

# Expose port 8000 for incoming API requests
EXPOSE 8000

# Define the command to run the application using uvicorn
# 'app:app' refers to a FastAPI instance named 'app' within a file named 'app.py'
# --host 0.0.0.0 makes the app accessible from outside the container
# --port 8000 ensures it listens on the exposed port
# Auto-reloads are turned off for production safety
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
```