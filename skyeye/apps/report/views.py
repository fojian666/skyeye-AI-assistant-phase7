import ast
import configparser
import datetime
import json
import os
import random
import time
import uuid

from PIL import Image
from django.utils.encoding import escape_uri_path
from playwright.sync_api import sync_playwright
from docx.shared import Mm
import docxtpl
from docxtpl import DocxTemplate
from django.conf import settings
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count
from django.http import JsonResponse, StreamingHttpResponse
from itertools import groupby
from operator import attrgetter
from apps.panorama.models import Batch, Scene, Clue, BufferFile
from .models import Report, BatchReport
from utils_tools.common import zip_folder, file_iterator, parse_jwt_token

config = configparser.ConfigParser()
config.read(os.path.join(settings.BASE_DIR, 'config.ini'), encoding='utf-8')
def report_list(request):
    """
    报告获取
    @param request:
    @return:
    """
    try:
        current_user = parse_jwt_token(request)
        county = current_user.county
        params = json.loads(request.body.decode('utf-8'))
        page = params.get('page', 1)
        limit = params.get('limit', 5)
        keyword = params.get('keyword')
        scene_id = params.get('scene_id')
        if scene_id:
            report_objs = Report.objects.filter(report_name__contains=keyword, scene_id=scene_id,batch_report__batch__grid__county=county).all()
        else:
            report_objs = Report.objects.filter(report_name__contains=keyword,batch_report__batch__grid__county=county).all()
        if len(report_objs) > 0:
            paginator = Paginator(report_objs, limit)
            results = paginator.page(page)
        else:
            results = []
        data = []
        for i in results:
            record = {
                'report_id': i.report_id,
                'report_name': i.report_name,
                'batch_id': i.batch_id,
                'file_id': i.file_id,
                'grid_operator': i.batch.grid.grid_operator.username,
                'scene_name': i.scene.scene_name,
                'create_time': i.create_time.strftime('%Y-%m-%d %H:%M:%S'),
            }
            data.append(record)

        return JsonResponse({"code": 0, 'msg': '', 'data': data, 'count': len(report_objs)})
    except Exception as e:
        print(f"获取报告列表失败，报错内容：{e}")
        return JsonResponse({"code": 500, 'msg': str(e)})


def report_params(request):
    """
    报告页面获取批次和场景
    @param request:
    @return:
    """
    try:
        batch_objs = Batch.objects.values('street').annotate(count=Count('street')).order_by('street')
        data = []
        for batch in batch_objs:
            street = batch['street']
            # 只展示待核实的批次
            all_batch = Batch.objects.filter(street=street, status=4).all()
            records = []
            for i in all_batch:
                record = {
                    'batch_id': i.batch_id,
                    'batch_name': i.batch_name,
                }
                records.append(record)
            data.append({'name': street, 'value': records})

        scene_list = [{'name': j.scene_name, 'value': j.scene_id} for j in Scene.objects.all()]
        result_data = {
            'batch_objs': data,
            'scene_list': scene_list
        }
        return JsonResponse({"code": 0, 'msg': '', 'data': result_data})
    except Exception as e:
        return JsonResponse({"code": 500, 'msg': str(e)})


def write_doc(list_array, batch_id, save_path, scene_name, division):
    """
    基于变化检测图斑生成word报告
    :param start_time: 检测时间
    :param outputPath: 报告的路径
    :return:
    """

    current_batch = Batch.objects.get(batch_id=batch_id)
    if current_batch.street == '龙潭街道':
        if division == 'village':
            tpl_file = os.path.join(settings.BASE_DIR, 'static', 'docx', 'template_lt_village.docx')
        else:
            tpl_file = os.path.join(settings.BASE_DIR, 'static', 'docx', 'template_lt_street.docx')
    else:
        tpl_file = os.path.join(settings.BASE_DIR, 'static', 'docx', 'template.docx')  # 模板文件路径
    tpl = DocxTemplate(tpl_file)
    report_time1 = (datetime.datetime.now().strftime("%Y-%m-%d")).split('-')  # 报告生成时间
    report_time = report_time1[0] + '年' + report_time1[1] + '月' + report_time1[2] + '日'

    street = current_batch.street
    shp_records = []
    classes = set()
    # 定义要创建的目录的路径
    temp_path = os.path.join(settings.BASE_DIR, 'static', 'temp')
    # 检查目录是否已存在
    if not os.path.exists(temp_path):
        # 如果目录不存在，则创建目录
        os.makedirs(temp_path)
    # 查询所有线索并排序
    all_clues = Clue.objects.filter(batch_id=batch_id, status__in=[2, 3, 5], clue_name__in=list_array).order_by(
        'address')

    # 按 village 分组
    if division == 'village':
        clues_by_division = {
            key: list(group)
            for key, group in groupby(all_clues, key=attrgetter('address'))
        }
    else:
        clues_by_division = {
            street: list(all_clues)
        }
    all_path = []
    for villages, clues in clues_by_division.items():
        path = os.path.join(save_path, f"{batch_id}_{scene_name}_{villages}.docx")
        for i in clues:
            shp_record = {}
            shp_record['screenshot_path'] = docxtpl.InlineImage(tpl,
                                                                os.path.join(settings.BASE_DIR, 'static',
                                                                             'screenshot',
                                                                             str(i.clue_id) + '.png'),
                                                                width=Mm(160), height=Mm(80))
            shp_record['map_path'] = docxtpl.InlineImage(tpl,
                                                         os.path.join(settings.BASE_DIR, 'static', 'screenshot',
                                                                      str(i.clue_id) + '_2.png'), width=Mm(100),
                                                         height=Mm(50))
            shp_record['result_path'] = docxtpl.InlineImage(tpl, os.path.join(settings.BASE_DIR,i.file_path.split('8009/')[1]), width=Mm(100), height=Mm(50))
            shp_record['filename'] = os.path.basename(i.file_path)
            shp_record['class'] = i.clue_name
            shp_record['address'] = i.address
            shp_record['grid_name'] = i.batch.grid.grid_name
            shp_record['location'] = (round(i.longitude, 3), round(i.latitude, 3))
            shp_record['inspector'] = i.inspector
            shp_record['create_time'] = i.batch.create_time
            shp_record['grid_operator'] = i.batch.grid.grid_operator
            shp_record['point_name'] = i.panorama_image.point.point_name
            shp_record['image_id'] = i.panorama_image.image_id
            shp_record['image_name'] = i.panorama_image.image_name
            shp_records.append(shp_record)
            classes.add(i.clue_name)
        context = {
            "report_time": report_time,
            "batch_id": batch_id,
            "alarm_count": len(all_clues),
            "classes": str(classes),
            "street": street,
            "village": villages,
            "title": current_batch.batch_name,
            "scene_name": scene_name,
            "records": shp_records,
            "start_date": current_batch.start_date,
            "end_date": current_batch.end_date,

        }
        print("开始写入doc文件{}".format(path))
        tpl.render(context)
        tpl.save(path)
        all_path.append(path)
    return all_path


def compress_picture(inputImage):
    """
    Pillow压缩图斑图片
    @param inputImage:输入图片路径
    @return:None
    """
    try:
        # Pillow读取img文件
        im = Image.open(inputImage)
        # 读取图片尺寸大小（像素宽高）
        (x, y) = im.size
        # 定义缩小后的标准宽度
        new_width = 400
        # 计算缩小后的高度
        new_height = int(y * new_width / x)
        # 改变尺寸，保持图片高品质
        out = im.resize((new_width, new_height))
        # 保存图片，替换原图
        out.save(inputImage)
    except Exception as e:
        print(f"压缩图片报错，报错内容：{str(e)}")


def get_data(clue_id):
    """
    根据iserver服务获取面积、经纬度，并通过selenium 获取图斑图片
    :param url: 服务地址
    :return:
    """
    config_common = config['screenshot']
    screenshot_url = config_common['screenshot_url']
    try:
        # 图片保存路径
        img_path = os.path.join(settings.BASE_DIR, 'static', 'screenshot')
        os.makedirs(img_path, exist_ok=True)
        # 请求截图的图斑图片url地址
        change_url =  f'{screenshot_url}/map-screenshot/{str(clue_id)}'
        print(change_url)
        pic_path = os.path.join(img_path, str(clue_id) + '.png')
        if not os.path.exists(pic_path):
            # 启动浏览器
            download_image(change_url, pic_path)
            compress_picture(pic_path)
            change_url2 = f'{screenshot_url}/mapview-screenshot/{str(clue_id)}'
            pic_path = os.path.join(img_path, str(clue_id) + '_2.png')
            download_image(change_url2, pic_path)
            compress_picture(pic_path)
            print(f"------图片:{pic_path} 屏幕截图成功------")
        return True
    except Exception as e:
        print("生成图片报错，报错内容：{}".format(str(e)))
        return False


def download_image(url, output_path):
    """
    下载图片
    Args:
        url:
        output_path:

    Returns:

    """
    try:
        with sync_playwright() as p:
            # 启动浏览器（无头模式）
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            # 访问网页并截图
            page.goto(url)
            time.sleep(3)
            page.screenshot(path=output_path, full_page=True)  # full_page 截取完整页面
            browser.close()
        return True
    except Exception as e:
        print("下载图片失败", e)
        return False


def batch_report(request):
    """
    批次报告页面获取报告信息
    @param request:
    @return:
    """
    params = json.loads(request.body.decode('utf-8'))
    limit = params.get('limit', 10)
    page = params.get('page', 1)
    keyword = params.get('keyword')
    scene_id = params.get('scene_id')
    if scene_id:
        report_objs = BatchReport.objects.filter(batch_id=keyword, scene_id=scene_id).all()
    else:
        report_objs = BatchReport.objects.all()
    if len(report_objs) > 0:
        paginator = Paginator(report_objs, limit)
        results = paginator.page(page)
    else:
        results = []
    data = []
    for i in results:
        record = {
            'id': i.id,
            'count': i.count,
            'batch_id': i.batch_id,
            'batch_name': i.batch.batch_name,
            'username': i.owner.username,
            'scene_name': i.scene.scene_name,
            'county': i.batch.street,
            'file_id': '6263943695325168',
            'create_time': i.create_time.strftime('%Y-%m-%d %H:%M:%S'),
        }
        data.append(record)

    return JsonResponse({"code": 0, 'msg': '', 'data': data, 'count': len(report_objs)})


def report_generate(request):
    """
    报告生成
    @param request:
    @return:
    """
    current_user = parse_jwt_token(request)
    with transaction.atomic():
        try:
            params = json.loads(request.body.decode('utf-8'))
            batch_id = params.get('batchId')
            scene_ids = params.get('sceneIds')
            division = params.get('division')  # ’village‘: 按村生成，'street':按街道生成
            success_report = []
            error_report = []
            for scene_id in scene_ids:
                scene_obj = Scene.objects.get(scene_id=scene_id)
                labels = scene_obj.labels
                list_array = ast.literal_eval(labels)
                clue_objs = Clue.objects.filter(status__in=[2, 3, 5], batch_id=batch_id, clue_name__in=list_array).all()
                for i in clue_objs:
                    get_data(i.clue_id)
                # 报告输出路径
                outputPath = os.path.join(settings.BASE_DIR, 'static', 'docx', str(batch_id))
                os.makedirs(outputPath, exist_ok=True)
                all_path = write_doc(list_array, batch_id, outputPath, scene_obj.scene_name, division)
                print(all_path)
                current_batch_report = BatchReport.objects.create(
                    batch_id=batch_id,
                    scene_id=scene_id,
                    owner=current_user,
                    count=len(all_path)
                )
                for i in all_path:
                    while True:
                        file_id = f"62{random.randint(10000000000000, 99999999999999)}"
                        is_exist = BufferFile.objects.filter(file_id=file_id)
                        if not is_exist:
                            break
                    Report.objects.create(
                        report_id=str(uuid.uuid1()).replace('-', ''),
                        report_name=os.path.basename(i),
                        batch_report=current_batch_report,
                        file_id=file_id
                    )

                    BufferFile.objects.create(
                        file_id=file_id,
                        file_name=os.path.basename(i),
                        file_extension='.docx',
                        file_path=i,
                        owner=current_user.username,
                        file_type='docx',
                        file_size=os.path.getsize(i)
                    )

                success_report.append(scene_obj.scene_name)
            return JsonResponse(
                {"code": 0, 'msg': f"成功生成报告{len(success_report)}份，其中场景{','.join(error_report)}报告已存在或者报告中无数据"})
        except Exception as e:
            print(f"生成报告失败，{str(e)}")
            transaction.set_rollback(True)
            return JsonResponse({"code": 500, 'msg': f"生成报告失败，{str(e)}"})


def report_delete(request):
    """
    删除报告
    @param request:
    @return:
    """
    temp_files_list = []
    with transaction.atomic():
        try:
            params = json.loads(request.body.decode('utf-8'))
            ids = params.get('ids')
            for i in ids:
                batch_report_obj = BatchReport.objects.filter(id=i).first()
                report_obj = Report.objects.filter(batch_report_id=batch_report_obj).first()
                if report_obj:
                    file_obj = BufferFile.objects.filter(file_id=report_obj.file_id).first()
                    path = file_obj.file_path
                    if os.path.exists(path):
                        os.remove(path)
                    file_obj.delete()
                    report_obj.delete()
                batch_report_obj.delete()
            return JsonResponse({'code': 0, 'msg': f'报告删除成功'})
        except Exception as e:
            print(f"报告删除失败，{str(e)}")
            transaction.set_rollback(True)
            return JsonResponse({"code": 500, 'msg': f"报告删除失败，{str(e)}"})


def report_download(request, batch_report_id):
    """
    下载报告
    @param request:
    @return:
    """
    current_obj = BatchReport.objects.filter(id=batch_report_id).first()
    #outputPath = os.path.join(settings.BASE_DIR, 'static', 'docx', str(current_obj.batch_id))
    report = Report.objects.filter(batch_report_id=batch_report_id).first()
    file_id = report.file_id
    file_obj = BufferFile.objects.filter(file_id=file_id).first()
    outputPath = file_obj.file_path
    file_name = file_obj.file_name
    print(outputPath)
    if not os.path.exists(outputPath):
        print("文件不存在！")
        return JsonResponse({'code': 500, 'msg': '报告不存在'})
    #zip_path = os.path.join(settings.BASE_DIR, 'static', 'docx', f'{current_obj.id}.zip')
    #zip_folder(outputPath, zip_path)
    # 设置响应头
    # StreamingHttpResponse将文件内容进行流式传输，数据量大可以用这个方法
    if not os.path.exists(outputPath):
        return JsonResponse({"error": "文件未找到"}, status=404)
    response = StreamingHttpResponse(file_iterator(outputPath))
    # 以流的形式下载文件,这样可以实现任意格式的文件下载
    response['Content-Type'] = 'application/octet-stream'
    # Content-Disposition就是当用户想把请求所得的内容存为一个文件的时候提供一个默认的文件名
    response['Content-Disposition'] = 'attachment;filename="{}"'.format(escape_uri_path(file_name))
    return response
