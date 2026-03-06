FROM public.ecr.aws/docker/library/python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app
ENV PYTHONPATH=/app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential pkg-config default-libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY . /app

RUN sed -i 's/\r$//' /app/entrypoint.sh && chmod +x /app/entrypoint.sh
ENTRYPOINT ["/app/entrypoint.sh"]

EXPOSE 8100
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8100"]

# FROM python:3.11-slim

# ENV PYTHONDONTWRITEBYTECODE=1
# ENV PYTHONUNBUFFERED=1
# ENV PYTHONPATH=/app

# WORKDIR /app

# # System deps:
# # - build-essential/pkg-config/default-libmysqlclient-dev: build mysqlclient
# # - libglib2.0-0 libgl1 libsm6 libxext6 libxrender1: OpenCV runtime (avoid libGL errors)
# RUN apt-get update && apt-get install -y --no-install-recommends \
#     build-essential \
#     pkg-config \
#     default-libmysqlclient-dev \
#     libglib2.0-0 \
#     libgl1 \
#     libsm6 \
#     libxext6 \
#     libxrender1 \
#     && rm -rf /var/lib/apt/lists/*

# COPY requirements.txt /app/requirements.txt
# RUN pip install --no-cache-dir -r /app/requirements.txt

# COPY . /app

# RUN sed -i 's/\r$//' /app/entrypoint.sh && chmod +x /app/entrypoint.sh
# ENTRYPOINT ["/app/entrypoint.sh"]

# EXPOSE 8100
# CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8100"]