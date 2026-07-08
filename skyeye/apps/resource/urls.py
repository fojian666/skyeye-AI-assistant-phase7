from django.urls import path
from . import views

urlpatterns = [
    path('resources/list', views.resourceLists),
    path('resources/add', views.resources),
    path('resources/del', views.resource_delete),
    path('resource_one', views.resource_one),
    path('resources/edit', views.resource_modify),
    path('resources/get_resources_on_one_map', views.get_resources_on_one_map), # 一张图页面获取资源数据
    path('resources/get_business_data', views.get_business_data),
    path('get_time_axis', views.get_time_axis),
    path("top-view/list", views.top_view_task),
    path('flight_view_task', views.flight_view_task),
    path('point-location/list', views.query_point_location),
    path('nest/list', views.get_machine_nest),
    path('get-buffer-list', views.get_buffer_list),
    path('region/get-region-tree-by-user', views.region_data),
    path('query_data_by_grid_id', views.query_data_by_grid_id),
    path('business_layer_data', views.business_layer_data),
    path('uav-info/list', views.get_uav_info),
    path('multivariate-data/files_upload',views.files_upload),
    path('multivariate-data/add',views.add_multivariate_data),
    path('multivariate-data/list',views.query_multivariate_data),
    path('multivariate-data/del',views.delete_multivariate_data),
    path('video/list',views.video_data),
    path('3dtiles-list',views.get_three_source_list),
    path('live-stream/info',views.live_stream),
    path('cog/upload', views.cog_upload, name='cog_upload'),
    path('cog/convert', views.cog_convert, name='cog_convert'),
    path('cog/status/<str:task_id>', views.cog_status, name='cog_status'),
    path('cog/file/<str:folder>/<str:filename>', views.cog_serve_file, name='cog_serve_file'),
]
