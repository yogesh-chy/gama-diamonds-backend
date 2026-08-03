from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    BrandViewSet,
    CategoryViewSet,
    CollectionViewSet,
    DiamondTypeViewSet,
    ProductViewSet,
    StyleViewSet,
    SubcategoryViewSet,
    SubcategoriesView,
)

app_name = "products"

router = DefaultRouter()
router.register(r"categories", CategoryViewSet, basename="category")
router.register(r"subcategories", SubcategoryViewSet, basename="subcategory")
router.register(r"styles", StyleViewSet, basename="style")
router.register(r"diamond-types", DiamondTypeViewSet, basename="diamond-type")
router.register(r"brands", BrandViewSet, basename="brand")
router.register(r"collections", CollectionViewSet, basename="collection")
router.register(r"", ProductViewSet, basename="product")

urlpatterns = [
    path("subcategories/summary/", SubcategoriesView.as_view(), name="subcategories-summary"),
    path("", include(router.urls)),
]

