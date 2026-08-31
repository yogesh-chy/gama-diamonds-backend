import os
import uuid
import cloudinary
import cloudinary.uploader
from django.conf import settings
from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.parsers import MultiPartParser, FormParser
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


class MediaUploadView(APIView):
    permission_classes = [permissions.AllowAny]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, format=None):
        file_obj = request.FILES.get('file') or request.FILES.get('image') or request.FILES.get('video')
        if not file_obj:
            return Response({"error": "No file uploaded"}, status=status.HTTP_400_BAD_REQUEST)

        ext = os.path.splitext(file_obj.name)[1]
        is_video = ext.lower() in ['.mp4', '.webm', '.mov', '.avi', '.mkv', '.ogv']

        cloud_name = getattr(settings, "CLOUDINARY_CLOUD_NAME", "")
        api_key = getattr(settings, "CLOUDINARY_API_KEY", "")
        api_secret = getattr(settings, "CLOUDINARY_API_SECRET", "")
        cloudinary_url = getattr(settings, "CLOUDINARY_URL", "")

        has_cloudinary = bool(cloudinary_url or (cloud_name and api_key and api_secret))

        if has_cloudinary:
            try:
                if cloudinary_url:
                    cloudinary.config(cloudinary_url=cloudinary_url)
                else:
                    cloudinary.config(
                        cloud_name=cloud_name,
                        api_key=api_key,
                        api_secret=api_secret,
                        secure=True,
                    )

                resource_type = "video" if is_video else "auto"
                result = cloudinary.uploader.upload(
                    file_obj,
                    resource_type=resource_type,
                    folder="gama_diamonds",
                )
                media_url = result.get("secure_url") or result.get("url")
                res_type = result.get("resource_type", "")
                if res_type == "video":
                    is_video = True

                return Response({
                    "success": True,
                    "url": media_url,
                    "public_id": result.get("public_id", ""),
                    "filename": file_obj.name,
                    "media_type": "video" if is_video else "image"
                }, status=status.HTTP_201_CREATED)
            except Exception as e:
                # Cloudinary failed — fall back to local disk storage
                pass

        # Fallback: Local disk storage
        upload_dir = os.path.join(settings.MEDIA_ROOT, "uploads")
        os.makedirs(upload_dir, exist_ok=True)

        unique_name = f"{uuid.uuid4().hex[:10]}{ext}"
        file_path = os.path.join(upload_dir, unique_name)

        with open(file_path, 'wb+') as destination:
            for chunk in file_obj.chunks():
                destination.write(chunk)

        media_url = f"{settings.MEDIA_URL.rstrip('/')}/uploads/{unique_name}"
        if not media_url.startswith('/'):
            media_url = '/' + media_url

        return Response({
            "success": True,
            "url": media_url,
            "filename": file_obj.name,
            "media_type": "video" if is_video else "image"
        }, status=status.HTTP_201_CREATED)




from django.db.models import Min, Max
from .models import Brand, Category, Collection, DiamondType, Product, ProductVariant, Style, Subcategory
from .serializers import (
    BrandSerializer,
    CategorySerializer,
    CollectionSerializer,
    DiamondTypeSerializer,
    ProductImageSerializer,
    ProductListSerializer,
    ProductSerializer,
    ProductVariantSerializer,
    StyleSerializer,
    SubcategorySerializer,
)


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all().prefetch_related(
        "images", "variants", "variants__images", "sizes", "styles", "collections", "diamond_spec"
    ).select_related("diamond_type", "brand", "category_ref", "subcategory_ref")
    serializer_class = ProductSerializer

    def get_permissions(self):
        if self.action in ("list", "retrieve", "resolve_variant"):
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated(), IsAdminUser()]

    def get_serializer_class(self):
        if self.action == "list":
            return ProductListSerializer
        return ProductSerializer

    def get_object(self):
        queryset = self.filter_queryset(self.get_queryset())
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        val = self.kwargs[lookup_url_kwarg]

        if val.isdigit():
            obj = queryset.filter(pk=val).first()
        else:
            obj = queryset.filter(slug__iexact=val).first()

        if not obj:
            from rest_framework.exceptions import NotFound
            raise NotFound(detail="Product not found.")

        self.check_object_permissions(self.request, obj)
        return obj

    def get_queryset(self):
        qs = super().get_queryset()

        category = self.request.query_params.get("category")
        if category:
          if category.lower() in ["rings", "ring"]:
            qs = qs.filter(Q(category__icontains="ring") | Q(category_ref__slug__icontains="ring"))
          else:
            qs = qs.filter(Q(category__iexact=category) | Q(category_ref__slug__iexact=category))

        status_param = self.request.query_params.get("status")
        if status_param == "active":
            qs = qs.filter(is_active=True)
        elif status_param == "inactive":
            qs = qs.filter(is_active=False)

        featured = self.request.query_params.get("featured")
        if featured == "true":
            qs = qs.filter(is_featured=True)

        shape = self.request.query_params.get("shape") or self.request.query_params.get("diamond_cut") or self.request.query_params.get("diamond_shape")
        if shape:
            s_clean = shape.lower().replace("-cut", "").replace("-brilliant", "").replace("-shape", "").strip()
            qs = qs.filter(Q(diamond_cut__iexact=shape) | Q(diamond_cut__iexact=s_clean) | Q(diamond_cut__icontains=s_clean) | Q(name__icontains=s_clean))

        style = self.request.query_params.get("style")
        if style:
            s_lower = style.lower().strip()
            style_q = Q(styles__slug__iexact=style) | Q(subcategory_ref__slug__iexact=style) | Q(subcategory_ref__name__icontains=style)
            if s_lower in ["three-stone", "trilogy", "triology"]:
                style_q |= Q(subcategory_ref__name__icontains="triology") | Q(subcategory_ref__name__icontains="trilogy") | Q(subcategory_ref__name__icontains="three") | Q(name__icontains="trilogy") | Q(name__icontains="three stone")
            elif s_lower in ["diamond-shoulder", "shoulder"]:
                style_q |= Q(subcategory_ref__name__icontains="shoulder") | Q(name__icontains="shoulder")
            elif s_lower in ["under-halo"]:
                style_q |= Q(subcategory_ref__name__icontains="under halo") | Q(name__icontains="under halo")
            elif s_lower in ["halo"]:
                style_q |= Q(subcategory_ref__name__iexact="halo") | Q(name__icontains="halo")
            elif s_lower in ["solitaire"]:
                style_q |= Q(subcategory_ref__name__iexact="solitaire") | Q(name__icontains="solitaire")
            else:
                s_clean = s_lower.replace("-", " ")
                style_q |= Q(subcategory_ref__name__icontains=s_clean) | Q(name__icontains=s_clean)
            qs = qs.filter(style_q)

        diamond_type = self.request.query_params.get("diamond_type")
        if diamond_type:
            qs = qs.filter(diamond_type__slug__iexact=diamond_type)

        brand = self.request.query_params.get("brand")
        if brand:
            qs = qs.filter(brand__slug__iexact=brand)

        collection = self.request.query_params.get("collection")
        if collection:
            qs = qs.filter(collections__slug__iexact=collection)

        metal = self.request.query_params.get("metal") or self.request.query_params.get("metal_type")
        if metal:
            qs = qs.filter(Q(metal_type__iexact=metal) | Q(variants__metal_type__iexact=metal))

        karat = self.request.query_params.get("karat") or self.request.query_params.get("metal_karat")
        if karat:
            qs = qs.filter(Q(metal_karat__iexact=karat) | Q(variants__metal_karat__iexact=karat))

        price_min = self.request.query_params.get("price_min") or self.request.query_params.get("min_price")
        if price_min:
            qs = qs.filter(Q(base_price__gte=price_min) | Q(variants__price__gte=price_min))

        price_max = self.request.query_params.get("price_max") or self.request.query_params.get("max_price")
        if price_max:
            qs = qs.filter(Q(base_price__lte=price_max) | Q(variants__price__lte=price_max))

        availability = self.request.query_params.get("availability")
        if availability in ("in_stock", "true", "yes"):
            qs = qs.filter(Q(total_stock__gt=0) | Q(variants__stock__gt=0))

        subcategory = self.request.query_params.get("subcategory")
        if subcategory:
            qs = qs.filter(
                Q(diamond_cut__iexact=subcategory) |
                Q(earring_type__iexact=subcategory) |
                Q(necklace_style__iexact=subcategory) |
                Q(bracelet_type__iexact=subcategory) |
                Q(styles__slug__iexact=subcategory) |
                Q(subcategory_ref__slug__iexact=subcategory)
            )

        search = self.request.query_params.get("search")
        if search:
            qs = qs.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search) |
                Q(sku__icontains=search) |
                Q(slug__icontains=search) |
                Q(variants__sku__icontains=search)
            )

        sort_param = self.request.query_params.get("sort") or self.request.query_params.get("ordering")
        if sort_param == "price_asc":
            qs = qs.annotate(min_price=Min("variants__price")).order_by("min_price", "base_price")
        elif sort_param == "price_desc":
            qs = qs.annotate(max_price=Max("variants__price")).order_by("-max_price", "-base_price")
        elif sort_param == "newest":
            qs = qs.order_by("-created_at")
        elif sort_param == "name_asc":
            qs = qs.order_by("name")
        elif sort_param == "name_desc":
            qs = qs.order_by("-name")
        elif sort_param == "featured":
            qs = qs.order_by("-is_featured", "-created_at")

        return qs.distinct()

    @action(detail=True, methods=["get"], url_path="resolve-variant")
    def resolve_variant(self, request, pk=None):
        product = self.get_object()
        metal_type = request.query_params.get("metal_type") or request.query_params.get("metal")
        metal_karat = request.query_params.get("metal_karat") or request.query_params.get("karat")
        size = request.query_params.get("size")
        length = request.query_params.get("length")
        bangle_size = request.query_params.get("bangle_size") or request.query_params.get("bangleSize")

        variant_qs = product.variants.filter(is_active=True)

        if metal_type:
            variant_qs = variant_qs.filter(metal_type__iexact=metal_type)
        if metal_karat:
            variant_qs = variant_qs.filter(metal_karat__iexact=metal_karat)
        if size is not None and size != "":
            variant_qs = variant_qs.filter(size__iexact=size)
        if length is not None and length != "":
            variant_qs = variant_qs.filter(length__iexact=length)
        if bangle_size is not None and bangle_size != "":
            variant_qs = variant_qs.filter(bangle_size__iexact=bangle_size)

        variant = variant_qs.first()
        if not variant:
            variant = product.variants.filter(is_active=True, is_default=True).first() or product.variants.filter(is_active=True).first()

        if not variant:
            return Response(
                {"detail": "No active variant available for this product."},
                status=status.HTTP_404_NOT_FOUND
            )

        variant_images = list(variant.images.all())
        if not variant_images:
            variant_images = list(product.images.all())

        return Response({
            "variant_id": variant.id,
            "sku": variant.sku,
            "metal_type": variant.metal_type,
            "metal_karat": variant.metal_karat,
            "size": variant.size,
            "length": variant.length,
            "bangle_size": variant.bangle_size,
            "price": float(variant.price),
            "compare_at_price": float(variant.compare_at_price) if variant.compare_at_price else None,
            "stock": variant.stock,
            "availability": variant.stock > 0,
            "images": ProductImageSerializer(variant_images, many=True).data,
        })

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

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


class FacetedFiltersView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, format=None):
        categories = list(Category.objects.values("id", "name", "slug"))
        styles = list(Style.objects.values("id", "name", "slug"))
        diamond_types = list(DiamondType.objects.values("id", "name", "slug"))
        brands = list(Brand.objects.values("id", "name", "slug"))
        collections = list(Collection.objects.values("id", "name", "slug"))

        diamond_shapes = [
            {"name": label, "value": code}
            for code, label in Product.DIAMOND_CUT_CHOICES
        ]

        metals = list(
            ProductVariant.objects.filter(is_active=True)
            .exclude(metal_type="")
            .values_list("metal_type", flat=True)
            .distinct()
        )
        karats = list(
            ProductVariant.objects.filter(is_active=True)
            .exclude(metal_karat="")
            .values_list("metal_karat", flat=True)
            .distinct()
        )
        sizes = list(
            ProductVariant.objects.filter(is_active=True)
            .exclude(size="")
            .values_list("size", flat=True)
            .distinct()
        )
        lengths = list(
            ProductVariant.objects.filter(is_active=True)
            .exclude(length="")
            .values_list("length", flat=True)
            .distinct()
        )
        bangle_sizes = list(
            ProductVariant.objects.filter(is_active=True)
            .exclude(bangle_size="")
            .values_list("bangle_size", flat=True)
            .distinct()
        )

        min_price = ProductVariant.objects.filter(is_active=True).aggregate(m=Min("price"))["m"] or 0
        max_price = ProductVariant.objects.filter(is_active=True).aggregate(m=Max("price"))["m"] or 10000

        return Response({
            "categories": categories,
            "styles": styles,
            "diamond_types": diamond_types,
            "diamond_shapes": diamond_shapes,
            "brands": brands,
            "collections": collections,
            "metals": metals,
            "karats": karats,
            "sizes": sizes,
            "lengths": lengths,
            "bangle_sizes": bangle_sizes,
            "price_range": {
                "min": float(min_price),
                "max": float(max_price),
            }
        })


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all().prefetch_related("subcategories")
    serializer_class = CategorySerializer

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated(), IsAdminUser()]


class SubcategoryViewSet(viewsets.ModelViewSet):
    queryset = Subcategory.objects.all().select_related("category")
    serializer_class = SubcategorySerializer

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated(), IsAdminUser()]


class StyleViewSet(viewsets.ModelViewSet):
    queryset = Style.objects.all()
    serializer_class = StyleSerializer

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated(), IsAdminUser()]


class DiamondTypeViewSet(viewsets.ModelViewSet):
    queryset = DiamondType.objects.all()
    serializer_class = DiamondTypeSerializer

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated(), IsAdminUser()]


class BrandViewSet(viewsets.ModelViewSet):
    queryset = Brand.objects.all()
    serializer_class = BrandSerializer

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated(), IsAdminUser()]


class CollectionViewSet(viewsets.ModelViewSet):
    queryset = Collection.objects.all()
    serializer_class = CollectionSerializer

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated(), IsAdminUser()]



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
