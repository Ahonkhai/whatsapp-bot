FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN useradd --create-home --uid 10001 whatsappbot \
    && chown -R whatsappbot:whatsappbot /app
USER whatsappbot

HEALTHCHECK --interval=60s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "import os,urllib.request; urllib.request.urlopen(f'http://127.0.0.1:{os.environ.get(\"PORT\",\"8080\")}/health', timeout=5)" || exit 1

# Railway (and most PaaS) inject PORT at runtime, so the bind has to read it
# at container start rather than being baked into the image.
CMD ["sh", "-c", "gunicorn -w 2 -b 0.0.0.0:${PORT:-8080} run:app"]
