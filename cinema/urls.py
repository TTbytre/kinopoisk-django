from django.urls import path
from . import views

urlpatterns = [
    path('', views.catalog_view, name='catalog'),
    path('movie/<slug:slug>/', views.movie_detail_view, name='movie_detail'),
    path('person/<slug:slug>/', views.person_detail_view, name='person_detail'),
    path('api/watchlist/<int:movie_id>/', views.ajax_toggle_watchlist_view, name='ajax_toggle_watchlist'),
    path('profile/', views.profile_view, name='profile'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path("movie/add/", views.movie_create_view, name="movie_create"),
    path("movie/<slug:slug>/edit/", views.movie_update_view, name="movie_update"),
    path("movie/<slug:slug>/delete/", views.movie_delete_view, name="movie_delete"),
]