from django.contrib.auth.models import User
from django.db.models import Count
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from .forms import NewBookForm, NewUnitForm, NewElementForm, NewFollowupForm
from django.utils.decorators import method_decorator
from .models import Book, Unit, Element, FollowUp
from django.views.generic import UpdateView
from django.utils import timezone
from django.views.generic import ListView
from django.http import HttpResponse
from .resources import BookResource

class BookListView(ListView):
    model = Book
    context_object_name = 'books'
    template_name = 'home.html'
    paginate_by = 5
    
    def get_queryset(self):
        queryset = Book.objects.all().order_by('-created_at')
        return queryset

def home(request):
    return render(request)

@login_required
def new_book(request):
    if request.method == 'POST':
        form = NewBookForm(request.POST)
        if form.is_valid():
            book = form.save(commit=False)
            book.title = form.cleaned_data.get('title')
            book.isbn = form.cleaned_data.get('isbn')
            book.created_at = form.cleaned_data.get('created_at')
            book.active = form.cleaned_data.get('active')
            book.save()
            # book = Book.objects.create(
            #     title = form.cleaned_data.get('title'),
            #     isbn = form.cleaned_data.get('isbn'),
            #     active = form.cleaned_data.get('active')
            # )
            return redirect('home')
    else:
        form = NewBookForm()
    return render(request, 'new_book.html', {'form': form})    


def book_units(request, pk):
    book = get_object_or_404(Book, pk=pk)
    return render(request, 'units.html', {'book': book})

def new_unit(request, pk):
    book = get_object_or_404(Book, pk=pk)
    user = User.objects.first()
    if request.method == 'POST':
        form = NewUnitForm(request.POST)
        if form.is_valid():
            unit = form.save(commit=False)
            unit.book = book
            unit.chapter_number = form.cleaned_data.get('chapter_number')
            unit.chapter_title = form.cleaned_data.get('chapter_title')
            unit.active = form.cleaned_data.get('active')
            unit.save()

            # unit = Unit.objects.create(
            #     book = book,
            #     chapter_number = form.cleaned_data.get('chapter_number'),
            #     chapter_title = form.cleaned_data.get('chapter_title'),
            #     active = form.cleaned_data.get('active'),
            # )

        # chapter_number = request.POST['chapter_number']
        # chapter_title = request.POST['chapter_title']
        # active = request.POST['active']

        #     unit = Unit.objects.create(
        #     chapter_number = chapter_number,
        #     chapter_title = chapter_title,
        #     active = active,
        #  )
            return redirect('book_units', pk=book.pk)
    else:
        form = NewUnitForm()
    return render(request, 'new_unit.html', {'book': book, 'form': form})


def unit_elements(request, pk, pk1):
    book = get_object_or_404(Book, pk=pk)
    unit = get_object_or_404(Unit, pk=pk1)
    return render(request, 'elements.html', {'book':book, 'unit': unit})


def new_element(request, pk, pk1):
    book = get_object_or_404(Book, pk=pk)
    unit = get_object_or_404(Unit, pk=pk1)
    
    if request.method == 'POST':
        form = NewElementForm(request.POST)
        if form.is_valid():
            element = form.save(commit=False)
            element.book = book
            element.unit = unit
            element.element_number = form.cleaned_data.get('element_number')
            element.requested_on = form.cleaned_data.get('requested_on')
            element.granted_on = form.cleaned_data.get('granted_on')
            element.status = form.cleaned_data.get('status')
            element.save()
            return redirect('unit_elements', pk=book.pk, pk1=unit.pk)
    else:
        form = NewElementForm()
    return render(request, 'new_element.html', {'book':book, 'unit': unit, 'form': form})

def element_followups(request, pk, pk1, fu):
    book = get_object_or_404(Book, pk=pk)
    unit = get_object_or_404(Unit, pk=pk1)
    element = get_object_or_404(Element, pk=fu)
    return render(request, 'followups.html', {'book':book, 'unit': unit, 'element': element})

def new_followup(request, pk, pk1, fu):
    book = get_object_or_404(Book, pk=pk)
    unit = get_object_or_404(Unit, pk=pk1)
    element = get_object_or_404(Element, pk=fu)
    if request.method == 'POST':
        form = NewFollowupForm(request.POST)
        if form.is_valid():
            followup = form.save(commit=False)
            followup.book = book
            followup.unit = unit
            followup.element = element
            followup.followedup_at = form.cleaned_data.get('followedup_at')
            followup.followedup_by = form.cleaned_data.get('followedup_by')
            followup.save()
            return redirect('element_followups', pk=book.pk, pk1=unit.pk, fu=element.pk)
    else:
        form = NewFollowupForm()
    return render(request, 'new_followup.html', {'book':book, 'unit': unit, 'element': element, 'form': form})

@login_required
def test(request):
    #books = Book.objects.all()
    return render(request, 'test.html')

@method_decorator(login_required, name='dispatch')
class FollowUpUpdateView(UpdateView):
    model = FollowUp
    fields = ('followedup_at', )
    template_name = 'edit_followup.html'
    pk_url_kwarg = 'followup_pk'
    context_object_name = 'followups'

    def form_valid(self, form):
        followups = form.save(commit=False)
        followups.updated_by = self.request.user
        followups.save()
        return redirect('element_followups', pk=followups.element.unit.book.pk, pk1=followups.element.unit.pk, fu=followups.element.pk)

def export_books(request):
    book_resource = BookResource()
    dataset = book_resource.export()
    response = HttpResponse(dataset.xls, content_type='application/vnd.ms-excel')
    response['Content-Disposition'] = 'attachment; filename="books.xls"'
    return response

def export_book(request, pk):
    book_resource = BookResource()
    queryset = Book.objects.filter(pk=pk)
    dataset = book_resource.export(queryset)
    response = HttpResponse(dataset.xls, content_type='application/vnd.ms-excel')
    response['Content-Disposition'] = 'attachment; filename={}.xls'.format(queryset[0])
    return response