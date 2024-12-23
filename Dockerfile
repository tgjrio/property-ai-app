# Use the official Python image as the base
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port that Streamlit will run on (optional, mainly for local development)
EXPOSE 8501

# Command to run the Streamlit app using shell form to enable environment variable expansion
CMD streamlit run main.py --server.port=$PORT --server.address=0.0.0.0