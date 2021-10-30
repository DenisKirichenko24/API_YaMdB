from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as CustomUserAdmin

from .models import Category, Comment, Genre, Review, Title, TitleGenre, User


class UserAdmin(CustomUserAdmin):
    fieldsets = tuple(
        (fieldset[0], {
            **{key: value for (key, value) in fieldset[1].items()
                if key != 'fields'},
            'fields': fieldset[1]['fields'] + ('bio', 'role')
        })
        if fieldset[0] == 'Personal info'
        else fieldset
        for fieldset in CustomUserAdmin.fieldsets
    )
    list_display = ['email', 'username', 'role', 'is_active']
    empty_value_display = '-пусто-'


admin.site.register(User, UserAdmin)


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'author', 'text', 'pub_date',)
    search_fields = ('id', 'title', 'author',)
    list_filter = ('pub_date', 'author')


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('author', 'pub_date', 'text',)
    search_fields = ('author',)
    list_filter = ('author',)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug',)
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug',)
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Title)
class TitleAdmin(admin.ModelAdmin):
    list_display = ('name', 'year', 'description', 'get_genres',
                    'category',)
    search_fields = ('name', 'description',)
    list_filter = ('year', 'genre', 'category',)


@admin.register(TitleGenre)
class TitleGenreAdmin(admin.ModelAdmin):
    list_display = ('genre', 'title',)
    search_fields = ('title',)
    list_filter = ('genre',)
