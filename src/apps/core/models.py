import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _

# 1. Gerenciador de Usuários (Login por Email)
class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError(_('O email é obrigatório'))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)

# 2. O Modelo de Empresa (Tenant)
class Tenant(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nome = models.CharField(max_length=255, verbose_name=_("Nome da Empresa"))
    cnpj = models.CharField(max_length=20, blank=True, null=True)
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nome

# 3. O Usuário do SaaS
class User(AbstractUser):
    username = None # Removemos o username
    email = models.EmailField(_('email address'), unique=True)
    
    tenant = models.ForeignKey(
        Tenant, 
        on_delete=models.CASCADE, 
        related_name='usuarios',
        null=True, 
        blank=True
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        return self.email

# 4. Classe Abstrata para proteger os outros Apps
class TenantAwareModel(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    
    class Meta:
        abstract = True