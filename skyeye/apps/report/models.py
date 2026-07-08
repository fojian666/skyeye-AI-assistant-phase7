from django.db import models
from apps.panorama.models import Batch, Scene
from apps.system.models import User


class BatchReport(models.Model):
    id = models.AutoField(verbose_name="报告编号", primary_key=True)
    batch = models.ForeignKey(Batch, verbose_name="所属批次", related_name='batch_report',on_delete=models.CASCADE, null=True)
    count = models.IntegerField(verbose_name="报告数量", default=0)
    scene = models.ForeignKey(Scene, verbose_name="关联场景", on_delete=models.CASCADE, null=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="操作用户")
    create_time = models.DateTimeField(auto_now_add=True, null=True, verbose_name='创建时间')

    def __str__(self):
        return str(self.count)

    class Meta:
        # Specify the database table name
        db_table = 't_batch_report'


class Report(models.Model):
    """
    报告表
    """
    report_id = models.CharField(verbose_name="报告编号", primary_key=True, max_length=100, default='')
    report_name = models.CharField(verbose_name="报告名称", max_length=100, default='')
    batch_report = models.ForeignKey(BatchReport,verbose_name='所属批次报告', on_delete=models.CASCADE)
    village = models.CharField(verbose_name='关联村', max_length=100, null=True, default='')
    file_id = models.CharField(verbose_name="文件地址", max_length=50, default='')
    create_time = models.DateTimeField(auto_now_add=True, null=True, verbose_name='创建时间')

    def __str__(self):
        return self.report_id

    class Meta:
        db_table = 't_report'



class Download(models.Model):
    """
    下载表
    """
    download_id = models.CharField(verbose_name="下载编号", max_length=50, default='', primary_key=True)
    report = models.ForeignKey(Report, verbose_name="所属报告", null=True, blank=True,
                               on_delete=models.CASCADE)
    downloader = models.ForeignKey(User, verbose_name="下载用户", null=True, blank=True,
                                   on_delete=models.CASCADE)
    count = models.IntegerField(verbose_name="下载次数", default=0)
    create_time = models.DateTimeField(auto_now_add=True, null=True, verbose_name='下载时间')
    last_modify_time = models.DateTimeField(auto_now=True, null=True, verbose_name='最后修改时间')

    def __str__(self):
        return self.download_id

    class Meta:
        db_table = 't_download'