FROM python:3.9-slim

WORKDIR /app

# Install required packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY Hasaki_crawling.py .

# Run the scraper
CMD ["python", "Hasaki_crawling.py"]