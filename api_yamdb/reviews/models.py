import uuid
import datetime as dt

from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class User(AbstractUser):
    USER = 'user'
    MODERATOR = 'moderator'
    ADMIN = 'admin'
    CHOICES = (
        (USER, 'user'),
        (MODERATOR, 'moderator'),
        (ADMIN, 'admin')
    )
    email = models.EmailField('Email', unique=True, max_length=254)
    username = models.CharField(
        'Никнеим', max_length=150, unique=True,
        help_text=('Обязательное поле, только цифры, буквы или @/./+/-/_.'),
        validators=[UnicodeUsernameValidator()],
        error_messages={
            'unique': 'Пользователь с таким никнеимом уже существует.',
        },
        blank=True,
        null=True,
    )
    bio = models.TextField(
        'О себе',
        blank=True,
        null=True,
    )
    role = models.CharField(
        'Статус',
        max_length=16,
        choices=CHOICES,
        default=USER,
    )

    confirmation_code = models.CharField(
        'Код подтверждения',
        max_length=100,
        null=True,
        default=uuid.uuid4
    )

    @property
    def is_moderator(self):
        return self.role == self.MODERATOR or self.is_admin

    @property
    def is_admin(self):
        return self.role == self.ADMIN or self.is_staff

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        ordering = ['id']
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.email


class Category(models.Model):
    name = models.CharField(max_length=256, verbose_name='Название категории')
    slug = models.SlugField(max_length=50, unique=True,
                            verbose_name='Уникальный идентификатор категории')

    class Meta:
        ordering = ['name']
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'

    def __str__(self):
        return self.name[:20]


class Genre(models.Model):
    name = models.CharField(max_length=256, verbose_name='Жанр')
    slug = models.SlugField(max_length=50, unique=True,
                            verbose_name='Уникальный идентификатор жанра')

    class Meta:
        ordering = ['name']
        verbose_name = 'Жанр'
        verbose_name_plural = 'Жанры'

    def __str__(self):
        return self.name[:20]


class Title(models.Model):
    name = models.CharField(max_length=256, verbose_name='Название')
    year = models.IntegerField(null=True, blank=True, validators=[
        MaxValueValidator(dt.date.today().year)
    ], verbose_name='год создания произведения')
    description = models.TextField(verbose_name='Описание произведения')
    genre = models.ManyToManyField(Genre, blank=True,
                                   related_name='genre',
                                   verbose_name='Жанр', through='TitleGenre')
    category = models.ForeignKey(Category, blank=True, null=True,
                                 on_delete=models.SET_NULL,
                                 related_name='category',
                                 verbose_name='Категория')

    class Meta:
        ordering = ['name']
        verbose_name = 'Произведение'
        verbose_name_plural = 'Произведения'

    def get_genres(self):
        return ",".join([str(gen) for gen in self.genre.all()])

    def __str__(self):
        return self.name[:20]


class TitleGenre(models.Model):
    genre = models.ForeignKey(Genre, on_delete=models.CASCADE)
    title = models.ForeignKey(Title, on_delete=models.CASCADE)

    class Meta:
        ordering = ['genre']
        verbose_name = 'Связь'
        verbose_name_plural = 'Связи'

    def __str__(self):
        return f'{self.genre} {self.title}'


class Review(models.Model):
    title = models.ForeignKey(Title, on_delete=models.CASCADE,
                              related_name='reviews')
    text = models.TextField(verbose_name='Текст отзыва')
    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               verbose_name='Автор отзыва')
    pub_date = models.DateTimeField(auto_now_add=True, db_index=True,
                                    verbose_name='Дата отзыва')
    score = models.IntegerField(
        null=True,
        blank=True,
        validators=[
            MinValueValidator(1),
            MaxValueValidator(10)
        ], verbose_name='Оценка произведения')

    class Meta:
        ordering = ('-pub_date', 'score')
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'
        constraints = [
            models.UniqueConstraint(
                fields=['title', 'author'],
                name='unique_title_author',
            )
        ]

    def __str__(self):
        return self.text


class Comment(models.Model):
    review = models.ForeignKey(Review, on_delete=models.CASCADE,
                               related_name='comments')
    text = models.TextField(verbose_name='Текст комментария')
    pub_date = models.DateTimeField(auto_now_add=True, db_index=True,
                                    verbose_name='Дата комментария')
    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               verbose_name='Автор комментария')

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'

    def __str__(self):
        return self.text
