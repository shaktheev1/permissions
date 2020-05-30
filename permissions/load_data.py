from csv import DictReader
from datetime import datetime

import pandas as pd
import math

from permissions.models import Book, Unit, Contact, Element
from pytz import UTC

def import_data(isbn, data):
    # data = pd.read_excel('/Volumes/Data/move_on/django/projects/myproject/myproject/data/data1.xlsx','Sheet1')
    # g = data
    book = Book.objects.get(isbn=isbn)
    for u in set(data['Chapter Number']):
        # print("{} - {}".format(u, type(u)))
        if pd.isnull(u)==False:
            if (Unit.objects.filter(book_id = book, chapter_number = u).count() == 0):
                unit = Unit()
                unit.book_id = book.pk
                unit.chapter_number = str(u)
                unit.active = True
                unit.save()
            else:
                return("Chapters already exist...")

    for i,x in enumerate(data['Chapter Number']):
        if pd.isnull(x)==False:
            unit = Unit.objects.get(chapter_number=x, book_id = book)
            if (Element.objects.filter(unit_id = unit, element_number = data['Element Number'][i]).count() == 0):
                element = Element()
                element.unit_id = unit.pk
                element.element_number = data['Element Number'][i]
                element.caption = data['Caption'][i]
                element.source = data['Source'][i]
                element.element_type = data['Type'][i]
                element.credit_line = data['Credit Line'][i]
                element.source_link = data['Source Link'][i]
                element.title = data['Title with author'][i]
                contact = Contact.objects.get(rh_email = data['RH Contact'][i])
                element.contact_id = contact.pk
                # element.rh_email = data['RH e-mail'][i]
                # element.alt_email = data['Alt - e-mail'][i]
                # element.rh_address = data['RH Address'][i]
                # element.phone = data['Phone'][i]
                # element.fax = data['Fax'][i]
                element.insert_1 = data['Insert 1'][i]
                element.jbl_rh_name = data['JBL RH Name'][i]
                element.file_location = data['File Location'][i]
                element.file_name = data['File name'][i]
                element.active = True
                element.save()
            else:
                return("Elements already exist...")
    return("Successfully imported!")

if __name__ == '__main__':
    try:
        arg = sys.argv[1]
    except IndexError:
        arg = None
    return_val = import_data(arg)