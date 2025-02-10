from csv import reader
import os

from django.core.management import BaseCommand

from recipes.models import Tag


class Command(BaseCommand):
    """Загрузка данных из CSV файла в базу данных."""

    help = 'Загрузка списка тегов из csv-файла в базу данных.'

    def handle(self, *args, **options):
        """Чтение данных из CSV файла и их загрузка в базу данных."""
        file_path = os.path.join('data', 'tags.csv')

        with open(file_path, encoding='utf-8') as csv_file:
            csv_reader = reader(csv_file)
            Tag.objects.bulk_create(
                [
                    Tag(
                        name=name.strip(),
                        slug=slug.strip(),
                    )
                    for name, slug in csv_reader
                ],
            )
        self.stdout.write(self.style.SUCCESS('Список тегов загружен!'))
