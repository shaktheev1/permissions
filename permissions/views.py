from django.contrib.auth.models import User
from django.db.models import Count
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from .forms import NewBookForm, NewUnitForm, NewElementForm, NewFollowupForm
from django.utils.decorators import method_decorator
from .models import Book, Unit, Element, FollowUp
from django.views.generic import DetailView, UpdateView, FormView, ListView, CreateView
from django.utils import timezone
from django.http import HttpResponse
from .resources import BookResource, UnitResource, ElementResource
from tablib import Dataset
from collections import defaultdict
from django.urls import reverse_lazy
import json
from django.conf import settings
from django.template.loader import render_to_string
import weasyprint
from django.core.mail import EmailMessage
from io import BytesIO
from django.db.models import Q

class BookListView(ListView):
    model = Book
    context_object_name = 'books'
    paginate_by = 3
    template_name = 'home.html'
    
    def get_queryset(self):
        queryset = Book.objects.all().order_by('-created_at')
        return queryset

@method_decorator(login_required, name='dispatch')
class NewBookView(CreateView):
    model = Book
    form_class = NewBookForm
    success_url = reverse_lazy('home')
    template_name = 'new_book.html'

# @login_required    
# def new_book(request):
#     if request.method == 'POST':
#         form = NewBookForm(request.POST)
#         if form.is_valid():
#             book = form.save(commit=False)
#             book.title = form.cleaned_data.get('title')
#             book.isbn = form.cleaned_data.get('isbn')
#             book.created_at = form.cleaned_data.get('created_at')
#             book.active = form.cleaned_data.get('active')
#             book.save()
#             # book = Book.objects.create(
#             #     title = form.cleaned_data.get('title'),
#             #     isbn = form.cleaned_data.get('isbn'),
#             #     active = form.cleaned_data.get('active')
#             # )
#             return redirect('home')
#     else:
#         form = NewBookForm()
#     return render(request, 'new_book.html', {'form': form})    


class UnitsListView(ListView):
    model = Unit
    context_object_name = 'units'
    paginate_by = 4
    template_name = 'units.html'

    def get_context_data(self, **kwargs):
        kwargs['book'] = self.book
        return super().get_context_data(**kwargs)

    def get_queryset(self):
        self.book = get_object_or_404(Book, pk=self.kwargs.get('pk'))
        queryset = self.book.units.order_by('chapter_number')
        return queryset
    
# def book_units(request, pk):
#     book = get_object_or_404(Book, pk=pk)
#     return render(request, 'units.html', {'book': book})

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
            return redirect('book_units', pk=book.pk)
    else:
        form = NewUnitForm()
    return render(request, 'new_unit.html', {'book': book, 'form': form})


class ElementsListView(ListView):
    model = Element
    context_object_name = 'elements'
    paginate_by = 4
    template_name = 'elements.html'

    def get_context_data(self, **kwargs):
        kwargs['unit'] = self.unit
        return super().get_context_data(**kwargs)

    def get_queryset(self):
        self.unit = get_object_or_404(Unit, book__pk=self.kwargs.get('pk'), pk=self.kwargs.get('pk1'))
        queryset = self.unit.elements.order_by('element_number')
        return queryset

# def unit_elements(request, pk, pk1):
#      book = get_object_or_404(Book, pk=pk)
#      unit = get_object_or_404(Unit, pk=pk1)
#      return render(request, 'elements.html', {'book':book, 'unit': unit})


def new_element(request, pk, pk1):
    book = get_object_or_404(Book, pk=pk)
    unit = get_object_or_404(Unit, pk=pk1)
    
    if request.method == 'POST':
        form = NewElementForm(request.POST)
        user = User.objects.first()
        if form.is_valid():
            element = form.save(commit=False)
            element.book = book
            element.unit = unit
            element.element_number = form.cleaned_data.get('element_number')
            element.specified_as = form.cleaned_data.get('specified_as')
            element.caption = form.cleaned_data.get('caption')
            element.source = form.cleaned_data.get('source')
            element.credit_line = form.cleaned_data.get('credit_line')
            element.status = form.cleaned_data.get('status')
            element.source_link = form.cleaned_data.get('source_link')
            element.title = form.cleaned_data.get('title')
            element.rh_email = form.cleaned_data.get('rh_email')
            element.alt_email = form.cleaned_data.get('alt_email')
            element.rh_address = form.cleaned_data.get('rh_address')
            element.phone = form.cleaned_data.get('phone')
            element.fax = form.cleaned_data.get('fax')
            element.insert_1 = form.cleaned_data.get('insert_1')
            element.jbl_rh_name = form.cleaned_data.get('jbl_rh_name')
            element.file_location = form.cleaned_data.get('file_location')
            element.file_name = form.cleaned_data.get('file_name')
            element.file_location = form.cleaned_data.get('file_location')
            element.requested_on = form.cleaned_data.get('requested_on')
            element.granted_on = form.cleaned_data.get('granted_on')
            element.created_by = user
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
class BookUpdateView(UpdateView):
    model = Book
    fields = ('isbn', 'title', 'edition', 'active')
    template_name = 'edit_book.html'
    pk_url_kwarg = 'book_pk'
    context_object_name = 'book_e'

    def form_valid(self, form):
        book_e = form.save(commit=False)
        book_e.updated_by = self.request.user
        book_e.save()
        return redirect('home')

@method_decorator(login_required, name='dispatch')
class UnitUpdateView(UpdateView):
    model = Unit
    fields = ('chapter_number', 'chapter_title', 'active')
    template_name = 'edit_unit.html'
    pk_url_kwarg = 'unit_pk'
    context_object_name = 'unit_e'

    def form_valid(self, form):
        unit_e = form.save(commit=False)
        unit_e.updated_by = self.request.user
        unit_e.save()
        return redirect('book_units', pk=unit_e.book.pk)

@method_decorator(login_required, name='dispatch')
class ElementUpdateView(UpdateView):
    model = Element
    fields = '__all__'
    template_name = 'edit_element.html'
    pk_url_kwarg = 'element_pk'
    context_object_name = 'element_e'

    def form_valid(self, form):
        element_e = form.save(commit=False)
        element_e.updated_by = self.request.user
        element_e.save()
        return redirect('unit_elements', pk=element_e.unit.book.pk, pk1=element_e.unit.pk)

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
    books_resource = BookResource()
    dataset = books_resource.export()
    response = HttpResponse(dataset.xlsx, content_type='application/vnd.ms-excel')
    response['Content-Disposition'] = 'attachment; filename="books.xlsx"'
    return response

def export_book(request, pk):
    book_resource = BookResource()
    queryset = Book.objects.filter(pk=pk)
    dataset = book_resource.export(queryset)
    response = HttpResponse(dataset.xlsx, content_type='application/vnd.ms-excel')
    response['Content-Disposition'] = 'attachment; filename={}.xlsx'.format(queryset[0])
    return response

def import_book(request):
    if request.method == 'POST':
        book_resource = BookResource()
        dataset = Dataset()
        new_book = request.FILES['myfile']

        imported_data = dataset.load(new_book.read())
        result = book_resource.import_data(dataset, dry_run=True)  # Test the data import

        if not result.has_errors():
            book_resource.import_data(dataset, dry_run=False)  # Actually import now
            # messages.success(request, 'Book submission successful')
            return redirect('home')

    return render(request, 'import_books.html')

def export_units(request, pk):
    units_resource = UnitResource()
    queryset = Unit.objects.filter(book=pk)
    dataset = units_resource.export(queryset)
    response = HttpResponse(dataset.xlsx, content_type='application/vnd.ms-excel')
    response['Content-Disposition'] = 'attachment; filename={}.xlsx'.format(pk)
    return response

def import_units(request, pk):
    if request.method == 'POST':
        unit_resource = UnitResource()
        dataset = Dataset()
        new_unit = request.FILES['myfile']

        imported_data = dataset.load(new_unit.read())
        result = unit_resource.import_data(dataset, dry_run=True)  # Test the data import

        if not result.has_errors():
            unit_resource.import_data(dataset, dry_run=False)  # Actually import now
            # messages.success(request, 'Unit submission successful')
            return redirect('book_units', pk=pk)
    return render(request, 'import_units.html')

def export_elements(request, pk, pk1):
    elements_resource = ElementResource()
    queryset = Element.objects.filter(unit=pk1)
    dataset = elements_resource.export(queryset)
    response = HttpResponse(dataset.xlsx, content_type='application/vnd.ms-excel')
    response['Content-Disposition'] = 'attachment; filename={}.xlsx'.format(pk1)
    return response

def import_elements(request, pk, pk1):
    if request.method == 'POST':
        element_resource = ElementResource()
        dataset = Dataset()
        new_element = request.FILES['myfile']

        imported_data = dataset.load(new_element.read())
        result = element_resource.import_data(dataset, dry_run=True)  # Test the data import

        if not result.has_errors():
            element_resource.import_data(dataset, dry_run=False)  # Actually import now
            # messages.success(request, 'Element submission successful')
            return redirect('unit_elements', pk=pk, pk1=pk1)
        # else:
            # messages.success(request, 'Import Unsuccessful')
    return render(request, 'import_elements.html')


def book_list(request):
    book = Book.objects.all()
    context = defaultdict(list)
    dict(context)
    for p in book:
        context[p.active].append(p.pk)
    context.default_factory = None
    return render(request, "booklist.html", {'context': context, 'book': book})

def unit_list(request, pk):
    book = get_object_or_404(Book, pk=pk)
#    unit = get_object_or_404(Unit, pk=pk1)
    element = Element.objects.filter(unit__book=pk, requested_on=None)
    context = defaultdict(list)
    dict(context)
    source=""
    credit_line=""
    rh_email=""
    for p in element:
        if not p.source is None:
            source=p.source.strip()
        if not p.credit_line is None:
            credit_line=p.credit_line.strip()
        if not p.rh_email is None:
            rh_email=p.rh_email.strip()
        s=source,credit_line,rh_email
        context[s].append(p.pk)
    context.default_factory = None
    return render(request, "elementlist.html", {'context': context, 'element': element, 'pk': pk, 'book': book})

# def book_list(request):
#     context = Book.objects.values_list('active', flat=True).distinct()
#     return render(request, "booklist.html", {'context': context})
    

def generate_agreement(request, pk, ems):
    element = Element.objects.filter(unit__book=pk)
    ems_list = json.loads(ems)
    html = render_to_string("generate_agreement.html", {'ems_list': ems_list, 'element': element})
    response = HttpResponse(content_type="application/pdf")
    #response['Content-Disposition'] = 'attachment; filename="agreement_{}.pdf"'.format(pk)
    response['Content-Disposition'] = 'filename="agreement_{}.pdf"'.format(pk)
    weasyprint.HTML(string=html, base_url=request.build_absolute_uri("/")).write_pdf(response, stylesheets=[weasyprint.CSS(settings.STATIC_ROOT + 'css/pdf.css')], presentational_hints=True)
    return response

def email_agreement(request, pk, ems):
    element = Element.objects.filter(unit__book=pk, requested_on=None)
    book = get_object_or_404(Book, pk=pk)
    ems_list = json.loads(ems)    
    subject = "Jones & Bartlett Permission Request - {}, {}".format(book.title, book.isbn)
    message = render_to_string("emailbody.html", {'ems_list': ems_list, 'element': element})

    email = EmailMessage(subject, message, 's4permission@gmail.com', ['shaktheev@gmail.com'])

    html = render_to_string("generate_agreement.html", {'ems_list': ems_list, 'element': element})
    out = BytesIO()
    stylesheets = [weasyprint.CSS(settings.STATIC_ROOT + 'css/pdf.css')]
    weasyprint.HTML(string=html).write_pdf(out, stylesheets=stylesheets)
    response = HttpResponse(content_type="application/pdf")
    # email.attach("agreement_{}.pdf".format(pk), out.getvalue(), 'application/pdf')
    email.content_subtype = "html"
    email.send()
    for ems in ems_list:
        for e in element:
            if ems==e.pk:
                e.requested_on=timezone.now()
                e.save()
    return render(request, 'done.html')


def email_body(request, pk, ems):
    element = Element.objects.filter(unit__book=pk)
    book = get_object_or_404(Book, pk=pk)
    ems_list = json.loads(ems)
    return render(request, 'emailbody.html', {'ems_list': ems_list, 'element': element})

def requested_list(request, pk):
    book = get_object_or_404(Book, pk=pk)
#    unit = get_object_or_404(Unit, pk=pk1)
    element = Element.objects.filter(~Q(requested_on=None), granted_on=None, unit__book=pk).order_by('requested_on')
    context = defaultdict(list)
    dict(context)
    source=""
    credit_line=""
    rh_email=""
    for p in element:
        if not p.source is None:
            source=p.source.strip()
        if not p.credit_line is None:
            credit_line=p.credit_line.strip()
        if not p.rh_email is None:
            rh_email=p.rh_email.strip()
        s=source,credit_line,rh_email
        context[s].append(p.pk)
    context.default_factory = None
    return render(request, "requested_list.html", {'context': context, 'element': element, 'pk': pk, 'book': book})

def granted_list(request, pk):
    book = get_object_or_404(Book, pk=pk)
#    unit = get_object_or_404(Unit, pk=pk1)
    element = Element.objects.filter(~Q(granted_on=None), unit__book=pk).order_by('granted_on')
    context = defaultdict(list)
    dict(context)
    source=""
    credit_line=""
    rh_email=""
    for p in element:
        if not p.source is None:
            source=p.source.strip()
        if not p.credit_line is None:
            credit_line=p.credit_line.strip()
        if not p.rh_email is None:
            rh_email=p.rh_email.strip()
        s=source,credit_line,rh_email
        context[s].append(p.pk)
    context.default_factory = None
    return render(request, "granted_list.html", {'context': context, 'element': element, 'pk': pk, 'book': book})

def update_followups(request, pk, ems):
    element = Element.objects.filter(unit__book=pk)
    book = get_object_or_404(Book, pk=pk)
    user = User.objects.first()
    # follow = Element.objects.all()
    
    ems_list = json.loads(ems)    
    for ems in ems_list:
        for e in element:
            if ems==e.pk:
                # f.followedup_at=timezone.now()
                # f.save()
                # print(follow_up.followedup_at)
                # print(e.follow_up)
                e.follow_up.create(followedup_at=timezone.now(), followedup_by=user)
                
    return render(request, 'update_followups.html', {'ems_list': ems_list})