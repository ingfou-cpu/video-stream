from django.contrib import admin
from .models import Ingfou


@admin.register(Ingfou)
class IngfouAdmin(admin.ModelAdmin):
    list_display = ['sous_secteur', 'n_operati', 'chapitre', 'libelle_op', 'ap_initial', 'commune', 'gest']
    search_fields = ['sous_secteur', 'libelle_op', 'commune']
    list_filter = ['commune', 'gest']
