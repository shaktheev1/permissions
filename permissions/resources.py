from import_export import resources
from .models import Book, Unit

class BookResource(resources.ModelResource):
    class Meta:
        model = Book

class UnitResource(resources.ModelResource):
    class Meta:
        model = Unit
