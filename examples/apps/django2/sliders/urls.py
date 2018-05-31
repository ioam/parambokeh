from django.urls import path

from . import views

app_name='sliders'
urlpatterns = [
#    path('test', views.sliders, name='sliders'),
    path('', views.sliders, name='sliders'),
#    path('<int:question_id>/', views.detail, name='detail'),
#    path('<int:question_id>/results/', views.results, name='results'),
#    path('<int:question_id>/vote/', views.vote, name='vote'),    
]
