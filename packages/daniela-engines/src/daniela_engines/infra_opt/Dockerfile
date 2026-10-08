FROM aig-base:latest

WORKDIR /app

COPY --chown=appuser:appuser ./engine/infra-opt/ .

ENV SERVICE_NAME=infra
ENV PORT=9700

EXPOSE 9700

CMD ["gunicorn", "--bind", "0.0.0.0:9700", "--workers", "2", "--threads", "4", "--timeout", "120", "server:app"]
