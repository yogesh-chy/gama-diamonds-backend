import logging
logger = logging.getLogger(__name__)
import os
import uuid
import cloudinary
import cloudinary.uploader
from django.conf import settings
from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
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


ALLOWED_IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
ALLOWED_VIDEO_EXTS = {".mp4", ".webm", ".mov"}
ALLOWED_DOC_EXTS = {".pdf", ".dxf", ".stl", ".obj"}
ALL_ALLOWED_EXTS = ALLOWED_IMAGE_EXTS | ALLOWED_VIDEO_EXTS | ALLOWED_DOC_EXTS

MAX_IMAGE_SIZE = 15 * 1024 * 1024      # 15 MB
MAX_VIDEO_SIZE = 100 * 1024 * 1024     # 100 MB


class MediaUploadView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, format=None):
        file_obj = request.FILES.get('file') or request.FILES.get('image') or request.FILES.get('video')
        if not file_obj:
            return Response({"error": "No file uploaded"}, status=status.HTTP_400_BAD_REQUEST)

        # 1. Extension validation against strict whitelist
        raw_name = getattr(file_obj, "name", "") or ""
        ext = os.path.splitext(raw_name)[1].lower()

        if ext not in ALL_ALLOWED_EXTS:
            return Response(
                {"error": f"Unsupported or prohibited file extension '{ext}'. Allowed: images, videos (.mp4, .webm, .mov), and CAD/docs (.pdf, .dxf, .stl, .obj)."},
                status=status.HTTP_400_BAD_REQUEST
            )

        is_video = ext in ALLOWED_VIDEO_EXTS

        # 2. Authorization check: product videos can only be uploaded by authenticated staff
        if is_video and not (request.user.is_authenticated and (request.user.is_staff or getattr(request.user, "is_superuser", False))):
            return Response(
                {"error": "Authentication with staff privileges is required to upload product videos."},
                status=status.HTTP_403_FORBIDDEN
            )

        # 3. File size validation
        max_size = MAX_VIDEO_SIZE if is_video else MAX_IMAGE_SIZE
        if file_obj.size > max_size:
            max_mb = max_size // (1024 * 1024)
            return Response(
                {"error": f"File size exceeds the {max_mb}MB limit."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 4. MIME content-type safety check
        content_type = getattr(file_obj, "content_type", "") or ""
        dangerous_mimes = ["text/html", "text/javascript", "application/javascript", "application/x-sh", "application/x-msdownload"]
        if any(d in content_type.lower() for d in dangerous_mimes):
            return Response({"error": "Invalid or dangerous file content type."}, status=status.HTTP_400_BAD_REQUEST)

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
                upload_params = {
                    "resource_type": resource_type,
                    "folder": "gama_diamonds",
                }

                # Cloudinary eager video transformations:
                # 1. sp_auto adaptive bitrate streaming (HLS .m3u8 manifest)
                # 2. Optimized responsive MP4 with auto quality & codec
                if is_video:
                    upload_params["eager"] = [
                        {"streaming_profile": "auto", "format": "m3u8"},
                        {"format": "mp4", "quality": "auto", "video_codec": "auto"}
                    ]
                    upload_params["eager_async"] = True

                result = cloudinary.uploader.upload(
                    file_obj,
                    **upload_params
                )
                media_url = result.get("secure_url") or result.get("url")
                res_type = result.get("resource_type", "")
                if res_type == "video":
                    is_video = True

                public_id = result.get("public_id", "")
                cloud = cloud_name or getattr(settings, "CLOUDINARY_CLOUD_NAME", "")

                # Derive HLS and Poster URLs for instant consumption
                hls_url = None
                poster_url = None
                if is_video and public_id and cloud:
                    hls_url = f"https://res.cloudinary.com/{cloud}/video/upload/sp_auto/{public_id}.m3u8"
                    poster_url = f"https://res.cloudinary.com/{cloud}/video/upload/so_0,f_auto,q_auto/{public_id}.jpg"

                # Sanitize reported filename
                safe_filename = os.path.basename(file_obj.name)

                return Response({
                    "success": True,
                    "url": media_url,
                    "public_id": public_id,
                    "filename": safe_filename,
                    "media_type": "video" if is_video else "image",
                    "hls_url": hls_url,
                    "poster_url": poster_url,
                }, status=status.HTTP_201_CREATED)
            except Exception as e:
                logger.error("Cloudinary media upload failed: %s", str(e), exc_info=True)

        # Fallback: Local disk storage
        upload_dir = os.path.join(settings.MEDIA_ROOT, "uploads")
        os.makedirs(upload_dir, exist_ok=True)

        # Strictly generate UUID name with validated extension
        unique_name = f"{uuid.uuid4().hex[:12]}{ext}"
        file_path = os.path.join(upload_dir, unique_name)

        with open(file_path, 'wb+') as destination:
            for chunk in file_obj.chunks():
                destination.write(chunk)

        # Build an absolute URL so the frontend (on a different origin) can load it
        media_path = f"{settings.MEDIA_URL.rstrip('/')}/uploads/{unique_name}"
        if not media_path.startswith('/'):
            media_path = '/' + media_path
        media_url = request.build_absolute_uri(media_path)

        safe_filename = os.path.basename(file_obj.name)
        return Response({
            "success": True,
            "url": media_url,
            "filename": safe_filename,
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
            cat_lower = category.lower().strip()
            if cat_lower in ["engagement-rings", "engagement", "engagement-ring", "rings", "ring"]:
                qs = qs.filter(
                    Q(category__in=["engagement-rings", "rings"]) |
                    Q(category_ref__slug__in=["engagement-rings", "rings"]) |
                    Q(category_ref__name__icontains="engagement") |
                    Q(category_ref__name__iexact="rings")
                )
            elif cat_lower in ["wedding-bands", "wedding", "wedding-rings", "wedding-ring"]:
                qs = qs.filter(
                    Q(category__in=["wedding-bands", "wedding-rings", "wedding"]) |
                    Q(category_ref__slug__in=["wedding-bands", "wedding-rings", "wedding"]) |
                    Q(category_ref__name__icontains="wedding")
                )
            elif cat_lower in ["eternity-bands", "eternity", "eternity-rings", "eternity-ring"]:
                qs = qs.filter(
                    Q(category__in=["eternity-bands", "eternity-rings", "eternity"]) |
                    Q(category_ref__slug__in=["eternity-bands", "eternity-rings", "eternity"]) |
                    Q(category_ref__name__icontains="eternity") |
                    Q(subcategory_ref__slug__icontains="eternity") |
                    Q(subcategory_ref__name__icontains="eternity") |
                    Q(ring_type__icontains="eternity") |
                    Q(ring_style__icontains="eternity")
                )
            elif cat_lower in ["earrings", "earring"]:
                qs = qs.filter(
                    Q(category__in=["earrings", "earring"]) |
                    Q(category_ref__slug__in=["earrings", "earring"]) |
                    Q(category_ref__name__icontains="earring") |
                    Q(subcategory_ref__slug__in=["earrings", "hoop-earrings", "solitaire-studs", "drop-earrings", "halo-earrings", "chandelier-earrings"]) |
                    Q(subcategory_ref__name__icontains="earring") |
                    Q(subcategory_ref__name__icontains="hoop") |
                    Q(subcategory_ref__name__icontains="stud") |
                    Q(earring_type__in=["studs", "hoops", "drops", "huggies", "climbers", "chandelier"]) |
                    Q(name__icontains="earring") |
                    Q(name__icontains="hoop")
                )
            elif cat_lower in ["necklaces", "necklace", "pendants", "pendant"]:
                qs = qs.filter(
                    Q(category__in=["necklaces", "necklace", "pendants", "pendant"]) |
                    Q(category_ref__slug__in=["necklaces", "necklace", "pendants", "pendant"]) |
                    Q(category_ref__name__icontains="necklace") |
                    Q(category_ref__name__icontains="pendant") |
                    Q(subcategory_ref__slug__in=["necklace", "pendants", "heart-pendants", "cross-pendants", "tennis-necklaces", "chains"]) |
                    Q(subcategory_ref__name__icontains="necklace") |
                    Q(subcategory_ref__name__icontains="pendant") |
                    Q(necklace_style__in=["pendant", "chain", "choker", "collar", "station", "lariat", "tennis"]) |
                    Q(name__icontains="necklace") |
                    Q(name__icontains="pendant")
                )
            elif cat_lower in ["bracelets", "bracelet", "bangles", "bangle"]:
                qs = qs.filter(
                    Q(category__in=["bracelets", "bracelet", "bangles", "bangle"]) |
                    Q(category_ref__slug__in=["bracelets", "bracelet", "bangles", "bangle"]) |
                    Q(category_ref__name__icontains="bracelet") |
                    Q(category_ref__name__icontains="bangle") |
                    Q(subcategory_ref__slug__in=["bracelets-bangles", "tennis-bracelets", "bangles", "cuff-bracelets", "chain-bracelets"]) |
                    Q(subcategory_ref__name__icontains="bracelet") |
                    Q(subcategory_ref__name__icontains="bangle") |
                    Q(bracelet_type__in=["bangle", "tennis", "chain", "cuff", "charm", "link"]) |
                    Q(name__icontains="bracelet") |
                    Q(name__icontains="bangle")
                )
            elif cat_lower in ["jewellery", "jewelry", "other", "all-precious-jewellery"]:
                qs = qs.filter(
                    Q(category__in=["jewellery", "jewelry", "other", "earrings", "necklaces", "bracelets", "pendants", "bangles"]) |
                    Q(category_ref__slug__in=["jewellery", "jewelry", "other", "earrings", "necklaces", "bracelets", "pendants", "bangles"]) |
                    Q(category_ref__name__icontains="jewellery") |
                    Q(category_ref__name__icontains="jewelry")
                )
            elif cat_lower in ["hoop-earrings", "hoops", "hoop"]:
                qs = qs.filter(
                    Q(subcategory_ref__slug__in=["hoop-earrings", "hoops"]) |
                    Q(subcategory_ref__name__icontains="hoop") |
                    Q(earring_type="hoops") |
                    Q(name__icontains="hoop")
                )
            elif cat_lower in ["solitaire-studs", "studs", "stud"]:
                qs = qs.filter(
                    Q(subcategory_ref__slug__in=["solitaire-studs", "studs"]) |
                    Q(subcategory_ref__name__icontains="stud") |
                    Q(earring_type="studs") |
                    Q(name__icontains="stud")
                )
            elif cat_lower in ["tennis-bracelets"]:
                qs = qs.filter(
                    Q(subcategory_ref__slug="tennis-bracelets") |
                    Q(bracelet_type="tennis") |
                    Q(name__icontains="tennis")
                )
            elif cat_lower in ["heart-pendants"]:
                qs = qs.filter(
                    Q(subcategory_ref__slug="heart-pendants") |
                    Q(pendant_shape="heart") |
                    Q(name__icontains="heart")
                )
            elif cat_lower in ["cross-pendants"]:
                qs = qs.filter(
                    Q(subcategory_ref__slug="cross-pendants") |
                    Q(pendant_shape="cross") |
                    Q(name__icontains="cross")
                )
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

        gender = self.request.query_params.get("gender")
        if gender:
            qs = qs.filter(gender__iexact=gender)

        ring_type = self.request.query_params.get("ring_type")
        if ring_type:
            rt_clean = ring_type.replace("-", " ")
            qs = qs.filter(Q(ring_type__icontains=rt_clean) | Q(ring_style__icontains=rt_clean))

        shape = self.request.query_params.get("shape") or self.request.query_params.get("diamond_cut") or self.request.query_params.get("diamond_shape")
        if shape:
            s_clean = shape.lower().replace("-cut", "").replace("-brilliant", "").replace("-shape", "").strip()
            qs = qs.filter(
                Q(diamond_cut__iexact=shape) |
                Q(diamond_cut__iexact=s_clean) |
                Q(diamond_cut__icontains=s_clean) |
                Q(diamond_spec__diamond_shape__iexact=shape) |
                Q(diamond_spec__diamond_shape__icontains=s_clean) |
                Q(name__icontains=s_clean)
            )

        style = self.request.query_params.get("style")
        if style:
            s_lower = style.lower().strip()
            s_clean = s_lower.replace("-", " ")
            style_q = (
                Q(styles__slug__iexact=style) |
                Q(styles__name__icontains=s_clean) |
                Q(subcategory_ref__slug__iexact=style) |
                Q(subcategory_ref__name__icontains=s_clean) |
                Q(ring_style__icontains=s_clean) |
                Q(ring_type__icontains=s_clean) |
                Q(ring_profile__icontains=s_clean) |
                Q(earring_type__iexact=style) |
                Q(necklace_style__iexact=style) |
                Q(bracelet_type__iexact=style)
            )
            if s_lower in ["three-stone", "trilogy", "triology"]:
                style_q |= Q(name__icontains="trilogy") | Q(name__icontains="three stone")
            elif s_lower in ["diamond-shoulder", "shoulder"]:
                style_q |= Q(name__icontains="shoulder")
            elif s_lower in ["under-halo"]:
                style_q |= Q(name__icontains="under halo")
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
            sub_clean = subcategory.lower().replace("-", " ").strip()
            sub_lower = subcategory.lower().strip()
            from django.utils.text import slugify
            sub_slug = slugify(subcategory)
            sub_q = (
                Q(subcategory_ref__slug__iexact=subcategory) |
                Q(subcategory_ref__slug__iexact=sub_slug) |
                Q(subcategory_ref__name__iexact=sub_clean) |
                Q(subcategory_ref__name__icontains=sub_clean) |
                Q(subcategory_ref__name__icontains=subcategory) |
                Q(ring_type__icontains=sub_clean) |
                Q(ring_style__icontains=sub_clean) |
                Q(ring_profile__icontains=sub_clean) |
                Q(earring_type__iexact=subcategory) |
                Q(earring_style__icontains=sub_clean) |
                Q(necklace_style__iexact=subcategory) |
                Q(necklace_type__icontains=sub_clean) |
                Q(bracelet_type__iexact=subcategory) |
                Q(bracelet_style__icontains=sub_clean) |
                Q(styles__slug__iexact=subcategory) |
                Q(styles__name__icontains=sub_clean) |
                Q(diamond_cut__iexact=subcategory) |
                Q(name__icontains=sub_clean)
            )
            if sub_lower in ["solitaire-studs", "studs", "stud"]:
                sub_q |= Q(earring_type__icontains="stud") | Q(name__icontains="stud") | Q(subcategory_ref__slug__icontains="stud") | Q(subcategory_ref__name__icontains="stud")
            elif sub_lower in ["hoop-earrings", "hoops", "hoop"]:
                sub_q |= Q(earring_type__icontains="hoop") | Q(name__icontains="hoop") | Q(subcategory_ref__slug__icontains="hoop") | Q(subcategory_ref__name__icontains="hoop")
            elif sub_lower in ["tennis-bracelets", "tennis"]:
                sub_q |= Q(bracelet_type__icontains="tennis") | Q(name__icontains="tennis") | Q(subcategory_ref__slug__icontains="tennis")
            elif sub_lower in ["heart-pendants", "heart"]:
                sub_q |= Q(pendant_shape__icontains="heart") | Q(name__icontains="heart") | Q(subcategory_ref__slug__icontains="heart")
            elif sub_lower in ["cross-pendants", "cross"]:
                sub_q |= Q(pendant_shape__icontains="cross") | Q(name__icontains="cross") | Q(subcategory_ref__slug__icontains="cross")
            elif sub_lower in ["plain", "mens-plain", "womens-plain"]:
                sub_q |= (
                    Q(ring_style__icontains="plain") |
                    Q(ring_profile__icontains="plain") |
                    Q(name__icontains="plain") |
                    Q(subcategory_ref__slug__icontains="plain") |
                    Q(subcategory_ref__name__icontains="plain")
                )
            elif sub_lower in ["diamond", "mens-diamond"]:
                sub_q |= (
                    Q(ring_style__icontains="diamond") |
                    Q(ring_profile__icontains="diamond") |
                    Q(name__icontains="diamond") |
                    Q(subcategory_ref__slug__icontains="diamond") |
                    Q(subcategory_ref__name__icontains="diamond")
                )
            elif sub_lower in ["pattern", "mens-pattern", "patterned"]:
                sub_q |= (
                    Q(ring_style__icontains="pattern") |
                    Q(ring_profile__icontains="pattern") |
                    Q(name__icontains="pattern") |
                    Q(subcategory_ref__slug__icontains="pattern") |
                    Q(subcategory_ref__name__icontains="pattern")
                )
            elif sub_lower in ["traditional-court", "traditional court", "traditional"]:
                sub_q |= (
                    Q(ring_profile__icontains="traditional") |
                    Q(ring_style__icontains="traditional") |
                    Q(name__icontains="traditional") |
                    Q(subcategory_ref__slug__icontains="traditional") |
                    Q(subcategory_ref__name__icontains="traditional")
                )
            elif sub_lower in ["flat-court", "flat court", "flat"]:
                sub_q |= (
                    Q(ring_profile__icontains="flat") |
                    Q(ring_style__icontains="flat") |
                    Q(name__icontains="flat") |
                    Q(subcategory_ref__slug__icontains="flat") |
                    Q(subcategory_ref__name__icontains="flat")
                )
            elif sub_lower in ["soft-court", "soft court", "soft"]:
                sub_q |= (
                    Q(ring_profile__icontains="soft") |
                    Q(ring_style__icontains="soft") |
                    Q(name__icontains="soft") |
                    Q(subcategory_ref__slug__icontains="soft") |
                    Q(subcategory_ref__name__icontains="soft")
                )
            elif sub_lower in ["eternity", "eternity-rings"]:
                sub_q |= (
                    Q(category__icontains="eternity") |
                    Q(name__icontains="eternity") |
                    Q(ring_type__icontains="eternity") |
                    Q(ring_style__icontains="eternity") |
                    Q(subcategory_ref__slug__icontains="eternity") |
                    Q(subcategory_ref__name__icontains="eternity")
                )
            elif sub_lower in ["statement-rings", "statement"]:
                sub_q |= Q(ring_type__icontains="statement") | Q(name__icontains="statement") | Q(subcategory_ref__slug__icontains="statement")
            elif sub_lower in ["gold-colour", "gold"]:
                sub_q |= Q(metal_type__icontains="yellow") | Q(variants__metal_type__icontains="yellow") | Q(name__icontains="yellow gold")
            elif sub_lower in ["silver-colour", "silver", "white-gold"]:
                sub_q |= Q(metal_type__icontains="white") | Q(metal_type__icontains="silver") | Q(metal_type__icontains="platinum") | Q(variants__metal_type__icontains="white") | Q(variants__metal_type__icontains="silver") | Q(variants__metal_type__icontains="platinum")
            elif sub_lower in ["rose-gold"]:
                sub_q |= Q(metal_type__icontains="rose") | Q(variants__metal_type__icontains="rose")
            qs = qs.filter(sub_q)

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
