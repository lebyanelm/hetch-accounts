FROM python:3.7.2-stretch

# Env & Arg variables
ARG USERNAME=pythonssh
ARG USERPASS=sshpass

# Apt update & apt install required packages
# whois: required for mkpasswd
RUN apt update && apt -y install openssh-server whois

# Add a non-root user & set password
RUN useradd -ms /bin/bash $USERNAME
# Save username on a file
RUN echo "$USERNAME" > /.non-root-username

# Set password for non-root user
RUN usermod --password $(echo "$USERPASS" | mkpasswd -s) $USERNAME

# Remove no-needed packages
RUN apt purge -y whois && apt -y autoremove && apt -y autoclean && apt -y clean

# Change to non-root user
USER $USERNAME
WORKDIR /home/$USERNAME

# Create the ssh directory and authorized_keys file
USER $USERNAME
RUN mkdir /home/$USERNAME/.ssh && touch /home/$USERNAME/.ssh/authorized_keys
USER root

WORKDIR /app/
COPY requirements.txt   .

ENV PATH=$PATH:/app/.local/bin:/app/python/bin/
ENV PYTHONPATH=$PYTHONPATH:/app/python
RUN curl https://bootstrap.pypa.io/get-pip.py | python && pip install -r requirements.txt --target=/app/python

# COPY ALL THE REST OF THE SOURCE CODE
COPY .           .

WORKDIR /app/

# SETUP FLASK APP TO RUN
WORKDIR /app/

EXPOSE 5000
CMD ["uwsgi", "app.ini"]
HEALTHCHECK --interval=5s CMD [ curl -f http://localhost:5000/status ] || exit 1