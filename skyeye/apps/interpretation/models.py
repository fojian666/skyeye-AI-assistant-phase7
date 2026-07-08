from django.db import models


class InterpretationTask(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(verbose_name="任务名", default='', max_length=255)
    model_name = models.CharField(verbose_name="模型名", default='', max_length=255)
    model_path = models.CharField(verbose_name="模型路径", default='', max_length=255)
    model_network = models.CharField(verbose_name="模型网络", default='', max_length=255)
    fragment = models.CharField(verbose_name="碎片化", default='', max_length=255)
    status = models.IntegerField(verbose_name="状态", default=0)
    config_path = models.CharField(verbose_name="配置文件路径", default='', max_length=255)
    input_path = models.CharField(verbose_name="输入路径", default='', max_length=255, null=True, blank=True)
    input_path_prev = models.CharField(verbose_name="前景输入路径", default='', max_length=255, null=True, blank=True)
    input_path_next = models.CharField(verbose_name="后景输入路径", default='', max_length=255, null=True, blank=True)
    output_path = models.CharField(verbose_name="输出路径", default='', max_length=255, null=True, blank=True)
    building_regular = models.IntegerField(verbose_name="建筑物规则化", default=0)
    create_person = models.CharField(verbose_name="创建用户", default='', max_length=100)
    create_time = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)
    update_time = models.DateTimeField(verbose_name="更新时间", auto_now=True)
    task_type = models.CharField(verbose_name="任务类型", default='', max_length=255)
    detection_type = models.CharField(verbose_name="检测类型", default='', max_length=255)
    county = models.CharField(verbose_name="区县", default='', max_length=255)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 't_interpretation_task'


class InterpretationTaskResult(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(verbose_name="任务名", default='', max_length=255)
    path_id = models.IntegerField(verbose_name="影像分割服务ID", default=0, null=True, blank=True)
    prev_id = models.IntegerField(verbose_name="前序任务ID", default=0, null=True, blank=True)
    next_id = models.IntegerField(verbose_name="后续任务ID", default=0, null=True, blank=True)
    data_path_id = models.IntegerField(verbose_name="数据路径ID", default=0, null=True, blank=True)
    task_type = models.CharField(verbose_name="任务类型", default='', max_length=255)
    county = models.CharField(verbose_name="区县", default='', max_length=255)
    create_person = models.CharField(verbose_name="创建用户", default='', max_length=100)
    create_time = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 't_interpretation_task_result'
