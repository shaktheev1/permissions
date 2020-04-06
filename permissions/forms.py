from django import forms
from .models import Book, Unit, Element, FollowUp

class NewBookForm(forms.ModelForm):
    class Meta:
        model = Book
        #fields = '__all__'
        fields = ['title', 'isbn', 'active']

class NewUnitForm(forms.ModelForm):
    class Meta:
        model = Unit
        fields = ['chapter_number', 'chapter_title', 'active']

class NewElementForm(forms.ModelForm):
    class Meta:
        model = Element
        #fields = '__all__'
        fields = ['element_number', 'requested_on', 'granted_on', 'status']

class NewFollowupForm(forms.ModelForm):
    class Meta:
        model = FollowUp
        #fields = '__all__'
        fields = ['followedup_at', 'followedup_by']

