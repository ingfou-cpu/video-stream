from django.urls import path
from . import views
from .views import contactcreteview, HomeView, temoignageView, temoignageViewV, circuitChoisiView

urlpatterns = [
    #path('', views.home, name='home'),
    path ('',HomeView.as_view(), name='home'),# variante HomeView de home 

    path('about/', views.about, name='about'), 

    #path('contact/', views.contact, name='contact'),
    path('contact/', contactcreteview.as_view(), name='contact'),# variante creteview de contact
    

    #path('temoignage/', views.temoignage, name='temoignage'),
    path('temoignage/', temoignageViewV.as_view(), name='temoignage'),# variante HomeView de home 

    path('testimonial_form/', temoignageView.as_view(), name='testimonial_form'),# variante creteview de contact
    path('circuit/', views.circuit, name='circuit'),
    path('croisiere/', views.croisiere, name='croisiere'),
    path('reselieuChoisi/<int:destination_id>/', views.reselieuChoisi, name='reselieuChoisi'),

    #path('circuitChoisi/<int:pack_travel_id>/', views.circuitChoisi, name='circuitChoisi'),
    path('circuitChoisi/<int:pk>/', circuitChoisiView.as_view(), name='circuitChoisi'),

    path('reservCroisiere/<int:pack_travel_id>/', views.reservCroisiere, name='reservCroisiere'),
    
    # Paiement Stripe
    path('payment/', views.payment_home, name='payment_home'),
    path('payment/checkout/destination/<int:destination_id>/', views.create_checkout_destination, name='checkout_destination'),
    path('payment/checkout/pack/<int:pack_id>/', views.create_checkout_pack, name='checkout_pack'),
    path('payment/success/', views.payment_success, name='payment_success'),
    path('payment/cancel/', views.payment_cancel, name='payment_cancel'),
    path('payment/webhook/', views.stripe_webhook, name='stripe_webhook'),
    path('history/', views.payment_history, name='payment_history'),
    path('currency/', views.convertir_devise, name='currency'),
    path('api/historical-rates/', views.historical_rates_api, name='historical_rates_api'),

    # Authentification
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile, name='profile'),

    # Blog
    path('blog/', views.blog_list, name='blog_list'),
    path('blog/<slug:slug>/', views.blog_detail, name='blog_detail'),

    # Newsletter
    path('newsletter/subscribe/', views.newsletter_subscribe, name='newsletter_subscribe'),

    # Recherche
    path('search/', views.search_destinations, name='search'),

    # Carte interactive
    path('map/', views.map_view, name='map'),

    # Récap avant paiement
    path('booking/recap/<int:destination_id>/', views.booking_recap, name='booking_recap'),

    # Changement de langue
    path('lang/<str:lang_code>/', views.set_language, name='set_language'),
]
