from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('1/', views.index1, name='index1'),
    path('2/', views.index2, name='index2'),
    path('3/', views.index3, name='index3'),
    path('add/', views.add_record, name='add_record'),
    path('edit/<int:pk>/', views.edit_record, name='edit_record'),
    path('delete/', views.delete_records, name='delete_records'),
    path('delete/all/', views.delete_all, name='delete_all'),
    path('export/excel/', views.export_excel, name='export_excel'),
    path('import/excel/', views.import_excel, name='import_excel'),
    path('count/', views.count_records, name='count_records'),
    path('detail/<int:pk>/', views.get_record, name='get_record'),
]
