FROM python:3.7.3-alpine
WORKDIR /app
COPY requirements.txt
RUN pip install -r requirements.txt
CMD ["python", "your_app.py"]