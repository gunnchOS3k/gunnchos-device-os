FROM debian:bookworm-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    nginx \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /gunnchos

COPY requirements.txt ./
RUN pip3 install --break-system-packages -r requirements.txt pyyaml || pip3 install -r requirements.txt pyyaml

COPY gunnchos_device_os ./gunnchos_device_os
COPY config ./config
COPY apps/launcher_mock ./apps/launcher_mock

RUN cd apps/launcher_mock && npm install && npm run build

COPY os_build/linux_desktop/nginx.conf /etc/nginx/sites-available/default
COPY os_build/linux_desktop/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 80

ENTRYPOINT ["/entrypoint.sh"]
