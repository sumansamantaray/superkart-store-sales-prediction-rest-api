# Use an official Python runtime as a parent image
FROM python:3.9-slim-buster

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Expose port 7860 for the Flask application
EXPOSE 7860

# Define environment variable
ENV FLASK_APP=app.py

# Run the Flask application using Gunicorn for production
# Gunicorn is a production-ready WSGI HTTP server for Unix.
# You might need to install gunicorn in your requirements.txt if not already there.
# For development, you can use `flask run --host=0.0.0.0`
CMD ["gunicorn", "app:app", "-w", "4", "-b", "0.0.0.0:7860"]

# Command to run the Flask application using the development server
# This is suitable for Codespaces for initial setup and testing
#CMD ["flask", "run", "--host=0.0.0.0", "--port=5000"]
