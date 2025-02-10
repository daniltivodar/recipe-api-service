from csv import reader
import os

from django.core.management import BaseCommand

from recipes.models import Ingredient


class Command(BaseCommand):
    """Загрузка данных из CSV файла в базу данных."""

    help = 'Загрузка списка ингредиентов из csv-файла в базу данных.'

    def handle(self, *args, **options):
        """Чтение данных из CSV файла и их загрузка в базу данных."""
        file_path = os.path.join('data', 'ingredients.csv')

        with open(file_path, encoding='utf-8') as csv_file:
            csv_reader = reader(csv_file)
            Ingredient.objects.bulk_create(
                [
                    Ingredient(
                        name=name.strip(),
                        measurement_unit=measurement_unit.strip(),
                    )
                    for name, measurement_unit in csv_reader
                ],
            )
        self.stdout.write(self.style.SUCCESS('Список ингредиентов загружен!'))
