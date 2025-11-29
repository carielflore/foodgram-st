set -e

echo "Foodgram Backend Starting"

echo "Waiting for PostgreSQL to be ready..."
while ! nc -z $POSTGRES_HOST 5432; do
    echo "Waiting for PostgreSQL at $POSTGRES_HOST:5432..."
    sleep 1
done
echo "PostgreSQL is ready!"

if [ ! -f "/app/users/migrations/0001_initial.py" ]; then
    echo "Creating initial migrations..."
    python manage.py makemigrations users
    python manage.py makemigrations recipes
    python manage.py makemigrations api
fi

echo "Applying database migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Starting Gunicorn"
exec gunicorn --bind 0.0.0.0:8000 --workers 3 --timeout 120 foodgram.wsgi:application
