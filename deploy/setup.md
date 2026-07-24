# Deployment Guide — Solgar Internal Platform

Ubuntu 22.04 / 24.04 LTS on a Linux VM.

---

## 1. System packages

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3.10 python3.10-venv python3-pip \
    nginx git pkg-config python3-dev default-libmysqlclient-dev build-essential
```

`default-libmysqlclient-dev` and `build-essential` are required to compile
`mysqlclient`; installation fails without them.

## 2. Application directory

```bash
sudo mkdir -p /var/www/solgar-platform
sudo chown -R $USER:$USER /var/www/solgar-platform
cd /var/www/solgar-platform
```

## 3. Clone the repository

```bash
git clone https://github.com/cnrcvk7/solgar-internal-platform.git .
```

For a private repo, use a deploy key or a personal access token.

## 4. Virtual environment

```bash
python3.10 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## 5. Environment file

```bash
cp .env.example .env
nano .env
```

Fill in:

| Variable | Value |
|---|---|
| `DJANGO_SECRET_KEY` | Generate a new one (see below) |
| `DJANGO_DEBUG` | `False` |
| `ALLOWED_HOSTS` | Server hostname / domain |
| `DB_*` | MySQL connection details |
| `AZURE_AD_*` | From App Registration |

Generate a key:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Restrict permissions — the file holds secrets:

```bash
chmod 600 .env
```

## 6. Database

```bash
python manage.py migrate
python manage.py createsuperuser
```

## 7. Static files

```bash
python manage.py collectstatic --noinput
```

## 8. Log directory

```bash
sudo mkdir -p /var/log/solgar
sudo chown www-data:www-data /var/log/solgar
```

## 9. Permissions

```bash
sudo chown -R www-data:www-data /var/www/solgar-platform
sudo chmod -R 755 /var/www/solgar-platform
```

## 10. Gunicorn service

```bash
sudo cp deploy/gunicorn.service /etc/systemd/system/solgar.service
sudo systemctl daemon-reload
sudo systemctl enable --now solgar
sudo systemctl status solgar
```

Expect `active (running)`. If it fails:

```bash
sudo journalctl -u solgar -n 50 --no-pager
```

## 11. Nginx

Edit `deploy/nginx.conf` and replace `SERVER_NAME_HERE` with the real hostname,
then:

```bash
sudo cp deploy/nginx.conf /etc/nginx/sites-available/solgar
sudo ln -s /etc/nginx/sites-available/solgar /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl reload nginx
```

## 12. Firewall

```bash
sudo ufw allow 'Nginx Full'
sudo ufw allow OpenSSH
sudo ufw enable
sudo ufw status
```

## 13. SSL

For a public domain, Let's Encrypt:

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

For an internal-only host, use the corporate certificate instead — ask IT.

Note: `SECURE_SSL_REDIRECT = True` is active when `DEBUG=False`. Without a
working certificate the site will redirect to HTTPS and fail. Either configure
SSL first, or temporarily disable that setting.

---

## Updating after a code change

```bash
cd /var/www/solgar-platform
source venv/bin/activate
git pull
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart solgar
```

---

## Troubleshooting

| Symptom | Check |
|---|---|
| 502 Bad Gateway | `sudo systemctl status solgar` — is Gunicorn running? |
| Static files missing | Was `collectstatic` run? Is the Nginx `alias` path correct? |
| Redirect loop | Is `X-Forwarded-Proto` set in Nginx? |
| `DisallowedHost` error | Is the hostname in `ALLOWED_HOSTS`? |
| Database connection fails | Check `DB_HOST`, firewall rules, and SSL settings |

Logs:

```bash
sudo journalctl -u solgar -f          # application
sudo tail -f /var/log/nginx/error.log # nginx
sudo tail -f /var/log/solgar/error.log
```