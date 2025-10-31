# 1. Wybieramy Python
FROM python:3.10

WORKDIR /app

# 2. Instalacja zależności systemowych
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gdal-bin libgdal-dev libproj-dev libgeos-dev \
    postgresql-client python3-dev curl \
    && rm -rf /var/lib/apt/lists/*

# 3. Symlink dla GDAL
RUN GDAL_LIB=$(ldconfig -p | grep libgdal.so | head -n1 | awk '{print $4}') && \
    ln -sf $GDAL_LIB /usr/lib/libgdal.so

# 4. Kopiujemy tylko requirements i instalujemy pakiety
COPY requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# 5. Kopiujemy cały projekt **przed collectstatic**
COPY . .

# 6. Uruchamiamy collectstatic (TERAZ manage.py istnieje)
RUN python manage.py collectstatic --noinput

# 7. Test GDAL
RUN python -c "from ctypes import CDLL; CDLL('$GDAL_LIBRARY_PATH')"

# 8. Port
EXPOSE 8080

# 9. Uruchomienie Gunicorna
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8080", "--workers", "3"]