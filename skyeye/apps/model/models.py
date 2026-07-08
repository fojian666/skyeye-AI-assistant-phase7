from django.db import models


class Models(models.Model):
    """
    模型数据表
    """
    id = models.AutoField(verbose_name="模型编号", primary_key=True)
    name = models.CharField(verbose_name="模型名称", default='', max_length=100)
    epoch = models.IntegerField(verbose_name="迭代次数")
    thumbnail = models.ImageField(verbose_name="缩略图", upload_to='thumbnail/', default='')
    framework = models.CharField(verbose_name="模型框架", max_length=50)
    network = models.CharField(verbose_name="网络", max_length=50, default='')
    learning_rate = models.FloatField(verbose_name="学习率")
    country = models.CharField(verbose_name="样本区域", max_length=50, default='')
    datasets_count = models.IntegerField(verbose_name="样本数量", default=0)
    datasets_size = models.CharField(verbose_name="样本大小", max_length=50, default='256x256', null=True)
    model_path = models.CharField(verbose_name="模型路径", default='', max_length=500)
    status = models.BooleanField(verbose_name="模型状态", help_text="0 废弃，1 使用", default=True)
    order = models.IntegerField(verbose_name="排序号", default=0)
    is_del = models.IntegerField(default=1, verbose_name="是否可用")
    create_person = models.CharField(verbose_name="创建用户", default='', max_length=100)
    create_time = models.DateTimeField('创建时间', auto_now_add=True)
    note = models.TextField(verbose_name="备注", null=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 't_models'
        verbose_name = '模型'
        verbose_name_plural = '模型'


class Category(models.Model):
    """检测标签表"""
    id = models.AutoField(verbose_name="标签ID", primary_key=True)
    name = models.CharField(max_length=100, verbose_name="标签名称")
    code = models.CharField(max_length=50, unique=True, verbose_name="标签代码")
    description = models.TextField(blank=True, verbose_name="标签描述")
    is_del = models.IntegerField(default=1, verbose_name="是否可用")
    order = models.IntegerField(verbose_name="排序号", default=0)
    create_person = models.CharField(verbose_name="创建用户", default='', max_length=100)
    color = models.CharField(max_length=7, default='#FF0000', verbose_name="显示颜色")
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    class Meta:
        db_table = 't_category'
        verbose_name = '检测标签'
        verbose_name_plural = '检测标签'

    def __str__(self):
        return f"{self.name} ({self.code})"


class ModelLabel(models.Model):
    """模型能力关联表 - 表示模型能够识别哪些目标"""
    id = models.AutoField(verbose_name="标签ID", primary_key=True)
    model = models.ForeignKey(Models, on_delete=models.CASCADE, verbose_name="检测模型")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name="检测标签")
    category_name = models.CharField(verbose_name="标签名称", default='', max_length=100)
    is_del = models.IntegerField(default=1, verbose_name="是否可用")
    order = models.IntegerField(verbose_name="排序号", default=0)
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    class Meta:
        db_table = 't_model_label'
        verbose_name = '模型能力'
        verbose_name_plural = '模型能力'

    def __str__(self):
        return self.category_name


class ModelScene(models.Model):
    """
    模型场景表
    """
    id = models.AutoField(primary_key=True)
    name = models.CharField(verbose_name="模型场景", default='', max_length=100)
    model = models.ForeignKey(Models, on_delete=models.CASCADE, verbose_name="检测模型")
    is_del = models.IntegerField(default=1, verbose_name="是否可用")
    order = models.IntegerField(verbose_name="排序号", default=0)
    create_person = models.CharField(verbose_name="创建用户", default='', max_length=100)
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    class Meta:
        db_table = 't_model_scene'
        verbose_name = '模型场景表'
        verbose_name_plural = '模型场景表'

    def __str__(self):
        return self.name


class ModelSceneLabel(models.Model):
    """场景标签配置表 - 配置场景中要识别哪些目标"""
    model_scene = models.ForeignKey(ModelScene, on_delete=models.CASCADE, verbose_name="模型场景")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name="模型能力")
    category_name = models.CharField(verbose_name='标签', default='', max_length=100)
    is_del = models.IntegerField(default=1, verbose_name="是否可用")
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    class Meta:
        db_table = 't_model_scene_label'
        verbose_name = '场景标签配置'
        verbose_name_plural = '场景标签配置'
