from django.contrib import admin
from .models import Destination, Hotel, Booking, Contact, Testimonial, pack_travel, reser_circuit, PaymentRecord, BlogPost
# Register your models here.

admin.site.register(Destination)   
admin.site.register(Hotel)
admin.site.register(Booking)
admin.site.register(Contact)
admin.site.register(Testimonial)
admin.site.register(pack_travel)
admin.site.register(reser_circuit)
admin.site.register(BlogPost)

@admin.register(PaymentRecord)
class PaymentRecordAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer_name', 'customer_email', 'amount', 'currency', 'status', 'destination', 'pack', 'created_at')
    list_filter = ('status', 'currency', 'created_at')
    search_fields = ('customer_name', 'customer_email', 'stripe_checkout_session_id', 'stripe_payment_intent_id')
    readonly_fields = ('stripe_checkout_session_id', 'stripe_payment_intent_id', 'stripe_customer_id', 'created_at', 'updated_at')
    ordering = ('-created_at',)

