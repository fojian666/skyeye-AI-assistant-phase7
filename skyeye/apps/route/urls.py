from django.urls import path
from . import views

urlpatterns = [
   
    # 视频直播
    path('get_video', views.get_onlineuav_info),
    path('get_uav_fly_track', views.get_uav_fly_track),

    # 航线规划
    path('routes/add', views.route_plan),
    path('routes/list', views.route_list),
    path('routes/map-detail/<file_id>', views.route_map_detail),
    path('routes/del', views.delete_plan),
    path('routes/batch-delete', views.batch_delete_plans),
    path('routes/upload', views.receive_zip),
    path('routes/filter-parcels', views.filter_parcels_by_range),
    path('jobs/<str:job_id>', views.route_job_status),
    path('jobs/<str:job_id>/kmz', views.download_job_kmz),
    path('jobs/<str:job_id>/excluded-parcels', views.download_excluded_parcels),
    path('get_uav_info', views.get_uav_info),
    path('get_zipfile_list', views.get_zipfile_list),
    path('panoramic_point/add', views.panoramic_point_plan),
    path('modify_panoramic_point', views.modify_panoramic_point),
    path('routes/view-plan/<file_id>', views.view_plan),
    path('route_plan', views.add_route_plan),
    path('route_plan_async', views.add_route_plan_async),

]
