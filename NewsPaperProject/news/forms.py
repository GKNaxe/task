
from django import forms
from .models import Post, Category


class NewsForm(forms.ModelForm):

    class Meta:
        model = Post
        fields = ['title', 'text', 'categories', 'post_type']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'text': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'categories': forms.SelectMultiple(attrs={'class': 'form-control'}),
            'post_type': forms.Select(attrs={'class': 'form-control'}),
        }


class ArticleForm(forms.ModelForm):


    class Meta:
        model = Post
        fields = ['title', 'text', 'categories', 'post_type']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'text': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'categories': forms.SelectMultiple(attrs={'class': 'form-control'}),
            'post_type': forms.Select(attrs={'class': 'form-control'}),
        }

from allauth.account.forms import SignupForm
from django.contrib.auth.models import Group

class CustomSignupForm(SignupForm):
    def save(self, request):
        user = super(CustomSignupForm, self).save(request)
        common_group, created = Group.objects.get_or_create(name='common')
        user.groups.add(common_group)
        return user