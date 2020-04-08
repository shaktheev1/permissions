from import_export import resources
from .models import Book, Unit, Element

class BookResource(resources.ModelResource):
    class Meta:
        model = Book

class UnitResource(resources.ModelResource):
    class Meta:
        model = Unit

class ElementResource(resources.ModelResource):
    class Meta:
        model = Element