from django.urls import path

from anatomy import views

urlpatterns = [
    path("", views.index, name="index"),
    path("pump/", views.pump, name="pump"),
    path("physics/", views.physics, name="physics"),
    path("curves/", views.curves, name="curves"),
    path("research/", views.research, name="research"),
    path("research/analyze/", views.research_analyze, name="research-analyze"),
    path("research/review/<str:intake_id>/", views.research_review, name="research-review"),
    path("research/import/<str:intake_id>/", views.research_import, name="research-import"),
    path("research/cancel/<str:intake_id>/", views.research_cancel, name="research-cancel"),
    path("research/reprofile/<str:dataset_id>/", views.research_reprofile, name="research-reprofile"),
    path("research/mapping/<str:dataset_id>/", views.research_mapping_save, name="research-mapping"),
    path("about/", views.about, name="about"),
    path("config/", views.config_page, name="config"),
    path("physics/api/hydraulics/", views.physics_hydraulics, name="physics-hydraulics"),
    path("physics/api/charts/", views.physics_charts, name="physics-charts"),
    path("physics/api/compare/", views.physics_compare, name="physics-compare"),
    path("physics/api/curves/", views.physics_curves, name="physics-curves"),
    path("physics/api/curves/<slug:curve_id>/", views.physics_curve_detail, name="physics-curve"),
    path(
        "physics/api/curves/<slug:curve_id>/marker/",
        views.physics_curve_marker,
        name="physics-curve-marker",
    ),
    path("health/", views.health, name="health"),
]
