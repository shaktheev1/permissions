from csv import DictReader
from datetime import datetime

from django.core.management import BaseCommand

from permissions.models import Book, Unit, Element
from pytz import UTC


class Command(BaseCommand):
    # Show this when the user types help
    help = "Loads data from pet_data.csv into our Pet model"

    def handle(self, *args, **options):
        for row in DictReader(open('../data/data.xlsx')):
            print(row['Chapter Number'])   
            # pet = Pet()
            # pet.name = row['Pet']
            # pet.submitter = row['Submitter']
            # pet.species = row['Species']
            # pet.breed = row['Breed']
            # pet.description = row['Pet Description']
            # pet.sex = row['Sex']
            # pet.age = row['Age']
            # raw_submission_date = row['submission date']
            # submission_date = UTC.localize(
            #     datetime.strptime(raw_submission_date, DATETIME_FORMAT))
            # pet.submission_date = submission_date
            # pet.save()
            # raw_vaccination_names = row['vaccinations']
            # vaccination_names = [name for name in raw_vaccination_names.split('| ') if name]
            # for vac_name in vaccination_names:
            #     vac = Vaccine.objects.get(name=vac_name)
            #     pet.vaccinations.add(vac)
            # pet.save()
