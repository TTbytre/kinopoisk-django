from django.contrib import admin

from django.contrib import admin
from .models import Genre, Movie, Person, Rating, Review, Watchlist


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'country', 'birth_date')
    prepopulated_fields = {'slug': ('full_name',)}
    search_fields = ('full_name', 'country')


@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = ('title', 'content_type', 'year', 'country', 'age_rating', 'is_published')
    list_filter = ('content_type', 'year', 'genres', 'is_published')
    search_fields = ('title', 'original_title', 'description')
    prepopulated_fields = {'slug': ('title',)}
    filter_horizontal = ('genres', 'directors', 'actors')


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('title', 'movie', 'user', 'tone', 'created_at')
    list_filter = ('tone', 'created_at')
    search_fields = ('title', 'text', 'movie__title')


admin.site.register(Rating)
admin.site.register(Watchlist)
