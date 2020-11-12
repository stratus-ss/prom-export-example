FROM centos:8
RUN dnf install -y platform-python-pip python3 && \
  pip3 install prometheus_client

RUN mkdir -p /app
COPY client.py /app
EXPOSE 8080
CMD ["python3", "/app/client.py"]
