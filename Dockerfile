FROM python:3.10-slim

# Install all dependencies
ADD . /senselink

RUN python -m pip install -r /senselink/requirements.txt
RUN pip install /senselink

# Make non-root user
RUN useradd --create-home appuser
WORKDIR /home/appuser
USER appuser

# Run
CMD ["python", "-m", "senselink"]