FROM python:3.8.5
ENV http_proxy http://proxy.fcen.uba.ar:8080
ENV https_proxy http://proxy.fcen.uba.ar:8080
# Password is taken from the file 'auth', in the root of
# the repo. This file should be in .gitignore to prevent it from
# being committed.
RUN apt-get update && apt-get install -y python3-opencv openssh-server sudo
RUN useradd -rm -d /home/ubuntu -s /bin/bash -g root -G sudo -u 1000 itba 
RUN mkdir /var/run/sshd
ADD auth /
RUN cat /auth | chpasswd 
RUN sed -i 's/#*PermitRootLogin prohibit-password/PermitRootLogin yes/g' /etc/ssh/sshd_config
# SSH login fix. Otherwise user is kicked off after login
RUN sed -i 's@session\s*required\s*pam_loginuid.so@session optional pam_loginuid.so@g' /etc/pam.d/sshd
ENV NOTVISIBLE "in users profile"
RUN echo "export VISIBLE=now" >> /etc/profile
EXPOSE 22
RUN /etc/init.d/ssh start

RUN mkdir /web
ADD requirements.txt /web
WORKDIR /web
RUN pip install -r requirements.txt

CMD /etc/init.d/ssh start && python pf_filament_tracking.py
