import pytest
from decimal import Decimal
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from accounts.models import User
from products.models import Product, ProductVariant, Category, DiamondSpecification, Style, DiamondType


@pytest.fixture
def admin_client(db):
    user = User.objects.create_superuser(email="admin_test@gamadiamonds.com", password="Password123!")
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def categories(db):
    c1 = Category.objects.create(name="Engagement Rings", slug="engagement-rings")
    c2 = Category.objects.create(name="Earrings", slug="earrings")
    c3 = Category.objects.create(name="Necklaces", slug="necklaces")
    c4 = Category.objects.create(name="Bracelets", slug="bracelets")
    return {"rings": c1, "earrings": c2, "necklaces": c3, "bracelets": c4}


@pytest.mark.django_db
class TestUniversalProductSystem:
    def test_create_engagement_ring_with_9_variants(self, admin_client, categories):
        payload = {
            "name": "Classic Solitaire Engagement Ring",
            "slug": "classic-solitaire-engagement-ring",
            "sku": "CSR-SOL-100",
            "description": "Timeless solitaire engagement ring",
            "category": "engagement-rings",
            "base_price": 1500,
            "metal_type": "yellow-gold",
            "metal_karat": "18K",
            "diamond_cut": "round",
            "ring_style": "Solitaire",
            "band_fit": "comfort",
            "diamond_spec": {
                "diamond_origin": "lab_grown",
                "diamond_shape": "round",
                "carat_weight": 1.00,
                "center_carat_weight": 1.00,
                "cut_grade": "excellent",
                "colour_grade": "F",
                "clarity_grade": "VS1",
                "certification_lab": "GIA",
                "certificate_number": "GIA-12345678"
            },
            "variants": [
                {"sku": "CSR-YG18-06", "metal_type": "yellow-gold", "metal_karat": "18K", "size": "6", "price": 1500, "stock": 5, "is_default": True},
                {"sku": "CSR-YG18-07", "metal_type": "yellow-gold", "metal_karat": "18K", "size": "7", "price": 1500, "stock": 8},
                {"sku": "CSR-YG18-08", "metal_type": "yellow-gold", "metal_karat": "18K", "size": "8", "price": 1500, "stock": 3},
                {"sku": "CSR-WG18-06", "metal_type": "white-gold", "metal_karat": "18K", "size": "6", "price": 1550, "stock": 4},
                {"sku": "CSR-WG18-07", "metal_type": "white-gold", "metal_karat": "18K", "size": "7", "price": 1550, "stock": 6},
                {"sku": "CSR-WG18-08", "metal_type": "white-gold", "metal_karat": "18K", "size": "8", "price": 1550, "stock": 2},
                {"sku": "CSR-PT-06", "metal_type": "platinum", "metal_karat": "950Pt", "size": "6", "price": 1900, "stock": 1},
                {"sku": "CSR-PT-07", "metal_type": "platinum", "metal_karat": "950Pt", "size": "7", "price": 1900, "stock": 2},
                {"sku": "CSR-PT-08", "metal_type": "platinum", "metal_karat": "950Pt", "size": "8", "price": 1900, "stock": 3},
            ]
        }

        url = reverse("products:product-list")
        res = admin_client.post(url, payload, format="json")
        assert res.status_code == status.HTTP_201_CREATED

        prod_id = res.data["id"]
        prod = Product.objects.get(pk=prod_id)

        assert prod.name == "Classic Solitaire Engagement Ring"
        assert prod.variants.count() == 9
        assert prod.diamond_spec.carat_weight == Decimal("1.00")
        assert prod.diamond_spec.certification_lab == "GIA"

        # Check price range calculation
        pr = prod.price_range
        assert pr["min"] == 1500.0
        assert pr["max"] == 1900.0
        assert pr["display"] == "From £1,500.00"

    def test_create_earring_product(self, admin_client, categories):
        payload = {
            "name": "Diamond Solitaire Stud Earrings",
            "slug": "diamond-solitaire-stud-earrings",
            "sku": "EAR-STUD-050",
            "category": "earrings",
            "earring_type": "studs",
            "closure_type": "Push Back",
            "base_price": 850,
            "variants": [
                {"sku": "EAR-YG18", "metal_type": "yellow-gold", "metal_karat": "18K", "size": "", "price": 850, "stock": 10, "is_default": True},
                {"sku": "EAR-WG18", "metal_type": "white-gold", "metal_karat": "18K", "size": "", "price": 875, "stock": 8},
            ]
        }

        url = reverse("products:product-list")
        res = admin_client.post(url, payload, format="json")
        assert res.status_code == status.HTTP_201_CREATED

        prod = Product.objects.get(pk=res.data["id"])
        assert prod.earring_type == "studs"
        assert prod.variants.count() == 2

    def test_create_necklace_with_chain_length_variants(self, admin_client, categories):
        payload = {
            "name": "Heart Pendant Diamond Necklace",
            "slug": "heart-pendant-diamond-necklace",
            "sku": "NCK-HEART-100",
            "category": "necklaces",
            "necklace_style": "pendant",
            "chain_type": "Box Chain",
            "base_price": 1200,
            "variants": [
                {"sku": "NCK-YG18-16", "metal_type": "yellow-gold", "metal_karat": "18K", "length": '16"', "price": 1200, "stock": 5},
                {"sku": "NCK-YG18-18", "metal_type": "yellow-gold", "metal_karat": "18K", "length": '18"', "price": 1200, "stock": 5},
                {"sku": "NCK-YG18-20", "metal_type": "yellow-gold", "metal_karat": "18K", "length": '20"', "price": 1250, "stock": 5},
                {"sku": "NCK-WG18-16", "metal_type": "white-gold", "metal_karat": "18K", "length": '16"', "price": 1250, "stock": 5},
                {"sku": "NCK-WG18-18", "metal_type": "white-gold", "metal_karat": "18K", "length": '18"', "price": 1250, "stock": 5},
                {"sku": "NCK-WG18-20", "metal_type": "white-gold", "metal_karat": "18K", "length": '20"', "price": 1300, "stock": 5},
            ]
        }

        url = reverse("products:product-list")
        res = admin_client.post(url, payload, format="json")
        assert res.status_code == status.HTTP_201_CREATED

        prod = Product.objects.get(pk=res.data["id"])
        assert prod.variants.count() == 6

    def test_variant_resolution_with_length(self, client, admin_client, categories):
        # Create necklace
        payload = {
            "name": "Tennis Chain Necklace",
            "slug": "tennis-chain-necklace",
            "sku": "NCK-TENNIS",
            "category": "necklaces",
            "base_price": 2500,
            "variants": [
                {"sku": "NCK-TENNIS-YG18-16", "metal_type": "yellow-gold", "metal_karat": "18K", "length": '16"', "price": 2500, "stock": 3},
                {"sku": "NCK-TENNIS-YG18-18", "metal_type": "yellow-gold", "metal_karat": "18K", "length": '18"', "price": 2700, "stock": 4},
            ]
        }
        res_create = admin_client.post(reverse("products:product-list"), payload, format="json")
        slug = res_create.data["slug"]

        url = reverse("products:product-resolve-variant", args=[slug])
        res = client.get(url, {"metal_type": "yellow-gold", "metal_karat": "18K", "length": '18"'})
        assert res.status_code == status.HTTP_200_OK
        assert res.data["sku"] == "NCK-TENNIS-YG18-18"
        assert res.data["price"] == 2700.0

    def test_category_filtering(self, client, admin_client, categories):
        # Create ring & necklace
        admin_client.post(reverse("products:product-list"), {
            "name": "Eternity Band Ring", "category": "engagement-rings", "base_price": 1000,
            "variants": [{"sku": "RNG-ET-1", "price": 1000, "stock": 5}]
        }, format="json")

        admin_client.post(reverse("products:product-list"), {
            "name": "Diamond Pendant Necklace", "category": "necklaces", "base_price": 1500,
            "variants": [{"sku": "NCK-PD-1", "price": 1500, "stock": 5}]
        }, format="json")

        # Query rings
        res_rings = client.get(reverse("products:product-list"), {"category": "engagement-rings"})
        assert res_rings.status_code == status.HTTP_200_OK
        data_rings = res_rings.data["data"]
        assert any(p["name"] == "Eternity Band Ring" for p in data_rings)
        assert not any(p["name"] == "Diamond Pendant Necklace" for p in data_rings)

        # Query necklaces
        res_nck = client.get(reverse("products:product-list"), {"category": "necklaces"})
        assert res_nck.status_code == status.HTTP_200_OK
        data_nck = res_nck.data["data"]
        assert any(p["name"] == "Diamond Pendant Necklace" for p in data_nck)
        assert not any(p["name"] == "Eternity Band Ring" for p in data_nck)
