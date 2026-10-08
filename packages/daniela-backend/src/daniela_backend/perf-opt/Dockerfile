FROM aig-base:latest

WORKDIR /app

COPY --chown=appuser:appuser ./backend/perf-opt/ .

ENV SERVICE_NAME=perf
ENV PORT=9998

EXPOSE 9998

CMD ["gunicorn", "--bind", "0.0.0.0:9998", "--workers", "2", "--threads", "4", "--timeout", "120", "server:app"]
