FROM python:3.11-slim

WORKDIR /app

COPY engine/scale_engine/ ./scale_engine/

# server.py:31 hace `from optimization import ...` y se refiere al MODULO
# LOCAL scale_engine/optimization.py (OptimizationManager, QueryPlan...),
# NO al servicio optimization/ (que ni los exporta). Con /app primero,
# el paquete del servicio lo eclipsaba -> ImportError. El dir propio va
# primero, igual que en host resuelve conftest (engine/scale_engine en path).
ENV PYTHONPATH=/app/scale_engine:/app
ENV PYTHONUNBUFFERED=1

RUN pip install --no-cache-dir flask

EXPOSE 9820

CMD ["python", "-m", "scale_engine.server"]
