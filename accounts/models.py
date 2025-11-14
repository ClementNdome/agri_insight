from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Custom user model extending AbstractUser with agriculture-specific fields"""
    
    CROP_INTERESTS = [
        ('wheat', 'Wheat'),
        ('corn', 'Corn'),
        ('rice', 'Rice'),
        ('soybean', 'Soybean'),
        ('cotton', 'Cotton'),
        ('sugar_cane', 'Sugar Cane'),
        ('potato', 'Potato'),
        ('tomato', 'Tomato'),
        ('barley', 'Barley'),
        ('sorghum', 'Sorghum'),
        ('millet', 'Millet'),
        ('other', 'Other'),
    ]
    
    is_farmer = models.BooleanField(
        default=True,
        help_text="Designates whether this user is a farmer"
    )
    bio = models.TextField(
        blank=True,
        null=True,
        max_length=500,
        help_text="User biography"
    )
    crop_interests = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Comma-separated list of crop interests"
    )
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text="Phone number for SMS alerts"
    )
    preferred_units = models.CharField(
        max_length=10,
        choices=[('hectares', 'Hectares'), ('acres', 'Acres')],
        default='hectares',
        help_text="Preferred unit for area measurements"
    )
    email_verified = models.BooleanField(
        default=False,
        help_text="Whether the user's email has been verified"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
    
    def __str__(self):
        return self.username

