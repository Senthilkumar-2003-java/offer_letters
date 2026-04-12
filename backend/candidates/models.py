from django.db import models

class Candidate(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    previous_company = models.CharField(max_length=100)
    role = models.CharField(max_length=100)
    current_salary = models.IntegerField()
    expected_salary = models.IntegerField()

    def __str__(self):
        return self.name