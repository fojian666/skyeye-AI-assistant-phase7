# _*_ coding: utf-8 _*_
# @Time : 2024/7/31 10:52 
# @Author : xxx 
# @Version：V 0.1
# @File : urls.py
# @desc :
from django.urls import path
from . import views

urlpatterns = [

    path('sourceOverview', views.source_overview, name='资源概览'),
    path('dict-type/list', views.dict_type_list, name='获取字典类型数据'),
    path("dict-type/add", views.dict_type_insert, name='新增字典类型数据'),
    path('dict-type/edit', views.dict_type_modify),
    path('dict-type/del', views.dict_type_delete),
    path('dict-data/list', views.dict_data_list, name='获取字典枚举数据'),
    path('dict-data/add', views.dict_data_insert, name='新增字典枚举数据'),
    path('dict-data/edit', views.dict_data_modify),

    path('get-dict-by-type', views.get_enum),
    path('get-public-key',views.get_public_key),
    path('server_path', views.server_path),
    path('get_logs', views.get_logs, name='获取日志'),
    path('get_menus', views.get_menus),
    path('get_info', views.get_info, name='获取统计信息'),
    path('menu_operation', views.menu_operation, name='menu_operation'),  # 菜单的增删改查
    path('role_operation', views.role_operation, name='role_operation'),  # 角色的增删改查
    path('user_related', views.user_related, name='user_related'),  # 角色关联用户
    path('menu_related', views.menu_related, name='menu_related'),  # 角色关联菜单
    path('login_check', views.login_check),  # 用户登录验证
    path('user/temp-login', views.temp_login),  # 临时登录
    path('user/current-user', views.get_current_user),
    path('password', views.password),
    path('user/list', views.get_users),
    path('user/add', views.add_user),
    path('user-status/edit', views.edit_status),
    path('user/edit', views.user_modify),
    path('user/del', views.user_delete, name='删除用户'),
    path('user_role_relation', views.user_role_relation),
    path('map_info', views.map_info),

    # 日志查询
    path('logs_search', views.logs_search),

    # 机巢管理
    path('nest/del', views.nest_delete),
    path('nest/add', views.nest_insert),
    path('nest/import', views.nest_import),
    path('nest/list', views.get_nest),
    path('nest/all', views.nest_info),
    path('menu_list', views.menu_list),
    path('data_analysis', views.data_analysis),
    path('statistics_illegal_clues', views.statistics_illegal_clues),
    path('clue_confirmed', views.clue_confirmed),
    path('village_list', views.village_list),
    path('nest_modify', views.nest_modify),

    path('multivariate_data/dict', views.multivariate_data),
    path('multivariate_data/query_task', views.query_task),

    # 行政区划接口
    path('regions/list', views.get_regions),  # 获取列表（GET）
    path('regions/add', views.add_region),  # 新增（POST）
    path('regions/edit', views.update_region),  # 更新（PUT）
    path('regions/del', views.delete_region),  # 删除（DELETE）
    path('region/parent', views.get_region_parents),  # 获取区划父类

    path('system-name', views.get_system_name), # 获取系统名称
    path('region/get-region-tree-by-user', views.proxy_region_tree_by_user),
    path('region/region-info-list', views.proxy_region_info_list),

    # AI Chat
    path('chat/completions', views.chat_completions),
]
