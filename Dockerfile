FROM python:3.11-slim

WORKDIR /app

# отключаем кэширование *.pyc
ENV PYTHONDONTWRITEBYTECODE=1
# отключаем буферизацию вывода, чтобы логи сразу отображались
ENV PYTHONUNBUFFERED=1
# отключаем проверку версии pip при каждом запуске
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

COPY requirements.txt .
RUN pip install --no-cache-dir -U pip setuptools wheel \
    && pip install --no-cache-dir -r requirements.txt

COPY . .

CMD sh -c "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT"