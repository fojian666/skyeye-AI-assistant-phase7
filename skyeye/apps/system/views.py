import ast
import base64
import configparser
import datetime
import json
import os
import logging
import time

# LangChain 内部使用 asyncio，会触发 Django ORM 的 async 安全检测
# 设置此环境变量允许在 event loop 存在时使用同步 ORM
os.environ.setdefault('DJANGO_ALLOW_ASYNC_UNSAFE', 'true')

import pandas as pd
import requests
from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.core.paginator import Paginator
from django.db.models import Q, Count, Func
from django.db.models.functions import TruncDate, TruncMonth
from django.apps import apps
from django.http import JsonResponse, HttpResponse, StreamingHttpResponse
from django.shortcuts import render
from django.db import transaction
from django.utils import timezone
from django.views import View
from utils_tools.utils import parse_json_request, paginate_queryset, validate_region_data

from config import OperationOptions
from .models import *
from django.contrib import auth
from utils_tools.common import create_log, ok, error, warning, ok_data, login_request, get_center, parse_jwt_token
from apps.panorama.models import Resource, Scene, Clue, Grid, PointLocation, Batch, PanoramaImage
from apps.report.models import Report, BatchReport
from .tokens import LoginSerializer
from django.utils.encoding import escape_uri_path
from logger import Logger

logger = Logger(logname='resource_views.log', loglevel=5, logger='resource').getlog()


def get_system_name(request):
    system_name_dict = {
        "唐山市(130200)": "唐山市综合空间数据管理系统",

    }
    user = parse_jwt_token(request)
    county = user.county
    if county == "唐山市(130200)":
        system_name = "唐山市综合空间数据管理系统"
    elif county == "无锡市(320200)":
        system_name = "项目跟踪管理"
    else:
        system_name = "自然资源耕保无人机智能监测系统"
    return JsonResponse({"code": 0, "data": {"system_name": system_name}})


def server_path(request):
    """
    获取服务器路径
    @param request:
    @return:
    """
    try:
        folder_path = os.path.join(settings.BASE_DIR, 'static/temp')
        file_list = [i for i in os.listdir(folder_path) if os.path.isdir(os.path.join(folder_path, i))]
        return JsonResponse({'code': 0, 'msg': 'success', 'data': file_list, 'count': len(file_list)})
    except Exception as e:
        logger.error("获取服务器路径失败，错误信息：%s" % str(e))
        return JsonResponse({'code': 1, 'msg': 'str(e)'})


def dict_type_list(request):
    """
    获取字典类型数据
    @param request:
    @return:
    """
    try:

        params = json.loads(request.body.decode('utf-8'))
        keywords = params.get('query', '')
        limit = params.get('limit', 10)
        page = params.get('page', 1)
        if not keywords:
            results_obj = SysDictType.objects.all()
        else:
            results_obj = SysDictType.objects.filter(cn_name__contains=keywords).all()
        paginator = Paginator(results_obj, limit)
        results = paginator.page(page)
        data_list = []
        for result in results:
            records = {
                'id': result.id,
                'cn_name': result.cn_name,
                'en_name': result.en_name,
                'status': True if result.status == 1 else False,
                'create_by': result.create_by,
                'create_time': result.create_time.strftime('%Y-%m-%d %H:%M:%S'),
                'remark': result.remark,
            }
            data_list.append(records)
        response_data = {
            'code': 0,
            'msg': '字典数据获取成功！',
            'data': data_list,
            'count': len(results_obj)
        }
        return JsonResponse(response_data)
    except Exception as e:
        logger.error(f'字典数据获取失败:{e}')
        return JsonResponse({'code': 500, 'msg': '字典数据获取失败！'})


def dict_type_insert(request):
    with transaction.atomic():
        try:
            params = json.loads(request.body.decode('utf-8'))
            cn_name = params.get('cn_name', '')
            en_name = params.get('en_name', '')
            remark = params.get('remark', '')
            SysDictType.objects.create(
                cn_name=cn_name,
                en_name=en_name,
                remark=remark,
                create_by=request.session['username']
            )
            response_data = {
                'code': 0,
                'msg': '字典数据新增成功！',
                'data': [],
            }
            return JsonResponse(response_data)
        except Exception as e:
            logger.error(f'字典数据新增失败:{e}')
            response_data = {
                'code': 500,
                'msg': '字典数据新增失败！',
                'data': [],
            }
            return JsonResponse(response_data)


def dict_type_delete(request):
    """
    删除字典类型
    """
    params = json.loads(request.body.decode('utf-8'))
    dict_type_ids = params.get('nest_ids')
    for dict_type_id in dict_type_ids:
        dict_type_obj = SysDictType.objects.get(id=dict_type_id)
        if dict_type_obj:
            dict_type_obj.delete()
    return ok('删除成功')


def dict_type_modify(request):
    """
    字典类型修改
    @param request:
    @return:
    """
    with transaction.atomic():
        try:
            params = json.loads(request.body.decode('utf-8'))
            dict_type_id = params.get('id')
            cn_name = params.get('cn_name', '')
            en_name = params.get('en_name', '')
            remark = params.get('remark', '')
            SysDictType.objects.filter(id=dict_type_id).update(
                cn_name=cn_name,
                en_name=en_name,
                remark=remark,
            )
            response_data = {
                'code': 0,
                'msg': '字典数据修改成功！',
                'data': [],
            }
            return JsonResponse(response_data)
        except Exception as e:
            logger.error(f'字典数据修改失败:{e}')
            return JsonResponse({'code': 0, 'msg': f'字典数据修改失败:{e}', 'data': [], })


def dict_data_list(request):
    """
       获取字典枚举数据
       @param request:
       @return:
       """
    try:
        params = json.loads(request.body.decode('utf-8'))
        keywords = params.get('query', '')
        limit = params.get('limit', 10)
        page = params.get('page', 1)
        dict_type = params.get('dict_type', '')
        if not keywords:
            results_obj = SysDictData.objects.filter(dict_type=dict_type).all()
        else:
            results_obj = SysDictData.objects.filter(name__contains=keywords, dict_type_id=dict_type).all()
        paginator = Paginator(results_obj, limit)
        results = paginator.page(page)
        data_list = []
        for result in results:
            records = {
                'id': result.id,
                'name': result.name,
                'value': result.value,
                'status': True if result.status == 1 else False,
                'create_by': result.create_by,
                'create_time': result.create_time.strftime('%Y-%m-%d %H:%M:%S'),
                'remark': result.remark,
                'sort': result.sort,
                'dict_type': result.dict_type,
            }
            data_list.append(records)
        response_data = {
            'code': 0,
            'msg': '字典枚举数据获取成功！',
            'data': data_list,
            'count': len(results_obj)
        }
        return JsonResponse(response_data)
    except Exception as e:
        logger.error(f'字典枚举数据获取失败:{e}')
        return JsonResponse({'code': 500, 'msg': '字典枚举数据获取失败！'})


def dict_data_insert(request):
    with transaction.atomic():
        try:
            params = json.loads(request.body.decode('utf-8'))
            name = params.get('name', '')
            value = params.get('value', '')
            remark = params.get('remark', '')
            sort = params.get('sort', 0)
            dict_type = params.get('dict_type', '')
            exists = SysDictData.objects.filter(name=name, dict_type=dict_type).first()
            if exists:
                return JsonResponse({'code': 404, 'msg': '字典数据已存在！'})
            SysDictData.objects.create(
                name=name,
                value=value,
                remark=remark,
                sort=sort,
                dict_type=dict_type,
                create_by=request.session['username']
            )
            response_data = {
                'code': 0,
                'msg': '字典数据新增成功！',
                'data': [],
            }
            return JsonResponse(response_data)
        except Exception as e:
            logger.error(f'字典数据新增失败:{e}')
            return JsonResponse({'code': 500, 'msg': '字典数据新增失败！'})


def dict_data_modify(request):
    """
    字典数据修改
    @param request:
    @return:
    """
    with transaction.atomic():
        try:
            params = json.loads(request.body.decode('utf-8'))
            dict_data_id = params.get('id', '')
            name = params.get('name', '')
            value = params.get('value', '')
            remark = params.get('remark', '')
            sort = params.get('sort', 0)
            exists = SysDictData.objects.filter(Q(name=name) | Q(value=value)).exclude(id=dict_data_id).first()
            if exists:
                return JsonResponse({'code': 404, 'msg': '字典数据已存在！'})
            SysDictData.objects.filter(id=dict_data_id).update(
                name=name,
                value=value,
                remark=remark,
                sort=sort,
            )
            response_data = {
                'code': 0,
                'msg': '字典数据修改成功！',
                'data': [],
            }
            return JsonResponse(response_data)
        except Exception as e:
            logger.error('字典数据修改异常：{}'.format(e))
            return JsonResponse({'code': 500, 'msg': f'字典数据修改异常:{e}'})


def decode_pwd(encrypt_str):
    # 1. 解base64
    raw = base64.b64decode(encrypt_str).decode('latin-1')
    # 2. 反转回来
    raw = raw[::-1]
    # 3. 偏移还原
    mix_list = []
    for char in raw:
        old_code = ord(char) - 18
        mix_list.append(chr(old_code))
    mix_str = "".join(mix_list)
    # 4. 分割去掉密钥后缀，得到原密码
    if "|" in mix_str:
        plain = mix_str.split("|")[0]
        return plain
    return ""


def get_public_key(request):
    SECRET_KEY = "laiS2026pwd"
    OFFSET_NUM = 18
    return JsonResponse({"code": 0, 'data': {'public_key': SECRET_KEY, 'offset_num': OFFSET_NUM}})


@login_request
def get_enum(request):
    """
    获取枚举
    @param request:
    @return:
    """
    try:
        dict_type = request.GET.get('dict_type')
        print(dict_type)
        data_list = []
        results = SysDictData.objects.filter(dict_type=dict_type).all()
        for result in results:
            records = {
                'name': result.name,
                'value': result.value,
                'id': result.id
            }
            data_list.append(records)
        response_data = {
            'code': 0,
            'msg': '枚举数据获取成功！',
            'data': {
                dict_type: data_list
            }
        }
        return JsonResponse(response_data)
    except Exception as e:
        logger.error('枚举数据获取异常：{}'.format(e))
        return JsonResponse({'code': 500, 'msg': '枚举数据获取异常！'})


def get_info(request):
    """
    首页获取统计信息
    @param request:
    @return:
    """
    try:
        response_data = {
            'code': 0,
            'msg': '请求成功',
            'data': {}
        }
        # 网格总数
        total_grid = Grid.objects.count()
        # 全景点总数
        total_point = PointLocation.objects.count()
        # 任务总数
        total_clue = Clue.objects.filter(status__in=[2, 3], batch__grid__county=request.session.get('county')).count()
        total_batch = Batch.objects.count()
        data = {'total_grid': total_grid, 'total_point': total_point, 'total_clue': total_clue,
                'total_batch': total_batch}
        response_data['data'] = data
        return JsonResponse(response_data)
    except Exception as e:
        logger.error('首页获取统计信息异常：{}'.format(e))


def add_menu(request):
    """
    新增菜单
    @param request:
    @return:
    """
    with transaction.atomic():
        try:
            username = request.session['username']
            if request.method == 'POST':
                form_data = request.POST
                # 菜单显示隐藏
                if 'display' in form_data:
                    sfxs = 1
                else:
                    sfxs = 0
                SysMenu.objects.create(caption=form_data['caption'], order=form_data['order'],
                                       icon=form_data['icon'], url=form_data['url'], pid=form_data['key'],
                                       remark=form_data['remark'], display=sfxs)
                create_log(request, username, username, 'create',
                           username + '创建了菜单《' + form_data['caption'] + "》")
                return HttpResponse(json.dumps(True))
            else:
                # get_url = request.GET.get('type', None)
                menu_dic = {}
                menu_obj = SysMenu.objects.filter(pid=0)
                for m in menu_obj.values('id', 'caption'):
                    menu_dic[m['id']] = m['caption']
                menu_dic['0'] = 'ROOT'

                return render(request, 'system/menu_insert.html', {'menu_dic': menu_dic})
        except Exception as e:
            transaction.set_rollback(True)
            logger.error(f'{e}')


@login_request
def get_menus(request):
    """
    获取菜单列表
    @param request:
    @return:
    """
    try:
        response_data = {}
        # 从root开始查找，即pid=0
        menu_obj = SysMenu.objects.filter(pid=0).all()
        data = []
        for i in menu_obj:
            each_data = {
                'id': i.id,
                'order': i.order,  # 排序号
                'caption': i.caption,  # 菜单名称
                'icon': i.icon,  # 图标
                'url': i.url,  # 请求路由
                'pid': i.pid,  # 父节点id
                'remark': i.remark,  # 描述
                'display': i.display  # 显隐
            }
            if i.caption == '运维中心':
                children_obj = SysMenu.objects.filter(pid=i.id).all()  # 运维中心子节点
                children_list = []
                for j in children_obj:
                    value = get_children_data(j)
                    grand_children_obj = SysMenu.objects.filter(pid=j.id).all()
                    grand_children_list = []
                    for k in grand_children_obj:  # 下一级节点
                        grand_value = get_children_data(k)
                        grand_children_list.append(grand_value)
                    value['children'] = grand_children_list
                    children_list.append(value)
                each_data['children'] = children_list
            data.append(each_data)

        response_data['data'] = data
        response_data['code'] = 0

        return JsonResponse(response_data)
    except Exception as e:
        logger.error(f'获取菜单列表失败: {e}')
        return JsonResponse({'code': 500, 'msg': '获取菜单列表失败'})


def get_children_data(data):
    each_data = {
        'id': data.id,
        'order': data.order,
        'caption': data.caption,
        'icon': data.icon,
        'url': data.url,
        'pid': data.pid,
        'remark': data.remark,
        'display': data.display
    }
    return each_data


# @login_request
def menu_operation(request):
    """
    菜单增删改查
    @param request:
    @return:
    """
    current_user = parse_jwt_token(request)
    role = current_user.role
    with transaction.atomic():
        try:
            username = current_user.username
            # 修改
            if request.method == "PUT":
                params = json.loads(request.body.decode('utf-8'))
                update_id = params.get('id', '')
                menu_order = params.get('order', 1)
                menu_name = params.get('caption', '')
                menu_icon = params.get('icon', '')
                menu_url = params.get('url', '')
                menu_pid = params.get('pid', '')
                menu_remark = params.get('remark', '')
                menu_display = params.get('display')
                if menu_display:
                    menu_display = 1
                else:
                    menu_display = 0
                # 如果不重复，再修改
                menu_obj = SysMenu.objects.filter(id=update_id).first()
                menu_obj.order = int(menu_order)
                menu_obj.caption = menu_name
                menu_obj.icon = menu_icon
                menu_obj.url = menu_url
                menu_obj.pid = menu_pid
                menu_obj.remark = menu_remark
                # 获取当前用户的角色

                if not menu_display:
                    role_menu_obj = RoleMenu.objects.filter(role_id=role, menu_id=update_id).first()
                    if role_menu_obj and menu_display == 0:
                        role_menu_obj.delete()

                # 若修改的是父级元素，则子元素对应的display也要相应修改
                children = SysMenu.objects.filter(pid=menu_obj.id).all()
                if children:
                    for item in children:
                        item.display = menu_display
                        item.save()
                        if not menu_display:
                            # 删除role_menu关联的菜单
                            role_menu_obj = RoleMenu.objects.filter(role_id=role, menu_id=item.id).first()
                            if role_menu_obj and menu_display == 0:
                                role_menu_obj.delete()
                        sec_children = SysMenu.objects.filter(pid=item.id).all()
                        if sec_children:
                            for temp in sec_children:
                                temp.display = menu_display
                                temp.save()
                                if not menu_display:
                                    # 删除role_menu关联的菜单
                                    role_menu_obj = RoleMenu.objects.filter(role_id=role, menu_id=temp.id).first()
                                    if role_menu_obj and menu_display == 0:
                                        role_menu_obj.delete()
                                third_children = SysMenu.objects.filter(pid=temp.id).all()
                                if third_children:
                                    for tmp in third_children:
                                        tmp.display = menu_display
                                        tmp.save()
                                        if not menu_display:
                                            # 删除role_menu关联的菜单
                                            role_menu_obj = RoleMenu.objects.filter(role_id=role,
                                                                                    menu_id=tmp.id).first()
                                            if role_menu_obj and menu_display == 0:
                                                role_menu_obj.delete()
                menu_obj.display = menu_display
                menu_obj.save()
                # 判断修改数据是否重复
                children_name = SysMenu.objects.filter(pid=menu_pid, caption=menu_name).all()  # 判断父节点的菜单是否与新增菜单的名字重复
                if len(children_name) > 2:
                    menu_obj.delete()
                    return JsonResponse({'msg': '存在相同的菜单，请修改菜单名称后重试！', 'status': 'error'})
                create_log(request, username, username, 'update',
                           "修改了菜单《" + menu_obj.caption + "》")
                return JsonResponse({'msg': '修改成功！', 'code': 0})
            # 删除
            elif request.method == "DELETE":
                menu_id = request.GET.get('id')
                menu_obj = SysMenu.objects.filter(id=menu_id).first()
                if menu_obj:
                    # 判断是否有子节点，有子节点全部删除
                    children = SysMenu.objects.filter(pid=menu_id).all()
                    if children:
                        for j in children:
                            RoleMenu.objects.filter(menu_id=j.id).delete()
                            j.delete()
                    RoleMenu.objects.filter(menu_id=menu_id).delete()
                    create_log(request, username, username, 'delete',
                               "删除了菜单《" + menu_obj.caption + "》")
                    menu_obj.delete()
                    return ok('删除成功！')
                else:
                    return warning('删除失败,该菜单不存在！')
            # 新增菜单
            elif request.method == "POST":
                try:
                    params = json.loads(request.body.decode('utf-8'))
                    menu_order = params.get('order', 0)  # 排序号
                    menu_name = params.get('caption')  # 菜单名称
                    menu_icon = params.get('icon')  # 图标
                    menu_url = params.get('url')  # 请求路由
                    menu_pid = params.get('pid', 0)  # 父节点id
                    menu_remark = params.get('remark')  # 描述
                    menu_display = params.get('display')  # 显隐
                    if menu_display:
                        menu_display = 1
                    else:
                        menu_display = 0
                    # 判断新增数据是否重复
                    children_name = SysMenu.objects.filter(pid=menu_pid,
                                                           caption=menu_name).first()  # 判断父节点的菜单是否与新增菜单的名字重复
                    if children_name:
                        return warning('新增的菜单名字重复，请修改后重新添加！')
                    SysMenu.objects.create(
                        order=int(menu_order),
                        caption=menu_name,
                        icon=menu_icon,
                        url=menu_url,
                        pid=menu_pid,
                        remark=menu_remark,
                        display=int(menu_display),
                    )
                    create_log(request, username, username, 'create', "新增了菜单《" + menu_name + "》")
                    return ok('菜单新增成功！')
                except Exception as e:
                    logger.error(e)
                    return error('菜单新增失败！请查看后台日志')
            # 查询
            elif request.method == "GET":
                menu_name = request.GET.get('caption')
                response_data = {}
                # 构造首节点
                data = [{
                    "id": "0",
                    "order": 1,
                    "caption": "root",
                    "icon": "1",
                    "url": "1",
                    "pid": "-1",
                    "remark": "1",
                    "display": 1,
                    "children": []
                }]
                form_data = []
                # user_obj = auth.authenticate(username='admin', password='123456')
                # # create_log(request, user_obj.username, user_obj.username, "login", "登录了系统")
                # # 校验成功，调用auth.login（request, user_obj）方法：
                # auth.login(request, user_obj)
                try:
                    menus = RoleMenu.objects.filter(role_id=request.session['role']).all()
                except Exception as e:
                    logger.error(e)
                    menus = RoleMenu.objects.filter(role_id=3).all()
                # 导航栏显示的菜单
                nav_menus = []
                for i in menus:
                    available_menu = SysMenu.objects.filter(id=i.menu_id, display=1).first()
                    nav_menu = {
                        'id': available_menu.id,
                        'order': available_menu.order,
                        'caption': available_menu.caption,
                        'icon': available_menu.icon,
                        'url': available_menu.url,
                        'pid': available_menu.pid,
                        'remark': available_menu.remark,
                        'display': available_menu.display,
                    }
                    nav_menus.append(nav_menu)
                nav_menus = sorted(nav_menus, key=lambda nav_menu: int(nav_menu['order']))
                # 如果没有搜索，返回全部数据
                if not menu_name:
                    menu_obj = SysMenu.objects.filter(pid=0).all().order_by('order')
                else:
                    menu_obj = SysMenu.objects.filter(caption__contains=menu_name).all().order_by('order')
                for i in menu_obj:
                    each_data = {
                        'id': i.id,
                        'order': i.order,
                        'caption': i.caption,
                        'icon': i.icon,
                        'url': i.url,
                        'pid': i.pid,
                        'remark': i.remark,
                        'display': i.display,
                        'level': 1
                    }
                    if i.caption == '平台概述':
                        each_data['active'] = True
                    else:
                        each_data['active'] = False
                    # 根据父节点查询子节点菜单，逐级查找
                    children_obj = SysMenu.objects.filter(pid=i.id).all().order_by('order')
                    children_list = []
                    if children_obj:
                        for j in children_obj:
                            value = get_children_data(j)
                            value['level'] = 2
                            grand_children_obj = SysMenu.objects.filter(pid=j.id).all().order_by('order')
                            grand_children_list = []
                            for k in grand_children_obj:
                                grand_value = get_children_data(k)
                                grand_value['disabled'] = True
                                grand_value['level'] = 3
                                grand_value['ppid'] = SysMenu.objects.filter(
                                    id=SysMenu.objects.filter(id=grand_value['pid']).first().pid).first().id
                                grand_children_list.append(grand_value)
                            value['children'] = grand_children_list
                            children_list.append(value)
                        each_data['children'] = children_list

                    data[0]["children"].append(each_data)
                    form_data.append(each_data)

                response_data['data'] = data
                response_data['form_data'] = form_data
                response_data['new_data'] = nav_menus
                response_data['code'] = 0
                return JsonResponse(response_data)
        except Exception as e:
            transaction.set_rollback(True)
            logger.error(f"获取菜单信息失败：{e}")
            return JsonResponse({"code": 401, 'msg': '获取菜单信息失败'})


def menu_list(request):
    """
    获取菜单列表（按目标格式改造）
    @param request:
    @return:
    """
    current_user = parse_jwt_token(request)
    if not current_user:
        return JsonResponse({"code": 405, 'msg': '请先登录'})

    role = current_user.role
    try:
        # 获取当前角色有权限的菜单ID
        role_menus = RoleMenu.objects.filter(role_id=role).values_list('menu_id', flat=True)
    except Exception as e:
        logger.error(e)
        # 异常时使用默认角色菜单
        role_menus = RoleMenu.objects.filter(role_id=1).values_list('menu_id', flat=True)
    role_menus = list(role_menus)  # 转换为列表便于后续判断

    # 获取所有有权限的菜单并构建ID映射（便于快速查找父节点和子节点）
    all_menus = SysMenu.objects.filter(id__in=role_menus, display=1).order_by('order')
    menu_map = {menu.id: menu for menu in all_menus}  # {id: menu_obj}

    def build_menu(menu_id, parent_id):
        """递归构建菜单结构"""
        menu = menu_map.get(menu_id)
        if not menu:
            return None

        # 基础字段映射
        menu_item = {
            "id": menu.id,  # 按示例格式拼接ID
            "enabled": 1,  # 默认为启用状态
            "caption": menu.caption,  # 菜单名称对应caption
            "description": menu.remark,
            "url": menu.url if menu.url else None,
            "internalPath": menu.url if menu.url else None,  # 内部路径同url
            "sequenceNumber": menu.order,  # 排序号对应order
            "parentId": parent_id,
            "isParent": has_children(menu.id),  # 是否有子菜单
            "checked": False,
            "icon": menu.icon if menu.icon else None,  # 图标对应icon字段
            "iconType": "3" if menu.icon else "1",  # 有图标则为3，否则为1
            "openMode": "currentTab",  # 默认为当前标签页打开
            "bearerToken": 1,
            "children": [],  # 子菜单列表（后续填充）
        }

        # 递归构建子菜单
        children = get_children(menu.id)
        for child_id in children:
            child_menu = build_menu(child_id, menu_item["id"])
            if child_menu:
                menu_item["children"].append(child_menu)

        # 无子菜单时置空children
        if not menu_item["children"]:
            menu_item["children"] = None

        return menu_item

    def has_children(menu_id):
        """判断菜单是否有子菜单"""
        return all_menus.filter(pid=menu_id).exists()

    def get_children(menu_id):
        """获取指定菜单的子菜单ID（按order排序）"""
        return [menu.id for menu in all_menus.filter(pid=menu_id).order_by('order')]

    # 构建根菜单（顶级菜单的parentId固定为示例中的根ID）
    root_parent_id = 0
    root_menus = [menu.id for menu in all_menus.filter(pid=0).order_by('order')]  # 顶级菜单（pid=0）
    result_data = []
    for root_id in root_menus:
        root_menu = build_menu(root_id, root_parent_id)
        if root_menu:
            result_data.append(root_menu)

    # 构建最终响应
    response = {
        "code": 0,
        "msg": "查询成功",
        "data": result_data
    }
    return JsonResponse(response, json_dumps_params={'ensure_ascii': False})


def map_info(request):
    """
    获取地图服务信息
    @param request:
    @return:
    """
    try:
        response_data = {'code': 0, 'msg': '', 'data': []}
        data = {}
        datasource_name = ''
        datasets_name = ''
        current_user = parse_jwt_token(request)
        county = current_user.county
        # county = '南京市(320100)'
        resource_obj = Resource.objects.filter(county=county, source_type='影像服务', is_show=1).first()
        if resource_obj:
            map_service = resource_obj.url
            center = resource_obj.center
            datasets_name = resource_obj.datasets_name
            datasource_name = resource_obj.datasource_name
            data['gis_service_type'] = resource_obj.gis_service_type
        else:
            map_service = ''
            center = []
        resource_obj2 = Resource.objects.filter(county=county, source_type='业务栅格数据服务').first()
        if resource_obj2:
            gengdi_service = resource_obj2.url
        else:
            gengdi_service = ''
        resource_obj3 = Resource.objects.filter(county=county, source_type='业务矢量数据服务',
                                                data_type='网格服务').first()
        if resource_obj3:
            grid_service = resource_obj3.url
            data['grid_datasource_name'] = resource_obj3.datasource_name
            data['grid_datasets_name'] = resource_obj3.datasets_name
        else:
            grid_service = ''
        related_resource = Resource.objects.filter(county=county, data_type='其他服务').values(
            'name', 'id', 'url', 'source_type', 'service_type', 'data_type', 'county', 'datasource_name',
            'datasets_name')

        data['grid_service'] = grid_service
        data['related_resource'] = list(related_resource)
        data['map_service'] = map_service
        data['gengdi_service'] = gengdi_service
        data['datasets_name'] = datasets_name

        data['datasource_name'] = datasource_name
        if isinstance(center, str):
            data['center'] = json.loads(center)
        else:
            data['center'] = center
        response_data['data'] = data
        return JsonResponse(response_data)
    except Exception as e:
        logger.error(f'获取地图服务信息失败{e}')
        return JsonResponse({'code': 500, 'msg': str(e), 'data': []})


@login_request
def role_operation(request):
    """
    角色增删改查操作
    @param request:
    @return:
    """
    with transaction.atomic():
        try:
            # 修改
            if request.method == "PUT":
                params = json.loads(request.body.decode('utf-8'))
                role_id = params.get('id', '')
                role_name = params.get('name', '')
                role_abbreviation = params.get('abbreviation', '')
                role_remark = params.get('remark', '')
                role_order = params.get('order', '')
                # 判断修改之后的数据名称是否重复
                counts = SysRole.objects.filter(name=role_name).exclude(id=role_id).count()
                if counts >= 1:
                    return warning('角色名称重复，新增失败！')
                SysRole.objects.filter(id=role_id).update(
                    name=role_name,
                    abbreviation=role_abbreviation,
                    remark=role_remark,
                    order=role_order
                )
                return ok('角色修改成功！')
            # 删除
            elif request.method == "DELETE":
                params = json.loads(request.body.decode('utf-8'))
                role_id = params.get('id')
                # 删除role关联的菜单
                RoleMenu.objects.filter(role_id=role_id).delete()
                # 用户表对应的角色置空
                user_obj = User.objects.filter(role=role_id).all()
                if user_obj:
                    for item in user_obj:
                        # 设置为无
                        item.role = 2
                        item.save()
                # 删除role
                SysRole.objects.filter(id=role_id).delete()
                return ok('角色删除成功！')
            # 增加
            elif request.method == "POST":
                try:
                    params = json.loads(request.body.decode('utf-8'))
                    role_name = params.get('name')  # 角色名
                    role_abbreviation = params.get('abbreviation')  # 缩写
                    role_remark = params.get('remark')  # 备注
                    role_order = params.get('order')  # 排序号
                    # 判断新增的角色名是否重复
                    in_name = SysRole.objects.filter(name=role_name).first()
                    if in_name:
                        return warning('新增角色名称重复，新增失败！')
                    SysRole.objects.create(
                        name=role_name,
                        abbreviation=role_abbreviation,
                        remark=role_remark,
                        order=role_order,
                    )
                    return ok('新增角色成功！')
                except Exception as e:
                    logger.error(e)
                    return error('新增角色失败！')
            # 查询
            elif request.method == "GET":
                role_name = request.GET.get('name')
                data = []
                if not role_name:
                    role_obj = SysRole.objects.all().order_by('order')
                else:
                    role_obj = SysRole.objects.filter(name__contains=role_name).all().order_by('order')
                if role_obj:
                    for item in role_obj:
                        each_data = {
                            'id': item.id,
                            'name': item.name,
                            'abbreviation': item.abbreviation,
                            'remark': item.remark,
                            'order': item.order,
                        }
                        data.append(each_data)
                    return ok_data(data)
                else:
                    return warning('无角色数据！')
        except Exception as e:
            logger.error('角色增删改查操作失败！' + str(e))


@login_request
def get_logs(request):
    """
   获取日志信息 | 模糊查询
   :param request:
   :return:
   """
    try:
        params = json.loads(request.body.decode('utf-8'))
        keyword = params.get('name')
        log_type = params.get('type')
        page = params.get("page", '')
        limit = params.get("limit", '')
        response_data = {}
        response_data['code'] = 201
        response_data['msg'] = ''
        data = []
        # 查询条件判断
        if not keyword and not log_type:
            logs_obj = SysLog.objects.all().order_by("-id")
        elif keyword and not log_type:
            logs_obj = SysLog.objects.filter(name=keyword).all().order_by("-id")
        elif not keyword and log_type:
            logs_obj = SysLog.objects.filter(type=log_type).all().order_by("-id")
        else:
            logs_obj = SysLog.objects.filter(name=keyword, type=log_type).all().order_by("-id")
        paginator = Paginator(logs_obj, limit)
        results = paginator.page(page)
        if results:
            for result in results:
                record = {
                    "id": result.id,
                    "account": result.account,
                    "name": result.name,
                    "desc": result.desc,
                    "addr": "本地局域网",
                    "type": result.type,
                    'append_time': result.append_time.strftime('%Y-%m-%d %H:%M:%S'),
                    "content": result.content,
                    'ip': result.ip
                }
                data.append(record)
            response_data['count'] = len(logs_obj)
            response_data['data'] = data
        return JsonResponse(response_data)
    except Exception as e:
        logger.error(f'获取日志信息失败{e}')
        return JsonResponse({'code': 500, 'msg': '获取日志信息失败'})


def get_nest(request):
    """
   获取机巢信息 | 模糊查询
   :param request:
   :return:
   """
    try:
        params = json.loads(request.body.decode('utf-8'))
        keyword = params.get('name')
        page = params.get("page", '')
        limit = params.get("limit", '')
        response_data = {'code': 0, 'msg': '', 'data': []}
        data = []
        # 查询条件判断
        if not keyword:
            nest_obj = Nest.objects.all().order_by("-id")
        else:
            nest_obj = Nest.objects.filter(name=keyword).all().order_by("-id")
        paginator = Paginator(nest_obj, limit)
        results = paginator.page(page)
        if results:
            for result in results:
                record = {
                    "id": result.id,
                    'name': result.name,
                    'model': result.model,
                    'nestSn': result.nest_sn,
                    'planeModel': result.plane_model,
                    'planeSn': result.plane_sn,
                    'location': result.location,
                    'organization': result.organization,
                    'longitude': result.longitude,
                    'latitude': result.latitude,
                    'status': result.status,
                    'owner': result.owner,
                    'createDate': result.create_time.strftime('%Y-%m-%d %H:%M:%S'),
                }
                data.append(record)
            response_data['total'] = len(nest_obj)
            response_data['data'] = data
        return JsonResponse(response_data)
    except Exception as e:
        logger.error(f'获取机巢信息失败{e}')
        return JsonResponse({'code': 500, 'msg': '获取机巢信息失败'})


@login_request
def user_related(request):
    """
    角色id关联用户
    """
    with transaction.atomic():
        try:
            # 查询
            if request.method == 'GET':
                user_obj = User.objects.all()
                data = []
                if user_obj:
                    for item in user_obj:
                        each_data = {
                            'id': item.id,
                            'name': item.username,
                            'role_id': item.role,
                            'description': item.description,
                            'realname': item.username,
                        }
                        if item.role == '无':
                            each_data['role'] = '无'
                        else:
                            each_data['role'] = SysRole.objects.filter(id=item.role).first().name
                        data.append(each_data)
                    return ok_data(data)
                else:
                    return warning('无用户！')
            # 新增
            elif request.method == "POST":
                try:
                    params = json.loads(request.body.decode('utf-8'))
                    get_role_id = params.get('role_id')
                    user_id = params.get('user_id')

                    # 查询对应的用户并赋权
                    for item in user_id:
                        user_obj = User.objects.filter(id=int(item)).first()
                        user_obj.role = get_role_id
                        user_obj.save()
                    return ok('修改成功！')
                except Exception as e:
                    logger.error(e)
                    return error('修改失败！')
        except Exception as e:
            transaction.set_rollback(True)
            logger.error(f'角色id关联用户请求失败{e}')


@login_request
def menu_related(request):
    """
    角色关联菜单
    """

    # 查询
    if request.method == 'GET':
        response_data = {}
        form_data = []
        # 选中的树节点
        value = []
        role_id = request.GET.get('id')
        all_menus = SysMenu.objects.all()
        pids = list(set([menu.pid for menu in all_menus]))
        # 根据id选中的菜单
        role_menu = RoleMenu.objects.filter(role_id=role_id).all()
        if role_menu:
            for tmp in role_menu:
                if tmp.menu_id not in pids:
                    value.append(tmp.menu_id)
        response_data['value'] = value
        menu_obj = SysMenu.objects.filter(pid=0, display=1).all().order_by('order')
        for i in menu_obj:
            each_data = {
                'id': i.id,
                'order': i.order,
                'caption': i.caption,
                'icon': i.icon,
                'url': i.url,
                'pid': i.pid,
                'remark': i.remark,
                'display': i.display,
            }
            # 逐级查找，组织成树的形式
            children_obj = SysMenu.objects.filter(pid=i.id).all().order_by('order')
            if children_obj:
                children_list = []
                for j in children_obj:
                    value = get_children_data(j)
                    grand_children_obj = SysMenu.objects.filter(pid=j.id).all().order_by('order')
                    grand_children_list = []
                    for k in grand_children_obj:
                        grand_value = get_children_data(k)
                        grand_children_list.append(grand_value)
                    value['children'] = grand_children_list
                    children_list.append(value)
                each_data['children'] = children_list
            form_data.append(each_data)
        response_data['data'] = form_data
        response_data['code'] = 0
        return JsonResponse(response_data)
    # 修改
    elif request.method == "POST":

        params = json.loads(request.body.decode('utf-8'))
        role_id = params.get('role_id')
        menu_id = params.get('menu_id')
        # 获取角色下所有的菜单并删除
        role_obj = RoleMenu.objects.filter(role_id=role_id).all()
        role_obj.delete()
        for item in menu_id:
            RoleMenu.objects.create(
                menu_id=item,
                role_id=role_id
            )
        return ok('角色菜单关联成功！')


def temp_login(request):
    """
    接入scp单点登录
    """
    params = json.loads(request.body.decode('utf-8'))
    code = params.get('code')
    token_url = f"http://22.200.9.3/scp-account/oauth/token?grant_type=authorization_code&code={code}&redirect_uri=http://www.baidu.com&client_id=resUiClientId&client_secret=IyFxI6pCl8PNDE9Iwwll"
    res = requests.post(url=token_url).json()
    access_token = res['access_token']
    user_info_url = f"http://22.200.9.3/scp-account/rest/v1/users/current-user?access_token={access_token}"
    resp = requests.get(user_info_url).json()
    username = resp['username']
    is_superuser = int(resp['admin'])
    user_obj = User.objects.filter(username=username).first()
    # 判断用户是否存在，如果不存在就创建用户
    if not user_obj:
        user_obj = User.objects.create_user(resp['username'], '2@qq.com', '123456')
        user_obj.is_staff = True
        user_obj.is_active = True  # 新建用户默认“启用”状态
        user_obj.county = '连云港市(320700)'
        user_obj.role = 3
        user_obj.save()

    # 校验用户账密是否正确
    params = {'username': username, 'password': '123456'}
    ser = LoginSerializer(data=params)
    if ser.is_valid(raise_exception=False):
        username = ser.context.get('username')
        token = ser.context.get('token')
        create_log(request, username, username, "login", "登录了系统")
        request.session["user_id"] = ser.context.get('user_id')
        request.session["username"] = username
        request.session['role'] = ser.context.get('role')

        user_info = {
            "id": user_obj.id,
            'username': user_obj.username,
            'role': user_obj.role,
            'county': user_obj.county,
            'tokens': token
        }
        return JsonResponse({"data": user_info, 'code': 0, "msg": '获取成功'})
    return JsonResponse({"code": 1, "msg": '用户名或密码错误'})


def login_check(request):
    """
    登录校验
    """
    try:
        response_data = {}
        params = json.loads(request.body.decode('utf-8'))
        username = params.get('username')
        decrypt_password = decode_pwd(params.get('password'))
        params['password'] = decrypt_password
        ser = LoginSerializer(data=params)
        if ser.is_valid(raise_exception=False):
            username = ser.context.get('username')
            token = ser.context.get('token')
            create_log(request, username, username, "login", "登录了系统")
            request.session["user_id"] = ser.context.get('user_id')
            request.session["username"] = username
            request.session['role'] = ser.context.get('role')
            # request.session['county'] =  ser.context.county
            response_data['msg'] = '登录成功'
            response_data['role'] = ser.context.get('role')
            response_data['code'] = 0
            response_data['tokens'] = token
            return JsonResponse(response_data)
        else:
            response_data['msg'] = '用户名或者密码不正确'
            response_data['code'] = 401
            return JsonResponse(response_data)
        if params.get("token") is None:
            password_value = params.get('password')
            # 调用auth.authenticate()方法进行登录校验
            user_obj = auth.authenticate(username=username, password=password_value)
            if user_obj:
                create_log(request, user_obj.username, user_obj.username, "login", "登录了系统")
                # 校验成功，调用auth.login（request, user_obj）方法：
                auth.login(request, user_obj)

                request.session["user_id"] = user_obj.id
                request.session["user_name"] = user_obj.username
                response_data['msg'] = '登录成功'
                response_data['role_id'] = user_obj.role
                response_data['code'] = 0
                response_data['tokens'] = tokens_value
                print(f'{user_obj.username}登录成功,{tokens_value}')

                return JsonResponse(response_data, status=201)
            else:
                response_data['msg'] = '用户名或者密码不正确'
                response_data['code'] = 401
                return JsonResponse(response_data)
        # 其他系统跳转登录
        else:
            create_log(request, "跳转系统的用户：", username, "login", "登录了系统")
            request.session["user_id"] = -1
            request.session["user_name"] = username
            user_obj = auth.authenticate(username="admin", password="123456")
            auth.login(request, user_obj)
            # 更新信息
            request.session["user_id"] = user_obj.id
            request.session["user_name"] = user_obj.username
            response_data['msg'] = '登录成功'
            response_data['role_id'] = 3
            response_data['code'] = 0
            return JsonResponse(response_data, status=201)
    except Exception as e:
        logger.error(f'登录失败：{e}')
        return JsonResponse({'msg': '登录失败', 'code': 500}, status=500)


@login_request
def password(request):
    """
    修改密码
    @param request:
    @return:
    """
    old_password = request.POST.get('old_password')
    new_password = request.POST.get('new_password')
    username = request.POST.get('username')
    user = auth.authenticate(username=username, password=old_password)
    if user:
        create_log(request, user.username, user.username, "update", "修改了密码")
        user.set_password(new_password)  # 只是修改对象属性
        user.save()
        return ok('修改成功')
    else:
        logger.error('原密码不正确')
        return warning('原密码不正确')


def nest_delete(request):
    """
    删除机巢
    """
    params = json.loads(request.body.decode('utf-8'))
    nest_ids = params.get('nestIds')
    for nest_id in nest_ids:
        nest_obj = Nest.objects.get(id=nest_id)
        if nest_obj:
            nest_obj.delete()
    return ok('删除成功')


def nest_insert(request):
    try:
        current_user = parse_jwt_token(request)
        # 解析请求体中的 JSON 数据
        params = json.loads(request.body.decode('utf-8'))

        # 获取参数
        nest_name = params.get('name')  # 机巢名称
        nest_model = params.get('model')  # 机巢型号
        nest_sn = params.get('nestSn')  # 机巢SN
        plane_model = params.get('planeModel')  # 飞机型号
        plane_sn = params.get('planeSn')  # 飞机SN
        location = params.get('location')  # 机巢位置
        organization = params.get('organization')  # 所属单位
        longitude = params.get('longitude', 0)  # 经度，默认值为0
        latitude = params.get('latitude', 0)  # 纬度，默认值为0
        status = params.get('status', 1)  # 状态，默认值为1

        # 校验机巢SN是否重复
        existing_nest = Nest.objects.filter(nest_sn=nest_sn).first()
        if existing_nest:
            return warning('新增机巢失败，机巢SN已存在！')

        # 创建新的机巢记录
        Nest.objects.create(
            name=nest_name,
            model=nest_model,
            nest_sn=nest_sn,
            plane_model=plane_model,
            plane_sn=plane_sn,
            location=location,
            organization=organization,
            longitude=longitude,
            latitude=latitude,
            status=status,
            owner=current_user.username
        )

        return JsonResponse({'code': 0, 'msg': '新增机巢成功！'})

    except Exception as e:
        return error(f'新增机巢失败：{str(e)}')


NEST_IMPORT_HEADER_MAP = {
    '机巢名称': 'name',
    '机巢型号': 'model',
    '机巢SN': 'nest_sn',
    '飞机型号': 'plane_model',
    '飞机SN': 'plane_sn',
    '机巢位置': 'location',
    '所属单位': 'organization',
    '机巢经度': 'longitude',
    '机巢纬度': 'latitude',
}


def _normalize_nest_import_row(row):
    """将导入行数据清洗为 Nest 字段字典。"""
    def _to_str(value):
        if pd.isna(value):
            return ''
        return str(value).strip()

    def _to_float(value):
        text = _to_str(value)
        if not text:
            return 0.0
        return float(text)

    return {
        'name': _to_str(row.get('name')),
        'model': _to_str(row.get('model')),
        'nest_sn': _to_str(row.get('nest_sn')),
        'plane_model': _to_str(row.get('plane_model')),
        'plane_sn': _to_str(row.get('plane_sn')),
        'location': _to_str(row.get('location')),
        'organization': _to_str(row.get('organization')),
        'longitude': _to_float(row.get('longitude')),
        'latitude': _to_float(row.get('latitude')),
    }


def _is_nest_template_example(row_data):
    """跳过模板中的示例行。"""
    return (
        row_data['name'] == '示例机巢01'
        or row_data['nest_sn'] == 'NEST-SN-001'
    )


def _parse_nest_import_file(upload_file):
    """解析 CSV / Excel 导入文件，返回标准化后的行列表。"""
    filename = upload_file.name.lower()
    if filename.endswith('.csv'):
        df = pd.read_csv(upload_file, encoding='utf-8-sig', dtype=str)
    elif filename.endswith(('.xlsx', '.xls')):
        df = pd.read_excel(upload_file, dtype=str)
    else:
        raise ValueError('仅支持 CSV 或 Excel 文件')

    if df.empty:
        raise ValueError('导入文件为空')

    df.columns = [str(col).strip() for col in df.columns]
    rename_map = {col: NEST_IMPORT_HEADER_MAP[col] for col in df.columns if col in NEST_IMPORT_HEADER_MAP}
    if not rename_map:
        raise ValueError('文件表头不正确，请使用系统提供的导入模板')

    df = df.rename(columns=rename_map)
    rows = []
    for _, row in df.iterrows():
        rows.append(_normalize_nest_import_row(row))
    return rows


def nest_import(request):
    """
    批量导入机巢（CSV / Excel，FormData 字段名: file）
    """
    if request.method != 'POST':
        return JsonResponse({'code': 500, 'msg': '不支持的请求方式'})

    try:
        current_user = parse_jwt_token(request)
        upload_file = request.FILES.get('file')
        if not upload_file:
            return warning('请上传导入文件')

        rows = _parse_nest_import_file(upload_file)
        success_count = 0
        fail_list = []

        for index, row_data in enumerate(rows, start=2):
            if not any(row_data.values()):
                continue
            if _is_nest_template_example(row_data):
                continue
            if not row_data['name']:
                fail_list.append({'row': index, 'reason': '机巢名称不能为空'})
                continue
            if not row_data['nest_sn']:
                fail_list.append({'row': index, 'reason': '机巢SN不能为空'})
                continue
            if Nest.objects.filter(nest_sn=row_data['nest_sn']).exists():
                fail_list.append({'row': index, 'reason': f"机巢SN已存在: {row_data['nest_sn']}"})
                continue

            Nest.objects.create(
                name=row_data['name'],
                model=row_data['model'],
                nest_sn=row_data['nest_sn'],
                plane_model=row_data['plane_model'],
                plane_sn=row_data['plane_sn'],
                location=row_data['location'],
                organization=row_data['organization'],
                longitude=row_data['longitude'],
                latitude=row_data['latitude'],
                status=1,
                owner=current_user.username,
            )
            success_count += 1

        if success_count == 0 and fail_list:
            return JsonResponse({
                'code': 1,
                'msg': '导入失败，请检查文件内容',
                'data': {
                    'successCount': 0,
                    'failCount': len(fail_list),
                    'failList': fail_list,
                }
            })

        return JsonResponse({
            'code': 0,
            'msg': f'导入完成，成功 {success_count} 条',
            'data': {
                'successCount': success_count,
                'failCount': len(fail_list),
                'failList': fail_list,
            }
        })
    except ValueError as e:
        return warning(str(e))
    except Exception as e:
        logger.error(f'机巢导入失败: {e}')
        return error(f'机巢导入失败：{str(e)}')


def nest_info(request):
    # 获取所有唯一的机巢型号
    # 获取所有唯一的机巢型号并构造目标格式
    nest_models_list = [{'value': model} for model in Nest.objects.values_list('model', flat=True).distinct()]

    # 获取所有唯一的飞机型号并构造目标格式
    plane_models_list = [{'value': model} for model in Nest.objects.values_list('plane_model', flat=True).distinct()]

    # 获取所有唯一的飞机型号
    # 获取所有唯一的机巢型号并构造目标格式
    organization_list = [{'value': model} for model in Nest.objects.values_list('organization', flat=True).distinct()]

    return JsonResponse({'code': 0, "msg": "数据获取成功",
                         "data": {'nest_models': nest_models_list, 'plane_models': plane_models_list,
                                  'organization_list': organization_list}})


@login_request
def add_user(request):
    """
    创建新用户
    """
    with transaction.atomic():
        # 获取当前用户角色
        current_username = request.session['username']
        params = json.loads(request.body.decode('utf-8'))
        try:
            username = params.get("username")
            email = params.get('email', '1@qq.com')
            passwd = params.get("password")
            county = params.get("county")
            role = params.get("role", 2)
            user = User.objects.create_user(username, email, passwd)
            create_log(request, current_username, current_username, "add", "新增了用户《" + username + "》")
            user.is_staff = True
            user.is_active = True  # 新建用户默认“启用”状态
            user.county = county
            user.role = role
            user.save()
        except Exception as e:
            transaction.set_rollback(True)
            logger.error(f'用户创建失败{e}')
            return JsonResponse({"msg": "用户创建失败", "code": 400, 'status': False})
        return JsonResponse({"msg": "用户创建成功", "code": 0, 'status': True})


@login_request
def get_users(request):
    """
       获取用户列表信息 | 模糊查询
       :param request:
       :return:
    """
    try:
        params = json.loads(request.body.decode('utf-8'))
        keyword = params.get('query')
        page = params.get("page", 1)
        limit = params.get("limit", 5)
        response_data = {}
        response_data['code'] = 0
        response_data['msg'] = ''
        data = []
        if not keyword:
            results_obj = User.objects.all()
        else:
            results_obj = User.objects.filter(username__contains=keyword).all()
        paginator = Paginator(results_obj, limit)
        results = paginator.page(page)
        if results:
            for user in results:
                record = {
                    "id": user.id,
                    "username": user.username,
                    "description": user.description,
                    "role": SysRole.objects.filter(id=user.role).first().name,
                    'date_joined': user.date_joined.strftime('%Y-%m-%d %H:%m:%S'),
                    "desc": user.description,
                    "email": user.email,
                    'county': user.county,
                    "is_superuser": "是" if user.is_superuser else "否",
                    "is_active": "true" if user.is_active else "false",
                }
                data.append(record)
            response_data['count'] = len(results_obj)
            response_data['data'] = data
        return JsonResponse(response_data)
    except Exception as e:
        logger.error(f"获取用户列表失败: {str(e)}")
        return JsonResponse({"msg": "获取用户失败", "code": 400})


@login_request
def user_delete(request):
    """
    删除用户
    @param request:
    @return:
    """
    try:
        params = json.loads(request.body.decode('utf-8'))
        user_id = params.get('id')
        response_delete_data = {}
        user_obj = User.objects.filter(id=user_id).first()
        if user_obj:
            create_log(request, request.session['username'], request.session['username'], "delete",
                       "删除了用户《" + user_obj.username + "》")
            user_obj.delete()
            response_delete_data['msg'] = '删除成功！'
            response_delete_data['code'] = 0
        else:
            response_delete_data['msg'] = '用户删除失败，找不到id为{}的用户！'.format(user_id)
            response_delete_data['code'] = 400
        return JsonResponse(response_delete_data)
    except Exception as e:
        logger.error(f"删除用户失败: {str(e)}")
        return JsonResponse({"code": 500, "msg": "删除失败，当前用户存在绑定的数据！"})


@login_request
def user_role_relation(request):
    # 修改用户权限
    with transaction.atomic():
        try:
            params = json.loads(request.body.decode('utf-8'))
            user_id = params.get('user_id')
            role_id = params.get('role_id')
            response_post_data = {}
            user_obj = User.objects.filter(id=user_id).first()
            user_obj.role = role_id
            if role_id == 3:
                role = '管理员'
            else:
                role = '普通用户'
            create_log(request, request.session['username'], request.session['username'], "update",
                       "修改了用户《" + user_obj.username + "》的权限为" + role)

            user_obj.save()
            response_post_data['msg'] = '分配成功'
            response_post_data['code'] = 0
            return JsonResponse(response_post_data)
        except Exception as e:
            transaction.set_rollback(True)
            logger.error(f"分配用户权限失败: {str(e)}")


@login_request
def user_modify(request):
    """
    修改用户信息
    @param request:
    @return:
    """
    with transaction.atomic():
        try:
            params = json.loads(request.body.decode('utf-8'))
            user_id = params.get('id')
            username = params.get('username')
            email = params.get('email')
            county = params.get('county')
            role = params.get('role')
            new_password = params.get('password')
            user_obj = User.objects.get(id=user_id)
            if user_obj:
                user_obj.username = username
                user_obj.email = email
                user_obj.county = county
                user_obj.role = role
                # user_obj.set_password(new_password)  # 只是修改对象属性
                create_log(request, request.session['username'], request.session['username'], "update",
                           "修改了用户《" + user_obj.username + "》的信息")
                user_obj.save()

                response_data = {'msg': '修改成功！',
                                 'code': 0
                                 }
                return JsonResponse(response_data)
            return JsonResponse({'msg': '修改失败,用户不存在！', 'code': 1})
        except Exception as e:
            logger.error(f"修改用户信息失败: {str(e)}")
            return JsonResponse({'msg': '修改失败！', 'code': 1})


@login_request
def edit_status(request):
    """
    修改用户状态
    @param request:
    @return:
    """
    response_data = {}
    params = json.loads(request.body.decode('utf-8'))
    username = request.session['username']
    user_id = params.get('id')
    is_active = params.get('is_active')
    with transaction.atomic():
        try:
            user = User.objects.filter(id=user_id).first()
            if is_active == 'true':
                is_active = True
                create_log(request, username, username, "update",
                           "启用了用户《" + user.username + "》")
            else:
                is_active = False
                create_log(request, username, username, "update",
                           "禁用了用户《" + user.username + "》")

            user.is_active = is_active
            user.save()
            response_data['msg'] = '用户状态修改成功！'
            response_data['code'] = 0
        except Exception as e:
            response_data['msg'] = '用户状态修改失败！'
            response_data['code'] = 400
            transaction.set_rollback(True)
            logger.error(f'用户状态修改失败:{e}')
        return JsonResponse(response_data)


def getTimeData(data_list, sDateStr, eDateStr, separate):
    """
    :param data_list:数据库查询出的列表
    :param sDateStr:开始日期
    :param eDateStr:结束日期
    :param separate: 日期分隔，以日分隔，以月分割
    :return:
    """
    out_list = []
    # 格式化日期字符串
    dateStart = datetime.datetime.strptime(sDateStr, '%Y-%m-%d')
    dateEnd = datetime.datetime.strptime(eDateStr, '%Y-%m-%d')
    while dateStart < dateEnd:
        time_dic = {}
        if separate == 'day':
            dateStart += datetime.timedelta(days=1)
            time_dic['create_time'] = dateStart.strftime('%Y-%m-%d')
            time_dic['count'] = 0
        elif separate == 'month':
            dateStart += relativedelta(months=1)
            time_dic['create_time'] = dateStart.strftime('%Y-%m')
            time_dic['count'] = 0
        out_list.append(time_dic)

    for item in list(data_list):
        for week_item in out_list:
            if week_item['create_time'] == item['create_date']:
                week_item['count'] = item['count']

    # 直接以列表的形式存储
    output_dic = {}
    # 存储时间的列表
    output_time_list = []
    # 存储数量的列表
    output_count_list = []
    for item in out_list:
        create_time = item['create_time']
        count = item['count']
        output_time_list.append(create_time)
        output_count_list.append(count)
    output_dic['create_time'] = output_time_list
    output_dic['count'] = output_count_list
    return output_dic


class DateFormat(Func):
    function = 'TO_CHAR'
    template = "%(function)s(%(expressions)s, 'YYYY-MM-DD')"


class monthDateFormat(Func):
    function = 'TO_CHAR'
    template = "%(function)s(%(expressions)s, 'YYYY-MM')"


@login_request
def source_overview(request):
    """
    资源概览
    """
    # try:
    if 1 == 1:
        # 根据时间统计资源，并返回前端以柱状图形式展示
        data = {}
        # 获取当前时间
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        # 相对当前时间的前一周
        week_time = (datetime.datetime.now() + relativedelta(weeks=-1)).strftime("%Y-%m-%d")
        # 相对当前时间的前一月
        month_time = (datetime.datetime.now() + relativedelta(months=-1)).strftime("%Y-%m-%d")
        # 相对当前时间的前一年
        year_time = (datetime.datetime.now() + relativedelta(years=-1)).strftime("%Y-%m-%d")

        # 服务注册统计，分组统计一周资源数据
        week_data = Batch.objects.filter(create_time__gte=week_time).annotate(
            create_date=DateFormat(TruncDate('create_time'))
        ).values('create_date').annotate(count=Count('batch_id'))

        # 分组统计一个月资源数据
        month_data = Batch.objects.filter(create_time__gte=month_time).annotate(
            create_date=DateFormat(TruncDate('create_time'))
        ).values('create_date').annotate(count=Count('batch_id'))
        # 分组统计一年的资源数据
        year_data = Batch.objects.filter(create_time__gte=year_time).annotate(
            create_date=monthDateFormat(TruncDate('create_time'))
        ).values('create_date').annotate(count=Count('batch_id'))
        # 返回统计的周数据
        week_data_list = getTimeData(list(week_data), week_time, today, 'day')
        # 返回统计的月数据
        month_data_list = getTimeData(list(month_data), month_time, today, 'day')
        # 返回统计的年数据 如 [7, 8, 9, 10]
        year_data_list = getTimeData(list(year_data), year_time, today, 'month')
        data["week_data"] = week_data_list
        data["month_data"] = month_data_list
        data["year_data"] = year_data_list

        # 全景融合种类分布
        map_view_info = {}
        clue_type = Clue.objects.all().extra(
            select={'clue_name': "clue_name"}).values(
            'clue_name').annotate(
            count=Count("clue_id"))
        map_view_info["clue_type"] = list(clue_type)
        data['map_view_info'] = map_view_info

        # 目标检测种类分布
        report_count = {}
        report_scene_list = BatchReport.objects.all().extra(
            select={'scene_id': "scene_id"}).values(
            'scene_id').annotate(
            count=Count("id"))
        report_count["name"] = []
        report_count["count"] = []
        for i in report_scene_list:
            report_count["name"].append(Scene.objects.get(scene_id=i['scene_id']).scene_name)
            report_count["count"].append(i['count'])

        data['report_count'] = report_count

        # 近七日使用量
        service_usage_week_info = {}
        # 全景图，分组统计一周资源数据
        panorama_week_data = Batch.objects.filter(create_time__gte=week_time).annotate(
            create_date=monthDateFormat(TruncDate('create_time'))
        ).values('create_date').annotate(count=Count('batch_id'))
        # 返回统计的周数据
        panorama_week_data_list = getTimeData(list(panorama_week_data), week_time, today, 'day')
        # 记录数据
        service_usage_week_info[OperationOptions.PANORAMA.value] = panorama_week_data_list
        service_usage_week_info[OperationOptions.OBJECT_DETECTION.value] = week_data_list
        data['service_usage_week_info'] = service_usage_week_info
        task_type_list = {}
        data["task_data"] = task_type_list
        response_data = {
            "code": 0,
            "data": data,
            "msg": '获取数据成功'
        }
        return JsonResponse(response_data)
    # except Exception as e:
    #     logger.error("获取数据失败，错误信息为：%s" % str(e))
    #     response_data = {
    #         "code": 500,
    #         "data": [],
    #         "msg": '获取数据失败'
    #     }
    #     return JsonResponse(response_data)


def file_iterator(file_path, chunk_size=512):
    """
    文件生成器,防止文件过大，导致内存溢出
    :param file_path: 文件绝对路径
    :param chunk_size: 块大小
    :return: 生成器
    """
    try:
        with open(file_path, mode='rb') as f:
            while True:
                c = f.read(chunk_size)
                if c:
                    yield c
                else:
                    break
    except FileNotFoundError as e:
        print(e)


def logs_search(request):
    """
    日志查询
    :param request:
    :return:
    """
    tab_dic = {
        '航线规划': 'route_views.log',
        '运维中心': 'resource_views.log',
        "体验中心": 'experience_views.log',
        "全景融合": 'panorama_views.log',
        '线索推送': 'verify_views.log',
        "模型日志": 'model_views.log',
        "系统日志": 'file.log'
    }
    try:
        para = json.loads(request.body)
        search_type = para.get('search_type', '')
        tag = para.get('tag', 'view')
        if tab_dic[search_type]:
            if tag == 'view':
                logs_path = os.path.join(settings.BASE_DIR, 'logs', tab_dic[search_type])
                with open(logs_path, 'r', encoding='utf-8') as file:
                    lines = file.read()
                    logs_txt = lines.split('\n')
                    if len(logs_txt) >= 400:
                        logs_txt = logs_txt[len(logs_txt) - 400:]
                    else:
                        logs_txt = logs_txt
                    logs_txt = '\n'.join(logs_txt)
                return JsonResponse({'code': '0', 'msg': "查询成功", 'logs_txt': logs_txt})
            elif tag == 'download':
                file_path = os.path.join(settings.BASE_DIR, 'logs', tab_dic[search_type])
                try:
                    # 设置响应头
                    # StreamingHttpResponse将文件内容进行流式传输，数据量大可以用这个方法
                    response = StreamingHttpResponse(file_iterator(file_path))
                    # 以流的形式下载文件,这样可以实现任意格式的文件下载
                    response['Content-Type'] = 'application/octet-stream'
                    # Content-Disposition就是当用户想把请求所得的内容存为一个文件的时候提供一个默认的文件名
                    response['Content-Disposition'] = 'attachment;filename="{}"'.format(
                        escape_uri_path(tab_dic[search_type]))
                except FileNotFoundError as e:
                    print(e)
                    return HttpResponse("没有找到文件", status=404)
                return response
        else:
            return JsonResponse({'code': 500, 'msg': "未查询到对应模块日志"})
    except Exception as e:
        logger.error(f"未找到该模块对应日志：{e}")
        return JsonResponse({'code': 500, 'msg': "查询失败"})


def data_analysis(request):
    """
    统计分析页面数值统计
    @param request:
    @return:
    """
    today_min = datetime.datetime.combine(timezone.now().date(), datetime.datetime.min.time())
    today_max = datetime.datetime.combine(timezone.now().date(), datetime.datetime.max.time())
    day_count = Clue.objects.filter(create_time__range=(today_min, today_max)).count()
    day_closed_count = Clue.objects.filter(create_time__range=(today_min, today_max), status__in=[1, 4]).count()
    day_verified_count = Clue.objects.filter(create_time__range=(today_min, today_max), status__in=[2]).count()
    day_pending_rectification_count = Clue.objects.filter(create_time__range=(today_min, today_max),
                                                          status__in=[5]).count()
    day_rectified_count = Clue.objects.filter(create_time__range=(today_min, today_max), status__in=[6]).count()
    if day_pending_rectification_count == 0 and day_rectified_count == 0:
        day_percent = 0
    else:
        day_percent = day_rectified_count / (day_pending_rectification_count + day_rectified_count)
    day_value = {
        'day_count': day_count,
        'day_closed_count': day_closed_count,
        'day_verified_count': day_verified_count,
        'day_pending_rectification_count': day_pending_rectification_count,
        'day_rectified_count': day_rectified_count,
        'percent': day_percent
    }
    start_of_week = timezone.now().date() - datetime.timedelta(days=timezone.now().weekday())
    end_of_week = start_of_week + datetime.timedelta(days=6)
    week_start = datetime.datetime.combine(start_of_week, datetime.datetime.min.time())
    week_end = datetime.datetime.combine(end_of_week, datetime.datetime.max.time())
    week_count = Clue.objects.filter(create_time__range=(week_start, week_end)).count()
    week_closed_count = Clue.objects.filter(create_time__range=(today_min, today_max), status__in=[1, 4]).count()
    week_verified_count = Clue.objects.filter(create_time__range=(today_min, today_max), status__in=[2]).count()
    week_pending_rectification_count = Clue.objects.filter(create_time__range=(today_min, today_max),
                                                           status__in=[5]).count()
    week_rectified_count = Clue.objects.filter(create_time__range=(today_min, today_max), status__in=[6]).count()
    if week_rectified_count == 0 and week_pending_rectification_count == 0:
        week_percent = 0
    else:
        week_percent = week_rectified_count / (week_pending_rectification_count + week_rectified_count)
    week_value = {
        'week_count': week_count,
        'week_closed_count': week_closed_count,
        'week_verified_count': week_verified_count,
        'week_pending_rectification_count': week_pending_rectification_count,
        'week_rectified_count': week_rectified_count,
        'percent': week_percent
    }
    month_start = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    next_month = month_start.replace(month=month_start.month + 1) if month_start.month < 12 else month_start.replace(
        year=month_start.year + 1, month=1)
    month_count = Clue.objects.filter(create_time__gte=month_start, create_time__lt=next_month).count()
    month_closed_count = Clue.objects.filter(create_time__range=(today_min, today_max), status__in=[1, 4]).count()
    month_verified_count = Clue.objects.filter(create_time__range=(today_min, today_max), status__in=[2]).count()
    month_pending_rectification_count = Clue.objects.filter(create_time__range=(today_min, today_max),
                                                            status__in=[5]).count()
    month_rectified_count = Clue.objects.filter(create_time__range=(today_min, today_max), status__in=[6]).count()
    if month_rectified_count == 0 and month_pending_rectification_count == 0:
        month_percent = 0
    else:
        month_percent = month_rectified_count / (month_pending_rectification_count + month_rectified_count)
    month_value = {
        'month_count': month_count,
        'month_closed_count': month_closed_count,
        'month_verified_count': month_verified_count,
        'month_pending_rectification_count': month_pending_rectification_count,
        'month_rectified_count': month_rectified_count,
        'percent': month_percent,
    }
    year_start = timezone.now().replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    next_year = year_start.replace(year=year_start.year + 1)
    year_count = Clue.objects.filter(create_time__gte=year_start, create_time__lt=next_year).count()
    year_closed_count = Clue.objects.filter(create_time__range=(today_min, today_max), status__in=[1, 4]).count()
    year_verified_count = Clue.objects.filter(create_time__range=(today_min, today_max), status__in=[2]).count()
    year_pending_rectification_count = Clue.objects.filter(create_time__range=(today_min, today_max),
                                                           status__in=[5]).count()
    year_rectified_count = Clue.objects.filter(create_time__range=(today_min, today_max), status__in=[6]).count()
    if year_rectified_count == 0 and year_pending_rectification_count == 0:
        year_percent = 0
    else:
        year_percent = year_rectified_count / (year_pending_rectification_count + year_rectified_count)
    year_value = {
        'year_count': year_count,
        'year_closed_count': year_closed_count,
        'year_verified_count': year_verified_count,
        'year_pending_rectification_count': year_pending_rectification_count,
        'year_rectified_count': year_rectified_count,
        'percent': year_percent
    }
    data = {
        'day': day_value,
        'week': week_value,
        'month': month_value,
        'year': year_value,
    }
    response_data = {
        'code': 0,
        'msg': '数据获取成功',
        'data': data
    }
    # 使用方法

    return JsonResponse(response_data)


def statistics_illegal_clues(request):
    # 获取当前时间
    now = timezone.now()

    # 创建一个包含过去7个月（包括当前月）的日期列表
    months = []
    counts_fl = []
    counts_fn = []
    counts_wj = []
    for i in range(7):
        date = now - relativedelta(months=i)
        months.append(date.strftime('%Y-%m'))
    scene_obj = Scene.objects.filter(scene_name='耕地非粮化').first()
    labels = scene_obj.labels
    list_array = ast.literal_eval(labels)
    # 查询近七个月的数据，并按月分组统计
    monthly_new_clues_fl = Clue.objects.filter(clue_name__in=list_array).filter(
        create_time__gte=now - relativedelta(months=7)
    ).annotate(
        month=TruncMonth('create_time')
    ).values(
        'month'
    ).annotate(
        count=Count('clue_id')
    )
    # 转换查询结果为字典，方便查找
    clue_counts_dict = {item['month'].strftime('%Y-%m'): item['count'] for item in monthly_new_clues_fl}
    # 为每个月赋值，如果没有数据则设为0
    for month in months:
        counts_fl.append(clue_counts_dict.get(month, 0))

    scene_obj = Scene.objects.filter(scene_name='耕地非农化').first()
    labels = scene_obj.labels
    list_array = ast.literal_eval(labels)
    # 查询近七个月的数据，并按月分组统计
    monthly_new_clues_fn = Clue.objects.filter(clue_name__in=list_array).filter(
        create_time__gte=now - relativedelta(months=7)
    ).annotate(
        month=TruncMonth('create_time')
    ).values(
        'month'
    ).annotate(
        count=Count('clue_id')
    )
    # 转换查询结果为字典，方便查找
    clue_counts_dict = {item['month'].strftime('%Y-%m'): item['count'] for item in monthly_new_clues_fn}
    # 为每个月赋值，如果没有数据则设为0
    for month in months:
        counts_fn.append(clue_counts_dict.get(month, 0))

    scene_obj = Scene.objects.filter(scene_name='违规建房').first()
    labels = scene_obj.labels
    list_array = ast.literal_eval(labels)
    # 查询近七个月的数据，并按月分组统计
    monthly_new_clues_wg = Clue.objects.filter(clue_name__in=list_array).filter(
        create_time__gte=now - relativedelta(months=7)
    ).annotate(
        month=TruncMonth('create_time')
    ).values(
        'month'
    ).annotate(
        count=Count('clue_id')
    )
    # 转换查询结果为字典，方便查找
    clue_counts_dict = {item['month'].strftime('%Y-%m'): item['count'] for item in monthly_new_clues_wg}
    # 为每个月赋值，如果没有数据则设为0
    for month in months:
        counts_wj.append(clue_counts_dict.get(month, 0))
    # 反转列表以从最早到最近排序
    months.reverse()
    counts_fl.reverse()
    counts_fn.reverse()
    counts_wj.reverse()
    values = [{
        'name': '耕地非粮化', 'value': sum(counts_fl)},
        {'name': '耕地非农化', 'value': sum(counts_fn)},
        {'name': '违规建房', 'value': sum(counts_wj),
         }]
    return JsonResponse({'code': 0, 'data': {
        'months': months,
        'counts_fl': counts_fl,
        'counts_fn': counts_fn,
        'counts_wj': counts_wj,
        'values': values
    }})


def clue_confirmed(request):
    """
    获取核实后线索数据
    @param request:
    @return:
    """
    params = json.loads(request.body.decode('utf-8'))
    page = params.get("page", 1)
    limit = params.get("limit", 8)
    village = params.get('village')
    keyword = params.get('keyword')
    clue_list = Clue.objects.filter(status__in=[5, 6], address__contains=village, clue_name__contains=keyword).all()
    paginator = Paginator(clue_list, limit)
    results = paginator.page(page)
    data_list = []
    for clue_obj in results:
        records = {
            'clue_id': clue_obj.clue_id,
            'task_id': clue_obj.panorama_image_id,
            'center_x': clue_obj.center_x,
            'center_y': clue_obj.center_y,
            'longitude': clue_obj.longitude,
            'latitude': clue_obj.latitude,
            'label': clue_obj.clue_name,
            'position': clue_obj.position,
            'score': clue_obj.score,
            'yaw_degree': clue_obj.panorama_image.yaw_degree,
            'batch_id': clue_obj.batch_id,
            'panorama_image_lat': clue_obj.panorama_image.latitude,
            'panorama_image_lon': clue_obj.panorama_image.longitude,
            'verification_conclusion': clue_obj.verification_conclusion,
            'address': clue_obj.address,
            'status': clue_obj.status,
            'create_time': clue_obj.create_time.strftime('%Y-%m-%d %H:%M:%S'),
        }
        data_list.append(records)

    response_data = {
        'code': 0,
        'msg': '',
        'data': data_list,
        'count': len(clue_list)
    }
    return JsonResponse(response_data)


def village_list(request):
    """
    展示中心
    @param request:
    @return:
    """
    region_data = []
    query_list = Clue.objects.filter(address__isnull=False).values('address').annotate(count=Count('clue_id'))
    for i in query_list:
        region_data.append(i['address'])

    category_data = []
    query_list = Clue.objects.filter(clue_name__isnull=False).values('clue_name').annotate(count=Count('clue_id'))
    for i in query_list:
        category_data.append(i['clue_name'])
    response_data = {
        'code': 0,
        'msg': '',
        'data': {'category_data': category_data, 'region_data': region_data},
    }
    return JsonResponse(response_data)


def nest_modify(request):
    """
    机巢修改
    :param request:
    :return:
    """
    try:
        # 解析请求体中的 JSON 数据
        params = json.loads(request.body.decode('utf-8'))

        # 获取参数
        id = params.get('id')  # 机巢ID
        nest_name = params.get('name')  # 机巢名称
        nest_model = params.get('model')  # 机巢型号
        nest_sn = params.get('nest_sn')  # 机巢SN
        plane_model = params.get('plane_model')  # 飞机型号
        plane_sn = params.get('plane_sn')  # 飞机SN
        location = params.get('location')  # 机巢位置
        organization = params.get('organization')  # 所属单位
        longitude = params.get('longitude', 0)  # 经度，默认值为0
        latitude = params.get('latitude', 0)  # 纬度，默认值为0

        # 校验机巢SN是否重复
        existing_nest = Nest.objects.filter(id=id).first()
        if not existing_nest:
            return JsonResponse({'code': 500, 'msg': '修改机巢失败，未查询到机巢信息！！'})
        if existing_nest.nest_sn != nest_sn:
            if Nest.objects.filter(nest_sn=nest_sn).exists():
                return JsonResponse({'code': 500, 'msg': '修改机巢失败，机巢SN已存在！'})

        # 更新机巢信息
        existing_nest.name = nest_name
        existing_nest.model = nest_model
        existing_nest.nest_sn = nest_sn
        existing_nest.plane_model = plane_model
        existing_nest.plane_sn = plane_sn
        existing_nest.location = location
        existing_nest.organization = organization
        existing_nest.longitude = longitude
        existing_nest.latitude = latitude
        existing_nest.save()
        return JsonResponse({'code': 0, 'msg': '修改机巢成功！'})

    except Exception as e:
        return error(f'修改机巢失败：{str(e)}')


def get_current_user(request):
    """
    获取当前用户信息
    """

    current_user = parse_jwt_token(request)
    if current_user:
        user_info = {
            "id": current_user.id,
            'username': current_user.username,
            'role': current_user.role,
            'county': current_user.county,
        }
        return JsonResponse({"data": user_info, 'code': 0, "msg": '获取成功'})
    else:
        return JsonResponse({"code": 500, "data": [], "msg": "当前用户未登录！"})


def multivariate_data(request):
    response_data = {
        "code": 0,
        "msg": 'null',
        "data": {
            "flight": [
                {
                    "label": "M4E",
                    "value": "M4E"
                },
                {
                    'label': 'M300 RTK',
                    'value': 'M300 RTK'
                },
                {
                    'label': 'M350 RTK',
                    'value': 'M350 RTK'
                },
                {
                    'label': 'M3E',
                    'value': 'M3E'
                },
                {
                    'label': 'M600 Pro',
                    'value': 'M600 Pro'
                },
                {
                    'label':'P4R',
                    'value':'P4R'
                }
            ],
            "organization": [
                {
                    "label": "1",
                    "value": "1"
                },
                {
                    "label": "2",
                    "value": "2"
                }
            ]
        }
    }
    return JsonResponse(response_data)


def query_task(request):
    """根据 batch_id 查询任务是否存在，供 AI 助手调用"""
    if request.method == 'OPTIONS':
        resp = HttpResponse()
        resp['Access-Control-Allow-Origin'] = request.headers.get('Origin', '*')
        resp['Access-Control-Allow-Credentials'] = 'false'
        resp['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        resp['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return resp

    def _cors(resp):
        origin = request.headers.get('Origin', '*')
        resp['Access-Control-Allow-Origin'] = origin
        resp['Access-Control-Allow-Credentials'] = 'false'
        return resp

    try:
        params = json.loads(request.body.decode('utf-8'))
        task_id = params.get('task_id', '').strip()
        if not task_id:
            return _cors(JsonResponse({'code': 0, 'found': False, 'msg': '请输入任务编号'}))
        batch = Batch.objects.filter(batch_id=task_id).first()
        if batch:
            return _cors(JsonResponse({
                'code': 0,
                'found': True,
                'data': {
                    'batch_id': batch.batch_id,
                    'batch_name': batch.batch_name,
                    'status': batch.status,
                    'region': batch.region or '',
                    'start_date': str(batch.start_date) if batch.start_date else '',
                    'end_date': str(batch.end_date) if batch.end_date else '',
                }
            }))
        return _cors(JsonResponse({'code': 0, 'found': False, 'msg': f'未查询到任务编号为 {task_id} 的任务'}))
    except Exception as e:
        return _cors(JsonResponse({'code': 1, 'found': False, 'msg': str(e)}))


def get_regions(request):
    """
    获取行政区划列表 | 支持模糊查询（名称/代码）和分页
    :param request: GET请求，参数包含query(可选)、page(可选)、limit(可选)
    :return: JsonResponse
    """
    try:
        # GET请求从query_params获取参数
        params = json.loads(request.body.decode('utf-8'))
        keyword = params.get('query', '')
        page = int(params.get('page', 1))
        limit = int(params.get('limit', 10))
        response_data = {
            'code': 0,
            'msg': '',
            'data': [],
            'total': 0
        }

        # 基础查询集
        queryset = Region.objects.all()

        # 模糊查询（名称或代码包含关键词）
        if keyword:
            queryset = queryset.filter(
                models.Q(region_name__contains=keyword) |
                models.Q(region_code__contains=keyword)
            )

        # 分页处理
        paginator = Paginator(queryset, limit)
        results = paginator.page(page)

        # 构建返回数据
        for region in results:
            data_item = {
                'region_id': region.region_id,
                'region_name': region.region_name,
                'region_level': region.region_level,
                'region_code': region.region_code,
                'parent_id': region.parent_id,
                'parent_name': region.parent_name,
                'parent_code': region.parent_code,
                'longitude': region.longitude,
                'latitude': region.latitude,
                'create_time': region.create_time.strftime('%Y-%m-%d %H:%M:%S') if region.create_time else ''
            }
            response_data['data'].append(data_item)

        # 总条数
        response_data['total'] = paginator.count
        return JsonResponse(response_data)

    except Exception as e:
        logger.error(f"获取行政区划列表失败: {str(e)}")
        return JsonResponse({"code": 400, "msg": f"获取失败: {str(e)}"})


def add_region(request):
    """
    新增行政区划
    :param request: POST请求，body包含行政区划信息
    :return: JsonResponse
    """
    try:
        # 解析POST请求体
        params = json.loads(request.body.decode('utf-8'))

        # 验证必填字段
        required_fields = ['region_name', 'region_level', 'region_code']
        for field in required_fields:
            if field not in params or not params[field]:
                return JsonResponse({"code": 400, "msg": f"缺少必填字段: {field}"})

        # 创建新记录
        new_region = Region(
            region_name=params['region_name'],
            region_level=params['region_level'],
            region_code=params['region_code'],
            parent_id=params.get('parent_id', 0),
            parent_name=params.get('parent_name', ''),
            parent_code=params.get('parent_code', ''),
            longitude=params.get('longitude', 0.0),
            latitude=params.get('latitude', 0.0)
        )
        new_region.save()

        # 返回创建的记录
        return JsonResponse({
            "code": 0,
            "msg": "新增成功",
            "data": {
                "region_id": new_region.region_id,
                "region_name": new_region.region_name
            }
        })

    except Exception as e:
        logger.error(f"新增行政区划失败: {str(e)}")
        return JsonResponse({"code": 400, "msg": f"新增失败: {str(e)}"})


def update_region(request):
    """
    更新行政区划信息
    :param request: PUT请求，body包含region_id和需要更新的字段
    :return: JsonResponse
    """
    try:
        params = json.loads(request.body.decode('utf-8'))

        # 验证region_id是否存在
        region_id = params.get('region_id')
        if not region_id:
            return JsonResponse({"code": 400, "msg": "缺少region_id"})

        # 查询要更新的记录
        try:
            region = Region.objects.get(region_id=region_id)
        except Region.DoesNotExist:
            return JsonResponse({"code": 400, "msg": "行政区划不存在"})

        # 更新字段（只更新提供的字段）
        update_fields = ['region_name', 'region_level', 'region_code',
                         'parent_id', 'parent_name', 'parent_code',
                         'longitude', 'latitude']
        for field in update_fields:
            if field in params:
                setattr(region, field, params[field])

        region.save()

        return JsonResponse({
            "code": 0,
            "msg": "更新成功",
            "data": {"region_id": region.region_id}
        })

    except Exception as e:
        logger.error(f"更新行政区划失败: {str(e)}")
        return JsonResponse({"code": 400, "msg": f"更新失败: {str(e)}"})


def delete_region(request):
    """
    删除行政区划
    :param request: DELETE请求，body包含region_id
    :return: JsonResponse
    """
    try:
        params = json.loads(request.body.decode('utf-8'))
        region_id = params.get('region_id')

        if not region_id:
            return JsonResponse({"code": 400, "msg": "缺少region_id"})

        # 检查是否存在
        try:
            region = Region.objects.get(region_id=region_id)
        except Region.DoesNotExist:
            return JsonResponse({"code": 400, "msg": "行政区划不存在"})

        # 执行删除
        region.delete()

        return JsonResponse({
            "code": 0,
            "msg": "删除成功"
        })

    except Exception as e:
        logger.error(f"删除行政区划失败: {str(e)}")
        return JsonResponse({"code": 400, "msg": f"删除失败: {str(e)}"})


def get_region_parents(request):
    """
    根据父级层级获取行政区
    Args:
        request:

    Returns:

    """
    response_data = {'code': 0, 'msg': "获取成功", 'data': []}
    region_level = int(request.GET.get('region_level', 2))
    if region_level:
        results = Region.objects.filter(region_level=region_level - 1).all()
    else:
        results = Region.objects.filter(region_level__in=[0, 1, 2, 3, 4]).all()
    for region in results:
        data_item = {
            'region_id': region.region_id,
            'region_name': region.region_name,
            'region_level': region.region_level,
            'region_code': region.region_code,
            'parent_id': region.parent_id,
            'parent_name': region.parent_name,
            'parent_code': region.parent_code,
            'longitude': region.longitude,
            'latitude': region.latitude,
            'create_time': region.create_time.strftime('%Y-%m-%d %H:%M:%S') if region.create_time else ''
        }
        response_data['data'].append(data_item)
    return JsonResponse(response_data)


def proxy_region_tree_by_user(request):
    """代理 resource.region_data，兼容 wuxi 前端 /api/system/region/ 路径"""
    from apps.resource.views import region_data
    return region_data(request)


def proxy_region_info_list(request):
    """返回所有行政区列表（用于注册等场景）"""
    response_data = {'code': 0, 'msg': "获取成功", 'data': []}
    results = Region.objects.all().order_by('-region_level')
    for region in results:
        response_data['data'].append({
            'region_id': region.region_id,
            'region_name': region.region_name,
            'region_level': region.region_level,
            'region_code': region.region_code,
            'parent_id': region.parent_id,
            'parent_name': region.parent_name,
            'parent_code': region.parent_code,
            'longitude': region.longitude,
            'latitude': region.latitude,
        })
    return JsonResponse(response_data)


# ============================================================
# AI Chat — LangGraph + DeepSeek
# ============================================================

from langgraph.graph import StateGraph, START, END
from typing_extensions import TypedDict
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, ToolMessage
from langchain_openai import ChatOpenAI


def _get_llm(tools=None, model=None, temperature=None, max_tokens=None):
    config = configparser.ConfigParser()
    config.read(os.path.join(settings.BASE_DIR, 'config.ini'), encoding='utf-8')
    api_key = config.get('deepseek', 'api_key')
    api_url = config.get('deepseek', 'api_url')
    # 优先用前端传入的参数，未传则 fallback 到 config.ini 或默认值
    model = model or config.get('deepseek', 'model')
    temperature = temperature if temperature is not None else 0.7
    max_tokens = max_tokens if max_tokens is not None else 4096
    llm = ChatOpenAI(
        api_key=api_key, base_url=api_url, model=model,
        temperature=temperature, max_tokens=max_tokens,
    )
    if tools:
        llm = llm.bind_tools(tools, tool_choice='auto')
    return llm


SYSTEM_PROMPT = (
    '你是金陵阡陌系统（SkyEye）的 AI 智能助手，具备无人机巡检、全景图分析、'
    '目标检测、航线规划、GIS 遥感等领域的专业知识。\n\n'
    '【核心规则 — 工具冲突裁决】\n'
    '当用户的一句话同时可能触发 navigate_page 和 query_data 时，按以下优先级裁决：\n'
    '1. 如果用户提到"数据"、"统计"、"概览"、"汇总"、"有多少"、"状态"、"列表"、"明细"等数据词汇 → 用 query_data\n'
    '2. "当前页面" / "这个页面" 开头的请求 → 用 query_data，不走 navigate_page\n'
    '3. 只有用户明确说出具体页面名称（如"一张图""全景检测""航线规划""报告管理"）时，才用 navigate_page\n'
    '4. 用户说"查看数据概览""打开统计页面"——"查看/打开"后面跟的是数据词汇 → query_data\n'
    '5. 用户说"打开全景检测""带我去航线规划"——"打开/带我去"后面跟的是具体页面 → navigate_page\n\n'
    '【工具选择规则 — 问题分类后对号入座】\n'
    '━━━ 页面跳转（navigate_page）━━━\n'
    '用户明确要打开/跳转/前往某个页面。仅限以下意图：\n'
    '  "项目管理" → /task-mgmt/verify-clue\n'
    '  "一张图" → /data-management/one-map\n'
    '  "影像管理" → /data-management/table\n'
    '  "航线规划"（泛指）→ /route-planning/manual-planning\n'
    '  "全景规划" → /route-planning/panoramicpoint-planning\n'
    '  "算法规划" → /route-planning/algorithm-planning\n'
    '  "地图总览" → /panoramic-detection/map-view\n'
    '  "范围管理/网格管理" → /panoramic-detection/grid-management\n'
    '  "批次管理" → /panoramic-detection/task-management\n'
    '  "全景检测" → /panoramic-detection/main-detection\n'
    '  "不检测区域" → /panoramic-detection/frame-area\n'
    '  "全景变化" → /panoramic-detection/panorama-change-detection\n'
    '  "场景管理" → /panoramic-detection/scene\n'
    '  "线索总览" → /panoramic-detection/clue-view\n'
    '  "临时批次" → /panoramic-detection/main-detection-temp\n'
    '  "报告管理" → /panoramic-detection/report\n'
    '  "图斑核实/核实任务" → /pattern-verifiy/task_management\n'
    ' 注意：用户问数据/统计/数量/列表时，不属于此类，用 query_data。\n\n'
    '━━━ 地图定位（map_action）━━━\n'
    '用户明确要求在地图上查看/定位/展示某个具体地点。\n'
    '排除项："防尘网""线索""图斑""批次""全景图"等业务术语不是地点，不要调用。\n\n'
    '━━━ 任务校验（lookup_task）━━━\n'
    '用户提供了明确的批次/任务编号（如 LS320...）并要求查状态。仅编号前缀模糊时不调用。\n\n'
    '━━━ 数据查询（query_data）━━━\n'
    '用户要获取系统里的实际数据。调用场景包括但不限于：\n'
    '  - 数量统计："有多少全景图""鼓楼区几个批次""线索状态分布"\n'
    '  - 列表/明细："有哪些高风险项""列出异常线索""鼓楼区全部批次"\n'
    '  - 条件筛选："本周新增的线索""待核实的图斑""score>7 的"\n'
    '  - 概览/摘要：当前页面数据概况\n'
    '支持的数据类型：全景图、线索、图斑、图斑任务、批次、网格、航线、资源、AI模型、\n'
    '  信息解读任务、多源任务、报告、核实任务、核实线索、飞行订单、场景。\n\n'
    '━━━ 未知/模糊（凭你判断）━━━\n'
    '以上四类都不匹配时：能直接回答就回答，需要确认的就反问用户，不要强行调用工具。\n\n'
    '【回复格式】\n'
    '纯文字回复时，正文后附加 |||，然后给出 3 个用户可能追问的问题，每行一个，不要编号。\n'
    '用中文回答，风格灵活自然。'
)


QUERY_SCHEMA = {
    'panorama_image': {
        'display': '全景图',
        'model': ('panorama', 'PanoramaImage'),
        'desc': '全景图像数据，包含拍摄位置、状态、所属批次、采集点等信息',
        'fields': {
            'status': {'type': 'int'},
            'batch_id': {'type': 'str', 'desc': '所属批次ID'},
            'upload_batch_id': {'type': 'str', 'desc': '上传批次ID'},
            'point_id': {'type': 'str', 'desc': '采集点ID'},
            'longitude': {'type': 'float'},
            'latitude': {'type': 'float'},
            'count': {'type': 'int', 'desc': '关联数量'},
        },
    },
    'clue': {
        'display': '线索',
        'model': ('panorama', 'Clue'),
        'desc': '问题线索，关联批次和全景图，包含经纬度、地址、状态、评分等',
        'fields': {
            'status': {'type': 'int', 'choices': {0: '待核实', 1: '已核实', 2: '已派发', 3: '已处置', 4: '已验收', 5: '已关闭'}},
            'address': {'type': 'str'},
            'position': {'type': 'str'},
            'score': {'type': 'float'},
            'batch_id': {'type': 'str', 'desc': '所属批次ID'},
            'panorama_image_id': {'type': 'str', 'desc': '所属全景图ID'},
            'inspector_id': {'type': 'str', 'desc': '核查员ID'},
            'longitude': {'type': 'float'},
            'latitude': {'type': 'float'},
            'is_new_clue': {'type': 'int'},
            'clue_source': {'type': 'str'},
        },
    },
    'polygon_data': {
        'display': '图斑',
        'model': ('panorama', 'PolygonData'),
        'desc': '图斑多边形数据，关联图斑任务，包含名称、状态、核实结论等',
        'fields': {
            'status': {'type': 'int'},
            'verify_conclusion': {'type': 'str'},
            'unit_name': {'type': 'str'},
            'name': {'type': 'str'},
            'polygon_task_id': {'type': 'str', 'desc': '所属图斑任务ID'},
        },
    },
    'polygon_task': {
        'display': '图斑任务',
        'model': ('panorama', 'PolygonTask'),
        'desc': '图斑核实任务，关联核查员',
        'fields': {
            'status': {'type': 'str'},
            'street': {'type': 'str'},
            'task_type': {'type': 'str'},
            'verifier_id': {'type': 'str', 'desc': '核查员ID'},
            'task_id': {'type': 'str'},
            'need_verify': {'type': 'int'},
            'verified': {'type': 'int'},
        },
    },
    'batch': {
        'display': '批次',
        'model': ('panorama', 'Batch'),
        'desc': '全景检测批次，关联网格，包含时间段、状态、类型等',
        'fields': {
            'status': {'type': 'int', 'choices': {0: '草稿', 1: '运行中', 2: '暂停', 3: '已完成'}},
            'batch_type': {'type': 'str'},
            'year': {'type': 'int'},
            'month': {'type': 'int'},
            'region': {'type': 'str'},
            'grid_id': {'type': 'str', 'desc': '所属网格ID'},
            'street': {'type': 'str'},
            'count': {'type': 'int', 'desc': '全景图数量'},
            'operator': {'type': 'str'},
        },
    },
    'grid': {
        'display': '网格',
        'model': ('panorama', 'Grid'),
        'desc': '地理网格划分，包含街道、区县、操作员',
        'fields': {
            'county': {'type': 'str'},
            'street': {'type': 'str'},
            'grid_operator_id': {'type': 'str', 'desc': '网格员ID'},
            'uploader_id': {'type': 'str', 'desc': '上传者ID'},
            'count': {'type': 'int', 'desc': '关联数量'},
        },
    },
    'route': {
        'display': '航线',
        'model': ('panorama', 'Route'),
        'desc': '飞行航线，包含类型、状态、高度、起终点',
        'fields': {
            'route_type': {'type': 'str'},
            'status': {'type': 'int'},
            'name': {'type': 'str'},
            'height': {'type': 'float'},
            'start_point': {'type': 'str'},
            'end_point': {'type': 'str'},
        },
    },
    'resource': {
        'display': '资源',
        'model': ('panorama', 'Resource'),
        'desc': '地图资源服务，包含影像服务、矢量数据等',
        'fields': {
            'source_type': {'type': 'str'},
            'data_type': {'type': 'str'},
            'county': {'type': 'str'},
            'owner_id': {'type': 'str', 'desc': '所有者ID'},
            'name': {'type': 'str'},
        },
    },
    'model_ai': {
        'display': 'AI模型',
        'model': ('model', 'Models'),
        'desc': 'AI检测模型',
        'fields': {
            'framework': {'type': 'str'},
            'network': {'type': 'str'},
            'status': {'type': 'int'},
            'name': {'type': 'str'},
        },
    },
    'interpretation_task': {
        'display': '解译任务',
        'model': ('interpretation', 'InterpretationTask'),
        'desc': 'AI解译任务',
        'fields': {
            'status': {'type': 'str'},
            'task_type': {'type': 'str'},
            'county': {'type': 'str'},
            'name': {'type': 'str'},
        },
    },
    'multivariate_task': {
        'display': '多元任务',
        'model': ('resource', 'MultivariateTask'),
        'desc': '多元数据采集任务，关联无人机巢',
        'fields': {
            'task_type': {'type': 'str'},
            'collect_type': {'type': 'str'},
            'organization': {'type': 'str'},
            'nest_id': {'type': 'str', 'desc': '无人机巢ID'},
            'county': {'type': 'str'},
            'task_status': {'type': 'int'},
        },
    },
    'report': {
        'display': '报告',
        'model': ('report', 'Report'),
        'desc': '检测报告，关联批次报告',
        'fields': {
            'batch_report_id': {'type': 'str', 'desc': '批次报告ID'},
            'report_name': {'type': 'str'},
            'village': {'type': 'str'},
        },
    },
    'verify_task': {
        'display': '核实任务',
        'model': ('panorama', 'VerifyTask'),
        'desc': '图斑核实任务',
        'fields': {
            'status': {'type': 'str'},
            'task_name': {'type': 'str'},
        },
    },
    'verify_clue': {
        'display': '核实线索',
        'model': ('panorama', 'VerifyClue'),
        'desc': '待核实的线索数据，关联核实任务',
        'fields': {
            'level': {'type': 'str'},
            'status': {'type': 'str'},
            'address': {'type': 'str'},
            'task_id': {'type': 'str', 'desc': '所属核实任务ID'},
            'division_code': {'type': 'str'},
        },
    },
    'fly_order': {
        'display': '飞行指令',
        'model': ('panorama', 'FlyOrder'),
        'desc': '无人机飞行指令，关联航线',
        'fields': {
            'data_type': {'type': 'str'},
            'organization': {'type': 'str'},
            'status': {'type': 'str'},
            'county': {'type': 'str'},
            'route_id': {'type': 'str', 'desc': '所属航线ID'},
            'order_name': {'type': 'str'},
            'collect_type': {'type': 'str'},
        },
    },
    'scene': {
        'display': '场景',
        'model': ('panorama', 'Scene'),
        'desc': '检测场景分类，关联操作员',
        'fields': {
            'operator_id': {'type': 'str', 'desc': '操作员ID'},
            'scene_name': {'type': 'str'},
        },
    },
}


QUERY_PARSE_PROMPT = (
    '你是一个数据库查询解析器。根据用户的问题和给定的数据库表结构，'
    '输出一个 JSON 对象，包含要查询的模型、操作类型和过滤条件。\n\n'
    '可用的表和字段：\n{schemas}\n\n'
    '操作类型：count（总数）、filter_count（按条件过滤后计数）、group_count（按字段分组计数）\n'
    '过滤条件用 Django ORM 格式，例如：{{"status": 1}} 或 {{"address__contains": "鼓楼"}}\n'
    '分组用 group_field 字段指定。\n\n'
    '重要规则（按优先级）：\n'
    '1.【上下文优先】如果用户问题末尾附带了【上下文】，其中包含"用户已选中对象"和"字段映射"，'
    '且用户问"这个/当前/该/此"等指代词时，必须使用 filter_count，'
    '在 filters 中用字段映射指定的字段（如 batch_id）加上选中对象的值（如 LS32020000120260701）。\n'
    '2. 如果用户有明确筛选条件（如"状态为1"、"鼓楼区的"、"某个具体ID的"），用 filter_count\n'
    '3. 如果问分布（如"按状态分组"、"各类型有多少"），用 group_count\n'
    '4. 只有用户明确问全表总数、没有任何筛选条件、也没有上下文选中对象时，才用 count\n'
    '- model 必须是上面列出的 key 之一\n'
    '- filters 中的字段必须在对应表的 fields 里\n'
    '- 如果完全无法理解查询，返回 {{"error": "无法理解"}}\n\n'
    '用户问题：{query}\n'
    '请只输出 JSON，不要有其他文字。'
)


def _parse_query_via_llm(query: str) -> dict:
    """用 LLM 将自然语言查询解析为结构化参数"""
    schema_lines = []
    for key, info in QUERY_SCHEMA.items():
        parts = []
        for k, v in info['fields'].items():
            d = v.get('desc', '')
            parts.append(f'{k}({v["type"]}{" " + d if d else ""})')
        fields_str = ', '.join(parts)
        schema_lines.append(f'  {key}({info["display"]}): {info["desc"]} 字段=[{fields_str}]')
    schemas = '\n'.join(schema_lines)

    prompt = QUERY_PARSE_PROMPT.format(schemas=schemas, query=query)

    try:
        config = configparser.ConfigParser()
        config.read(os.path.join(settings.BASE_DIR, 'config.ini'), encoding='utf-8')
        api_key = config.get('deepseek', 'api_key')
        api_url = config.get('deepseek', 'api_url')
        model = config.get('deepseek', 'model')

        from langchain_core.messages import HumanMessage
        llm = ChatOpenAI(api_key=api_key, base_url=api_url, model=model, temperature=0, max_tokens=512)
        resp = llm.invoke([HumanMessage(content=prompt)])
        text = resp.content.strip()
        # Remove markdown code fences if present
        if text.startswith('```'):
            text = text.split('\n', 1)[-1]
            if text.endswith('```'):
                text = text[:-3]
        return json.loads(text)
    except Exception as e:
        logger = logging.getLogger('skyeye')
        logger.warning(f'query_data LLM 解析失败: {e}')
        return {'error': str(e)}


def _execute_query(params: dict) -> str:
    """安全执行 ORM 查询并返回结果文本"""
    model_key = params.get('model', '')
    if model_key not in QUERY_SCHEMA:
        return f'不支持的查询对象：{model_key}'

    schema = QUERY_SCHEMA[model_key]
    app_label, model_name = schema['model']
    try:
        model_cls = apps.get_model(app_label, model_name)
    except LookupError:
        return f'找不到模型：{app_label}.{model_name}'

    operation = params.get('operation', 'count')
    filters = params.get('filters', {})
    group_field = params.get('group_field')

    # 校验 filter 字段
    allowed_fields = set(schema.get('fields', {}).keys())
    safe_filters = {}
    for field, value in filters.items():
        # 支持 __contains, __gte 等 Django lookup
        base_field = field.split('__')[0]
        if base_field in allowed_fields:
            safe_filters[field] = value

    qs = model_cls.objects.all()
    if safe_filters:
        qs = qs.filter(**safe_filters)

    display = schema['display']

    if operation == 'count':
        cnt = qs.count()
        filter_desc = ''
        if safe_filters:
            parts = []
            for f, v in safe_filters.items():
                field_info = schema['fields'].get(f.split('__')[0], {})
                choices = field_info.get('choices', {})
                if choices and isinstance(v, int):
                    v = choices.get(v, str(v))
                parts.append(f'{f}={v}')
            filter_desc = '（筛选条件：' + '，'.join(parts) + '）'
        return f'当前共有 {cnt} 条{display}数据{filter_desc}。'

    elif operation == 'group_count':
        if group_field and group_field in allowed_fields:
            groups = qs.values(group_field).annotate(cnt=Count('id')).order_by('-cnt')
            lines = [f'{display}按 {group_field} 分布：']
            for g in groups[:20]:
                val = g[group_field] or '(空)'
                field_info = schema['fields'].get(group_field, {})
                choices = field_info.get('choices', {})
                if choices and isinstance(val, int):
                    val = choices.get(val, str(val))
                lines.append(f'  {val}: {g["cnt"]} 条')
            return '\n'.join(lines)
        else:
            return f'{display}不支持按 {group_field} 分组'

    elif operation == 'filter_count':
        cnt = qs.count()
        return _execute_query({**params, 'operation': 'count'})

    return f'不支持的操作类型：{operation}'


def _handle_query_data(args: dict, context: dict = None) -> dict:
    """处理 query_data 工具调用"""
    query = args.get('query', '')
    if not query:
        return {'_query_result': '请提供要查询的问题。'}

    logger = logging.getLogger('skyeye')
    logger.info(f'query_data 查询: {query}')

    # 注入上下文到查询解析，让 LLM 知道字段映射
    if context:
        ctx_hints = []
        sel = context.get('selected_info', '')
        if sel:
            ctx_hints.append(f'用户已选中对象：{sel}')
        field_map = context.get('field_map', '')
        if field_map:
            ctx_hints.append(f'字段映射：{field_map}')
        if ctx_hints:
            query = query + '\n【上下文】' + '；'.join(ctx_hints)

    params = _parse_query_via_llm(query)
    if 'error' in params:
        return {'_query_result': f'无法解析查询：「{query}」—— {params["error"]}'}

    result = _execute_query(params)
    return {'_query_result': result, '_query_params': params}


class ChatState(TypedDict):
    messages: list


def _raw_messages_to_lc(raw_messages):
    lc_msgs = []
    for m in raw_messages:
        role = m['role']
        content = m.get('content', '')
        if role == 'system':
            lc_msgs.append(SystemMessage(content=content))
        elif role == 'user':
            lc_msgs.append(HumanMessage(content=content))
        elif role == 'assistant':
            ai = AIMessage(content=content)
            if m.get('tool_calls'):
                ai.tool_calls = m['tool_calls']
            lc_msgs.append(ai)
        elif role == 'tool':
            lc_msgs.append(ToolMessage(
                content=content, tool_call_id=m.get('tool_call_id', ''),
            ))
    return lc_msgs


def _geocode_amap(address, city=''):
    """高德地理编码：地名 → 经纬度"""
    config = configparser.ConfigParser()
    config.read(os.path.join(settings.BASE_DIR, 'config.ini'), encoding='utf-8')
    api_key = config.get('amap', 'api_key')
    params = {'key': api_key, 'address': address, 'output': 'JSON'}
    if city:
        params['city'] = city
    try:
        resp = requests.get('https://restapi.amap.com/v3/geocode/geo', params=params, timeout=5)
        data = resp.json()
        if data.get('status') == '1' and data.get('geocodes'):
            loc = data['geocodes'][0]['location']
            lng, lat = loc.split(',')
            return {'lat': float(lat), 'lng': float(lng), 'address': data['geocodes'][0].get('formatted_address', address)}
    except Exception:
        pass
    return None


def _get_district_amap(keywords, city='', subdistrict=0):
    """高德行政区划查询（优先缓存，未命中则实时查询并缓存）"""
    from utils_tools.district_cache import query_district
    return query_district(keywords, city=city, use_cache=True)


def _lc_to_result(msg):
    result = {}
    if msg.content:
        result['content'] = msg.content
    if msg.tool_calls:
        # 归一化为 OpenAI 标准格式：{ id, type: 'function', function: { name, arguments } }
        normalized = []
        for tc in msg.tool_calls:
            if isinstance(tc, dict):
                # LangChain dict 格式 {name, args, id} → 转成 OpenAI 格式
                if 'function' in tc:
                    # 已是 OpenAI 格式
                    normalized.append(tc)
                else:
                    args = tc.get('args', {})
                    args_str = json.dumps(args, ensure_ascii=False) if isinstance(args, dict) else str(args or '')
                    normalized.append({
                        'id': tc.get('id', ''),
                        'type': 'function',
                        'function': {
                            'name': tc.get('name', ''),
                            'arguments': args_str,
                        },
                    })
            else:
                # Pydantic 对象
                args = getattr(tc, 'args', {})
                name = getattr(tc, 'name', '')
                tid = getattr(tc, 'id', '')
                args_str = json.dumps(args, ensure_ascii=False) if isinstance(args, dict) else str(args or '')
                normalized.append({
                    'id': tid,
                    'type': 'function',
                    'function': {
                        'name': name,
                        'arguments': args_str,
                    },
                })
        result['tool_calls'] = normalized
    result['finish_reason'] = 'tool_calls' if msg.tool_calls else 'stop'
    return result


def _sse_event(data):
    """格式化 SSE 事件"""
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


def _generate_sse(raw_messages, frontend_tools, request, chat_mode='chat', context=None, model=None, temperature=None, max_tokens=None):
    """SSE 生成器：按阶段流式返回事件"""
    try:
        has_system = any(m.get('role') == 'system' for m in raw_messages)
        if not has_system:
            prompt = SYSTEM_PROMPT
            if chat_mode == 'chat':
                prompt += (
                    '\n\n【当前模式：聊天模式】'
                    '\n你当前处于普通聊天模式，不具备数据查询（query_data）能力。'
                    '\n如果用户询问数据统计/数量/分布等问题（如"有多少全景图""线索数据有多少条"等），'
                    '\n请友好告知："当前处于聊天模式，如需查询系统数据，请点击侧边栏星星按钮切换到数据查询模式。"'
                    '\n如果用户要求跳转页面、地图定位或查询任务编号，正常使用对应工具即可。'
                )
            if context and chat_mode in ('query', 'summary'):
                ctx_lines = ['\n\n【当前上下文 — 用户正在操作的页面和对象】']
                page = context.get('page', {})
                if page:
                    title = page.get('title', '') or page.get('name', '') or page.get('path', '')
                    ctx_lines.append(f'- 用户当前页面：{title}（路径: {page.get("path", "")}）')
                params = context.get('params', {})
                query = context.get('query', {})
                ctx_labels = []
                for key, label in [('taskId', '任务编号'), ('clueId', '线索/图斑编号'), ('batchId', '批次编号')]:
                    if params.get(key):
                        ctx_labels.append(f'{label}: {params[key]}')
                for key, label in [('selectedId', '选中对象'), ('taskId', '任务编号'), ('batchId', '批次编号'),
                                   ('clueId', '线索编号'), ('gridId', '网格编号'), ('id', '选中ID')]:
                    if query.get(key) and key not in params:
                        ctx_labels.append(f'{label}: {query[key]}')
                if ctx_labels:
                    ctx_lines.append('- 用户已选中对象：' + '，'.join(ctx_labels))
                page_path = page.get('path', '')
                if 'verifyClue' in page_path or 'task-management' in page_path or 'taskManagement' in page_path:
                    ctx_lines.append('- 【字段映射】选中 ID 是 batch_id，查询数据时请使用 batch 表的 batch_id 字段筛选，不要用 address__contains 等字段。')
                elif 'clue-view' in page_path or 'clueView' in page_path:
                    ctx_lines.append('- 【字段映射】此页面选中对象为线索，查询时请使用 clue 表的对应字段筛选。')
                ctx_lines.append('用户说"这个任务"、"当前页面"、"该线索"等指代词时，请关联到以上上下文中的对象。')

                # 摘要在 summary 模式下启用
                if chat_mode == 'summary':
                    has_selection = bool(ctx_labels)
                    if has_selection:
                        ctx_lines.append('\n【智能摘要规则】')
                        ctx_lines.append('如果用户发出模糊询问（如"怎么样""什么情况""帮我看看""分析一下""汇总""总结""报告"），')
                        ctx_lines.append('你应该自动调用 query_data 多次，收集该对象的进度、异常、待办、状态分布等维度数据，')
                        ctx_lines.append('然后生成一份结构化摘要，包含：')
                        ctx_lines.append('1. 📊 数据概况（总量/进度）')
                        ctx_lines.append('2. ⚠️ 异常/风险项（如有疑似违法线索、检测失败等）')
                        ctx_lines.append('3. 📋 待办事项')
                        ctx_lines.append('4. 🟢/🟡/🔴 风险等级评估')
                        ctx_lines.append('5. 💡 推荐下一步操作')
                        ctx_lines.append('禁止编造数据，必须基于 query_data 返回的真实结果。若无选中对象则忽略此规则。')

                # 追问生成规则
                ctx_lines.append('\n【追问生成规则】')
                ctx_lines.append('每次回复末尾，用 "|||" 分隔符生成 3 个与当前页面和选中对象高度相关的追问。')
                ctx_lines.append('追问应与当前上下文紧密贴合，不要生成无关的通用问题。')

                prompt += '\n'.join(ctx_lines)

                # 构建 query_data 的第二层上下文
                query_context = {}
                if ctx_labels:
                    selected_info = '，'.join(ctx_labels)
                    query_context['selected_info'] = selected_info
                if 'verifyClue' in page_path or 'task-management' in page_path or 'taskManagement' in page_path:
                    query_context['field_map'] = 'batch 表的 batch_id 字段'
                elif 'clue-view' in page_path or 'clueView' in page_path:
                    query_context['field_map'] = 'clue 表的对应索引字段'
            else:
                query_context = {}
            raw_messages.insert(0, {'role': 'system', 'content': prompt})

        lc_msgs = _raw_messages_to_lc(raw_messages)
        llm = _get_llm(tools=frontend_tools, model=model, temperature=temperature, max_tokens=max_tokens)

        # 阶段 1: 理解问题
        yield _sse_event({"phase": "understanding", "message": "正在理解问题..."})

        # 多轮 Agent 循环：LLM 可反复调用工具，直到不再需要或达到上限
        result = {}
        for iteration in range(5):
            def node_chat(state: ChatState) -> dict:
                response = llm.invoke(state['messages'])
                return {'messages': [response]}

            graph = StateGraph(ChatState)
            graph.add_node('chat', node_chat)
            graph.add_edge(START, 'chat')
            graph.add_edge('chat', END)
            compiled = graph.compile()

            result_state = compiled.invoke({'messages': lc_msgs})
            last_msg = result_state['messages'][-1]
            lc_msgs = result_state['messages']  # 累积消息，供下一轮使用

            result = _lc_to_result(last_msg)
            tool_calls = result.get('tool_calls')
            if not tool_calls:
                break  # LLM 不再需要工具，循环结束

            # 处理工具调用
            query_actions = []
            emit_tool_calls = []    # 需要发给前端的工具调用（map/navigate/lookup）
            for tc in tool_calls:
                fn = tc.get('function', {})
                tc_id = tc.get('id', '')
                name = fn.get('name', '')

                if name == 'map_action':
                    yield _sse_event({"phase": "geocoding", "message": "正在定位地图..."})
                    try:
                        args = json.loads(fn['arguments']) if isinstance(fn.get('arguments'), str) else fn.get('arguments', {})
                    except (json.JSONDecodeError, TypeError):
                        args = {}
                    if args.get('location') and not args.get('lat') and not args.get('polygon'):
                        city = args.get('city', '南京')
                        district = _get_district_amap(args['location'], city=city, subdistrict=1)
                        if district and district.get('polygon'):
                            args['polygon'] = district['polygon']
                            if district.get('center'):
                                args['lat'] = district['center']['lat']
                                args['lng'] = district['center']['lng']
                            if district.get('sub_regions'):
                                args['sub_regions'] = district['sub_regions']
                            geo = _geocode_amap(args['location'], city)
                            args['name'] = geo.get('address', args['location']) if geo else district.get('name', args['location'])
                        else:
                            geo = _geocode_amap(args['location'], city)
                            if geo:
                                args['lat'] = geo['lat']
                                args['lng'] = geo['lng']
                                args['name'] = geo.get('address', args['location'])
                        fn['arguments'] = json.dumps(args, ensure_ascii=False)
                    # map_action 发给前端处理
                    emit_tool_calls.append(tc)

                elif name == 'lookup_task':
                    yield _sse_event({"phase": "looking_up", "message": "正在查找任务..."})
                    try:
                        lookup_args = json.loads(fn['arguments']) if isinstance(fn.get('arguments'), str) else fn.get('arguments', {})
                    except (json.JSONDecodeError, TypeError):
                        lookup_args = {}
                    task_id = lookup_args.get('task_id', '').strip()
                    if task_id:
                        batch = Batch.objects.filter(batch_id=task_id).first()
                        if batch:
                            lookup_args['_lookup_found'] = True
                            lookup_args['_batch_name'] = batch.batch_name
                            lookup_args['_status'] = batch.status
                            lookup_args['_region'] = batch.region or ''
                        else:
                            lookup_args['_lookup_found'] = False
                            lookup_args['_msg'] = f'未查询到任务编号为 {task_id} 的任务'
                        fn['arguments'] = json.dumps(lookup_args, ensure_ascii=False)
                    emit_tool_calls.append(tc)

                elif name == 'navigate_page':
                    emit_tool_calls.append(tc)

                elif name == 'query_data':
                    yield _sse_event({"phase": "querying", "message": "正在查询数据..."})
                    try:
                        query_args = json.loads(fn['arguments']) if isinstance(fn.get('arguments'), str) else fn.get('arguments', {})
                    except (json.JSONDecodeError, TypeError):
                        query_args = {}
                    try:
                        query_result = _handle_query_data(query_args, query_context)
                        query_args.update(query_result)
                    except Exception as qe:
                        query_args['_query_result'] = f'查询失败：{str(qe)[:200]}'
                    fn['arguments'] = json.dumps(query_args, ensure_ascii=False)
                    query_actions.append(ToolMessage(content=query_args.get('_query_result', ''), tool_call_id=tc_id))

            # 非查询类工具：直接发给前端，结束 Agent 循环
            if emit_tool_calls:
                yield _sse_event({"phase": "done", "result": {
                    "content": "",
                    "finish_reason": "tool_calls",
                    "tool_calls": emit_tool_calls,
                }})
                return

            # query_data：ToolMessage 反馈给 LLM，继续循环
            if query_actions:
                lc_msgs.extend(query_actions)
            else:
                break  # 无有效工具，跳出

        # 阶段最后: 生成回答
        yield _sse_event({"phase": "generating", "message": "正在生成回答..."})

        # 注入用户名
        current_user = parse_jwt_token(request)
        result['username'] = current_user.username if current_user else '用户'

        # 注入模型名
        config = configparser.ConfigParser()
        config.read(os.path.join(settings.BASE_DIR, 'config.ini'), encoding='utf-8')
        result['model'] = config.get('deepseek', 'model')

        yield _sse_event({"phase": "done", "result": result})

    except Exception as e:
        import traceback
        logger = logging.getLogger('skyeye')
        logger.error(f"chat_completions SSE error: {e}\n{traceback.format_exc()}")
        yield _sse_event({"phase": "error", "message": str(e)})
        yield _sse_event({"phase": "done", "result": {
            "content": f"抱歉，处理请求时出错：{str(e)[:200]}",
            "finish_reason": "stop",
        }})


def chat_completions(request):
    """LangGraph + DeepSeek 聊天（SSE 流式）"""
    if request.method == 'OPTIONS':
        resp = HttpResponse()
        resp['Access-Control-Allow-Origin'] = request.headers.get('Origin', '*')
        resp['Access-Control-Allow-Credentials'] = 'false'
        resp['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        resp['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return resp

    if request.method != 'POST':
        return error('仅支持 POST 请求')

    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return error('请求体 JSON 解析失败')

    raw_messages = body.get('messages', [])
    if not raw_messages:
        return error('messages 不能为空')

    frontend_tools = body.get('tools')
    chat_mode = body.get('chat_mode', 'chat')
    context = body.get('context')
    model = body.get('model')
    temperature = body.get('temperature')
    max_tokens = body.get('max_tokens')

    response = StreamingHttpResponse(
        _generate_sse(raw_messages, frontend_tools, request, chat_mode, context, model, temperature, max_tokens),
        content_type='text/event-stream',
    )
    origin = request.headers.get('Origin', '*')
    response['Access-Control-Allow-Origin'] = origin
    response['Access-Control-Allow-Credentials'] = 'false'
    response['Cache-Control'] = 'no-cache'
    response['X-Accel-Buffering'] = 'no'
    return response
