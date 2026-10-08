FROM python:3.12

RUN useradd -ms /bin/bash appuser

WORKDIR /home/appuser/src

COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=appuser:appuser . .

USER appuser

CMD ["sh", "-c", "alembic upgrade head && exec uvicorn app.main:app --host 0.0.0.0 --port 8000"]
#the shell stays as PID 1 and may not forward stop signals to uvicorn, so docker stop waits 10 seconds and then kills it. Use exec, it replaces the shell with uvicorn so signals arrive properly