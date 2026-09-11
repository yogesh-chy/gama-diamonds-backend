from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

def health_check(request):
    return JsonResponse({"status": "ok", "app": "Gama Diamonds API"})

def root_view(request):
    return JsonResponse({
        "status": "online",
        "app": "Gama Diamonds API",
        "docs": "/api/docs/",
        "admin": "/admin/",
        "health": "/health/"
    })

urlpatterns = [
    path("", root_view, name="api-root"),
    path("health/", health_check, name="health-check"),
    path("api/health/", health_check, name="api-health-check"),
    path("admin/", admin.site.urls),

    path("api/auth/", include("accounts.urls")),
    path("api/products/", include("products.urls")),
    path("api/orders/", include("orders.urls")),
    path("api/payments/", include("payments.urls")),

    # OpenAPI / Swagger docs (FR: drf-spectacular)
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

