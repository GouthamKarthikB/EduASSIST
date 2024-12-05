# core/models/api_response.py
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from .document import Document

class APIResponse(models.Model):
    DETAIL_CHOICES = [
        ('low', 'Low Detail'),
        ('medium', 'Medium Detail'),
        ('high', 'High Detail')
    ]

    question = models.TextField(
        help_text="The extracted question from document"
    )
    answer = models.TextField(
        null=True, 
        blank=True,
        help_text="Generated answer for the question"
    )
    question_id = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        help_text="Sequential ID of the question in document"
    )
    detail_level = models.CharField(
        max_length=10,
        choices=DETAIL_CHOICES,
        default='medium',
        help_text="Detail level used for answer generation"
    )
    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name='api_responses'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='responses'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    generation_time = models.FloatField(
        null=True, 
        help_text="Time taken to generate answer in seconds"
    )
    tokens_used = models.PositiveIntegerField(
        null=True,
        help_text="Number of tokens used in answer generation"
    )

    class Meta:
        unique_together = ['document', 'question_id']
        ordering = ['question_id']
        verbose_name = 'API Response'
        verbose_name_plural = 'API Responses'
        indexes = [
            models.Index(fields=['document', 'question_id']),
            models.Index(fields=['user', 'created_at'])
        ]

    def __str__(self):
        return f"Q{self.question_id}: {self.question[:50]}"

    def save(self, *args, **kwargs):
        # Ensure question_id is unique per document
        if not self.pk:  # Only for new instances
            existing_max = APIResponse.objects.filter(
                document=self.document
            ).aggregate(models.Max('question_id'))['question_id__max']
            self.question_id = (existing_max or 0) + 1
        super().save(*args, **kwargs)
