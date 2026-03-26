FROM apache/spark-py

WORKDIR /app

USER root

# Copy the source code into the container.
COPY . .

# Install Python dependencies.
RUN python3 -m pip install --no-cache-dir -r requirements.txt


# Expose the port that the application listens on.
EXPOSE 5000

# Run the application.
CMD gunicorn 'app:app' --bind=0.0.0.0:5000
