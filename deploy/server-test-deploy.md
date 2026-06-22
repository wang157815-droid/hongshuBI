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
