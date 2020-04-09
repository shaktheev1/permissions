from django.db import models
from django.contrib.auth.models import User

STATUS_CHOICES = [ 
        ('Filled', 'FILLED'),
        ('In Review', 'IN REVIEW'),
        ('Invoice Requested', 'INVOICE REQUESTED'),
        ('Killed', 'KILLED'),
        ('TK from Author', 'TK FROM AUTHOR'),
        ('Need AU Confirmation', 'NEED AU CONFIRMATION'),
        ('Need Comp Copy', 'NEED COMP COPY'),
        ('Need Invoice', 'NEED INVOICE'),
        ('Need PD Confirmation', 'NEED PD CONFIRMATION'),
        ('Need Permission', 'NEED PERMISSION'),
        ('Perm Requested', 'PERM REQUESTED'),
        ('Photo Shoot', 'PHOTO SHOOT'),
        ('Processing Image', 'PROCESSING IMAGE'),
        ('Research', 'RESEARCH'),
        ('Create Original', 'CREATE ORIGINAL'),
    ]
SPECIFIED_CHOICES = [ 
        ('Killed', 'KILLED'),
        ('New', 'NEW'),
        ('Pickup', 'PICKUP'),
        ('Re-use', 'RE-USE'),
        ('Revised', 'REVISED'),
    ]

class Book(models.Model):
    title = models.CharField(max_length=100)
    isbn = models.CharField(max_length=13, unique=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self):
        return self.title

    def get_chapters_count(self):
        return self.units.count()

    def get_elements_count(self):
        return Element.objects.filter(unit__book=self).count() 
   

class Unit(models.Model):
    book = models.ForeignKey(Book, null=True, related_name='units', on_delete=models.CASCADE)
    chapter_number = models.CharField(max_length=30)
    chapter_title = models.CharField(max_length=100)
    active = models.BooleanField()

    def __str__(self):
        return self.chapter_title

class Element(models.Model):
    unit = models.ForeignKey(Unit, null=True, related_name='elements', on_delete=models.CASCADE)
    element_number = models.CharField(max_length=30)
    specified_as = models.CharField(max_length=25, choices=SPECIFIED_CHOICES)
    caption = models.TextField(max_length=300, null=True)
    source = models.CharField(max_length=75, null=True)
    credit_line = models.TextField(max_length=300, null=True)
    status = models.CharField(max_length=25, choices=STATUS_CHOICES)
    source_link = models.CharField(max_length=100, null=True)
    title = models.CharField(max_length=100, null=True)
    rh_email = models.EmailField(null=True)
    alt_email = models.EmailField(null=True)
    rh_address = models.TextField(max_length=100, null=True)
    phone = models.CharField(max_length=20, null=True)
    fax = models.CharField(max_length=20, null=True)
    insert_1 = models.CharField(max_length=100, null=True)
    jbl_rh_name = models.CharField(max_length=75, null=True)
    file_location = models.CharField(max_length=100, null=True)
    file_name = models.CharField(max_length=40, null=True)
    requested_on = models.DateField(null=True)
    granted_on = models.DateField(null=True, blank=True)
    created_at = models.DateField(auto_now_add=True)
    updated_at = models.DateField(null=True)
    created_by = models.ForeignKey(User, null=True, related_name='+', on_delete=models.CASCADE)
    updated_by = models.ForeignKey(User, null=True, related_name='+', on_delete=models.CASCADE)
    active = models.BooleanField(default=True)


    def __str__(self):
        return self.element_number

    def get_last_followup(self):
        return FollowUp.objects.filter(element=self).order_by('followedup_at').last()
    
    def get_source_as_markdown(self):
        return mark_safe(markdown(self.source, safe_mode='escape'))

class FollowUp(models.Model):
    element = models.ForeignKey(Element, null=True, related_name='follow_up', on_delete=models.CASCADE)
    followedup_at = models.DateTimeField(null=True)
    followedup_by = models.ForeignKey(User, null=True, related_name="+", on_delete=models.CASCADE)

    def __str__(self):
        return str(self.followedup_at)

    