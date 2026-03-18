from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from django.urls import reverse_lazy
from django.views.generic import FormView, DetailView, TemplateView
from django.core.exceptions import PermissionDenied

from .forms import TextForm
from .models import Paste
from .selectors import get_paste_views, get_paste_by_hash
from .services import PasteService, PasteViewService
from .integrations import S3Storage


class Home(FormView):
    form_class = TextForm
    template_name = "paste/home.html"
    model = Paste
    context_object_name = "content"

    def form_valid(self, form):
        service = PasteService()
        self.paste_hash = service.create_paste(
            text=form.cleaned_data['paste_text'],
            expiration=form.cleaned_data['expiration'],
            visibility=form.cleaned_data['visibility'],
            user=self.request.user,
        )
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('paste_detail', kwargs={'data': self.paste_hash})


class PasteDetail(DetailView):
    model = Paste
    template_name = "paste/paste_detail.html"
    context_object_name = 'paste'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['views'] = get_paste_views(self.object.hash)
        context['can_edit'] = (
            self.request.user.is_authenticated and
            self.object.owner == self.request.user
        )
        return context

    def get_object(self, queryset=None):
        service = PasteViewService(self.request, self.kwargs.get('data'))
        paste = service.get_full_paste_content()

        if not paste:
            raise Http404

        return paste


class EditPaste(LoginRequiredMixin, FormView):
    login_url = reverse_lazy('users:login')
    form_class = TextForm
    template_name = 'paste/paste_edit.html'
    context_object_name = 'data'

    def dispatch(self, request, *args, **kwargs):
        self.paste = get_paste_by_hash(self.kwargs.get('data'))
        if self.paste.owner != request.user:
            raise PermissionDenied

        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse_lazy('paste_detail', kwargs={'data': self.paste.hash})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['hash'] = self.paste.hash
        context['orig_text'] = S3Storage().get_content(self.paste.hash)

        return context

    # если буду добавлять изменение продолжительности пасты то надо добавлять через patch запрос
    def form_valid(self, form):

        PasteService().update_paste_content(
            paste_hash=self.paste.hash,
            text=form.cleaned_data['paste_text'],
        )

        return super().form_valid(form)

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
