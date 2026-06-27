from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify

# Create your models here.
#-------------------Destinations ----------------------------------------------------------#
class Destination(models.Model):
    name = models.CharField(max_length=100, blank=False, null=False, default='') 
    price = models.DecimalField(max_digits=10, decimal_places=2, blank=False, null=False, default=0.00)  
    city_name = models.CharField(max_length=100)
    description = models.TextField( blank=True)
    image = models.ImageField(upload_to='destination_images/', blank=True, null=True)
    latitude = models.FloatField(default=33.7)
    longitude = models.FloatField(default=3.0)
    def __str__(self): 
        return self.name

#-------------------Hôtels-------------------------------------------------------#
class Hotel (models.Model):
    destination = models.ForeignKey(Destination, on_delete=models.CASCADE)
    hotel_name = models.CharField(max_length=100)
    description = models.TextField( blank=True)
    calification_stars = models.PositiveIntegerField(choices=[(i, str(i)) for i in range(1, 6)])  # Calification from 1 to 5 stars
    price = models.DecimalField(max_digits=10, decimal_places=2)
    reservation_link = models.URLField(blank=True)
    image = models.ImageField(upload_to='hotel_images/', blank=True, null=True)
    status = models.BooleanField(default=True)  # True for Pending, False for Confirmed or Cancelled
    def __str__(self):
        return self.hotel_name
#-------------------Réservation-------------------------------------------------------#
class Booking(models.Model): # Booking = Réservation 
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, default=None, null=True, blank=True)
    destination = models.ForeignKey(Destination, on_delete=models.CASCADE)
    customer_name = models.CharField(max_length=100)
    customer_email = models.EmailField( blank=True, null=True, default='')
    check_in_date = models.DateTimeField(auto_now_add=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True, default='')  
    check_out_date = models.DateTimeField(blank=True, null=True)
    means_of_transport = models.CharField(max_length=100, blank=True, null=True,choices=[('avion', 'Avion'), ('train', 'Train'), ('bus', 'Bus'), ('voiture', 'Voiture de location')])  # choices=[('avion', 'Avion'), ('train', 'Train'), ('bus', 'Bus'), ('voiture', 'Voiture de location')])

    class Meta:
        verbose_name = 'Réservation'  # Nom au singulier dans l'interface d'administration
        verbose_name_plural = 'Réservations'  # Nom au pluriel dans l'interface d'administration
        ordering = ['-check_in_date']  # Order by booking date descending
    def __str__(self):
        return f"Booking for Mr {self.customer_name} to {self.destination.name}"  
        

"""class Reservation(models.Model):
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE)
    customer_email = models.EmailField()
    check_in_date = models.DateField()
    check_out_date = models.DateField()
    room = models.ForeignKey(Room, on_delete=models.SET_NULL, null=True)
    
    def is_available(self):
        # Logique pour vérifier si la chambre est libre pour les dates
        return not Reservation.objects.filter(
            room=self.room,
            check_in_date__lt=self.check_out_date,
            check_out_date__gt=self.check_in_date
        ).exists()"""

#-------------------pack_travel -------------------------------------------------------#
class pack_travel(models.Model):
    pack_name = models.CharField(max_length=100)
    description = models.TextField( blank=True)
    image = models.ImageField(upload_to='pack_travel_images/', blank=True, null=True)
    image_circuit = models.ImageField(upload_to='circuit_images/', blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    galerie_photos = models.ImageField(upload_to='galerie_photos/', blank=True, null=True) 
    itinerary = models.TextField(blank=True)
    date = models.DateField(blank=True, null=True)
    fiche_technique = models.TextField(blank=True)
    def __str__(self):
        return self.pack_name
#-------------------reservation pack_travel -------------------------------------------------------#
class reser_circuit(models.Model):
    pack_travel = models.ForeignKey(pack_travel, on_delete=models.CASCADE)
    customer_name = models.CharField(max_length=100)
    customer_email = models.EmailField( blank=True, null=True, default='')
    phone_number = models.CharField(max_length=20, blank=True, null=True, default='') 
     
    def __str__(self):
        return f"Booking for Mr {self.customer_name} to {self.pack_travel.pack_name}"

#-------------------Contact form -------------------------------------------------------#

class Contact(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField( blank=True, null=True, default=''    )
    phone = models.CharField(max_length=20, blank=True, null=True, default='')
    message = models.TextField( blank=True)
    sent_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Contact: {self.name} - Email: {self.email} - Phone: {self.phone} - Message: {self.message[:50]}..."  # Affiche les 50 premiers caractères du message
#------------------- testimonials-------------------------------------------------------#
class Testimonial(models.Model): # Testimonial = Avis = témoignage
    customer_name = models.ForeignKey(Booking, on_delete=models.CASCADE)
    destination = models.ForeignKey(Destination, on_delete=models.CASCADE)
    rating = models.PositiveIntegerField(choices=[(i, str(i)) for i in range(1, 6)])  # Rating from 1 to 5
    comment = models.TextField( blank=True, null=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Testimonial by {self.customer_name} for {self.destination.name}"


#-------------------Paiement Stripe-------------------------------------------------------#
class PaymentRecord(models.Model):
    """Enregistrement des paiements Stripe"""
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('completed', 'Complété'),
        ('failed', 'Échoué'),
        ('refunded', 'Remboursé'),
        ('expired', 'Expiré'),
    ]

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    booking = models.ForeignKey(Booking, on_delete=models.SET_NULL, null=True, blank=True, related_name='payments')
    reser_circuit = models.ForeignKey(reser_circuit, on_delete=models.SET_NULL, null=True, blank=True, related_name='payments')
    destination = models.ForeignKey(Destination, on_delete=models.SET_NULL, null=True, blank=True)
    pack = models.ForeignKey(pack_travel, on_delete=models.SET_NULL, null=True, blank=True)

    stripe_checkout_session_id = models.CharField(max_length=255, unique=True, blank=True, null=True)
    stripe_payment_intent_id = models.CharField(max_length=255, blank=True, null=True)
    stripe_customer_id = models.CharField(max_length=255, blank=True, null=True)

    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    currency = models.CharField(max_length=3, default='eur')
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')

    customer_name = models.CharField(max_length=100, blank=True, default='')
    customer_email = models.EmailField(blank=True, default='')
    customer_phone = models.CharField(max_length=20, blank=True, default='')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Paiement"
        verbose_name_plural = "Paiements"

    def __str__(self):
        return f"Paiement {self.stripe_checkout_session_id or 'N/A'} - {self.amount}€ ({self.status})"

#-------------------Blog / Articles de voyage-------------------------------------------------------#
class BlogPost(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    author = models.CharField(max_length=100, default='El Bayadh Travels')
    excerpt = models.TextField(max_length=300)
    content = models.TextField()
    image = models.ImageField(upload_to='blog/', blank=True, null=True)
    destination = models.ForeignKey(Destination, on_delete=models.SET_NULL, null=True, blank=True)
    published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Article"
        verbose_name_plural = "Articles"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

#-------------------Newsletter-------------------------------------------------------#
class NewsletterSubscriber(models.Model):
    email = models.EmailField(unique=True)
    subscribed_at = models.DateTimeField(auto_now_add=True)
    active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Abonné"
        verbose_name_plural = "Abonnés"

    def __str__(self):
        return self.email
        

