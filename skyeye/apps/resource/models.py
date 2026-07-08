from django.db import models

# Create your models here.
from apps.system.models import Nest


class MultivariateTask(models.Model):
    id = models.AutoField(primary_key=True)
    task_name = models.CharField(max_length=255, verbose_name="任务名称", default='')
    task_type = models.CharField(max_length=255, verbose_name="任务类型", default='')
    task_status = models.IntegerField(verbose_name="任务状态", default=1)
    count = models.IntegerField(verbose_name="任务数量", default=0)
    nest = models.ForeignKey(Nest, on_delete=models.CASCADE, verbose_name="机巢")
    flight = models.CharField(verbose_name="飞行器", default='', max_length=255)
    flight_type = models.CharField(verbose_name="飞行器类型", default='', max_length=10)
    organization = models.CharField(verbose_name="组织", default='', max_length=255)
    collect_time = models.DateTimeField(verbose_name="采集时间", auto_now=True)
    collect_type = models.CharField(verbose_name="采集方式", default='', max_length=100)
    tiff_name = models.CharField(verbose_name="航片文件名", default='', max_length=100)
    tiff_service_collection = models.CharField(verbose_name="航片服务集合名", default='', max_length=100)
    tiff_center = models.CharField(verbose_name="航片中心点", default='', max_length=100)
    county = models.CharField(verbose_name="县区", default='', max_length=100)
    tiff_service_url = models.CharField(verbose_name="航片服务url", default='', max_length=100)
    tiff_size = models.IntegerField(verbose_name="航片大小", default=0)
    tiff_resolution = models.IntegerField(verbose_name="航片分辨率", default=0)
    create_person = models.CharField(verbose_name="创建人", default='', max_length=100)
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    class Meta:
        db_table = 't_multivariate_task'
        verbose_name = "多元数据表"
        verbose_name_plural = verbose_name
        ordering = ['-create_time']  # 按创建时间倒序排列

    def __str__(self):
        return self.task_name


class MultivariateData(models.Model):
    id = models.AutoField(primary_key=True)
    data_name = models.CharField(max_length=255, verbose_name="数据名称", default='')
    file_id = models.CharField(verbose_name="文件ID", default='', max_length=100)
    latitude = models.FloatField(verbose_name="纬度", default=0)
    longitude = models.FloatField(verbose_name="经度", default=0)
    path = models.CharField(verbose_name="路径", default='', max_length=100)
    order = models.IntegerField(verbose_name="顺序", default=0)
    collect_time = models.DateTimeField(verbose_name="采集时间", auto_now=True)
    task = models.ForeignKey(MultivariateTask, on_delete=models.CASCADE, verbose_name="任务")
    bounds = models.CharField(verbose_name="边界", default='', max_length=255)
    task_type = models.CharField(verbose_name="任务类型", default='', max_length=10)
    county = models.CharField(verbose_name="县区", default='', max_length=100)
    file_size = models.IntegerField(verbose_name="文件大小", default=0)
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    create_person = models.CharField(verbose_name="创建人", default='', max_length=100)

    class Meta:
        db_table = 't_multivariate_data'
        verbose_name = "多元数据单表"
        verbose_name_plural = verbose_name
        ordering = ['-create_time']  # 按创建时间倒序排列

    def __str__(self):
        return self.data_name