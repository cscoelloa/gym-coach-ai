from django import forms

from .models import KnowledgeDocument
from .validators import validate_knowledge_document


class KnowledgeDocumentForm(forms.ModelForm):
    class Meta:
        model = KnowledgeDocument
        fields = ("vector_store", "title", "file", "attributes")

    def clean_file(self):
        uploaded = self.cleaned_data["file"]
        if hasattr(uploaded, "size"):
            validate_knowledge_document(uploaded)
        return uploaded
