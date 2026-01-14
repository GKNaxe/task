from django import forms
from .models import Post

class NewsForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['title', 'text', 'categories']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'text': forms.Textarea(attrs={'class': 'form-control', 'rows': 10}),
            'categories': forms.SelectMultiple(attrs={'class': 'form-control'}),
        }