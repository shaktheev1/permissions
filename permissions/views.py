from django.contrib.auth.models import User
from django.db.models import Count
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from .forms import NewBookForm, NewUnitForm, NewElementForm, NewFollowupForm, NewContactForm
from django.utils.decorators import method_decorator
from .models import Book, Unit, Contact, Element, FollowUp
from django.views.generic import DetailView, UpdateView, FormView, ListView, CreateView, DeleteView
from django.utils import timezone
from django.http import HttpResponse, HttpResponseRedirect
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
import subprocess
from .image_process import i_process
from .load_data import import_data
from .load_contacts import import_contacts
import pandas as pd
import logging
import socket
import errno
from os import path
from django.conf import settings

logging.config.dictConfig({
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'console': {
            'format': '%(name)-12s %(levelname)-8s %(message)s'
        },
        'file': {
            'format': '%(asctime)s %(name)-12s %(levelname)-8s %(message)s'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'console'
        },
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'formatter': 'file',
            'filename': '/Volumes/Data/move_on/django/projects/myproject/myproject/log/debug.log'
        }
    },
    'loggers': {
        '': {
            'level': 'DEBUG',
            # 'handlers': ['console', 'file']
        },
        'django.request': {
            'level': 'DEBUG',
            # 'handlers': ['console', 'file']
        }
    }
})


logger = logging.getLogger(__name__)

def testing(request):
    cmd = '../myproject/manag.sh'
    subprocess.call(cmd)
    #x = print_hello("Welcome to the party")
    #return HttpResponse("<html><body>{}</body></html>".format(x))
    return HttpResponse("Done")

def process_images(request, pk):
    book = get_object_or_404(Book, pk=pk)
    isbn = book.isbn
    media_path = settings.MEDIA_ROOT
    #cmd = '../myproject/manag.sh'
    #subprocess.call(cmd)
    result = i_process(isbn, media_path)
    user = request.user.username
    logger.info("ISBN: {}. Image process executed by {} at {}.".format(isbn, user, timezone.now()))
    #return HttpResponse("<html><body>{}</body></html>".format(x))
    return render(request, 'processed_images.html', {'result': result, 'book': book})

def process_data(request, pk):
    book = get_object_or_404(Book, pk=pk)
    if request.method == 'POST':
        # book_resource = BookResource()
        dataset = Dataset()
        new_book = request.FILES.get('myfile', False)
        if new_book == False:
            return render(request, 'import_books.html')
        imported_data = dataset.load(new_book.read())
        isbn = book.isbn
        media_path = settings.MEDIA_ROOT
        data = imported_data.export('df')
        result = import_data(isbn, data)
        user = request.user.username
        logger.info("ISBN: {}. Data imported by {} at {}.".format(isbn, user, timezone.now()))
    else:
        return render(request, 'import_books.html')
    return render(request, 'import_status.html', {'book': book, 'result': result})

def import_contact(request):
    if request.method == 'POST':
        dataset = Dataset()
        new_contact = request.FILES.get('myfile', False)
        if new_contact == False:
            return render(request, 'import_contacts.html')
        imported_data = dataset.load(new_contact.read())
        media_path = settings.MEDIA_ROOT
        data = imported_data.export('df')
        result = import_contacts(data)
        user = request.user.username
        logger.info("Contacts imported by {} at {}.".format(user, timezone.now()))
    else:
        return render(request, 'import_contacts.html')
    return render(request, 'import_contacts_status.html', {'result': result})

@method_decorator(login_required, name='dispatch')
class NewContactView(CreateView):
    model = Contact
    form_class = NewContactForm
    success_url = reverse_lazy('contacts')
    template_name = 'new_contact.html'

@method_decorator(login_required, name='dispatch')
class BookListView(ListView):
    model = Book
    context_object_name = 'books'
    paginate_by = 8
    template_name = 'home.html'
    
    def get_queryset(self):
        queryset = Book.objects.filter(active=True).order_by('-created_at')
        return queryset

class BookListInactiveView(ListView):
    model = Book
    context_object_name = 'books'
    paginate_by = 8
    template_name = 'home_inactive.html'
    
    def get_queryset(self):
        queryset = Book.objects.filter(active=False).order_by('-created_at')
        return queryset

@method_decorator(login_required, name='dispatch')
class ContactListView(ListView):
    model = Contact
    context_object_name = 'contacts'
    paginate_by = 8
    template_name = 'contacts.html'
    
    def get_queryset(self):
        queryset = Contact.objects.filter(active=True).order_by('-rh_firstname')
        return queryset

@method_decorator(login_required, name='dispatch')
class ContactUpdateView(UpdateView):
    model = Contact
    fields = ('rh_firstname', 'rh_lastname', 'rh_email', 'alt_email', 'rh_address', 'active')
    template_name = 'edit_contact.html'
    pk_url_kwarg = 'contact_pk'
    context_object_name = 'contact_e'

    def form_valid(self, form):
        contact_e = form.save(commit=False)
        contact_e.save()
        logger.info("Contact updated by {} at {}.".format(contact_e.rh_email, timezone.now()))
        return redirect('contacts')

def deactivate_contact(request, pk):
    contact = get_object_or_404(Contact, pk=pk)
    contact.active = False
    contact.save()
    user = request.user.username
    logger.info("Contact {} deactivated by {} at {}.".format(contact.rh_email, user, timezone.now()))
    return redirect('contacts')
    # return HttpResponseRedirect(request.path_info)

def activate_contact(request, pk):
    contact = get_object_or_404(Contact, pk=pk)
    contact.active = True
    contact.save()
    user = request.user.username
    logger.info("Contact {} activated by {} at {}.".format(contact.rh_email, user, timezone.now()))
    return redirect('contact_inactive')

class ContactListInactiveView(ListView):
    model = Contact
    context_object_name = 'contacts'
    paginate_by = 8
    template_name = 'contact_inactive.html'
    
    def get_queryset(self):
        queryset = Contact.objects.filter(active=False).order_by('-rh_firstname')
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
    paginate_by = 10
    template_name = 'units.html'

    def get_context_data(self, **kwargs):
        kwargs['book'] = self.book
        kwargs['user'] = self.request.user
        kwargs['group'] = self.request.user.groups.values_list('name', flat=True).first()
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
    user = User.objects.get(username=request.user.username)
    if request.method == 'POST':
        form = NewUnitForm(request.POST)
        if form.is_valid():
            unit = form.save(commit=False)
            unit.book = book
            unit.chapter_number = form.cleaned_data.get('chapter_number')
            unit.chapter_title = form.cleaned_data.get('chapter_title')
            # unit.active = form.cleaned_data.get('active')
            unit.save()
            return redirect('book_units', pk=book.pk)
    else:
        form = NewUnitForm()
    return render(request, 'new_unit.html', {'book': book, 'form': form})


class ElementsListView(ListView):
    model = Element
    context_object_name = 'elements'
    paginate_by = 10
    template_name = 'elements.html'

    def get_context_data(self, **kwargs):
        kwargs['unit'] = self.unit
        kwargs['group'] = self.request.user.groups.values_list('name', flat=True).first()
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
        user = User.objects.get(username=request.user.username)
        if form.is_valid():
            element = form.save(commit=False)
            element.book = book
            element.unit = unit
            element.element_number = form.cleaned_data.get('element_number')
            element.specified_as = form.cleaned_data.get('specified_as')
            element.caption = form.cleaned_data.get('caption')
            element.source = form.cleaned_data.get('source')
            element.element_type = form.cleaned_data.get('element_type')
            element.credit_line = form.cleaned_data.get('credit_line')
            element.status = form.cleaned_data.get('status')
            element.source_link = form.cleaned_data.get('source_link')
            element.title = form.cleaned_data.get('title')
            contact = Contact()
            element.contact = contact.rh_email
            # element.rh_email = form.cleaned_data.get('rh_email')
            # element.alt_email = form.cleaned_data.get('alt_email')
            # element.rh_address = form.cleaned_data.get('rh_address')
            # element.phone = form.cleaned_data.get('phone')
            # element.fax = form.cleaned_data.get('fax')
            element.insert_1 = form.cleaned_data.get('insert_1')
            element.jbl_rh_name = form.cleaned_data.get('jbl_rh_name')
            element.file_location = form.cleaned_data.get('file_location')
            element.file_name = form.cleaned_data.get('file_name')
            element.file_location = form.cleaned_data.get('file_location')
            # element.requested_on = form.cleaned_data.get('requested_on')
            # element.granted_on = form.cleaned_data.get('granted_on')
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
    user = User.objects.get(username=request.user.username)
    logger.info("Followup for ISBN: {}, chapter {}, element {} done by {} at {}.".format(book.isbn, unit.chapter_number, element.element_number, user, timezone.now()))
    return render(request, 'followups.html', {'book':book, 'unit': unit, 'element': element})

def new_followup(request, pk, pk1, fu):
    book = get_object_or_404(Book, pk=pk)
    unit = get_object_or_404(Unit, pk=pk1)
    element = get_object_or_404(Element, pk=fu)
    user = User.objects.get(username=request.user.username)
    if request.method == 'POST':
        form = NewFollowupForm(request.POST)
        if form.is_valid():
            followup = form.save(commit=False)
            followup.book = book
            followup.unit = unit
            followup.element = element
            followup.followedup_at = form.cleaned_data.get('followedup_at')
            # followup.followedup_by = form.cleaned_data.get('followedup_by')
            followup.followedup_by = user
            followup.save()
            logger.info("Followup for ISBN: {}, chapter {}, element {} done by {} at {}.".format(book.isbn, unit.chapter_number, element.element_number, user, timezone.now()))
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
        logger.info("ISBN: {} - Book updated by {} at {}.".format(book_e.isbn, book_e.updated_by, timezone.now()))
        return redirect('home')

@method_decorator(login_required, name='dispatch')
class UnitUpdateView(UpdateView):
    model = Unit
    fields = ('chapter_number', 'chapter_title')
    template_name = 'edit_unit.html'
    pk_url_kwarg = 'unit_pk'
    context_object_name = 'unit_e'

    def form_valid(self, form):
        unit_e = form.save(commit=False)
        unit_e.updated_by = self.request.user
        unit_e.save()
        logger.info("ISBN: {}, chapter {} updated by {} at {}.".format(unit_e.book.isbn, unit_e.chapter_number, unit_e.updated_by, timezone.now()))
        return redirect('book_units', pk=unit_e.book.pk)

def deactivate_book(request, pk):
    book = get_object_or_404(Book, pk=pk)
    book.active = False
    book.save()
    user = request.user.username
    logger.info("ISBN: {} deactivated by {} at {}.".format(book.isbn, user, timezone.now()))
    print(request.path_info)
    return redirect('home')
    # return HttpResponseRedirect(request.path_info)

def activate_book(request, pk):
    book = get_object_or_404(Book, pk=pk)
    book.active = True
    book.save()
    user = request.user.username
    logger.info("ISBN: {} activated by {} at {}.".format(book.isbn, user, timezone.now()))
    return redirect('home_inactive')

def delete_unit(request, pk, pk1):
    book = get_object_or_404(Book, pk=pk)
    unit = get_object_or_404(Unit, pk=pk1)
    unit.delete()
    user = request.user.username
    logger.info("ISBN: {}, chapter {} deleted by {} at {}.".format(book.isbn, unit.chapter_number, user, timezone.now()))
    return redirect('book_units', pk=pk)    

def delete_element(request, pk, pk1, pk2):
    book = get_object_or_404(Book, pk=pk)
    unit = get_object_or_404(Unit, pk=pk1)
    element = get_object_or_404(Element, pk=pk2)
    element.delete()
    user = request.user.username
    logger.info("ISBN: {}, chapter {}, element {} deleted by {} at {}.".format(book.isbn, unit.chapter_number, element.element_number, user, timezone.now()))
    return redirect('unit_elements', pk=pk, pk1=pk1)

def delete_followup(request, pk, pk1, pk2, pk3):
    book = get_object_or_404(Book, pk=pk)
    unit = get_object_or_404(Unit, pk=pk1)
    element = get_object_or_404(Element, pk=pk2)
    followup = get_object_or_404(FollowUp, pk=pk3)
    followup.delete()
    user = request.user.username
    logger.info("ISBN: {}, chapter {}, element {}, followup dated {} deleted by {} at {}.".format(book.isbn, unit.chapter_number, element.element_number, followup.followedup_at, user, timezone.now()))
    return redirect('element_followups', pk=pk, pk1=pk1, fu=pk2)

# class UnitDelete(DeleteView):
#     model = Unit
#     template_name = 'unit_confirm_delete.html'
#     success_url = reverse_lazy('home')

@method_decorator(login_required, name='dispatch')
class ElementUpdateView(UpdateView):
    model = Element
    # fields = '__all__'
    # fields = ('unit', 'element_number', 'caption', 'element_type', 'source', 'credit_line', 'source_link', 'title', 'rh_email', 'alt_email', 'rh_address', 'phone', 'fax', 'insert_1', 'jbl_rh_name', 'requested_on', 'granted_on', 'permission_status', 'denied_on')
    fields = ('unit', 'element_number', 'caption', 'element_type', 'source', 'credit_line', 'source_link', 'title', 'contact', 'insert_1', 'jbl_rh_name', 'requested_on', 'granted_on', 'permission_status', 'denied_on')
    template_name = 'edit_element.html'
    pk_url_kwarg = 'element_pk'
    context_object_name = 'element_e'

    def form_valid(self, form):
        element_e = form.save(commit=False)
        element_e.updated_by = self.request.user
        element_e.save()
        logger.info("ISBN: {}, chapter {}, element {} updated by {} at {}.".format(element_e.unit.book.isbn, element_e.unit.chapter_number, element_e.element_number, element_e.updated_by, timezone.now()))
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
        logger.info("Followup date updated to {} for ISBN: {}, chapter {}, element {} by {} at {}.".format(followups.followedup_at, followups.element.unit.book.isbn, followups.element.unit.chapter_number, followups.element.element_number, followups.updated_by, timezone.now()))
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
        if not p.contact.rh_email is None:
            rh_email=p.contact.rh_email.strip()
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
    response['Content-Disposition'] = 'attachment; filename="agreement_{}.pdf"'.format(pk)
    response['Content-Disposition'] = 'filename="agreement_{}.pdf"'.format(pk)
    weasyprint.HTML(string=html, base_url=request.build_absolute_uri("/")).write_pdf(response, stylesheets=[weasyprint.CSS(settings.STATIC_ROOT + 'css/pdf.css')], presentational_hints=True)
    return response

def email_agreement(request, pk, ems):
    element = Element.objects.filter(unit__book=pk, requested_on=None)
    book = get_object_or_404(Book, pk=pk)
    ems_list = json.loads(ems)    
    subject = "Jones & Bartlett Permission Request - {}, {}".format(book.title, book.isbn)
    media_path = settings.MEDIA_ROOT
    
    jbl_rh_name = ''
    for ems in ems_list:
        for e in element:
            if ems==e.pk:
                email_rh = e.contact.rh_email
                jbl_rh_name = e.jbl_rh_name

    if jbl_rh_name=='':
        return redirect('unit_list', pk=book.pk)
    
    rh_name = jbl_rh_name.replace(" ", "_")

    e_list = email_rh.split (",")
    rh_name.replace(" ", "_")
    user_data = User.objects.get(username=request.user.username)
    message = render_to_string("emailbody.html", {'ems_list': ems_list, 'element': element, 'user': user_data})
   
    email = EmailMessage(subject, message, 's4permission@gmail.com', e_list)

    html = render_to_string("generate_agreement.html", {'ems_list': ems_list, 'element': element})
    out = BytesIO()
    stylesheets = [weasyprint.CSS(settings.STATIC_ROOT + 'css/pdf.css')]
    weasyprint.HTML(string=html, base_url=request.build_absolute_uri("/")).write_pdf(out, stylesheets=stylesheets)
    response = HttpResponse(content_type="application/pdf")
    email.attach("Jones_and_Bartlett_Learning_{}_{}.pdf".format(book.isbn, rh_name), out.getvalue(), 'application/pdf')
    email.content_subtype = "html"
    # email.send()

    for ems in ems_list:
        for e in element:
            if ems==e.pk:
                links="{}/documents/{}/resized/{}_CH{}_{}{}.png".format(media_path, e.unit.book.isbn,e.unit.book.isbn,e.unit.chapter_number,e.shortform(),e.element_number)
                if path.exists(links):
                    if e.element_type == "Photo":
                        print(links)
                        email.attach_file(links)
                        
    internet_socket = True
    try:
        email.send()
    except socket.error as e:
        if e.errno == 8:
            print('There was an error sending an email: ', e)
            internet_socket = False
    user = request.user.username
    
    for ems in ems_list:
        for e in element:
            if ems==e.pk:
                e.requested_on=timezone.now()
                e.save()
                logger.info("Email agreement sent for ISBN {}, chapter {}, element {} by user {} at {}".format(book.isbn, e.unit.chapter_number, e.element_number, user, timezone.now()))
    return render(request, 'email_agreement_status.html', {'book': book, 'user': user_data, 'e_list': e_list, 'internet_socket': internet_socket})


def test_email_agreement(request, pk, ems):
    element = Element.objects.filter(unit__book=pk, requested_on=None)
    book = get_object_or_404(Book, pk=pk)
    ems_list = json.loads(ems)    
    subject = "Jones & Bartlett Permission Request - {}, {}".format(book.title, book.isbn)
    media_path = settings.MEDIA_ROOT

    jbl_rh_name = ''

    for ems in ems_list:
        for e in element:
            if ems==e.pk:
                jbl_rh_name = e.jbl_rh_name
    if jbl_rh_name=='':
        return redirect('unit_list', pk=book.pk)

    rh_name = jbl_rh_name.replace(" ", "_")
    user_data = User.objects.get(username=request.user.username)
    message = render_to_string("emailbody.html", {'ems_list': ems_list, 'element': element, 'user': user_data})

    email = EmailMessage(subject, message, 's4permission@gmail.com', [request.user.email])
    
    html = render_to_string("generate_agreement.html", {'ems_list': ems_list, 'element': element})
    out = BytesIO()
    stylesheets = [weasyprint.CSS(settings.STATIC_ROOT + 'css/pdf.css')]
    weasyprint.HTML(string=html, base_url=request.build_absolute_uri("/")).write_pdf(out, stylesheets=stylesheets)
    response = HttpResponse(content_type="application/pdf")
    email.attach("Jones_and_Bartlett_Learning_{}_{}.pdf".format(book.isbn, rh_name), out.getvalue(), 'application/pdf')
    email.content_subtype = "html"
    # email.send()

    for ems in ems_list:
        for e in element:
            if ems==e.pk:
                links="{}/documents/{}/resized/{}_CH{}_{}{}.png".format(media_path, e.unit.book.isbn,e.unit.book.isbn,e.unit.chapter_number,e.shortform(),e.element_number)
                if path.exists(links):
                    if e.element_type == "Photo":
                        print(links)
                        email.attach_file(links)
    
    internet_socket = True
    try:
        email.send()
    except socket.error as e:
        if e.errno == 8:
            print('There was an error sending an email: ', e)
            internet_socket = False

    return render(request, 'test_email_agreement_status.html', {'book': book, 'user': user_data, 'internet_socket': internet_socket})

def email_body(request, pk, ems):
    element = Element.objects.filter(unit__book=pk)
    book = get_object_or_404(Book, pk=pk)
    ems_list = json.loads(ems)
    user_data = User.objects.get(username=request.user.username)
    return render(request, 'emailbody.html', {'ems_list': ems_list, 'element': element, 'user': user_data})

def requested_list(request, pk):
    book = get_object_or_404(Book, pk=pk)
#    unit = get_object_or_404(Unit, pk=pk1)
    element = Element.objects.filter(~Q(requested_on=None), granted_on=None, permission_status=True, unit__book=pk).order_by('requested_on')
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
        if not p.contact.rh_email is None:
            rh_email=p.contact.rh_email.strip()
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
        if not p.contact.rh_email is None:
            rh_email=p.contact.rh_email.strip()
        s=source,credit_line,rh_email
        context[s].append(p.pk)
    context.default_factory = None
    return render(request, "granted_list.html", {'context': context, 'element': element, 'pk': pk, 'book': book})

def update_followups(request, pk, ems):
    element = Element.objects.filter(unit__book=pk)
    book = get_object_or_404(Book, pk=pk)
    user = User.objects.get(username=request.user.username)
    
    ems_list = json.loads(ems)    
    for ems in ems_list:
        for e in element:
            if ems==e.pk:
                e.follow_up.create(followedup_at=timezone.now(), followedup_by=user)
                logger.info("Followup date updated to {} for ISBN {}, chapter {}, element {} by {} at {}".format(timezone.now(), book.isbn, e.unit.chapter_number, e.element_number, user, timezone.now()))    
    return render(request, 'update_followups.html', {'ems_list': ems_list, 'element': element})

def update_granted(request, pk, ems):
    element = Element.objects.filter(unit__book=pk)
    book = get_object_or_404(Book, pk=pk)
    user = User.objects.get(username=request.user.username)
    
    ems_list = json.loads(ems)    
    for ems in ems_list:
        for e in element:
            if ems==e.pk:
                e.granted_on=timezone.now()
                e.updated_by=user
                e.save()
                logger.info("Permission granted for ISBN {}, elements {} by {} at {}".format(book.isbn, e.element_number, e.updated_by, timezone.now())) 
                # element.create(granted_on=timezone.now(), updated_by=user)
    return render(request, 'update_granted.html', {'ems_list': ems_list, 'book': book, 'element': element})

def update_granted_e(request, pk, pk1, pk2):
    book = get_object_or_404(Book, pk=pk)
    unit = get_object_or_404(Unit, pk=pk1)
    element = get_object_or_404(Element, pk=pk2)
    user = User.objects.get(username=request.user.username)
    element.granted_on=timezone.now()
    element.updated_by=user
    element.save()
                # element.create(granted_on=timezone.now(), updated_by=user)
    return render(request, 'update_granted_e.html', {'book': book, 'element': element})

def followup_agreement(request, pk, ems):
    element = Element.objects.filter(unit__book=pk)
    ems_list = json.loads(ems)
    html = render_to_string("generate_followup_agreement.html", {'ems_list': ems_list, 'element': element})
    response = HttpResponse(content_type="application/pdf")
    response['Content-Disposition'] = 'attachment; filename="agreement_{}.pdf"'.format(pk)
    response['Content-Disposition'] = 'filename="agreement_{}.pdf"'.format(pk)
    weasyprint.HTML(string=html, base_url=request.build_absolute_uri("/")).write_pdf(response, stylesheets=[weasyprint.CSS(settings.STATIC_ROOT + 'css/pdf.css')], presentational_hints=True)
    return response

def followup_agreement_e(request, pk, pk1, pk2):
    book = get_object_or_404(Book, pk=pk)
    unit = get_object_or_404(Unit, pk=pk1)
    element = get_object_or_404(Element, pk=pk2)
    user = User.objects.get(username=request.user.username)
    html = render_to_string("generate_followup_agreement_e.html", {'element': element})
    response = HttpResponse(content_type="application/pdf")
    response['Content-Disposition'] = 'attachment; filename="agreement_{}.pdf"'.format(pk)
    response['Content-Disposition'] = 'filename="agreement_{}.pdf"'.format(pk)
    weasyprint.HTML(string=html, base_url=request.build_absolute_uri("/")).write_pdf(response, stylesheets=[weasyprint.CSS(settings.STATIC_ROOT + 'css/pdf.css')], presentational_hints=True)
    return response

def followup_email_body(request, pk, ems):
    element = Element.objects.filter(unit__book=pk)
    book = get_object_or_404(Book, pk=pk)

    # followup = FollowUp.objects.filter(element__unit__book=pk)

    dates = defaultdict(list)
    dict(dates)

    ems_list = json.loads(ems)

    for ems in ems_list:
        for e in element:
            if ems==e.pk:
                dates[e.element_number].append(e.follow_up.all().order_by('followedup_at'))
                #dates=e.follow_up.all()
    dates.default_factory = None
    user_data = User.objects.get(username=request.user.username)                
    return render(request, 'emailbody_followup.html', {'ems_list': ems_list, 'element': element, 'user': user_data, 'dates': dates})

def followup_email_body_e(request, pk, pk1, pk2):
    book = get_object_or_404(Book, pk=pk)
    unit = get_object_or_404(Unit, pk=pk1)
    element = get_object_or_404(Element, pk=pk2)
    user_data = User.objects.get(username=request.user.username)
    return render(request, 'emailbody_followup_e.html', {'element': element, 'user': user_data})


def followup_email_agreement(request, pk, ems):
    element = Element.objects.filter(unit__book=pk)
    book = get_object_or_404(Book, pk=pk)
    media_path = settings.MEDIA_ROOT

    dates = defaultdict(list)
    dict(dates)
    ems_list = json.loads(ems)
    jbl_rh_name = ''   
    for ems in ems_list:
        for e in element:
            if ems==e.pk:
                dates[e.element_number].append(e.follow_up.all().order_by('followedup_at'))
                email_rh = e.contact.rh_email
                jbl_rh_name = e.jbl_rh_name
    if jbl_rh_name=='':
        return redirect('unit_list', pk=book.pk)

    rh_name = jbl_rh_name.replace(" ", "_")
                #dates=e.follow_up.all()

    e_list = email_rh.split (",")            
    dates.default_factory = None
    user_data = User.objects.get(username=request.user.username)  
    subject = "Jones & Bartlett Permission Request - {}, {}".format(book.title, book.isbn)
    message = render_to_string("emailbody_followup.html", {'ems_list': ems_list, 'element': element, 'user': user_data, 'dates': dates})

    email = EmailMessage(subject, message, 's4permission@gmail.com', e_list)

    html = render_to_string("generate_followup_agreement.html", {'ems_list': ems_list, 'element': element})
    out = BytesIO()
    stylesheets = [weasyprint.CSS(settings.STATIC_ROOT + 'css/pdf.css')]
    weasyprint.HTML(string=html, base_url=request.build_absolute_uri("/")).write_pdf(out, stylesheets=stylesheets)
    response = HttpResponse(content_type="application/pdf")
    email.attach("Jones_and_Bartlett_Learning_{}_{}.pdf".format(book.isbn,rh_name), out.getvalue(), 'application/pdf')
    email.content_subtype = "html"
    # email.send()
    
    for ems in ems_list:
        for e in element:
            if ems==e.pk:
                links="{}/documents/{}/resized/{}_CH{}_{}{}.png".format(media_path, e.unit.book.isbn,e.unit.book.isbn,e.unit.chapter_number,e.shortform(),e.element_number)
                if path.exists(links):
                    if e.element_type == "Photo":
                        print(links)
                        email.attach_file(links)

    internet_socket = True
    try:
        email.send()
    except socket.error as e:
        if e.errno == 8:
            print('There was an error sending an email: ', e)
            internet_socket = False
    user = request.user.username

    user = User.objects.get(username=request.user.username)
    for ems in ems_list:
        for e in element:
            if ems==e.pk:
                e.follow_up.create(followedup_at=timezone.now(), followedup_by=user)
                e.save()
                logger.info("Followup date updated to {} for ISBN {}, chapter {}, element {} by {} at {}".format(timezone.now(), book.isbn, e.unit.chapter_number, e.element_number, user, timezone.now()))  
    return render(request, 'followup_email_agreement_status.html', {'book': book, 'user': user_data, 'e_list': e_list, 'internet_socket': internet_socket})

def test_followup_email_agreement(request, pk, ems):
    element = Element.objects.filter(unit__book=pk)
    book = get_object_or_404(Book, pk=pk)
    ems_list = json.loads(ems)
    media_path = settings.MEDIA_ROOT

    subject = "Jones & Bartlett Permission Request - {}, {}".format(book.title, book.isbn)
    user_data = User.objects.get(username=request.user.username)
    message = render_to_string("emailbody_followup.html", {'ems_list': ems_list, 'element': element, 'user': user_data})
    
    email = EmailMessage(subject, message, 's4permission@gmail.com', [request.user.email])

    for ems in ems_list:
        for e in element:
            if ems==e.pk:
                jbl_rh_name = e.jbl_rh_name
    rh_name = jbl_rh_name.replace(" ", "_")
    
    html = render_to_string("generate_followup_agreement.html", {'ems_list': ems_list, 'element': element})
    out = BytesIO()
    stylesheets = [weasyprint.CSS(settings.STATIC_ROOT + 'css/pdf.css')]
    weasyprint.HTML(string=html, base_url=request.build_absolute_uri("/")).write_pdf(out, stylesheets=stylesheets)
    response = HttpResponse(content_type="application/pdf")
    email.attach("Jones_and_Bartlett_Learning_{}_{}.pdf".format(book.isbn, rh_name), out.getvalue(), 'application/pdf')
    email.content_subtype = "html"
    # email.send()

    for ems in ems_list:
        for e in element:
            if ems==e.pk:
                links="{}/documents/{}/resized/{}_CH{}_{}{}.png".format(media_path, e.unit.book.isbn,e.unit.book.isbn,e.unit.chapter_number,e.shortform(),e.element_number)
                if path.exists(links):
                    if e.element_type == "Photo":
                        print(links)
                        email.attach_file(links)

    internet_socket = True
    try:
        email.send()
    except socket.error as e:
        if e.errno == 8:
            print('There was an error sending an email: ', e)
            internet_socket = False
    return render(request, 'test_followup_email_agreement_status.html', {'book': book, 'user': user_data, 'internet_socket': internet_socket})

def followup_email_agreement_e(request, pk, pk1, pk2):
    book = get_object_or_404(Book, pk=pk)
    unit = get_object_or_404(Unit, pk=pk1)
    element = get_object_or_404(Element, pk=pk2)
    user = User.objects.get(username=request.user.username)

    subject = "Jones & Bartlett Permission Request - {}, {}".format(book.title, book.isbn)
    
    jbl_rh_name = element.jbl_rh_name
    if jbl_rh_name=='':
        return redirect('unit_list', pk=book.pk)
    rh_name = jbl_rh_name.replace(" ", "_")
    
    email_rh = element.contact.rh_email
    e_list = email_rh.split (",")

    user_data = User.objects.get(username=request.user.username)
    message = render_to_string("emailbody_followup_e.html", {'element': element, 'user': user_data})

    email = EmailMessage(subject, message, 's4permission@gmail.com', e_list)
   

    html = render_to_string("generate_followup_agreement_e.html", {'element': element})
    out = BytesIO()
    stylesheets = [weasyprint.CSS(settings.STATIC_ROOT + 'css/pdf.css')]
    weasyprint.HTML(string=html, base_url=request.build_absolute_uri("/")).write_pdf(out, stylesheets=stylesheets)
    response = HttpResponse(content_type="application/pdf")
    email.attach("Jones_and_Bartlett_Learning_{}_{}.pdf".format(book.isbn, rh_name), out.getvalue(), 'application/pdf')
    email.content_subtype = "html"
    # email.send()

    media_path = settings.MEDIA_ROOT
    links="{}/documents/{}/resized/{}_CH{}_{}{}.png".format(media_path, element.unit.book.isbn,element.unit.book.isbn,element.unit.chapter_number,element.shortform(),element.element_number)
    if path.exists(links):
        if element.element_type == "Photo":
            email.attach_file(links)

    internet_socket = True
    try:
        email.send()
    except socket.error as e:
        if e.errno == 8:
            print('There was an error sending an email: ', e)
            internet_socket = False

    element.follow_up.create(followedup_at=timezone.now(), followedup_by=user)
    element.save()
    logger.info("Followup date updated to {} for ISBN {}, chapter {}, element {} by {} at {}".format(timezone.now(), book.isbn, unit.chapter_number, element.element_number, user, timezone.now()))  
    return render(request, 'followup_email_agreement_status.html', {'book': book, 'user': user_data, 'e_list': e_list, 'internet_socket': internet_socket})

def test_followup_email_agreement_e(request, pk, pk1, pk2):
    book = get_object_or_404(Book, pk=pk)
    unit = get_object_or_404(Unit, pk=pk1)
    element = get_object_or_404(Element, pk=pk2)

    subject = "Jones & Bartlett Permission Request - {}, {}".format(book.title, book.isbn)
    user_data = User.objects.get(username=request.user.username)
    message = render_to_string("emailbody_followup_e.html", {'element': element, 'user': user_data})

    email = EmailMessage(subject, message, 's4permission@gmail.com', [request.user.email])

    jbl_rh_name = element.jbl_rh_name
    rh_name = jbl_rh_name.replace(" ", "_")

    html = render_to_string("generate_followup_agreement_e.html", {'element': element})
    out = BytesIO()
    stylesheets = [weasyprint.CSS(settings.STATIC_ROOT + 'css/pdf.css')]
    weasyprint.HTML(string=html, base_url=request.build_absolute_uri("/")).write_pdf(out, stylesheets=stylesheets)
    response = HttpResponse(content_type="application/pdf")
    email.attach("Jones_and_Bartlett_Learning_{}_{}.pdf".format(book.isbn, rh_name), out.getvalue(), 'application/pdf')
    email.content_subtype = "html"
    # email.send()  

    media_path = settings.MEDIA_ROOT
    links="{}/documents/{}/resized/{}_CH{}_{}{}.png".format(media_path, element.unit.book.isbn,element.unit.book.isbn,element.unit.chapter_number,element.shortform(),element.element_number)
    print(links)
    if path.exists(links):
        if element.element_type == "Photo":
            email.attach_file(links)

    internet_socket = True
    try:
        email.send()
    except socket.error as e:
        if e.errno == 8:
            print('There was an error sending an email: ', e)
            internet_socket = False
    return render(request, 'test_followup_email_agreement_status.html', {'book': book, 'user': user_data, 'internet_socket': internet_socket})

def update_status_denied(request, pk, pk1, pk2):
    book = get_object_or_404(Book, pk=pk)
    unit = get_object_or_404(Unit, pk=pk1)
    element = get_object_or_404(Element, pk=pk2)
    user = User.objects.get(username=request.user.username)
    element.permission_status=False
    element.denied_on=timezone.now()
    element.updated_by=user
    element.save()
    logger.info("Permission denied on {} for ISBN {}, chapter {}, element {} by {} at {}".format(timezone.now(), book.isbn, unit.chapter_number, element.element_number, user, timezone.now())) 
                # element.create(granted_on=timezone.now(), updated_by=user)
    return render(request, 'update_status_denied.html', {'book':book, 'element': element})


def update_status_restore(request, pk, pk1, pk2):
    book = get_object_or_404(Book, pk=pk)
    unit = get_object_or_404(Unit, pk=pk1)
    element = get_object_or_404(Element, pk=pk2)
    user = User.objects.get(username=request.user.username)
    element.permission_status=True
    element.denied_on=None
    element.updated_by=user
    element.save()
    logger.info("Permission restored on {} for ISBN {}, chapter {}, element {} by {} at {}".format(timezone.now(), book.isbn, unit.chapter_number, element.element_number, user, timezone.now())) 
                # element.create(granted_on=timezone.now(), updated_by=user)
    return render(request, 'update_status_restore.html', {'book': book, 'element': element})

def denied_list(request, pk):
    book = get_object_or_404(Book, pk=pk)
#    unit = get_object_or_404(Unit, pk=pk1)
    element = Element.objects.filter(permission_status=False, unit__book=pk)
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
        if not p.contact.rh_email is None:
            rh_email=p.contact.rh_email.strip()
        s=source,credit_line,rh_email
        context[s].append(p.pk)
    context.default_factory = None
    return render(request, "denied_list.html", {'context': context, 'element': element, 'pk': pk, 'book': book})