from django.db import models

from django.conf import settings
from django.db import models
from django.urls import reverse


class Genre(models.Model):
    name = models.CharField('Название жанра', max_length=100)
    slug = models.SlugField('URL-слаг', max_length=120, unique=True)

    class Meta:
        verbose_name = 'Жанр'
        verbose_name_plural = 'Жанры'
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return f"{reverse('catalog')}?genre={self.slug}"


class Person(models.Model):
    full_name = models.CharField('Имя и фамилия', max_length=200)
    slug = models.SlugField('URL-слаг', max_length=220, unique=True)
    birth_date = models.DateField('Дата рождения', blank=True, null=True)
    country = models.CharField('Страна', max_length=100, blank=True)
    bio = models.TextField('Биография', blank=True)
    photo = models.ImageField('Фото', upload_to='persons/', blank=True, null=True)

    class Meta:
        verbose_name = 'Персона (актёр / режиссёр)'
        verbose_name_plural = 'Персоны'
        ordering = ['full_name']

    def __str__(self):
        return self.full_name

    def get_absolute_url(self):
        return reverse('person_detail', kwargs={'slug': self.slug})


class Movie(models.Model):
    TYPE_CHOICES = [
        ('movie', 'Фильм'),
        ('series', 'Сериал'),
        ('anime', 'Аниме'),
    ]

    title = models.CharField('Название', max_length=255)
    original_title = models.CharField('Оригинальное название', max_length=255, blank=True)
    slug = models.SlugField('URL-слаг', max_length=255, unique=True)
    content_type = models.CharField('Тип', max_length=20, choices=TYPE_CHOICES, default='movie')
    tagline = models.CharField('Слоган', max_length=255, blank=True)
    description = models.TextField('Описание сюжета', blank=True)
    year = models.PositiveIntegerField('Год выхода', default=2025)
    country = models.CharField('Страна', max_length=120, default='США')
    duration = models.PositiveIntegerField('Длительность (мин)', default=120)
    age_rating = models.CharField('Возрастной рейтинг', max_length=10, default='16+')
    poster = models.ImageField('Постер', upload_to='posters/', blank=True, null=True)
    trailer_url = models.URLField('Ссылка на трейлер', blank=True)

    genres = models.ManyToManyField(Genre, related_name='movies', verbose_name='Жанры')
    directors = models.ManyToManyField(
        Person, related_name='directed_movies', blank=True, verbose_name='Режиссёры'
    )
    actors = models.ManyToManyField(
        Person, related_name='acted_movies', blank=True, verbose_name='В главных ролях'
    )

    is_published = models.BooleanField('Опубликован', default=True)
    created_at = models.DateTimeField('Дата добавления', auto_now_add=True)

    class Meta:
        verbose_name = 'Фильм / Сериал'
        verbose_name_plural = 'Фильмы и сериалы'
        ordering = ['-year', '-created_at']

    def __str__(self):
        return f'{self.title} ({self.year})'

    def get_absolute_url(self):
        return reverse('movie_detail', kwargs={'slug': self.slug})

    @property
    def average_rating(self):
        ratings = list(self.ratings.all())
        if not ratings:
            return None
        return round(sum(r.score for r in ratings) / len(ratings), 1)

    @property
    def ratings_count(self):
        return self.ratings.count()


class Rating(models.Model):
    movie = models.ForeignKey(
        Movie, on_delete=models.CASCADE, related_name='ratings', verbose_name='Фильм'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='Пользователь'
    )
    score = models.PositiveSmallIntegerField('Оценка (1-10)', default=8)
    created_at = models.DateTimeField('Дата', auto_now_add=True)

    class Meta:
        verbose_name = 'Оценка'
        verbose_name_plural = 'Оценки'
        unique_together = ('movie', 'user')

    def __str__(self):
        return f'{self.user} -> {self.movie}: {self.score}/10'


class Review(models.Model):
    TONE_CHOICES = [
        ('positive', 'Положительная'),
        ('neutral', 'Нейтральная'),
        ('negative', 'Отрицательная'),
    ]

    movie = models.ForeignKey(
        Movie, on_delete=models.CASCADE, related_name='reviews', verbose_name='Фильм'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='Автор'
    )
    tone = models.CharField('Тип рецензии', max_length=20, choices=TONE_CHOICES, default='positive')
    title = models.CharField('Заголовок рецензии', max_length=200)
    text = models.TextField('Текст рецензии')
    created_at = models.DateTimeField('Дата публикации', auto_now_add=True)

    class Meta:
        verbose_name = 'Рецензия'
        verbose_name_plural = 'Рецензии'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.title} ({self.movie})'


class Watchlist(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='watchlist',
        verbose_name='Пользователь',
    )
    movie = models.ForeignKey(
        Movie, on_delete=models.CASCADE, related_name='in_watchlists', verbose_name='Фильм'
    )
    created_at = models.DateTimeField('Добавлено', auto_now_add=True)

    class Meta:
        verbose_name = 'Буду смотреть'
        verbose_name_plural = 'Списки «Буду смотреть»'
        unique_together = ('user', 'movie')
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user} -> {self.movie}'
