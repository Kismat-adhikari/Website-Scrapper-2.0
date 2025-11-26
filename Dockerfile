# Use Apify's Python base image with Playwright pre-installed
FROM apify/actor-python-playwright:3.11

# Copy requirements first for better caching
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers (Chromium only for speed)
RUN playwright install chromium
RUN playwright install-deps chromium

# Copy source code
COPY . ./

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV APIFY_HEADLESS=1

# Run the actor
CMD ["python", "-m", "main"]
