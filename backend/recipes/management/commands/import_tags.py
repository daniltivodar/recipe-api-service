import os
from csv import reader

from django.core.management import BaseCommand
from recipes.models import Tag


class Command(BaseCommand):
    """Загрузка данных из CSV файла с тегами в базу данных."""

    help = 'Загрузка списка тегов из csv-файла в базу данных.'

    def handle(self, *args, **options):
        """Чтение данных из CSV файла и их загрузка в базу данных."""
        file_path = os.path.join('data', 'tags.csv')

        with open(file_path, encoding='utf-8') as csv_file:
            csv_reader = reader(csv_file)
            for row in csv_reader:
                Tag.objects.update_or_create(
                    name=row[0].strip(), slug=row[1].strip(),
                )
        self.stdout.write(self.style.SUCCESS('Список тегов загружен!'))
