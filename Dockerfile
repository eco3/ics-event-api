# Use the official Python image from Docker Hub
FROM python:3.12-slim-bookworm
# Install uv and uvx from the Astral repository
COPY --from=ghcr.io/astral-sh/uv:0.7.12 /uv /uvx /bin/

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Sync the project dependencies using uv
RUN uv sync --locked

# Make port 5000 available to the world outside this container
EXPOSE 5000

# Define environment variable
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV FLASK_DEBUG=False

# Run the application
CMD ["uv", "run", "flask", "run", "--host=0.0.0.0", "--port=5000"]
