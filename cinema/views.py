from django.shortcuts import render

from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db.models import Avg, Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from .models import Genre, Movie, Person, Rating, Review, Watchlist
from django.contrib import messages
from django.db import IntegrityError
from .models import Movie


def catalog_view(request):
    movies = (
        Movie.objects.filter(is_published=True)
        .prefetch_related('genres')
        .annotate(avg_score=Avg('ratings__score'), votes=Count('ratings'))
    )
    genres = Genre.objects.all()

    query = request.GET.get('q', '').strip()
    if query:
        movies = movies.filter(
            Q(title__icontains=query)
            | Q(original_title__icontains=query)
            | Q(description__icontains=query)
        )

    content_type = request.GET.get('type', '').strip()
    if content_type in {'movie', 'series', 'anime'}:
        movies = movies.filter(content_type=content_type)

    genre_slug = request.GET.get('genre', '').strip()
    if genre_slug:
        movies = movies.filter(genres__slug=genre_slug)

    year = request.GET.get('year', '').strip()
    if year.isdigit():
        movies = movies.filter(year=int(year))

    sort = request.GET.get('sort', 'rating')
    if sort == 'new':
        movies = movies.order_by('-year', '-created_at')
    elif sort == 'title':
        movies = movies.order_by('title')
    else:
        movies = movies.order_by('-avg_score', '-votes', '-year')

    years = (
        Movie.objects.filter(is_published=True)
        .values_list('year', flat=True)
        .distinct()
        .order_by('-year')
    )

    paginator = Paginator(movies, 12)
    page_obj = paginator.get_page(request.GET.get('page'))

    watchlist_ids = set()
    if request.user.is_authenticated:
        watchlist_ids = set(
            Watchlist.objects.filter(user=request.user).values_list('movie_id', flat=True)
        )

    return render(
        request,
        'cinema/catalog.html',
        {
            'page_obj': page_obj,
            'genres': genres,
            'years': years,
            'query': query,
            'selected_type': content_type,
            'selected_genre': genre_slug,
            'selected_year': year,
            'sort': sort,
            'watchlist_ids': watchlist_ids,
        },
    )


def movie_detail_view(request, slug):
    movie = get_object_or_404(
        Movie.objects.prefetch_related('genres', 'directors', 'actors', 'reviews__user'),
        slug=slug,
        is_published=True,
    )

    user_rating = None
    in_watchlist = False
    if request.user.is_authenticated:
        rating_obj = Rating.objects.filter(movie=movie, user=request.user).first()
        if rating_obj:
            user_rating = rating_obj.score
        in_watchlist = Watchlist.objects.filter(movie=movie, user=request.user).exists()

    if request.method == 'POST':
        if not request.user.is_authenticated:
            messages.error(request, 'Войдите в аккаунт, чтобы оценить фильм или написать рецензию.')
            return redirect('login')

        action = request.POST.get('action')
        if action == 'rate':
            score_raw = request.POST.get('score', '8')
            try:
                score = max(1, min(10, int(score_raw)))
            except ValueError:
                score = 8
            Rating.objects.update_or_create(
                movie=movie, user=request.user, defaults={'score': score}
            )
            messages.success(request, f'Ваша оценка {score}/10 сохранена.')
            return redirect('movie_detail', slug=movie.slug)

        if action == 'review':
            tone = request.POST.get('tone', 'positive')
            if tone not in {'positive', 'neutral', 'negative'}:
                tone = 'positive'
            title = request.POST.get('title', '').strip()
            text = request.POST.get('text', '').strip()
            if not title or not text:
                messages.error(request, 'Заполните заголовок и текст рецензии.')
            else:
                Review.objects.create(
                    movie=movie, user=request.user, tone=tone, title=title, text=text
                )
                messages.success(request, 'Рецензия опубликована!')
                return redirect('movie_detail', slug=movie.slug)

    return render(
        request,
        'cinema/movie_detail.html',
        {
            'movie': movie,
            'user_rating': user_rating,
            'in_watchlist': in_watchlist,
            'score_range': range(1, 11),
        },
    )


def person_detail_view(request, slug):
    person = get_object_or_404(Person, slug=slug)
    directed = person.directed_movies.filter(is_published=True)
    acted = person.acted_movies.filter(is_published=True)
    return render(
        request,
        'cinema/person_detail.html',
        {'person': person, 'directed': directed, 'acted': acted},
    )


@require_POST
def ajax_toggle_watchlist_view(request, movie_id):
    if not request.user.is_authenticated:
        return JsonResponse(
            {'ok': False, 'message': 'Войдите в аккаунт, чтобы сохранять фильмы.'}, status=401
        )

    movie = get_object_or_404(Movie, id=movie_id, is_published=True)
    item = Watchlist.objects.filter(user=request.user, movie=movie).first()
    if item:
        item.delete()
        return JsonResponse(
            {
                'ok': True,
                'added': False,
                'message': f'«{movie.title}» удалён из «Буду смотреть».',
            }
        )

    Watchlist.objects.create(user=request.user, movie=movie)
    return JsonResponse(
        {
            'ok': True,
            'added': True,
            'message': f'«{movie.title}» добавлен в «Буду смотреть»!',
        }
    )


@login_required
def profile_view(request):
    watchlist = Watchlist.objects.filter(user=request.user).select_related('movie')
    ratings = Rating.objects.filter(user=request.user).select_related('movie').order_by('-created_at')
    reviews = Review.objects.filter(user=request.user).select_related('movie')
    return render(
        request,
        'cinema/profile.html',
        {'watchlist': watchlist, 'ratings': ratings, 'reviews': reviews},
    )


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, 'Добро пожаловать в Кинопоиск!')
            return redirect('catalog')
        messages.error(request, 'Неверный логин или пароль.')
    return render(request, 'cinema/login.html')


def register_view(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        password2 = request.POST.get('password2', '')

        if not username or not password:
            messages.error(request, 'Введите логин и пароль.')
        elif password != password2:
            messages.error(request, 'Пароли не совпадают.')
        elif User.objects.filter(username=username).exists():
            messages.error(request, 'Такой логин уже занят.')
        else:
            user = User.objects.create_user(username=username, password=password)
            login(request, user)
            messages.success(request, 'Аккаунт успешно создан!')
            return redirect('catalog')

    return render(request, 'cinema/register.html')




def movie_create_view(request):
    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        original_title = request.POST.get("original_title", "").strip()
        slug = request.POST.get("slug", "").strip()
        tagline = request.POST.get("tagline", "").strip()
        description = request.POST.get("description", "").strip()
        year_raw = request.POST.get("release_year", "").strip()
        release_year = int(year_raw) if year_raw.isdigit() else None
        country = request.POST.get("country", "").strip()
        duration = request.POST.get("duration", "").strip()
        age_rating = request.POST.get("age_rating", "").strip()
        poster = request.FILES.get("poster")
        is_published = "is_published" in request.POST

        if not title or not slug:
            messages.error(request, "Заполни хотя бы название и slug.")
            return render(request, "cinema/movie_create.html")

        try:
            movie = Movie.objects.create(
                title=title,
                original_title=original_title,
                slug=slug,
                tagline=tagline,
                description=description,
                release_year=release_year,
                country=country,
                duration=duration,
                age_rating=age_rating,
                poster=poster,
                is_published=is_published,
            )
            messages.success(request, f"Фильм «{movie.title}» добавлен!")
            return redirect("movie_detail", slug=movie.slug)
        except IntegrityError:
            messages.error(request, "Такой slug уже существует. Придумай другой, например igra-v-osminoga-2.")

    return render(request, "cinema/movie_create.html")


def movie_update_view(request, slug):
    movie = get_object_or_404(Movie, slug=slug)

    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        new_slug = request.POST.get("slug", "").strip()
        year_raw = request.POST.get("release_year", "").strip()

        if not title or not new_slug:
            messages.error(request, "Название и slug не могут быть пустыми.")
            return render(request, "cinema/movie_update.html", {"movie": movie})

        movie.title = title
        movie.original_title = request.POST.get("original_title", "").strip()
        movie.slug = new_slug
        movie.tagline = request.POST.get("tagline", "").strip()
        movie.description = request.POST.get("description", "").strip()
        movie.release_year = int(year_raw) if year_raw.isdigit() else None
        movie.country = request.POST.get("country", "").strip()
        movie.duration = request.POST.get("duration", "").strip()
        movie.age_rating = request.POST.get("age_rating", "").strip()
        movie.is_published = "is_published" in request.POST

        if "poster" in request.FILES:
            movie.poster = request.FILES["poster"]

        try:
            movie.save()
            messages.success(request, f"Изменения для «{movie.title}» сохранены.")
            return redirect("movie_detail", slug=movie.slug)
        except IntegrityError:
            messages.error(request, "Этот slug уже занят другим фильмом.")

    return render(request, "cinema/movie_update.html", {"movie": movie})


def movie_delete_view(request, slug):
    movie = get_object_or_404(Movie, slug=slug)

    if request.method == "POST":
        title = movie.title
        movie.delete()
        messages.success(request, f"«{title}» удалён.")
        return redirect("catalog")

    return render(request, "cinema/movie_confirm_delete.html", {"movie": movie})
