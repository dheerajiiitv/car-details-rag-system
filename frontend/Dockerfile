# Use Python base image
FROM python:3.9-slim

# Set working directory
WORKDIR /

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .


# Expose the port the app runs on
EXPOSE 8501

# Command to run the application
CMD ["streamlit", "run", "app.py"]
