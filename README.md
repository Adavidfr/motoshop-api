uv add django djangorestframework djangorestframework-simplejwt \
django-filter django-cors-headers psycopg2-binary python-decouple

New-Item -ItemType Directory -Force motoshop\models, motoshop\serializers, motoshop\views, motoshop\tests

$files = @(
    "motoshop\models\__init__.py",
    "motoshop\serializers\__init__.py",
    "motoshop\views\__init__.py",
    "motoshop\tests\__init__.py",
    "motoshop\filters.py",
    "motoshop\permissions.py"
)
$files | ForEach-Object { New-Item -ItemType File -Force $_ }

CREATE USER motoshop_user WITH PASSWORD 'motoshop_pass';
CREATE DATABASE motoshop_db OWNER motoshop_user;
GRANT ALL PRIVILEGES ON DATABASE motoshop_db TO motoshop_user;
\q