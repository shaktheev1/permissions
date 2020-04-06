from django.contrib import admin
from .models import Book, Unit, Element, FollowUp

# Register your models here.

admin.site.register(Book)
admin.site.register(Unit)
admin.site.register(Element)
admin.site.register(FollowUp)