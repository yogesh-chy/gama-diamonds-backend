from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Q
from core.permissions import IsAdminUser
from .models import Brand, Category, Collection, DiamondType, Product, Style, Subcategory
from .serializers import (
    BrandSerializer,
    CategorySerializer,
    CollectionSerializer,
    DiamondTypeSerializer,
    ProductSerializer,
    StyleSerializer,
    SubcategorySerializer,
)


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all().prefetch_related(
        "images", "sizes", "styles", "collections", "diamond_spec"
    ).select_related("diamond_type", "brand")
    serializer_class = ProductSerializer

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated(), IsAdminUser()]

    def get_queryset(self):
        qs = super().get_queryset()

        category = self.request.query_params.get("category")
        if category:
            qs = qs.filter(category__iexact=category)

        status_param = self.request.query_params.get("status")
        if status_param == "active":
            qs = qs.filter(is_active=True)
        elif status_param == "inactive":
            qs = qs.filter(is_active=False)

        featured = self.request.query_params.get("featured")
        if featured == "true":
            qs = qs.filter(is_featured=True)

        # "Shop by Shape" — diamond_cut already covers this (round, oval,
        # pear, etc.) so no new model was needed for it.
        shape = self.request.query_params.get("shape")
        if shape:
            qs = qs.filter(diamond_cut__iexact=shape)

        # "Shop by Style" — many-to-many, a product can match more than one.
        style = self.request.query_params.get("style")
        if style:
            qs = qs.filter(styles__slug__iexact=style)

        diamond_type = self.request.query_params.get("diamond_type")
        if diamond_type:
            qs = qs.filter(diamond_type__slug__iexact=diamond_type)

        brand = self.request.query_params.get("brand")
        if brand:
            qs = qs.filter(brand__slug__iexact=brand)

        collection = self.request.query_params.get("collection")
        if collection:
            qs = qs.filter(collections__slug__iexact=collection)

        metal_type = self.request.query_params.get("metal_type")
        if metal_type:
            qs = qs.filter(metal_type__iexact=metal_type)

        price_min = self.request.query_params.get("price_min")
        if price_min:
            qs = qs.filter(base_price__gte=price_min)
        price_max = self.request.query_params.get("price_max")
        if price_max:
            qs = qs.filter(base_price__lte=price_max)

        subcategory = self.request.query_params.get("subcategory")
        if subcategory:
            qs = qs.filter(
                Q(diamond_cut__iexact=subcategory) |
                Q(earring_type__iexact=subcategory) |
                Q(necklace_style__iexact=subcategory) |
                Q(bracelet_type__iexact=subcategory) |
                Q(styles__slug__iexact=subcategory)
            )

        search = self.request.query_params.get("search")
        if search:
            qs = qs.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search) |
                Q(sku__icontains=search) |
                Q(slug__icontains=search)
            )

        return qs.distinct()

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        # Support page and limit params from Next.js queries
        limit_param = request.query_params.get("limit")
        page_param = request.query_params.get("page", 1)

        try:
            page_num = int(page_param)
        except ValueError:
            page_num = 1

        total = queryset.count()

        if limit_param:
            try:
                limit = int(limit_param)
                start = (page_num - 1) * limit
                queryset = queryset[start:start + limit]
            except ValueError:
                limit = total
        else:
            limit = total

        serializer = self.get_serializer(queryset, many=True)
        return Response({
            "success": True,
            "data": serializer.data,
            "pagination": {
                "page": page_num,
                "limit": limit,
                "total": total,
                "totalPages": (total + limit - 1) // limit if limit > 0 else 1,
            }
        })


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all().prefetch_related("subcategories")
    serializer_class = CategorySerializer

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated(), IsAdminUser()]


class StyleViewSet(viewsets.ReadOnlyModelViewSet):
    """Public, read-only — powers the "Shop by Style" filter menu."""
    queryset = Style.objects.all()
    serializer_class = StyleSerializer
    permission_classes = [permissions.AllowAny]


class DiamondTypeViewSet(viewsets.ReadOnlyModelViewSet):
    """Public, read-only — powers "Select Diamond Type"."""
    queryset = DiamondType.objects.all()
    serializer_class = DiamondTypeSerializer
    permission_classes = [permissions.AllowAny]


class BrandViewSet(viewsets.ReadOnlyModelViewSet):
    """Public, read-only — powers the "Brands" nav section."""
    queryset = Brand.objects.all()
    serializer_class = BrandSerializer
    permission_classes = [permissions.AllowAny]


class CollectionViewSet(viewsets.ReadOnlyModelViewSet):
    """Public, read-only — powers curated pages like New Arrivals, Next
    Day Delivery, and The Classics."""
    queryset = Collection.objects.all()
    serializer_class = CollectionSerializer
    permission_classes = [permissions.AllowAny]


class SubcategoriesView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, format=None):
        diamond_cuts = list(Product.objects.filter(is_active=True).values_list("diamond_cut", flat=True).distinct())
        earring_types = list(Product.objects.filter(category="earrings", is_active=True).values_list("earring_type", flat=True).distinct())
        necklace_styles = list(Product.objects.filter(category="necklaces", is_active=True).values_list("necklace_style", flat=True).distinct())
        bracelet_types = list(Product.objects.filter(category="bracelets", is_active=True).values_list("bracelet_type", flat=True).distinct())
        metal_types = list(Product.objects.filter(is_active=True).values_list("metal_type", flat=True).distinct())
        ring_styles = list(
            Style.objects.filter(products__category="rings", products__is_active=True)
            .values_list("slug", flat=True).distinct()
        )

        def clean_list(items):
            return [x for x in items if x]

        return Response({
            "success": True,
            "rings": clean_list(ring_styles),
            "diamond_cuts": clean_list(diamond_cuts),
            "earrings": clean_list(earring_types),
            "necklaces": clean_list(necklace_styles),
            "bracelets": clean_list(bracelet_types),
            "metal_types": clean_list(metal_types),
        })
