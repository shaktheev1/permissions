from django.contrib import admin
from import_export import resources
from .models import Book, Unit, Element, FollowUp
from import_export.admin import ImportExportModelAdmin

# Register your models here.

class BookResource(resources.ModelResource):
    class Meta:
        model = Book

class UnitResource(resources.ModelResource):
    class Meta:
        model = Unit

class ElementResource(resources.ModelResource):
    class Meta:
        model = Element

class BookAdmin(ImportExportModelAdmin):
    resource_class = BookResource

class UnitAdmin(ImportExportModelAdmin):
    resource_class = UnitResource

class ElementAdmin(ImportExportModelAdmin):
    resource_class = ElementResource

admin.site.register(Book, BookAdmin)
admin.site.register(Unit, UnitAdmin)
admin.site.register(Element, ElementAdmin)
admin.site.register(FollowUp)

# Register your models here.


