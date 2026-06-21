# setting up the base image
FROM python:3.11-slim

# setting up the working directory
WORKDIR /app

# copying the requirements file and installing the dependencies
COPY requirements-docker.txt .
RUN pip install --no-cache-dir -r requirements-docker.txt --extra-index-url https://download.pytorch.org/whl/cpu

# copying the rest of the application code
COPY src/app_pinecone.py .

# exposing the port for the application
EXPOSE 8000

# Running with port mapping + .env file
CMD ["uvicorn", "app_pinecone:app", "--host", "0.0.0.0", "--port", "8000"]

# Running with volume mapping + .env file

# build the Docker image
# docker build -t humanitarian-report-agent123 .

# running the Docker container with port mapping and volume mapping
# docker run -p 8000:8000 --env-file .env humanitarian-report-agent

# running with volumne(persistent storage) mapping + .env file
# docker run -p 8000:8000 --env-file .env \
# -v $(pwd)/lang_food_poverty_output:/app/lang_food_poverty_output \
# humanitarian-report-agent
