FROM python:3.7.2-stretch

# Env & Arg variables
ARG USERNAME=pythonssh
ARG USERPASS=sshpass

# Apt update & apt install required packages
# whois: required for mkpasswd
RUN apt update && apt -y install openssh-server whois jq

# Add a non-root user & set password
RUN useradd -ms /bin/bash $USERNAME
# Save username on a file ¿?¿?¿?¿?¿?
#RUN echo "$USERNAME" > /.non-root-username

# Set password for non-root user
RUN usermod --password $(echo "$USERPASS" | mkpasswd -s) $USERNAME

# Remove no-needed packages
RUN apt purge -y whois && apt -y autoremove && apt -y autoclean && apt -y clean

# Change to non-root user
USER $USERNAME
WORKDIR /home/$USERNAME

# Copy the entrypoint
# COPY entrypoint.sh entrypoint.sh
# RUN chmod +x /entrypoint.sh

# Create the ssh directory and authorized_keys file
USER $USERNAME
RUN mkdir /home/$USERNAME/.ssh && touch /home/$USERNAME/.ssh/authorized_keys
USER root

WORKDIR /app/
COPY requirements.txt   .

ENV PATH=$PATH:/app/.local/bin:/app/python/bin/
ENV PYTHONPATH=$PYTHONPATH:/app/python
ENV ENVIRONMENT=production
ENV SELF_ENDPOINT=http://apis.hetchfund.capital/accounts

# Production app environment
ENV SEED=20180175ca60a0129bd58197da0

# Database Management and Connection
ENV ARANGO_URL="https://b9bd58197da0.arangodb.cloud:18529"
ENV ARANGO_USERNAME="root"
ENV ARANGO_PASSWORD="mkwT0GWdt1l74jAJAN69"
ENV DATABASE_NAME="hetchfund_capital_sandbox"

RUN pip install -r requirements.txt --target=/app/python

# COPY ALL THE REST OF THE SOURCE CODE
COPY .           .

WORKDIR /app/

# SETUP FLASK APP TO RUN
WORKDIR /app/

# PRODUCTION
CMD gunicorn --bind 0.0.0.0:4000 run:server_instance
EXPOSE 4000

# HEALTHCHECK CMD curl --fail http://0.0.0.0:4000/accounts/status || exit 1
