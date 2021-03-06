from django.core.cache import cache
from django.http import HttpResponse
import threading
import channels
from django.shortcuts import render
import urllib.parse
from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied


class renderThread(threading.Thread):
    def __init__(self, fn, args, kwargs):
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        super().__init__()

    def run(self):
        request = self.args[0]
        page = request.path
        response = self.fn(*self.args, **self.kwargs)
        cache.set("page_{}".format(page), response.content, 12 * 60 * 60)
        channels.Group('render_page_{}'.format(urllib.parse.unquote(page).replace('/', '_').replace('&', '_'))).send({'text':'DONE'})


def render_async_and_cache(fn):
    def wrapper(*args, **kw):
        request = args[0]
        page = request.path

        try:
            if not request.user.is_anonymous:
                return fn(*args, **kw)
        except AttributeError:
            pass

        html = cache.get("page_{}".format(page))
        if html is None:
            renderThread(fn, args, kw).start()
            cache.set("page_".format(page), "rendering", 10*60)
            return render(request, 'waiting.html', {'channel' : page.replace('/', '_')})
        elif html == 'rendering':
            return render(request, 'waiting.html', {'channel': page.replace('/', '_')})
        else:
            return HttpResponse(html, None, None)

    return wrapper

def superuser_required():
    def is_superuser(u):
        if u.is_authenticated():
            if u.is_superuser:
                return True
            else:
                raise PermissionDenied("Access Denied: for admins only.")
        return False

    return user_passes_test(
        is_superuser,
        login_url='/admin/',
        redirect_field_name='next',
    )

