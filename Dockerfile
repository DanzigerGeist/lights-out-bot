FROM python:3-alpine
WORKDIR /app
COPY requirements.txt .
COPY main.py .
RUN pip3 install -r requirements.txt
CMD ["python3", "main.py"]