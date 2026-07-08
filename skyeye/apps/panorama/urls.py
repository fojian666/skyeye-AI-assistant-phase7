from django.urls import path
from .views import panorama_views
from .views import verify_views
from .views import supervision_views

urlpatterns = [
    path('file/download/<file_id>', panorama_views.download), # 文件下载


    path('message_notify', panorama_views.message_notify),
    path('files_upload', panorama_views.files_upload),
    # 网格管理
    path('grid/list', panorama_views.grid_list),
    path('grid/add', panorama_views.grid_add),
    path('grid/del', panorama_views.grid_delete),
    # 批次管理
    path('batch/list', panorama_views.batch_list),
    path('batch/add', panorama_views.batch_add),
    path('batch/del', panorama_views.batch_delete),
    path('batch/get-batch-by-id',panorama_views.get_batch_by_id),
    path('batch/status', panorama_views.batch_status),
    path('batch/change-status',panorama_views.change_status),
    path('batch/export-shp',panorama_views.export_shp),#导出批次中绘制的图斑
    path("upload-batch/down_detection_log/<str:upload_batch_id>", panorama_views.down_detection_log),  # 下载检测提交日志
    path('batch/temp-detection-batch-data',panorama_views.temp_detection_batch_data),#临时检测批次数据

    path('point_location', panorama_views.point_location),
    path('panorama-point/nearest',panorama_views.panorama_point_nearest),
    path('map_view_info', panorama_views.map_view_info),
    path('map_view_clue_list', panorama_views.map_view_clue_list),
    path('main_detection', panorama_views.main_detection),
    path('panorama_image_one', panorama_views.panorama_image_one),
    path('panorama_image_all', panorama_views.panorama_image_by_batch_id),
    path('panorama_image_by_params',panorama_views.panorama_image_by_params),
    path('panorama_image_by_point_id', panorama_views.panorama_image_by_point_id),
    path('panorama_image_sibling', panorama_views.panorama_image_sibling),
    path('upload_batch/list', panorama_views.upload_batch_list),
    path('point_list_by_batch', panorama_views.point_list_by_batch),
    path('upload_batch/del', panorama_views.upload_batch_delete),
    path('auto_start_detection', panorama_views.auto_start_detection),
    path('get_temp_data', panorama_views.get_temp_data),
    # 线索管理
    path('clue/clue_status', panorama_views.clue_status),
    path('clue/get_clue_by_panorama_image_id', panorama_views.get_clue_by_panorama_image_id),
    path('clue_view/<clue_id>', panorama_views.clue_view),
    path('clue/get_clue_data_by_id', panorama_views.get_clue_data_by_id),
    path('clue-location', panorama_views.clue_location),
    path('panorama_image/review', panorama_views.panorama_image_review),
    path('clue/objectives', panorama_views.add_label),  # 增加线索
    path('clue/list', panorama_views.clue_list),
    path('clue/clue_entry', panorama_views.clue_entry),
    path('clue/export_clue_data',panorama_views.export_clue_data),
    # 场景管理
    path('scene/list', panorama_views.scene),
    path('scene/add', panorama_views.scene_insert),
    path('scene/del', panorama_views.scene_delete),
    path('scene_modify', panorama_views.scene_modify),

    path('interpretation_progress', panorama_views.interpretation_progress),
    path('info', panorama_views.info),
    path('data_info', panorama_views.data_info),
    path('change-detection',panorama_views.change_detection),
    # 核实线索
    path('verify_clue', verify_views.verify_clue),
    path('verify_clue_list', verify_views.verify_clue_list),
    path('verify_task', verify_views.verify_task),
    path('verify_clue_delete', verify_views.verify_clue_delete),
    path('verify_task_params', verify_views.verify_task_params),
    path('verify_clue_add', verify_views.verify_clue_add),
    path('information_push', verify_views.information_push),
    path('files', verify_views.files),
    path('delete_clue_task', verify_views.delete_clue_task),

    path('polygon-task/add', verify_views.polygon_task_add),
    path('polygon-task/list', verify_views.polygon_task),
    path('polygon-data/list', verify_views.polygon_data),
    path('polygon-task/del', verify_views.polygon_task_delete),
    path('polygon-data/update-data-status', verify_views.polygon_data_status),
    path('polygon-data/verify', verify_views.polygon_data_conclusion),
    path('polygon-data/calculate_panorama', verify_views.calculate_panorama),
    path('pattern_report_export/<task_id>', verify_views.pattern_report_export),
    path('polygon-data/judge_clue', verify_views.judge_clue),
    # 不检测区域
    path('frame_area/list', panorama_views.frame_area_list),
    path('frame_area/add', panorama_views.frame_area),
    path('frame_area/del', panorama_views.frame_area_delete),
    path('frame_area/upload',verify_views.frame_area_upload),
    path('frame-area/get-upload-areas',panorama_views.get_upload_areas),
    path('get_target_area_list', panorama_views.get_target_area_list),
    path('target_area_clue_delete', panorama_views.target_area_clue_delete),


    path('get_buffer_gd', panorama_views.get_buffer_gd), # 获取耕地缓冲区

    path('temp_main_detection', panorama_views.temp_main_detection),
    # 标绘相关
    path('plot/add-plot',panorama_views.add_plot),
    path('plot/get-plot-by-image-id', panorama_views.get_plot_by_panorama_image_id),
    path('plot/get-plot-by-id',panorama_views.get_plot_by_id),
    path('plot/delete-plot', panorama_views.delete_plot),
    path('plot/update-plot', panorama_views.update_plot),

    path('order/list',panorama_views.order_list),
    path('order/add',panorama_views.order_add),
    path('order/del',panorama_views.order_delete),

    # 监管任务
    path('supervision/project/list', supervision_views.project_list),
    path('supervision/project/add', supervision_views.project_add),
    path('supervision/project/edit', supervision_views.project_edit),
    path('supervision/project/del', supervision_views.project_delete),
    # 监管图斑
    path('supervision/polygon/list', supervision_views.polygon_list),
    path('supervision/polygon/detail', supervision_views.polygon_detail),
    path('supervision/polygon/add', supervision_views.polygon_add),
    path('supervision/polygon/edit', supervision_views.polygon_edit),
    path('supervision/polygon/del', supervision_views.polygon_delete),
    # 监管航线关联
    path('supervision/route/list', supervision_views.route_list),
    path('supervision/route/add', supervision_views.route_add),
    path('supervision/route/edit', supervision_views.route_edit),
    path('supervision/route/del', supervision_views.route_delete),
]
