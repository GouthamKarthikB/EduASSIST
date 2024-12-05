# core/models/document.py
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator
from django.conf import settings
import os

class Document(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending Processing'),
        ('processed', 'Processed'),
        ('failed', 'Processing Failed')
    ]

    name = models.CharField(max_length=255)
    file = models.FileField(
        upload_to='documents/',
        validators=[FileExtensionValidator(allowed_extensions=['pdf'])]
    )
    answers = models.FileField(
        upload_to='answers/', 
        null=True, 
        blank=True,
        help_text="Generated answers file"
    )
    preview = models.ImageField(
        upload_to='previews/', 
        null=True, 
        blank=True,
        help_text="PDF preview image"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    processing_error = models.TextField(null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='documents'
    )
    file_size = models.PositiveIntegerField(
        help_text="File size in bytes",
        null=True
    )

    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = 'Document'
        verbose_name_plural = 'Documents'
        
    def __str__(self):
        return f"{self.name} - {self.user.username}"

    def save(self, *args, **kwargs):
        if self.file:
            self.file_size = self.file.size
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # Store file paths before deletion
        files_to_delete = [
            self.file.path if self.file else None,
            self.answers.path if self.answers else None,
            self.preview.path if self.preview else None
        ]
        
        # Delete the model instance
        super().delete(*args, **kwargs)
        
        # Clean up files after successful model deletion
        for file_path in files_to_delete:
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except OSError:
                    pass
