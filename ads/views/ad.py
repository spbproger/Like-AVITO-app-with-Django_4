from django.http import JsonResponse

from django.utils.decorators import method_decorator

from django.views.generic import UpdateView, CreateView
from rest_framework.decorators import api_view, permission_classes

from rest_framework.generics import ListAPIView, RetrieveAPIView, UpdateAPIView, DestroyAPIView
from rest_framework.permissions import IsAuthenticated

from ads.models import Category
import json
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404

from ads.permissions import AdUpdatePermission
from ads.serializer import AdListSerializer, AdDetailSerializer, AdUpdateSerializer, AdDestroySerializer
from ads.models import Ad
from users.models import User


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def status(request):
    return JsonResponse({"status": "ok"}, status=200)


class AdListView(ListAPIView):
    queryset = Ad.objects.all().order_by('-price')
    serializer_class = AdListSerializer

    def get(self, request, *args, **kwargs):
        categories = request.GET.getlist('cat', None)
        if categories:
            self.queryset = self.queryset.filter(
                category__ad__in=categories
            )
        text = request.GET.get('text', None)
        if text:
            self.queryset = self.queryset.filter(
                name__icontains=text
            )
        location = request.GET.get('location', None)
        if location:
            self.queryset = self.queryset.filter(
                author__locations__name__icontains=location
            )
        price_from = request.GET.get('price_from')
        price_to = request.GET.get('price_to')
        if price_from:
            self.queryset = self.queryset.filter(price__gte=price_from)
        if price_to:
            self.queryset = self.queryset.filter(price__lte=price_to)

        return super().get(request, *args, **kwargs)


class AdDetailView(RetrieveAPIView):
    queryset = Ad.objects.all()
    serializer_class = AdDetailSerializer
    permission_classes = [IsAuthenticated]


@method_decorator(csrf_exempt, name='dispatch')
class AdCreateView(CreateView):
    model = Ad
    fields = ['name', 'author', 'price', 'description', 'is_published', 'category']

    def post(self, request, *args, **kwargs):
        ad_data = json.loads(request.body)

        new_ad = Ad.objects.create(
            name=ad_data['name'],
            author=get_object_or_404(User, pk=ad_data['author']),
            price=ad_data['price'],
            description=ad_data['description'],
            is_published=ad_data['is_published'],
            category=get_object_or_404(Category, pk=ad_data['category']))

        return JsonResponse({
            'id': new_ad.id,
            'name': new_ad.name,
            'author': new_ad.author.username,
            'price': new_ad.price,
            'description': new_ad.description,
            'is_published': new_ad.is_published,
            'category': new_ad.category.name,
            'image': new_ad.image.url if new_ad.image else None
        }, json_dumps_params={"ensure_ascii": False})


class AdUpdateView(UpdateAPIView):
    queryset = Ad.objects.all()
    serializer_class = AdUpdateSerializer
    permission_classes = [IsAuthenticated, AdUpdatePermission]


@method_decorator(csrf_exempt, name='dispatch')
class AdImageView(UpdateView):
    model = Ad
    fields = ['name', 'image']

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.image = request.FILES.get("image", None)
        self.object.save()

        return JsonResponse({
            'id': self.object.id,
            'name': self.object.name,
            'price': self.object.price,
            'description': self.object.description,
            'is_published': self.object.is_published,
            'category_id': self.object.category_id,
            'image': self.object.image.url if self.object.image else None,
        }, json_dumps_params={"ensure_ascii": False}, status=200)


class AdDeleteView(DestroyAPIView):
    queryset = Ad.objects.all()
    serializer_class = AdDestroySerializer
    permission_classes = [IsAuthenticated, AdUpdatePermission]