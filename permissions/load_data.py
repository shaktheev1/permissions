from csv import DictReader
from datetime import datetime

import pandas as pd

from permissions.models import Book, Unit, Element
from pytz import UTC

def import_data(isbn, data):
    # data = pd.read_excel('/Volumes/Data/move_on/django/projects/myproject/myproject/data/data1.xlsx','Sheet1')
    # g = data
    book = Book.objects.get(isbn=isbn)
    for u in set(data['Chapter Number']):
        if (Unit.objects.filter(book_id = book, chapter_number = u).count() == 0):
            unit = Unit()
            unit.book_id = book.pk
            unit.chapter_number = str(u)
            unit.active = True
            unit.save()
        else:
            return("Chapters already exist...")
    
    for i,x in enumerate(data['Chapter Number']):
        unit = Unit.objects.get(chapter_number=x, book_id = book)
        if (Element.objects.filter(unit_id = unit, element_number = data['Element Number'][i]).count() == 0):
            element = Element()
            element.unit_id = unit.pk
            element.element_number = data['Element Number'][i]
            element.caption = data['Caption'][i]
            element.active = True
            element.save()
        else:
            return("Elements already exist...")
    return("Done")

if __name__ == '__main__':
    try:
        arg = sys.argv[1]
    except IndexError:
        arg = None
    return_val = import_data(arg)