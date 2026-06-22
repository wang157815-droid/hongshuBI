FROM node:20-alpine AS web

WORKDIR /opt/vue-fastapi-admin/web
RUN npm config set registry https://registry.npmmirror.com && npm install -g pnpm
COPY /web/package.json /web/pnpm-lock.yaml ./
RUN --mount=type=cache,target=/root/.local/share/pnpm/store,id=web-pnpm-store \
    pnpm i --frozen-lockfile
COPY /web ./
RUN pnpm run build


FROM python:3.11-slim-bullseye

WORKDIR /opt/vue-fastapi-admin

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked,id=core-apt \
    --mount=type=cache,target=/var/lib/apt,sharing=locked,id=core-apt \
    sed -i "s@http://.*.debian.org@http://mirrors.ustc.edu.cn@g" /etc/apt/sources.list \
    && rm -f /etc/apt/apt.conf.d/docker-clean \
    && ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime \
    && echo "Asia/Shanghai" > /etc/timezone \
    && apt-get update \
    && apt-get install -y --no-install-recommends gcc python3-dev bash nginx vim curl procps net-tools

COPY /requirements.txt ./requirements.txt
RUN --mount=type=cache,target=/root/.cache/pip,id=core-pip \
    pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

ADD . .
COPY /deploy/entrypoint.sh .

COPY --from=web /opt/vue-fastapi-admin/web/dist /opt/vue-fastapi-admin/web/dist
ADD /deploy/web.conf /etc/nginx/sites-available/web.conf
RUN rm -f /etc/nginx/sites-enabled/default \
    && ln -sf /etc/nginx/sites-available/web.conf /etc/nginx/sites-enabled/web.conf

ENV LANG=zh_CN.UTF-8
EXPOSE 80

ENTRYPOINT [ "sh", "entrypoint.sh" ]
