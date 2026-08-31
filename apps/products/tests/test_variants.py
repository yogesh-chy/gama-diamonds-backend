import pytest
from decimal import Decimal
from django.db.utils import IntegrityError
from django.urls import reverse
from rest_framework import status
from products.models import Product, ProductVariant, Category, DiamondType, Style, Brand, Collection


@pytest.fixture
def sample_category(db):
    return Category.objects.create(name="Engagement Rings", slug="engagement-rings")


@pytest.fixture
def sample_diamond_type(db):
    return DiamondType.objects.create(name="Lab Grown", slug="lab-grown")


@pytest.fixture
def sample_style(db):
    return Style.objects.create(name="Trilogy", slug="trilogy")


@pytest.fixture
def sample_brand(db):
    return Brand.objects.create(name="Gama Signature", slug="gama-signature")


@pytest.fixture
def multi_variant_product(db, sample_category, sample_diamond_type, sample_style, sample_brand):
    p = Product.objects.create(
        name="Novaryn Trilogy Engagement Ring",
        slug="novaryn-trilogy-engagement-ring",
        sku="HLR438",
        description="Novaryn ring description",
        category="rings",
        category_ref=sample_category,
        diamond_type=sample_diamond_type,
        brand=sample_brand,
        base_price=Decimal("3045.00"),
        is_active=True,
    )
    p.styles.add(sample_style)

    v1 = ProductVariant.objects.create(
        product=p,
        sku="HLR438-PT-06",
        metal_type="platinum",
        metal_karat="950Pt",
        size="6",
        price=Decimal("3045.00"),
        stock=2,
        is_default=True,
        is_active=True,
    )
    v2 = ProductVariant.objects.create(
        product=p,
        sku="HLR438-PT-07",
        metal_type="platinum",
        metal_karat="950Pt",
        size="7",
        price=Decimal("3045.00"),
        stock=3,
        is_active=True,
    )
    v3 = ProductVariant.objects.create(
        product=p,
        sku="HLR438-YG18-06",
        metal_type="yellow-gold",
        metal_karat="18K",
        size="6",
        price=Decimal("2850.00"),
        stock=4,
        is_active=True,
    )
    return p


@pytest.mark.django_db
class TestProductVariantArchitecture:
    def test_price_range_and_availability(self, multi_variant_product):
        pr = multi_variant_product.price_range
        assert pr["min"] == 2850.0
        assert pr["max"] == 3045.0
        assert pr["display"] == "From £2,850.00"
        assert multi_variant_product.is_available is True

    def test_unique_sku_constraint(self, multi_variant_product):
        with pytest.raises(IntegrityError):
            ProductVariant.objects.create(
                product=multi_variant_product,
                sku="HLR438-PT-06",
                metal_type="yellow-gold",
                metal_karat="18K",
                size="8",
                price=Decimal("2900.00"),
                stock=1,
            )

    def test_unique_combination_constraint(self, multi_variant_product):
        with pytest.raises(IntegrityError):
            ProductVariant.objects.create(
                product=multi_variant_product,
                sku="HLR438-DUP-COMB",
                metal_type="platinum",
                metal_karat="950Pt",
                size="6",
                price=Decimal("3000.00"),
                stock=1,
            )

    def test_product_listing_returns_aggregated_cards(self, client, multi_variant_product):
        response = client.get(reverse("products:product-list"))
        assert response.status_code == status.HTTP_200_OK
        data = response.data["data"]
        assert len(data) >= 1
        item = [d for d in data if d["id"] == multi_variant_product.id][0]
        assert item["name"] == "Novaryn Trilogy Engagement Ring"
        assert item["price"]["min"] == 2850.0
        assert item["price"]["max"] == 3045.0

    def test_product_detail_exposes_options_and_variants(self, client, multi_variant_product):
        url = reverse("products:product-detail", args=[multi_variant_product.slug])
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        data = response.data
        assert len(data["variants"]) == 3
        assert "platinum" in data["options"]["metal"]
        assert "yellow-gold" in data["options"]["metal"]
        assert "6" in data["options"]["size"]

    def test_variant_resolution_endpoint(self, client, multi_variant_product):
        url = reverse("products:product-resolve-variant", args=[multi_variant_product.slug])
        response = client.get(url, {"metal_type": "yellow-gold", "metal_karat": "18K", "size": "6"})
        assert response.status_code == status.HTTP_200_OK
        assert response.data["sku"] == "HLR438-YG18-06"
        assert response.data["price"] == 2850.0
        assert response.data["stock"] == 4

    def test_faceted_filters_endpoint(self, client, multi_variant_product):
        url = reverse("products:product-filters")
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert "platinum" in response.data["metals"]
        assert "yellow-gold" in response.data["metals"]
        assert response.data["price_range"]["min"] <= 2850.0

    def test_admin_nested_product_and_variant_creation(self, sample_category):
        from rest_framework.test import APIClient
        from accounts.models import User
        admin_user = User.objects.create_superuser(email="admin_spec@example.com", password="PassWord123!")
        client = APIClient()
        client.force_authenticate(user=admin_user)
        payload = {
            "name": "Eternity Diamond Ring",
            "slug": "eternity-diamond-ring",
            "style_code": "HLR999",
            "description": "Full eternity diamond ring",
            "category": "rings",
            "base_price": 4500,
            "is_active": True,
            "diamond_spec": {
                "carat_weight": 2.0,
                "cut_grade": "excellent",
                "colour_grade": "F",
                "clarity_grade": "VS1",
                "certification_lab": "GIA"
            },
            "variants": [
                {
                    "sku": "HLR999-WG-06",
                    "metal_type": "white-gold",
                    "metal_karat": "18K",
                    "size": "6",
                    "price": 4500,
                    "stock": 5,
                    "is_default": True
                },
                {
                    "sku": "HLR999-WG-07",
                    "metal_type": "white-gold",
                    "metal_karat": "18K",
                    "size": "7",
                    "price": 4500,
                    "stock": 3
                }
            ]
        }
        response = client.post(reverse("products:product-list"), payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        new_prod_id = response.data["id"]
        product_obj = Product.objects.get(pk=new_prod_id)
        assert product_obj.variants.count() == 2
        assert product_obj.diamond_spec.carat_weight == Decimal("2.00")
