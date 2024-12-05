# backend/core/services/document_service.py
import os
import logging
from typing import List, Optional
from django.conf import settings
from django.core.files import File
from django.contrib.auth.models import User
from core.models.document import Document
from core.models.api_response import APIResponse
from core.services.pdf_service import PDFService

logger = logging.getLogger(__name__)

class DocumentService:
    @staticmethod
    def create_document(file, name: str, user: User) -> Document:
        """Create a new document with initial processing"""
        try:
            document = Document.objects.create(
                name=name,
                file=file,
                user=user
            )
            
            # Process the uploaded PDF
            PDFService.process_uploaded_pdf(document)
            return document
            
        except Exception as e:
            logger.error(f"Error creating document {name}: {str(e)}")
            raise

    @staticmethod
    def delete_document_with_files(document: Document) -> None:
        """Delete document and all associated files"""
        try:
            # Delete associated responses first
            APIResponse.objects.filter(document=document).delete()
            
            # Document's delete method will handle file deletion
            document.delete()
            
        except Exception as e:
            logger.error(f"Error deleting document {document.id}: {str(e)}")
            raise

    @staticmethod
    def get_user_documents(user: User) -> List[Document]:
        """Get all documents for a user"""
        return Document.objects.filter(user=user).order_by('-uploaded_at')

    @staticmethod
    def update_document_answers(document: Document, answers_file_path: str) -> None:
        """Update document with generated answers PDF"""
        try:
            with open(answers_file_path, 'rb') as f:
                answers_name = f"answers_{document.id}.pdf"
                document.answers.save(answers_name, File(f), save=True)
                
            # Clean up temporary file
            if os.path.exists(answers_file_path):
                os.remove(answers_file_path)
                
        except Exception as e:
            logger.error(f"Error updating answers for document {document.id}: {str(e)}")
            raise

    @staticmethod
    def get_document_questions(document: Document) -> List[dict]:
        """Extract questions from document"""
        try:
            return PDFService.extract_questions(document.file.path)
        except Exception as e:
            logger.error(f"Error extracting questions from document {document.id}: {str(e)}")
            raise

    @staticmethod
    def clear_document_answers(document: Document) -> None:
        """Clear generated answers for a document"""
        try:
            if document.answers:
                document.answers.delete()
            document.save()
            APIResponse.objects.filter(document=document).delete()
        except Exception as e:
            logger.error(f"Error clearing answers for document {document.id}: {str(e)}")
            raise
