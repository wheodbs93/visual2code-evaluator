FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir python-docx

COPY app ./app
COPY data ./data
COPY renders ./renders
COPY demo_sites ./demo_sites
COPY web.py .

ENV PYTHONUNBUFFERED=1
ENV PORT=10000

EXPOSE 10000

CMD ["python", "web.py"]
