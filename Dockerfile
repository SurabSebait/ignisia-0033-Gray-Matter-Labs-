FROM public.ecr.aws/lambda/python:3.11

# Install system dependencies (needed for ML libs)
RUN yum install -y gcc gcc-c++ make

# Upgrade pip/tools and install wheel
RUN pip install --upgrade pip setuptools wheel

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy your code
COPY lambda_function.py .
COPY embedder.py .
COPY parser.py .

# Set handler
CMD ["lambda_function.lambda_handler"]