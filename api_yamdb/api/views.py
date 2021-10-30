from django.conf import settings
from django.core.mail import send_mail
from django.db.models import Avg
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, status, views, viewsets
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import AccessToken
from reviews.models import Category, Comment, Genre, Review, Title, User

from .filters import TitlesFilter
from .permissions import (IsAdmin, IsAdminOrReadOnly,
                          IsOwnerAdminModeratorOrReadOnly)
from .serializers import (CategorySerializer, CommentSerializer,
                          ConfirmationCodeSerializer, EmailSerializer,
                          GenreSerializer, ReviewSerializer, TitleSerializer,
                          TitleWriteSerializer, UserSerializer)


class ListCreateDestroyViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet
):
    pass


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdmin]
    http_method_names = ['get', 'post', 'patch', 'delete']
    search_fields = ['username']
    lookup_field = 'username'

    @action(detail=False, methods=['get', 'patch'],
            permission_classes=[IsAuthenticated])
    def me(self, request):
        if request.method == 'GET':
            serializer = self.get_serializer(request.user)
            return Response(data=serializer.data)
        if request.method == 'PATCH':
            serializer = self.get_serializer(
                request.user,
                data=request.data,
                partial=True
            )
            serializer.is_valid(raise_exception=True)
            serializer.save(role=request.user.role)
            return Response(data=serializer.data)


class EmailRegistrationView(views.APIView):
    permission_classes = [AllowAny]

    @staticmethod
    def mail_send(email, user):
        send_mail(
            subject='YaMDB Confirmation Code',
            message=f'Hello! \n\nYour confirmation: '
                    f'{user.confirmation_code}',
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[email],
            fail_silently=False
        )

    def post(self, request):
        serializer = EmailSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            email = serializer.validated_data['email']
            username = serializer.validated_data['username']
            serializer.save(username=username)
            user = get_object_or_404(User, username=username)
            self.mail_send(email, user)
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AccessTokenView(views.APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ConfirmationCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        confirmation_code = serializer.validated_data['confirmation_code']
        username = serializer.validated_data['username']
        try:
            user = get_object_or_404(User, username=username)
        except User.DoesNotExist:
            return Response({
                'email':
                    'Not found'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if user.confirmation_code != confirmation_code:
            return Response({
                'confirmation_code':
                    f'Invalid confirmation code for email {user.email}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(self.get_token(user), status=status.HTTP_200_OK)

    @staticmethod
    def get_token(user):
        return {
            'token': str(AccessToken.for_user(user))
        }


class ReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewSerializer
    permission_classes = [IsOwnerAdminModeratorOrReadOnly]
    queryset = Review.objects.all()

    def get_queryset(self):
        return get_object_or_404(
            Title,
            id=self.kwargs.get('title_id')
        ).reviews.all()

    def perform_create(self, serializer):
        title = get_object_or_404(Title, id=self.kwargs.get("title_id"))
        serializer.save(author=self.request.user, title=title)


class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = CommentSerializer
    permission_classes = (IsOwnerAdminModeratorOrReadOnly,)

    def get_queryset(self):
        review = get_object_or_404(Review, pk=self.kwargs.get('review_id'))
        return Comment.objects.filter(review=review)

    def create(self, request, *args, **kwargs):
        review = get_object_or_404(Review, id=self.kwargs.get('review_id'))
        serializer = CommentSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save(author=self.request.user, review_id=review.id)
            return Response(serializer.data, status=status.HTTP_201_CREATED)


class CategoryViewSet(ListCreateDestroyViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    lookup_field = 'slug'
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = (SearchFilter,)
    search_fields = ('name',)


class GenreViewSet(ListCreateDestroyViewSet):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    lookup_field = 'slug'
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = (SearchFilter,)
    search_fields = ('name',)


class TitleViewSet(viewsets.ModelViewSet):
    queryset = Title.objects.all().annotate(rating=Avg('reviews__score'))
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = (DjangoFilterBackend,)
    filterset_class = TitlesFilter
    filterset_fields = ('category', 'genre', 'name', 'year')

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return TitleSerializer
        return TitleWriteSerializer
