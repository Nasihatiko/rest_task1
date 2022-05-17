from datetime import timedelta

from django.db.models import Q
from django.shortcuts import render
from django.utils import timezone
from rest_framework import generics, viewsets, status
from rest_framework.decorators import api_view, action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import *
from .serializers import CategorySerializer, PostSerializer, PostImageSerializer
from .permissions import IsPostAuthor

#
# @api_view(['GET'])
# def categories(request):
#     categories = Category.objects.all()
#     serializer = CategorySerializer(categories, many=True)
#     return Response(serializer.data)
#
#
# class PostListView(APIView):
#     def get(self, request):
#         posts = Post.objects.all()
#         serializer = PostSerializer(posts, many=True)
#         return Response(serializer.data)
#
#     def post(self, request):
#         post = request.data
#         serializer = PostSerializer(data=post)
#         if serializer.is_valid():
#             post_saved = serializer.save()
#         return Response(serializer.data)


# class CategoryListView(generics.ListAPIView):
#     queryset = Category.objects.all()
#     serializer_class = CategorySerializer
#
#
# class PostView(generics.ListCreateAPIView):
#     queryset = Post.objects.all()
#     serializer_class = PostSerializer
#
#
# class PostDetailView(generics.RetrieveAPIView):
#     queryset = Post.objects.all()
#     serializer_class = PostSerializer
#
#
# class PostUpdateView(generics.UpdateAPIView):
#     queryset = Post.objects.all()
#     serializer_class = PostSerializer
#
#
# class PostDeleteView(generics.DestroyAPIView):
#     queryset = Post.objects.all()
#     serializer_class = PostSerializer


class MyPaginationClass(PageNumberPagination):
    page_size = 3

    def get_paginated_response(self, data):
        for i in range(self.page_size):
            text = data[i]['text']
            data[i]['text'] = text[:10] + '...'
        return super().get_paginated_response(data)


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [AllowAny,]


class PostsViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated, ]
    pagination_class = MyPaginationClass
   
    def get_serializer_context(self):
        return {'request': self.request}

    def get_permissions(self):
        """pereopredelim dannyi method"""
        if self.action in ['update', 'partial_update', 'destroy']:
            permissions = [IsPostAuthor, ]
        else:
            permissions = [IsAuthenticated, ]
        return [permission() for permission in permissions]

    def get_queryset(self):
        queryset = super().get_queryset()
        weeks_count = int(self.request.query_params.get('week', 0))
        if weeks_count > 0:
            start_date = timezone.now() - timedelta(weeks=weeks_count)
            queryset = queryset.filter(created_at__gte=start_date)
        return queryset

    @action(detail=False, methods=['get'])
    def own(self, request, pk=None):
        queryset = self.get_queryset()
        queryset = queryset.filter(author=request.user)
        serializer = PostSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])  #action dostupny tol'ko v ViewSet / router builds path/search/?q=paris
    def search(self, request, pk=None):
        q = request.query_params.get('q')    #request.query_params = request.GET
        queryset = self.get_queryset()
        queryset = queryset.filter(Q(title__icontains=q) |
                                   Q(text__icontains=q))
        serializer = PostSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class PostImageViewSet(viewsets.ModelViewSet):
    queryset = PostImage.objects.all()
    serializer_class = PostImageSerializer

    def get_serializer_context(self):
        return {'request': self.request}
