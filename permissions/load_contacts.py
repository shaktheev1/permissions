from csv import DictReader
from datetime import datetime

import pandas as pd
import math

from permissions.models import Contact
from pytz import UTC

def import_contacts(data):
    for i,u in enumerate(data['RH e-mail']):
        if pd.isnull(u)==False:
            contact = Contact()
            contact.rh_email = u
            contact.rh_firstname = data['First name'][i]
            contact.rh_lastname = data['Last name'][i]
            contact.alt_email = data['Alt - e-mail'][i]
            contact.rh_address = data['RH Address'][i]
            contact.phone = data['Phone'][i]
            contact.fax = data['Fax'][i]
            contact.active = True
            contact.save()
        else:
            return("Contact already exist...")
    return("Successfully imported!")

if __name__ == '__main__':
    try:
        arg = sys.argv[0]
    except IndexError:
        arg = None
    return_val = import_contacts(arg)