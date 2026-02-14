from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.conf import settings


class UserManager(BaseUserManager):
    def create_user(self, username, phone_number, email=None, password=None, **extra_fields):
        if not phone_number:
            raise ValueError('Phone number must be set')
        if not username:
            raise ValueError('Username must be set')

        user = self.model(
            username=username,
            email=email,
            phone_number=phone_number,
            **extra_fields
        )

        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()

        user.save(using=self._db)
        return user

    def create_superuser(self, username, phone_number, email=None, password=None, **extra_fields):
        if not phone_number:
            raise ValueError('Superusers must have a phone number')

        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('is_verified', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True')

        return self.create_user(
            username=username,
            phone_number=phone_number,
            email=email,
            password=password,
            **extra_fields
        )


class User(AbstractBaseUser, PermissionsMixin):

    class UserType(models.TextChoices):
        USER = 'User', 'User'
        YOGA_INSTRUCTOR = 'Yoga Trainer', 'Yoga Trainer'
        YOGA_DOCTOR = 'Yoga Doctor', 'Yoga Doctor'
        PHYSIOTHERAPIST = 'Physiotherapist', 'Physiotherapist'
        MANAGER = 'Manager', 'Manager'


    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(blank=True, null=True)   # No unique=True
    phone_number = models.CharField(max_length=15, unique=True)

    user_type = models.CharField(
        max_length=20,
        choices=UserType.choices,
        default=UserType.USER
    )

    # For OTP signup verification
    is_verified = models.BooleanField(default=False)

    # Only normal users are active immediately
    is_active = models.BooleanField(default=True)

    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = ['username', 'email']

    def __str__(self):
        return self.username


class UserRefreshToken(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="refresh_tokens"
    )
    refresh_token = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"RefreshToken for {self.user.username}"


class SignupRefreshToken(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="signup_refresh_tokens"
    )
    token = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"SignupRefreshToken for {self.user.username}"
