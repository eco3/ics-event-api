FROM python:3.12-slim-bookworm
COPY --from=ghcr.io/astral-sh/uv:0.13.7 /uv /uvx /bin/

WORKDIR /app
COPY . /app
RUN uv sync --locked --no-dev

ENV PATH="/app/.venv/bin:$PATH"
ENV FLASK_APP=app.py

EXPOSE 5000
CMD ["flask", "run", "--host=0.0.0.0", "--port=5000"]
