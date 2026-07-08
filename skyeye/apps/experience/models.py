from django.db import models
from apps.system.models import User

class Project(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, blank=True, null=True, verbose_name="项目名")
    order = models.IntegerField(blank=True, null=True, verbose_name="排序号")
    project_source = models.CharField(max_length=100, blank=True, null=True, verbose_name="项目来源")
    count = models.IntegerField(verbose_name="项目任务数量", default=1)
    remark = models.TextField(blank=True, null=True, verbose_name="描述")
    create_time = models.DateTimeField(auto_now=True, null=True, verbose_name='创建时间')

    class Meta:
        db_table = 't_project'


class Task(models.Model):
    """
    任务表
    """
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, default='', verbose_name='任务名称')
    path = models.CharField(verbose_name='任务路径', max_length=255, default='')
    count = models.IntegerField(verbose_name="图片数量", default=0)
    task_type = models.CharField(verbose_name='任务类型', default='', max_length=50)
    owner = models.ForeignKey(User, verbose_name='操作用户', default='', on_delete=models.CASCADE)
    longitude = models.FloatField(verbose_name='经度', null=True, blank=True)
    latitude = models.FloatField(verbose_name='纬度', null=True, blank=True)
    height = models.FloatField(verbose_name="高度", default=0)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, verbose_name='所属项目', default='', blank=True,
                                null=True)
    image_width = models.FloatField(verbose_name="图片宽度", default=0)
    image_height = models.FloatField(verbose_name="图片高度", default=0)
    status = models.IntegerField(verbose_name="任务状态", default=0)
    yaw_degree = models.CharField(verbose_name='yaw角度', null=True, blank=True, default='', max_length=100)
    create_time = models.DateTimeField(auto_now=True, null=True, verbose_name='创建时间')
    last_modify_time = models.DateTimeField(auto_now=True, null=True, verbose_name='最后修改时间')
    note = models.TextField(verbose_name='任务描述', default='')

    def __str__(self):
        return self.name

    class Meta:
        db_table = 't_task'


class Picture(models.Model):
    """
    图片表
    """
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, default='', verbose_name='图片名称')
    file_path = models.CharField(verbose_name='图片路径', max_length=255, default='')
    result_path = models.CharField(verbose_name='结果路径', max_length=255, default='')
    labels = models.CharField(verbose_name='检测结果标签', max_length=255, default='')
    alarms = models.TextField(verbose_name='框位置')
    task = models.ForeignKey(Task, on_delete=models.CASCADE, verbose_name="关联任务")
    create_time = models.DateTimeField(auto_now=True, null=True, verbose_name='创建时间')

    def __str__(self):
        return self.name

    class Meta:
        db_table = 't_picture'


class Alarms(models.Model):
    """
    报警表
    """
    id = models.AutoField(primary_key=True)
    label = models.CharField(max_length=100, default='', verbose_name='标签')
    file_path = models.CharField(verbose_name='图片路径', max_length=255, default='')
    alarms = models.TextField(verbose_name='框位置')
    longitude = models.FloatField(verbose_name='经度', null=True, blank=True)
    latitude = models.FloatField(verbose_name='纬度', null=True, blank=True)
    is_delete = models.IntegerField(verbose_name="是否删除", default=0)
    inspector = models.CharField(verbose_name="核验人", max_length=100, default='')
    center_x = models.IntegerField(verbose_name="像素中心点x坐标", null=True, blank=True)
    center_y = models.IntegerField(verbose_name="像素中心点y坐标", null=True, blank=True)
    task = models.ForeignKey(Task, on_delete=models.CASCADE, verbose_name="关联全景任务")
    create_time = models.DateTimeField(auto_now=True, null=True, verbose_name='创建时间')

    def __str__(self):
        return self.label

    class Meta:
        db_table = 't_alarms'
