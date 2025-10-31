import csv
import hashlib
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.contrib.gis.geos import Point

from mapa.models import Institution


class Command(BaseCommand):
    help = "Importuje instytucje z pliku CSV i przypisuje deterministyczne współrzędne bez korzystania z zewnętrznych API."

    def add_arguments(self, parser):
        parser.add_argument(
            "csv_path",
            nargs="?",
            default="institutions.csv",
            help="Ścieżka do pliku CSV z danymi instytucji (domyślnie institutions.csv w katalogu głównym).",
        )

    def handle(self, *args, **options):
        csv_path = Path(options["csv_path"]).resolve()
        if not csv_path.exists():
            raise CommandError(f"Nie znaleziono pliku: {csv_path}")

        created = 0
        updated = 0
        skipped = 0

        with csv_path.open(newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            for row_num, row in enumerate(reader, start=1):
                name = self._sanitize(row.get("name"), 255)
                address = self._sanitize(row.get("address"), 500)

                if not name or not address:
                    skipped += 1
                    self.stdout.write(f"[{row_num}] Pominięto – brak nazwy lub adresu")
                    continue

                inst, was_created = Institution.objects.update_or_create(
                    name=name,
                    address=address,
                    defaults=self._build_defaults(row, address),
                )

                if was_created:
                    created += 1
                    action = "Dodano"
                else:
                    updated += 1
                    action = "Zaktualizowano"

                self.stdout.write(f"[{row_num}] {action}: {inst.name}")

        total = Institution.objects.count()
        self.stdout.write(self.style.SUCCESS("\nImport zakończony"))
        self.stdout.write(f"Nowe rekordy : {created}")
        self.stdout.write(f"Zaktualizowane: {updated}")
        self.stdout.write(f"Pominięte    : {skipped}")
        self.stdout.write(f"Łącznie w bazie: {total}")

    def _build_defaults(self, row, address):
        phone_number = self._sanitize(row.get("phone_number"), 200)
        if row.get("phone_number") and "  " in row["phone_number"]:
            phone_number = " / ".join(part.strip() for part in row["phone_number"].split() if part.strip())[:200]

        data = {
            "phone_number": phone_number,
            "type": self._normalize_type(row.get("type")),
            "psychological_help": self._parse_bool(row.get("psychological_help")),
            "legal_help": self._parse_bool(row.get("legal_help")),
            "social_help": self._parse_bool(row.get("social_help")),
            "accommodation": self._parse_bool(row.get("accommodation")),
            "description": self._sanitize(row.get("description"), 2000) or "",
            "opening_hours": self._sanitize(row.get("opening_hours"), 255) or "",
            "email": self._sanitize(row.get("email"), 255) or None,
            "infoline": self._sanitize_infoline(row.get("infoline")),
            "location": self._pseudo_location(address),
        }
        return data

    @staticmethod
    def _sanitize(value, max_length):
        value = (value or "").strip()
        return value[:max_length]

    @staticmethod
    def _sanitize_infoline(value):
        value = (value or "").strip()
        if value.lower() in {"", "nie", "brak"}:
            return None
        return value[:255]

    @staticmethod
    def _parse_bool(value):
        return str(value).strip().lower() in {"true", "1", "tak", "t", "yes"}

    @staticmethod
    def _normalize_type(value):
        value = (value or "").strip().upper()
        return value if value in {"NGO", "GOV"} else "NGO"

    @staticmethod
    def _pseudo_location(address):
        bounds = {
            "lat_min": 49.0,
            "lat_max": 54.8,
            "lon_min": 14.0,
            "lon_max": 24.2,
        }
        digest = hashlib.sha1(address.encode("utf-8")).digest()
        lat_range = bounds["lat_max"] - bounds["lat_min"]
        lon_range = bounds["lon_max"] - bounds["lon_min"]
        lat = bounds["lat_min"] + (digest[0] / 255) * lat_range
        lon = bounds["lon_min"] + (digest[1] / 255) * lon_range
        return Point(lon, lat, srid=4326)
