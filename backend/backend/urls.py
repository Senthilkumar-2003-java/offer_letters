from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from candidates.views import (
    CandidateViewSet,
    upload_excel_generate_pdf,
    upload_excel_generate_appointment_pdf,
    upload_excel_generate_joining_pdf,
    upload_excel_generate_contract_pdf,
)

router = DefaultRouter()
router.register(r'candidates', CandidateViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api/generate-offer-letters/',       upload_excel_generate_pdf,                name='generate-offer-letters'),
    path('api/generate-appointment-letters/', upload_excel_generate_appointment_pdf,    name='generate-appointment-letters'),
    path('api/generate-joining-letters/',     upload_excel_generate_joining_pdf,        name='generate-joining-letters'),
    path('api/generate-contract-letters/', upload_excel_generate_contract_pdf, name='generate-contract-letters'),

]