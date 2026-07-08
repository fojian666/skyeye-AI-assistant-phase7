from django.urls import path
from . import views

urlpatterns = [
   path('interpretation-task-result/add', views.add_interpretation_task_result, name='interpretation'),
   path('interpretation-task-result/resource_list',views.get_all_task_resources),
   path('interpretation-task-result/list',views.get_all_task),
   path('interpretation-task-result/get_result/<task_id>',views.get_interpretation_task_result_by_id), # 根据id获取任务结果
   path('interpretation-task-result/fetch_task_fronted',views.fetch_interpretation_task_result_fronted), # 根据id删除任务结果
   path('interpretation-task-result/get_stat_info',views.get_stat_info),
   path('interpretation-task-result/get_detail_result/<task_id>',views.get_detail_result),

   path('interpretation-task/ai_detection_one_step', views.ai_detection_one_step),
   path('interpretation-task/server_paths', views.server_paths),
   path('interpretation-task/get_models_list', views.get_models_list),
   path('interpretation-task/get_process_status_node', views.get_process_status_node),
   path('interpretation-task/data_verify_main', views.data_verify_main),
   path('interpretation-task/get_gpu_free_memory', views.get_gpu_free_memory),
   path('interpretation-task/get_redis_count', views.get_redis_count),
   path('interpretation-task/search_redis_count', views.search_redis_count),
   path('interpretation-task/emptyRedis', views.emptyRedis),
   path('interpretation-task/task_terminatemain', views.task_terminatemain),
   path('interpretation-task/download_task_result', views.download_task_result),
]
