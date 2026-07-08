import json

from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import render
from apps.model.models import Models
from apps.system.models import SysDictData
from logger import Logger
logger = Logger(logname='model_views.log', loglevel=5, logger='model').getlog()

def model(request, model_id):
    try:
        model_obj = Models.objects.filter(id=model_id).first()
        records = {
            'id': model_obj.id,
            'name': model_obj.name,
            'epoch': model_obj.epoch,
            'thumbnail': model_obj.thumbnail.url,
            'framework': model_obj.framework,
            'create_time': model_obj.create_time.strftime('%Y-%m-%d %H:%M:%S'),
            'network': model_obj.network,
            'scene': SysDictData.objects.filter(value=model_obj.scene).first().name,
            'industry': SysDictData.objects.filter(value=model_obj.industry,dict_type='Industry').first().name,
            'note': model_obj.note,
            'country': model_obj.country,
            'datasets_size': model_obj.datasets_size,
            'model_path': model_obj.model_path,
        }
        response_data = {
            'code': 0,
            'msg': '字典数据获取成功！',
            'data': records,
        }
        return JsonResponse(response_data)
    except Exception as e:
        logger.error(f'获取字典数据失败！{e}')


def models_list(request):
    """
    获取字典类型数据
    @param request:
    @return:
    """
    try:
        params = json.loads(request.body.decode('utf-8'))
        keywords = params.get('keywords', '')
        limit = params.get('limit', 10)
        page = params.get('page', 1)
        if not keywords:
            results_obj = Models.objects.all()
        else:
            results_obj = Models.objects.filter(name__contains=keywords).all()
        paginator = Paginator(results_obj, limit)
        results = paginator.page(page)
        data_list = []
        for result in results:
            records = {
                'id': result.id,
                'name': result.name,
                'epoch': result.epoch,
                'thumbnail': result.thumbnail.url,
                'framework': result.framework,
                'create_time': result.create_time.strftime('%Y-%m-%d %H:%M:%S'),
                'network': result.network,
                'scene': SysDictData.objects.filter(value=result.scene).first().name,
                'industry': SysDictData.objects.filter(value=result.industry,dict_type='Industry').first().name,
                'note': result.note,
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
        logger.error(f'获取字典数据失败:{e}')
        return JsonResponse({'code': 500, 'msg': str(e)})


