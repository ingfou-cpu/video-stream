from django.shortcuts import render, redirect
import requests
from .models import SearchHistory
from datetime import datetime, timedelta

# Create your views here.


from django.conf import settings

API_KEY = getattr(settings, 'OPENWEATHER_API_KEY', "4d7e013edeb48f3561ed2c988b3cfaf1")


# Mapping des codes météo Open-Meteo vers descriptions FR et emojis
WMO_CODES = {
    0: ('Dégagé', '☀️'),
    1: '🌤️', 2: '⛅', 3: '☁️',
    45: '🌫️', 48: '🌫️',
    51: '🌦️', 53: '🌦️', 55: '🌧️',
    56: '🌧️', 57: '🌧️',
    61: '🌧️', 63: '🌧️', 65: '🌧️',
    66: '🌧️', 67: '🌧️',
    71: '❄️', 73: '❄️', 75: '❄️',
    77: '❄️',
    80: '🌦️', 81: '🌧️', 82: '⛈️',
    85: '🌨️', 86: '🌨️',
    95: '⛈️', 96: '⛈️', 99: '⛈️',
}

WMO_DESCRIPTIONS = {
    0: 'Dégagé', 1: 'Principalement dégagé', 2: 'Partiellement nuageux', 3: 'Couvert',
    45: 'Brouillard', 48: 'Brouillard givrant',
    51: 'Bruine légère', 53: 'Bruine modérée', 55: 'Bruine intense',
    56: 'Bruine verglaçante', 57: 'Bruine verglaçante forte',
    61: 'Pluie légère', 63: 'Pluie modérée', 65: 'Pluie forte',
    66: 'Pluie verglaçante', 67: 'Pluie verglaçante forte',
    71: 'Neige légère', 73: 'Neige modérée', 75: 'Neige forte',
    77: 'Grésil',
    80: 'Averses', 81: 'Averses modérées', 82: 'Averses violentes',
    85: 'Averses de neige', 86: 'Averses de neige fortes',
    95: 'Orage', 96: 'Orage avec grêle', 99: 'Orage violent avec grêle',
}


def get_weather_for_city(city_name):
    """Récupère les données météo actuelles pour une ville donnée.
    Retourne un dict avec les données météo ou None en cas d'erreur."""
    if not city_name:
        return None
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city_name}&appid={API_KEY}&units=metric"
    try:
        resp = requests.get(url, timeout=5)
        data = resp.json()
        if resp.status_code == 200:
            return {
                'city': f"{data['name']}, {data['sys']['country']}",
                'temperature': data['main']['temp'],
                'humidity': data['main']['humidity'],
                'pressure': data['main']['pressure'],
                'description': data['weather'][0]['description'].title(),
                'icon': data['weather'][0]['icon'],
                'lat': data['coord']['lat'],
                'lon': data['coord']['lon'],
            }
    except requests.RequestException:
        pass
    return None


def get_7day_forecast(city_name, lat=None, lon=None):
    """Récupère les prévisions météo sur 7 jours via Open-Meteo (API gratuite, sans clé).
    Retourne une liste de dicts avec les prévisions quotidiennes ou None."""
    if not city_name:
        return None

    # Si lat/lon ne sont pas fournis, les récupérer via OpenWeatherMap
    if lat is None or lon is None:
        weather = get_weather_for_city(city_name)
        if not weather or 'lat' not in weather or 'lon' not in weather:
            return None
        lat = weather['lat']
        lon = weather['lon']

    # Appel à Open-Meteo pour les prévisions sur 7 jours
    url = (
        f"https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        f"&daily=temperature_2m_max,temperature_2m_min,weathercode"
        f"&timezone=auto&forecast_days=7"
    )

    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        if resp.status_code != 200 or 'daily' not in data:
            return None

        daily = data['daily']
        forecast = []
        today = datetime.now()

        day_names_fr = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']
        month_names_fr = ['janv.', 'févr.', 'mars', 'avr.', 'mai', 'juin',
                          'juill.', 'août', 'sept.', 'oct.', 'nov.', 'déc.']

        for i in range(len(daily['time'])):
            date_obj = datetime.strptime(daily['time'][i], '%Y-%m-%d')
            weather_code = daily['weathercode'][i]

            # Emoji et description
            code_entry = WMO_CODES.get(weather_code, '❓')
            if isinstance(code_entry, tuple):
                emoji = code_entry[1]
                description = code_entry[0]
            else:
                emoji = code_entry
                description = WMO_DESCRIPTIONS.get(weather_code, 'Inconnu')

            # Nom du jour
            if date_obj.date() == today.date():
                day_label = "Aujourd'hui"
            elif date_obj.date() == (today + timedelta(days=1)).date():
                day_label = "Demain"
            else:
                day_label = day_names_fr[date_obj.weekday()]

            forecast.append({
                'date': daily['time'][i],
                'day_label': day_label,
                'day_short': day_names_fr[date_obj.weekday()][:3].upper(),
                'date_display': f"{date_obj.day} {month_names_fr[date_obj.month - 1]}",
                'temp_max': round(daily['temperature_2m_max'][i]),
                'temp_min': round(daily['temperature_2m_min'][i]),
                'weather_code': weather_code,
                'emoji': emoji,
                'description': description,
            })

        return forecast
    except requests.RequestException:
        return None


def index(request):
    weather = None
    error = None
    recent_searches = SearchHistory.objects.order_by('-searched_at')[:5]

    if request.method == "POST":
        city = request.POST.get('city', '').strip()
        if city:
            url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"
            try:
                resp = requests.get(url, timeout=5)
                data = resp.json()

                if resp.status_code == 200:
                    weather = {
                        'city': f"{data['name']}, {data['sys']['country']}",
                        'temperature': data['main']['temp'],
                        'humidity': data['main']['humidity'],
                        'pressure': data['main']['pressure'],
                        'description': data['weather'][0]['description'].title(),
                        'icon': data['weather'][0]['icon'],
                    }
                    SearchHistory.objects.create(
                        city_name=data['name'],
                        temperature=data['main']['temp'],
                        humidity=data['main']['humidity'],
                        pressure=data['main']['pressure'],
                        description=data['weather'][0]['description'].title()
                    )
                    recent_searches = SearchHistory.objects.order_by('-searched_at')[:5]
                else:
                    error = data.get("message", "Could not fetch weather data.")
            except requests.RequestException:
                error = "Network error. Please try again."
        else:
            error = "Please enter a city name."
    
    # Si la requête vient de home, sauvegarder en session et rediriger
    if request.POST.get('from_home'):
        request.session['weather_data'] = weather
        request.session['weather_error'] = error
        return redirect('home')

    return render(request, "index.html", {
        'weather': weather,
        'error': error,
        'recent_searches': recent_searches
    })