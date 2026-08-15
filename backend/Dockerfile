# Tilmon backend — FastAPI + uv.
# Migratsiyalar konteyner ichida (docker-entrypoint.sh), so'ng uvicorn.
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim
WORKDIR /app

# print()/log darhol chiqsin — konteynerda TTY yo'q, aks holda buferlanadi.
ENV PYTHONUNBUFFERED=1

# Avval faqat lock fayllar — bog'liqliklar qatlami keshlanadi.
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-install-project --no-dev

# Kod va ma'lumotlar. data/ shart: ontologiya YAML fayllarni /app/data dan o'qiydi.
COPY alembic.ini docker-entrypoint.sh ./
COPY migrations ./migrations
COPY app ./app
COPY data ./data
RUN chmod +x docker-entrypoint.sh

EXPOSE 8000
ENTRYPOINT ["./docker-entrypoint.sh"]
CMD [".venv/bin/uvicorn", "app.api:app", "--host", "0.0.0.0", "--port", "8000"]
