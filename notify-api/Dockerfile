FROM python:3.10.4-bullseye
USER root

ARG VCS_REF="missing"
ARG BUILD_DATE="missing"

ENV VCS_REF=${VCS_REF}
ENV BUILD_DATE=${BUILD_DATE}

LABEL org.label-schema.vcs-ref=${VCS_REF} \
    org.label-schema.build-date=${BUILD_DATE}

# Create working directory
RUN mkdir /opt/app-root && chmod 755 /opt/app-root
WORKDIR /opt/app-root

# Install the requirements
COPY ./requirements.txt .

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN pip install .

USER 1001

# Run the server
ENV PYTHONPATH=/opt/app-root/src

EXPOSE 8080

CMD ["gunicorn", "--bind", "0.0.0.0:8080",  "--config", "/opt/app-root/gunicorn_config.py", "wsgi:application"]
