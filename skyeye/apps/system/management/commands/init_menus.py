# -*- coding: utf-8 -*-
"""初始化系统菜单、角色及角色-菜单关联（供前端顶部导航使用）。"""
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.system.models import SysMenu, SysRole, RoleMenu

# 顶级菜单（Header 左右各 3 个，共 6 项）
TOP_MENUS = [
    {'id': 1, 'order': 1, 'caption': '统计大屏', 'url': '/data_overview_proto',
     'icon': 'icon-a-xitonggailan', 'pid': 0, 'remark': '无锡统计大屏', 'display': 1},
    {'id': 2, 'order': 2, 'caption': '低空数据', 'url': '/data-management/one-map',
     'icon': 'icon-a-iconshujuku', 'pid': 0, 'remark': '低空数据管理', 'display': 1},
    {'id': 3, 'order': 3, 'caption': '全景检测', 'url': '/panoramic-detection/clue-view',
     'icon': 'icon-quan-01', 'pid': 0, 'remark': '全景线索检测', 'display': 1},
    {'id': 4, 'order': 4, 'caption': '智能解译', 'url': '/intelligent/interpretation-task-management',
     'icon': 'icon-shujuchuli', 'pid': 0, 'remark': 'AI 解译分析', 'display': 1},
    {'id': 5, 'order': 5, 'caption': '实时监控', 'url': '/live-monitor',
     'icon': 'icon-fuwuguanli', 'pid': 0, 'remark': '无人机实时视频', 'display': 1},
    {'id': 6, 'order': 6, 'caption': '系统运维管理', 'url': '/resource-center/system-management/user-info',
     'icon': 'icon-shezhi', 'pid': 0, 'remark': '用户/角色/菜单管理', 'display': 1},
]

CHILD_MENUS = [
    # 低空数据
    {'id': 11, 'order': 1, 'caption': '一张图', 'url': '/data-management/one-map',
     'icon': 'icon-a-iconshujuku', 'pid': 2, 'remark': '', 'display': 1},
    {'id': 12, 'order': 2, 'caption': '数据上传', 'url': '/data-management/table',
     'icon': 'icon-shangchuan', 'pid': 2, 'remark': '', 'display': 1},
    {'id': 13, 'order': 3, 'caption': '订单管理', 'url': '/data-management/order-management',
     'icon': 'icon-a-iconrenwu', 'pid': 2, 'remark': '', 'display': 1},
    {'id': 14, 'order': 4, 'caption': '全景图片', 'url': '/data-management/panorama-image',
     'icon': 'icon-sanping', 'pid': 2, 'remark': '', 'display': 1},
    # 全景检测
    {'id': 21, 'order': 1, 'caption': '线索总览', 'url': '/panoramic-detection/clue-view',
     'icon': 'icon-quan-01', 'pid': 3, 'remark': '', 'display': 1},
    {'id': 22, 'order': 2, 'caption': '网格管理', 'url': '/panoramic-detection/grid-management',
     'icon': 'icon-gongjuxiang', 'pid': 3, 'remark': '', 'display': 1},
    {'id': 23, 'order': 3, 'caption': '任务管理', 'url': '/panoramic-detection/task-management',
     'icon': 'icon-a-iconrenwu', 'pid': 3, 'remark': '', 'display': 1},
    {'id': 24, 'order': 4, 'caption': '主检测', 'url': '/panoramic-detection/main-detection',
     'icon': 'icon-shujuchuli', 'pid': 3, 'remark': '', 'display': 1},
    {'id': 25, 'order': 5, 'caption': '线索核实', 'url': '/panoramic-detection/verifyClue',
     'icon': 'icon-data-Inquire', 'pid': 3, 'remark': '', 'display': 1},
    {'id': 26, 'order': 6, 'caption': '报告管理', 'url': '/panoramic-detection/report',
     'icon': 'icon-xiangmu', 'pid': 3, 'remark': '', 'display': 1},
    # 智能解译
    {'id': 31, 'order': 1, 'caption': '解译任务', 'url': '/intelligent/interpretation-task-management',
     'icon': 'icon-shujuchuli', 'pid': 4, 'remark': '', 'display': 1},
    {'id': 32, 'order': 2, 'caption': '变化检测', 'url': '/intelligent/land-change',
     'icon': 'icon-a-88_tuxiangronghe', 'pid': 4, 'remark': '', 'display': 1},
    {'id': 33, 'order': 3, 'caption': '地块分割', 'url': '/intelligent/land-dividing',
     'icon': 'icon-cemianji', 'pid': 4, 'remark': '', 'display': 1},
    # 系统运维
    {'id': 61, 'order': 1, 'caption': '用户管理', 'url': '/resource-center/system-management/user-info',
     'icon': 'icon-shezhi', 'pid': 6, 'remark': '', 'display': 1},
    {'id': 62, 'order': 2, 'caption': '角色管理', 'url': '/resource-center/system-management/role-management',
     'icon': 'icon-shezhi', 'pid': 6, 'remark': '', 'display': 1},
    {'id': 63, 'order': 3, 'caption': '菜单管理', 'url': '/resource-center/system-management/menu-management',
     'icon': 'icon-shezhi', 'pid': 6, 'remark': '', 'display': 1},
    {'id': 64, 'order': 4, 'caption': '数据字典', 'url': '/resource-center/system-management/data-dict',
     'icon': 'icon-shezhi', 'pid': 6, 'remark': '', 'display': 1},
    {'id': 65, 'order': 5, 'caption': '日志查看', 'url': '/resource-center/system-management/log-view',
     'icon': 'icon-shezhi', 'pid': 6, 'remark': '', 'display': 1},
    {'id': 66, 'order': 6, 'caption': '资源目录', 'url': '/resource-center/resource-management/resource-directory',
     'icon': 'icon-a-iconrenwu', 'pid': 6, 'remark': '', 'display': 1},
]

ROLES = [
    {'id': 1, 'name': '超级管理员', 'abbreviation': 'super', 'remark': '全部权限', 'order': 1},
    {'id': 2, 'name': '普通用户', 'abbreviation': 'user', 'remark': '业务用户', 'order': 3},
    {'id': 3, 'name': '管理员', 'abbreviation': 'admin', 'remark': '系统管理员', 'order': 2},
]

ALL_MENU_IDS = [m['id'] for m in TOP_MENUS + CHILD_MENUS]
ROLE_MENU_MAP = {
    1: ALL_MENU_IDS,
    2: ALL_MENU_IDS,
    3: ALL_MENU_IDS,
}


class Command(BaseCommand):
    help = '初始化 t_role / t_menus / t_role_menu，使前端顶部导航显示菜单按钮'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='清空已有菜单与角色关联后重新写入',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options['force']:
            RoleMenu.objects.all().delete()
            SysMenu.objects.all().delete()
            SysRole.objects.all().delete()
            self.stdout.write('已清空旧菜单与角色数据')

        for role in ROLES:
            SysRole.objects.update_or_create(id=role['id'], defaults=role)

        for menu in TOP_MENUS + CHILD_MENUS:
            SysMenu.objects.update_or_create(id=menu['id'], defaults=menu)

        for role_id, menu_ids in ROLE_MENU_MAP.items():
            for menu_id in menu_ids:
                RoleMenu.objects.get_or_create(role_id=role_id, menu_id=menu_id)

        self.stdout.write(self.style.SUCCESS(
            f'完成：角色 {SysRole.objects.count()} 个，'
            f'菜单 {SysMenu.objects.count()} 个，'
            f'关联 {RoleMenu.objects.count()} 条'
        ))
        self.stdout.write('请重新登录前端，或刷新页面后查看顶部导航。')
