
from django.shortcuts import render, get_object_or_404, redirect
from .models import Destination, Booking, Contact, Testimonial, pack_travel, Hotel, reser_circuit, PaymentRecord
from .forms import ContactForm
from django.http import HttpResponseRedirect, JsonResponse, HttpResponse
from django.urls import reverse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib import messages
import stripe, requests
from django.contrib.messages.views import SuccessMessageMixin #pour afficher le message de success
import logging
from django.views.generic.list import ListView 
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView
from django.urls import reverse_lazy
from weatherapp.models import SearchHistory
from weatherapp.views import get_weather_for_city, get_7day_forecast
from datetime import datetime, timedelta
#from weatherapp.views import index as weather_index


logger = logging.getLogger(__name__)

# Create your views here.-


"""def home(request):
    #bookings = Booking.objects.all()
    pack_travels = pack_travel.objects.all()
    Destinations = Destination.objects.all()
    return render(request, 'home.html', {'pack_travel': pack_travels, 'Destination': Destinations})"""

class HomeView(ListView):
    model = Destination
    #paginate_by = 4 # Afficher 4 destinations par page
    template_name = 'home.html'
    context_object_name = 'Destination'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['pack_travels'] = pack_travel.objects.all()
        context['SearchHistorys'] = SearchHistory.objects.order_by('-searched_at')[:5]
        # Récupérer les données météo de la session si elles existent
        context['weather_data'] = self.request.session.get('weather_data', None)
        context['weather_error'] = self.request.session.get('weather_error', None)

        # Récupérer les prévisions 7 jours (avec cache en session + TTL 1h)
        FORECAST_CACHE_TTL = 3600  # 1 heure en secondes
        forecast_city = self.request.session.get('forecast_city', None)
        cached_forecast = self.request.session.get('forecast_7days_cache', None)
        cached_city = self.request.session.get('forecast_7days_city', None)
        cached_timestamp = self.request.session.get('forecast_7days_timestamp', None)

        # Vérifier si le cache est encore valide
        cache_expired = True
        if cached_timestamp:
            elapsed = (datetime.now() - datetime.fromisoformat(cached_timestamp)).total_seconds()
            cache_expired = elapsed > FORECAST_CACHE_TTL

        if forecast_city and cached_forecast and cached_city == forecast_city and not cache_expired:
            # Utiliser les données en cache (pas expiré)
            context['forecast_7days'] = cached_forecast
        elif forecast_city:
            # Appel API si pas de cache, ville différente, ou cache expiré
            weather_session = self.request.session.get('weather_data', None)
            lat = weather_session.get('lat') if weather_session else None
            lon = weather_session.get('lon') if weather_session else None
            forecast = get_7day_forecast(forecast_city, lat=lat, lon=lon)
            context['forecast_7days'] = forecast
            # Mettre à jour le cache dans la session
            self.request.session['forecast_7days_cache'] = forecast
            self.request.session['forecast_7days_city'] = forecast_city
            self.request.session['forecast_7days_timestamp'] = datetime.now().isoformat()
        else:
            context['forecast_7days'] = None

        return context

    def post(self, request, *args, **kwargs):
        """Gérer la soumission du formulaire météo"""
        city = request.POST.get('city', '').strip()
        if city:
            weather = get_weather_for_city(city)
            if weather:
                request.session['weather_data'] = weather
                request.session['weather_error'] = None
                request.session['forecast_city'] = city
                # Invalider le cache forecast si la ville change
                if request.session.get('forecast_7days_city') != city:
                    request.session['forecast_7days_cache'] = None
                    request.session['forecast_7days_city'] = None
                    request.session['forecast_7days_timestamp'] = None
            else:
                request.session['weather_data'] = None
                request.session['weather_error'] = f"Impossible de trouver la météo pour '{city}'."
                request.session['forecast_city'] = None
                request.session['forecast_7days_cache'] = None
                request.session['forecast_7days_city'] = None
                request.session['forecast_7days_timestamp'] = None
        else:
            request.session['weather_data'] = None
            request.session['weather_error'] = "Veuillez entrer un nom de ville."
            request.session['forecast_city'] = None
            request.session['forecast_7days_cache'] = None
            request.session['forecast_7days_city'] = None
            request.session['forecast_7days_timestamp'] = None
        return redirect(reverse('home') + '#weather')

class contactcreteview(SuccessMessageMixin, CreateView):
    model = Contact
    form_class = ContactForm
    template_name = 'contact.html'
    success_url = reverse_lazy('contact') # redirige vers la même page après soumission du formulaire
    success_message = "✅ Votre message a été envoyé avec succès !"
    
"""def contact(request):
    submitted = False
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('contact') + '?submitted=True')
    else:
        form = ContactForm
        if 'submitted' in request.GET:
            submitted = True
    return render(request, 'contact.html', {'form': form, 'submitted': submitted})"""

class temoignageViewV(CreateView):
    model = Testimonial
    template_name = 'testimonial_form.html' # On peut aussi utiliser 'temoignage.html' à la place de 'testimonial_form.html' pour afficher les témoignages dans une page dédiée
    fields = ['customer_name', 'destination', 'rating', 'comment']
    context_object_name = 'Testimonial'
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Le livre a été créé avec succès.")
        return response
    success_url = reverse_lazy('temoignage') # redirige vers la page de témoignages après soumission du formulaire

"""def temoignage(request):
    testimonials = Testimonial.objects.all()
    destinations = Destination.objects.all()
    bookings = Booking.objects.all()
    return render(request, 'temoignage.html',{'Testimonial': testimonials, 'Destination': destinations,'Booking': bookings})"""

class temoignageView(ListView):
    model = Testimonial
    paginate_by = 2 # Nombre d'éléments par page
    template_name = 'temoignage.html'
    context_object_name = 'Testimonial'#Avec ListView et model = Testimonial, Django crée automatiquement la variable object_list (et non Testimonial).

def reservation(request):   
    Hotels = Hotel.objects.all()
    Destinations = Destination.objects.all()
    customer_name = ''
    if request.method == 'POST':
        name = request.POST.get('customer_name')
        email = request.POST.get('customer_email')
        phone_number = request.POST.get('phone_number')
        destination_id = request.POST.get('destination')
        check_in = request.POST.get('check_in')
        check_out = request.POST.get('check_out')
        hotel_id = request.POST.get('hotel')
        means_of_transport = request.POST.get('means_of_transport')
        customer_name = name or ''

        try:
            destination = Destination.objects.get(id=destination_id) if destination_id else None
            hotel = Hotel.objects.get(id=hotel_id) if hotel_id else None

            if destination:
                booking = Booking(
                    customer_name=name,
                    customer_email=email,
                    phone_number=phone_number,
                    destination=destination,
                    hotel=hotel,
                    check_in_date=check_in,
                    check_out_date=check_out,
                    means_of_transport=means_of_transport
                )
                booking.save()
        except (Destination.DoesNotExist, Hotel.DoesNotExist):
            pass
    return render(request, 'reservation.html', {'Hotels': Hotels, 'Destinations': Destinations, 'customer_name': customer_name})


def reselieuChoisi(request, destination_id):
    destination = Destination.objects.get(id=destination_id)
    hotels = Hotel.objects.filter(destination=destination)
    confirmation_message = None

    # Récupérer la météo de la destination (avec cache session TTL 1h)
    DEST_WEATHER_TTL = 3600
    dest_weather = None
    if destination.city_name:
        cache_key = f"dest_weather_{destination.id}"
        cache_ts_key = f"dest_weather_ts_{destination.id}"
        cached = request.session.get(cache_key, None)
        cached_ts = request.session.get(cache_ts_key, None)

        cache_expired = True
        if cached_ts:
            elapsed = (datetime.now() - datetime.fromisoformat(cached_ts)).total_seconds()
            cache_expired = elapsed > DEST_WEATHER_TTL

        if cached and not cache_expired:
            dest_weather = cached
        else:
            dest_weather = get_weather_for_city(destination.city_name)
            request.session[cache_key] = dest_weather
            request.session[cache_ts_key] = datetime.now().isoformat()

    if request.method == 'POST':
        name = request.POST.get('customer_name')
        email = request.POST.get('customer_email')
        phone_number = request.POST.get('phone_number')
        hotel_id = request.POST.get('hotel')
        check_in = request.POST.get('check_in')
        check_out = request.POST.get('check_out')
        means_of_transport = request.POST.get('means_of_transport')

        try:
            hotel = Hotel.objects.get(id=hotel_id) if hotel_id else None
            booking = Booking(
                customer_name=name,
                customer_email=email,
                phone_number=phone_number,
                destination=destination,
                hotel=hotel,
                check_in_date=check_in,
                check_out_date=check_out,
                means_of_transport=means_of_transport
            )
            booking.save()
            confirmation_message = "✅ Votre réservation a été confirmée avec succès !"
        except Hotel.DoesNotExist:
            confirmation_message = "❌ Erreur : l'hôtel sélectionné n'existe pas."

    return render(request, 'reselieuChoisi.html', {
        'destination': destination,
        'hotels': hotels,
        'confirmation_message': confirmation_message,
        'dest_weather': dest_weather,
    })


def reservCroisiere(request, pack_travel_id):
    pack_travel_instance = get_object_or_404(pack_travel, id=pack_travel_id)
    customer_name = ''
    customer_email = ''
    customer_phone = ''
    nombre_personnes = 1
    nombre_enfants = 0
    confirmation_message = None
    show_confirmation = False

    if request.method == 'POST':
        step = request.POST.get('step', 'calcul')

        name = request.POST.get('customer_name')
        email = request.POST.get('customer_email')
        phone_number = request.POST.get('phone_number')
        nombre_personnes = request.POST.get('nombre_personnes')
        nombre_enfants = request.POST.get('nombre_enfants')
        customer_name = name or ''
        customer_email = email or ''
        customer_phone = phone_number or ''
        nb_personnes = int(nombre_personnes) if nombre_personnes else 1
        nb_enfants = int(nombre_enfants) if nombre_enfants else 0

        if step == 'calcul':
            show_confirmation = True
        elif step == 'confirm':
            try:
                reservation = reser_circuit(
                    pack_travel=pack_travel_instance,
                    customer_name=name,
                    customer_email=email,
                    phone_number=phone_number,
                )
                reservation.save()
                confirmation_message = "✅ Votre réservation de croisière a été confirmée avec succès !"
            except Exception as e:
                confirmation_message = f"❌ Erreur lors de la réservation : {str(e)}"

    return render(request, 'reservCroisiere.html', {
        'pack_travel': pack_travel_instance,
        'customer_name': customer_name,
        'customer_email': customer_email,
        'customer_phone': customer_phone,
        'nombre_personnes': nombre_personnes,
        'nombre_enfants': nombre_enfants,
        'confirmation_message': confirmation_message,
        'show_confirmation': show_confirmation
    })

def about(request):
    return render(request, 'about.html', {  })


def croisiere(request):
    pack_travels = pack_travel.objects.all()
    return render(request, 'croisiere.html', {'pack_travel': pack_travels})


#-----------------------------circuit------------------------------------------------------------
def circuit(request):
    pack_travels = pack_travel.objects.all()
    Destinations = Destination.objects.all()
    return render(request, 'circuit_touris.html', {'Destination': Destinations, 'pack_travels': pack_travels})


class circuitChoisiView(DetailView):
    model = pack_travel
    template_name = 'circuitChoisi.html'
    context_object_name = 'pack_travels'

    def post(self, request, *args, **kwargs):
        """Gérer la soumission du formulaire de réservation"""
        self.object = self.get_object()
        pack_travel_instance = self.object
        
        name = request.POST.get('customer_name')
        email = request.POST.get('customer_email')
        phone_number = request.POST.get('phone_number')

        try:
            reservation = reser_circuit(
                customer_name=name,
                customer_email=email,
                phone_number=phone_number,
                pack_travel=pack_travel_instance
            )
            reservation.save()
            messages.success(request, "✅ Votre réservation a été confirmée avec succès !")
        except Exception as e:
            messages.error(request, f"❌ Erreur : {str(e)}")

        return redirect('circuitChoisi', pk=pack_travel_instance.pk)

"""def circuitChoisi(request, pack_travel_id):
    pack_travels = pack_travel.objects.get(id=pack_travel_id)
    confirmation_message = None

    if request.method == 'POST':
        name = request.POST.get('customer_name')
        email = request.POST.get('customer_email')
        phone_number = request.POST.get('phone_number')

        try:
            booking = reser_circuit(
                customer_name=name,
                customer_email=email,
                phone_number=phone_number,
                pack_travel=pack_travels
            )
            booking.save()
            confirmation_message = "✅ Votre réservation a été confirmée avec succès !"
        except Exception as e:
            confirmation_message = f"❌ Erreur : {str(e)}"

    return render(request, 'circuitChoisi.html', {
        'pack_travels': pack_travels,
        'confirmation_message': confirmation_message
    })"""
#============================= Corrency payment =============================#
CURRENCY_API = 'https://api.exchangerate-api.com/v4/latest/EUR'

def convertir_devise(request):
    taux_de_change = {}
    erreur = None

    try:
        response = requests.get(CURRENCY_API, timeout=10)
        data = response.json()

        if response.status_code == 200 and 'rates' in data:
            raw = data.get('rates', {})
            raw['EUR'] = 1.0
            wanted = {'EUR', 'USD', 'GBP', 'JPY', 'CNY', 'DZD', 'MAD', 'TND', 'CAD', 'CHF', 'TRY', 'SAR', 'AED', 'QAR', 'BHD', 'KWD', 'OMR'}
            taux_de_change = {k: v for k, v in raw.items() if k in wanted}
        else:
            erreur = "Impossible de récupérer les taux de change."
    except Exception as e:
        erreur = f"Connexion impossible : {str(e)}"

    contexte = {
        'taux': taux_de_change,
        'erreur': erreur
    }
    return render(request, 'convertisseur.html', contexte)


def historical_rates_api(request):
    """API endpoint qui retourne les taux historiques sur 7 jours"""
    from_currency = request.GET.get('from', 'EUR')
    to_currency = request.GET.get('to', 'USD')

    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')

    # Frankfurter ne supporte pas DZD, on utilise l'API principale pour ces paires
    frankfurter = f'https://api.frankfurter.app/{start_date}..{end_date}?from={from_currency}&to={to_currency}'

    try:
        resp = requests.get(frankfurter, timeout=10)
        data = resp.json()

        if resp.status_code == 200 and 'rates' in data:
            historical = []
            for date_str, rate_val in sorted(data['rates'].items()):
                historical.append({
                    'date': date_str,
                    'rate': rate_val.get(to_currency, 0)
                })
            return JsonResponse({'success': True, 'data': historical, 'base': from_currency, 'target': to_currency})
        else:
            return JsonResponse({'success': False, 'error': 'Données historiques non disponibles pour cette paire'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
#============================= VUES PAIEMENT STRIPE =============================#

def payment_home(request):
    """Page de paiement avec liste des destinations et packs"""
    destinations = Destination.objects.all()
    packs = pack_travel.objects.all()
    context = {
        'destinations': destinations,
        'packs': packs,
        'stripe_public_key': settings.STRIPE_PUBLIC_KEY,
    }
    return render(request, 'payment_home.html', context)


def create_checkout_destination(request, destination_id):
    """Crée une session de paiement Stripe pour une destination"""
    if request.method != "POST":
        return redirect('payment_home')

    stripe.api_key = settings.STRIPE_SECRET_KEY # 
    destination = get_object_or_404(Destination, id=destination_id)

    try:
        checkout_session = stripe.checkout.Session.create(
            line_items=[
                {
                    "price_data": {
                        "currency": "eur",
                        "product_data": {
                            "name": f"Voyage - {destination.name}",
                            "description": destination.description or f"Réservation pour {destination.name}",
                        },
                        "unit_amount": int(destination.price * 100),
                    },
                    "quantity": 1,
                }
            ],
            mode="payment",
            success_url=request.build_absolute_uri(reverse("payment_success")) + "?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=request.build_absolute_uri(reverse("payment_cancel")),
            metadata={
                'type': 'destination',
                'destination_id': destination.id,
                'customer_name': request.POST.get('customer_name', ''),
                'customer_email': request.POST.get('customer_email', ''),
                'customer_phone': request.POST.get('customer_phone', ''),
            }
        )

        PaymentRecord.objects.create(
            destination=destination,
            stripe_checkout_session_id=checkout_session.id,
            amount=destination.price,
            customer_name=request.POST.get('customer_name', ''),
            customer_email=request.POST.get('customer_email', ''),
            customer_phone=request.POST.get('customer_phone', ''),
            status='pending',
        )

        return redirect(checkout_session.url, code=303)

    except stripe.error.StripeError as e:
        logger.error(f"Stripe error: {str(e)}")
        messages.error(request, f"Erreur de paiement: {str(e)}")
        return redirect('payment_home')
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        messages.error(request, "Une erreur inattendue s'est produite.")
        return redirect('payment_home')


def create_checkout_pack(request, pack_id):
    """Crée une session de paiement Stripe pour un pack/circuit"""
    if request.method != "POST":
        return redirect('payment_home')

    stripe.api_key = settings.STRIPE_SECRET_KEY
    pack = get_object_or_404(pack_travel, id=pack_id)

    try:
        checkout_session = stripe.checkout.Session.create(
            line_items=[
                {
                    "price_data": {
                        "currency": "eur",
                        "product_data": {
                            "name": f"Pack - {pack.pack_name}",
                            "description": pack.description or f"Pack voyage: {pack.pack_name}",
                        },
                        "unit_amount": int(pack.price * 100),
                    },
                    "quantity": 1,
                }
            ],
            mode="payment",
            success_url=request.build_absolute_uri(reverse("payment_success")) + "?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=request.build_absolute_uri(reverse("payment_cancel")),
            metadata={
                'type': 'pack',
                'pack_id': pack.id,
                'customer_name': request.POST.get('customer_name', ''),
                'customer_email': request.POST.get('customer_email', ''),
                'customer_phone': request.POST.get('customer_phone', ''),
            }
        )

        PaymentRecord.objects.create(
            pack=pack,
            stripe_checkout_session_id=checkout_session.id,
            amount=pack.price,
            customer_name=request.POST.get('customer_name', ''),
            customer_email=request.POST.get('customer_email', ''),
            customer_phone=request.POST.get('customer_phone', ''),
            status='pending',
        )

        return redirect(checkout_session.url, code=303)

    except stripe.error.StripeError as e:
        logger.error(f"Stripe error: {str(e)}")
        messages.error(request, f"Erreur de paiement: {str(e)}")
        return redirect('payment_home')
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        messages.error(request, "Une erreur inattendue s'est produite.")
        return redirect('payment_home')


def payment_success(request):
    """Page de succès après un paiement Stripe"""
    session_id = request.GET.get('session_id')
    payment_record = None

    if session_id:
        try:
            payment_record = PaymentRecord.objects.get(
                stripe_checkout_session_id=session_id
            )
            payment_record.status = 'completed'
            payment_record.save()

            # Créer la réservation automatiquement
            if payment_record.destination and payment_record.customer_name:
                Booking.objects.create(
                    destination=payment_record.destination,
                    customer_name=payment_record.customer_name,
                    customer_email=payment_record.customer_email,
                    phone_number=payment_record.customer_phone,
                )
            elif payment_record.pack and payment_record.customer_name:
                reser_circuit.objects.create(
                    pack_travel=payment_record.pack,
                    customer_name=payment_record.customer_name,
                    customer_email=payment_record.customer_email,
                    phone_number=payment_record.customer_phone,
                )

        except PaymentRecord.DoesNotExist:
            logger.warning(f"Payment record not found: {session_id}")

    return render(request, 'payment_success.html', {'payment_record': payment_record})


def payment_cancel(request):
    """Page d'annulation de paiement"""
    return render(request, 'payment_cancel.html')


@csrf_exempt
@require_POST
def stripe_webhook(request):
    """Webhook pour gérer les événements Stripe"""
    stripe.api_key = settings.STRIPE_SECRET_KEY
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    webhook_secret = settings.STRIPE_WEBHOOK_SECRET

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
    except ValueError as e:
        logger.error(f"Invalid payload: {str(e)}")
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"Invalid signature: {str(e)}")
        return HttpResponse(status=400)

    event_type = event['type']
    logger.info(f"Received Stripe event: {event_type}")

    if event_type == 'checkout.session.completed':
        handle_checkout_completed(event['data']['object'])
    elif event_type == 'checkout.session.expired':
        handle_checkout_expired(event['data']['object'])
    elif event_type == 'payment_intent.succeeded':
        handle_payment_succeeded(event['data']['object'])
    elif event_type == 'payment_intent.payment_failed':
        handle_payment_failed(event['data']['object'])

    return HttpResponse(status=200)


def handle_checkout_completed(session):
    """Gère l'événement checkout.session.completed"""
    session_id = session.get('id')
    try:
        payment = PaymentRecord.objects.get(stripe_checkout_session_id=session_id)
        payment.status = 'completed'
        payment.stripe_customer_id = session.get('customer', '')
        payment.stripe_payment_intent_id = session.get('payment_intent', '')
        payment.save()
        logger.info(f"Payment completed: {session_id}")
    except PaymentRecord.DoesNotExist:
        logger.warning(f"Payment not found: {session_id}")


def handle_checkout_expired(session):
    """Gère l'événement checkout.session.expired"""
    session_id = session.get('id')
    try:
        payment = PaymentRecord.objects.get(stripe_checkout_session_id=session_id)
        payment.status = 'expired'
        payment.save()
    except PaymentRecord.DoesNotExist:
        pass


def handle_payment_succeeded(payment_intent):
    """Gère l'événement payment_intent.succeeded"""
    payment_intent_id = payment_intent.get('id')
    try:
        payment = PaymentRecord.objects.get(stripe_payment_intent_id=payment_intent_id)
        payment.status = 'completed'
        payment.save()
    except PaymentRecord.DoesNotExist:
        pass


def handle_payment_failed(payment_intent):
    """Gère l'événement payment_intent.payment_failed"""
    payment_intent_id = payment_intent.get('id')
    try:
        payment = PaymentRecord.objects.get(stripe_payment_intent_id=payment_intent_id)
        payment.status = 'failed'
        payment.save()
    except PaymentRecord.DoesNotExist:
        pass


def handler404(request, exception):
    return render(request, '404.html', status=404)

def payment_history(request):
    """Historique des paiements"""
    payments = PaymentRecord.objects.all().order_by('-created_at')
    return render(request, 'payment_history.html', {'payments': payments})

#-------------------Authentification-------------------------------------------------------#
from django.contrib.auth import login, authenticate, logout
from django.utils.translation import activate, get_language
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Inscription réussie ! Bienvenue parmi nous.')
            return redirect('home')
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            next_url = request.GET.get('next', 'home')
            messages.success(request, f'Bon retour, {user.username} !')
            return redirect(next_url)
    else:
        form = AuthenticationForm()
    return render(request, 'registration/login.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.info(request, 'Vous êtes déconnecté.')
    return redirect('home')

@login_required
def profile(request):
    bookings = Booking.objects.filter(customer_email=request.user.email)
    payments = PaymentRecord.objects.filter(customer_email=request.user.email)
    return render(request, 'registration/profile.html', {
        'bookings': bookings,
        'payments': payments,
    })

#-------------------Blog-------------------------------------------------------#
from .models import BlogPost, NewsletterSubscriber

def blog_list(request):
    articles = BlogPost.objects.filter(published=True)
    return render(request, 'blog/list.html', {'articles': articles})

def blog_detail(request, slug):
    article = get_object_or_404(BlogPost, slug=slug, published=True)
    recents = BlogPost.objects.filter(published=True).exclude(slug=slug)[:3]
    return render(request, 'blog/detail.html', {'article': article, 'recents': recents})

#-------------------Newsletter-------------------------------------------------------#
def newsletter_subscribe(request):
    if request.method == 'POST':
        email = request.POST.get('email', '')
        if email:
            NewsletterSubscriber.objects.get_or_create(email=email)
            messages.success(request, 'Merci pour votre inscription à notre newsletter !')
        else:
            messages.error(request, 'Veuillez entrer une adresse email valide.')
    return redirect(request.META.get('HTTP_REFERER', 'home'))

#-------------------Recherche destinations-------------------------------------------------------#
def search_destinations(request):
    query = request.GET.get('q', '')
    price_max = request.GET.get('price_max', '')
    destinations = Destination.objects.all()
    if query:
        destinations = destinations.filter(name__icontains=query) | destinations.filter(description__icontains=query)
    if price_max:
        destinations = destinations.filter(price__lte=price_max)
    return render(request, 'search.html', {
        'destinations': destinations,
        'query': query,
        'price_max': price_max,
    })

#-------------------Carte interactive-------------------------------------------------------#
def map_view(request):
    destinations = Destination.objects.all()
    circuits = pack_travel.objects.all()
    return render(request, 'map.html', {'destinations': destinations, 'circuits': circuits})

#-------------------Récap avant paiement-------------------------------------------------------#
@login_required
def booking_recap(request, destination_id):
    destination = get_object_or_404(Destination, id=destination_id)
    hotels = Hotel.objects.filter(destination=destination)
    return render(request, 'booking_recap.html', {
        'destination': destination,
        'hotels': hotels,
    })

#-------------------Changement de langue-------------------------------------------------------#
def set_language(request, lang_code):
    response = redirect(request.META.get('HTTP_REFERER', 'home'))
    if lang_code in ['fr', 'ar']:
        activate(lang_code)
        response.set_cookie(settings.LANGUAGE_COOKIE_NAME, lang_code)
    return response

