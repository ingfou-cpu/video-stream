from django.db import models


class Ingfou(models.Model):
    sous_secteur = models.CharField(max_length=50, verbose_name="SOUS_SECTEUR", blank=True, null=True)
    n_operati = models.IntegerField(verbose_name="N_OPERATI", blank=True, null=True)
    chapitre = models.IntegerField(verbose_name="CHAPITRE_", db_column='CHAPITRE_', blank=True, null=True)
    libelle_op = models.CharField(max_length=255, verbose_name="LIBELLE_OP", blank=True, null=True)
    ap_initial = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="AP_INITIAL", blank=True, null=True)
    commune = models.CharField(max_length=100, verbose_name="COMMUNE", blank=True, null=True)
    gest = models.CharField(max_length=50, verbose_name="GEST_", db_column='GEST_', blank=True, null=True)

    class Meta:
        db_table = 'ingfou'
        verbose_name = 'Enregistrement'
        verbose_name_plural = 'Enregistrements'

    def __str__(self):
        return f"{self.sous_secteur or ''} - {self.libelle_op or ''}"
