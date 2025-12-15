import requests

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from django.urls import reverse_lazy, reverse
from django.views.generic import FormView, DetailView, TemplateView
from rest_framework import generics
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from .forms import TextForm
from .models import Paste
from .serializers import PasteSerializer
from .utils import S3UtilsMixin, PasteExpirationMixin


class Home(S3UtilsMixin, FormView):
    form_class = TextForm
    template_name = "paste/home.html"
    model = Paste
    context_object_name = "content"

    def get_success_url(self):
        return reverse_lazy('user_text', kwargs={'data': self.paste_hash})

    def form_valid(self, form):
        paste_text = form.cleaned_data['paste_text']
        self.paste_hash = self.get_unique_hash()

        self.put_object_in_s3(
            file_hash=self.paste_hash,
            text=paste_text
        )

        Paste.objects.create(
            hash=self.paste_hash,
            expiration_type=form.cleaned_data['expiration'],
            is_private=form.cleaned_data['is_private'],
            owner=self.request.user if self.request.user.is_authenticated else None
        )

        return super().form_valid(form)


class UserText(S3UtilsMixin, DetailView):
    model = Paste
    template_name = "paste/user_text.html"
    context_object_name = 'paste'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        obj = context['paste']
        context['hash'] = self.kwargs.get('data')
        context['can_edit'] = (
            self.request.user.is_authenticated and
            obj.owner == self.request.user
        )

        return context

    def get_object(self, queryset=None):
        try:
            paste = self.get_paste_cached(self.kwargs.get('data'))
            # paste = Paste.objects.get(hash=self.kwargs.get('data'))
        except Exception as e:
            print('не удалось получить объект', e)
            raise Http404

        paste.text = self.get_object_from_s3(paste.hash)

        if paste.is_expired:
            print('паста срок жизни')
            raise Http404

        if paste.is_private == 'private' and self.request.user != paste.owner:
            raise PermissionDenied

        return paste

class EditPaste(LoginRequiredMixin, S3UtilsMixin, FormView):
    login_url = reverse_lazy('users:login')
    form_class = TextForm
    template_name = 'paste/edit_paste.html'
    context_object_name = 'data'

    def dispatch(self, request, *args, **kwargs):
        try:
            obj = Paste.objects.get(hash=self.kwargs.get('data'))
        except Exception as e:
            raise Http404

        if obj.owner != request.user:
            raise PermissionDenied

        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse_lazy('user_text', kwargs={'data': self.kwargs.get('data')})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['hash'] = self.kwargs.get('data')

        return context

    # если буду добавлять изменение продолжительности пасты то надо добавлять через patch запрос
    def form_valid(self, form):

        self.put_object_in_s3(
            file_hash=self.kwargs.get('data'),
            text=form.cleaned_data['paste_text']
        )

        return super().form_valid(form)


class PasteAPIList(PasteExpirationMixin, generics.RetrieveAPIView):
    queryset = Paste.objects.all()
    serializer_class = PasteSerializer
    lookup_field = 'hash'

    def retrieve(self, request, *args, **kwargs):
        obj = self.get_object()
        presigned_url = self.expiration_handler(obj)
        serializer = self.get_serializer_class()(obj, context={
            'download_url': presigned_url,
            'request': request
        })

        return Response(serializer.data)


class ErrorView(TemplateView):
    template_name = 'error.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['message'] = self.get_error_message(context['status_code'])

        return context

    def get_error_message(self, status_code):
        messages = {
            404: 'Page not found',
            500: 'Server error',
            403: 'Forbidden',
        }

        return messages.get(status_code, 'Something went wrong')

    def render_to_response(self, context, **response_kwargs):
        response_kwargs['status'] = context['status_code']

        return super().render_to_response(context, **response_kwargs)
