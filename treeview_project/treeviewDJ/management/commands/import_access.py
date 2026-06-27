import pandas as pd
import pyodbc
from django.core.management.base import BaseCommand, CommandError
from treeviewDJ.models import Ingfou


class Command(BaseCommand):
    help = 'Importe les données depuis la base Access (Nom.accdb) vers SQLite'

    def add_arguments(self, parser):
        parser.add_argument('--db-path', default=r'E:\Nom.accdb',
                            help='Chemin vers le fichier Access .accdb')
        parser.add_argument('--table', default='ingfou',
                            help='Nom de la table dans la base Access')
        parser.add_argument('--pwd', default='jinbei',
                            help='Mot de passe de la base Access')

    def handle(self, *args, **options):
        db_path = options['db_path']
        table = options['table']
        pwd = options['pwd']

        conn_str = (
            r'Driver={Microsoft Access Driver (*.mdb, *.accdb)};'
            f'DBQ={db_path};Pwd={pwd}'
        )

        self.stdout.write(f'Connexion à {db_path}...')
        try:
            conn = pyodbc.connect(conn_str)
        except pyodbc.Error as e:
            raise CommandError(f'Échec de connexion à Access : {e}')

        query = f'SELECT * FROM {table}'
        self.stdout.write(f'Exécution : {query}')
        df = pd.read_sql(query, conn)
        conn.close()

        self.stdout.write(f'{len(df)} lignes lues depuis Access.')

        # Renommer les colonnes pour correspondre au modèle Django
        col_map = {
            'SOUS_SECTEUR': 'sous_secteur',
            'N_OPERATI': 'n_operati',
            'CHAPITRE_': 'chapitre',
            'LIBELLE_OP': 'libelle_op',
            'AP_INITIAL': 'ap_initial',
            'COMMUNE': 'commune',
            'GEST_': 'gest',
        }
        df = df.rename(columns=col_map)
        # Ne garder que les colonnes du modèle
        model_fields = list(col_map.values())
        df = df[[c for c in df.columns if c in model_fields]]

        # Remplacer NaN par None
        df = df.where(pd.notnull(df), None)

        # Insérer en base
        created = 0
        for _, row in df.iterrows():
            Ingfou.objects.create(**row.to_dict())
            created += 1
            if created % 100 == 0:
                self.stdout.write(f'  ... {created} importés')

        self.stdout.write(self.style.SUCCESS(
            f'Import terminé : {created} enregistrements créés dans SQLite.'
        ))
