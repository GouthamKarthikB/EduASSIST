# backend/core/tests/test_pdf_service.py
import os
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth.models import User
from core.models.document import Document
from core.services.pdf_service import PDFService
from django.conf import settings

class PDFServiceTest(TestCase):
    def setUp(self):
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        # Create a test document using your existing PDF file
        with open('C:\Users\nanda\Downloads\ASSIGNMENT-2 (1).pdf', 'rb') as f:
            self.document = Document.objects.create(
                name='test.pdf',
                file=SimpleUploadedFile('test.pdf', f.read()),
                user=self.user
            )

    def tearDown(self):
        # Cleanup
        if self.document.file:
            self.document.file.delete()
        if self.document.preview:
            self.document.preview.delete()

    def test_process_uploaded_pdf(self):
        """Test PDF processing and preview generation"""
        PDFService.process_uploaded_pdf(self.document)
        self.assertTrue(self.document.preview)
        self.assertTrue(os.path.exists(self.document.preview.path))

    def test_extract_questions(self):
        """Test question extraction functionality"""
        questions = PDFService.extract_questions(self.document.file.path)
        self.assertIsInstance(questions, list)
        # Test the structure of extracted questions
        if questions:  # If questions were found
            self.assertIn('question_id', questions[0])
            self.assertIn('question', questions[0])
