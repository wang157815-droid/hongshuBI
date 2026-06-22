# 服务器测试部署说明

本部署方式用于测试环境，继续使用 SQLite，不切 PostgreSQL。

## 持久化目录

`compose.yaml` 会把服务器项目目录下的 `docker-data` 挂载到容器内 `/data`：

- SQLite 数据库：`docker-data/db.sqlite3`
- 上传文件：`docker-data/storage/redbook_uploads`

## 常用命令

```bash
mkdir -p docker-data/storage/redbook_uploads
```

```bash
docker compose build
```

默认构建只使用阿里云 PyPI 镜像，避免服务器访问 `files.pythonhosted.org` 超时。

如果国内镜像仍然缺包，可以临时指定官方 PyPI 作为兜底源重建：

```bash
docker compose build --build-arg PIP_INDEX_URL=https://mirrors.aliyun.com/pypi/simple/ --build-arg PIP_EXTRA_INDEX_URL=https://pypi.org/simple --build-arg PIP_DEFAULT_TIMEOUT=180 --build-arg PIP_RETRIES=20
```

```bash
docker compose up -d
```

```bash
docker compose logs -f
```

```bash
docker compose ps
```

```bash
docker compose down
```

如果服务器 80 端口已被占用，可以这样启动：

```bash
WEB_PORT=8080 docker compose up -d
```
