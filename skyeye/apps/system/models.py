from django.contrib.auth.models import AbstractUser
from django.db import models


class SysDictType(models.Model):
    """
    字典类别表
    """
    id = models.AutoField(primary_key=True)
    cn_name = models.CharField(verbose_name='字典中文名称', default='', max_length=50, unique=True)
    en_name = models.CharField(verbose_name='字典英文名称', default='', max_length=50)
    status = models.IntegerField(verbose_name='字典状态(1正常，0停用)', default=1)
    create_by = models.CharField(verbose_name='创建者', default='', max_length=50)
    create_time = models.DateTimeField(auto_now_add=True, null=True, verbose_name='创建时间')
    update_by = models.CharField(verbose_name='更新者', default='', max_length=50)
    update_time = models.DateTimeField(verbose_name='更新时间', auto_now=True)
    remark = models.CharField(verbose_name='备注', default='', max_length=255)

    def __str__(self):
        return self.en_name

    class Meta:
        db_table = 't_dict_type'


class SysDictData(models.Model):
    """
    字典数据表
    """
    id = models.AutoField(primary_key=True)
    name = models.CharField(verbose_name='字典标签', default='', max_length=50)
    value = models.CharField(verbose_name='字典键值', default='', max_length=500)
    sort = models.IntegerField(verbose_name='字典排序')
    dict_type = models.CharField(verbose_name='字典类型', default='', max_length=100)
    create_by = models.CharField(verbose_name='创建者', default='', max_length=50)
    status = models.IntegerField(verbose_name='标签状态(1正常，0停用)', default=1)
    create_time = models.DateTimeField(auto_now_add=True, null=True, verbose_name='创建时间')
    remark = models.CharField(verbose_name='备注', default='', max_length=255)

    def __str__(self):
        return self.value

    class Meta:
        db_table = 't_dict_data'


class User(AbstractUser):
    """
    用户表
    """
    id = models.BigAutoField(primary_key=True)
    county = models.CharField(verbose_name="所属行政区",max_length=30, default="")
    role = models.IntegerField(verbose_name='角色', default=2)
    description = models.TextField(verbose_name='个人描述')

    def __str__(self):
        return self.username

    class Meta:
        db_table = 't_user'


class SysLog(models.Model):
    """
    日志表
    """
    id = models.AutoField(primary_key=True)
    account = models.CharField(max_length=32, default='', null=True)
    name = models.CharField(max_length=32, default='', null=True)
    type = models.CharField(max_length=32, default='', null=True)
    content = models.CharField(max_length=255, default='', null=True)
    ip = models.CharField(max_length=32, default='', null=True)
    desc = models.CharField(verbose_name="描述", max_length=255, default='', null=True)
    status = models.IntegerField(verbose_name='状态', default=1)
    append_time = models.DateTimeField(auto_now=True, null=True, verbose_name='创建时间', max_length=100)

    def __str__(self):
        return self.name

    class Meta:
        managed = True
        db_table = 't_log'


class SysMenu(models.Model):
    """
    菜单表
    """
    id = models.AutoField(primary_key=True)
    order = models.IntegerField(blank=True, null=True, verbose_name="排序号")
    caption = models.CharField(max_length=32, blank=True, null=True, verbose_name="菜单名称")
    icon = models.CharField(max_length=32, blank=True, null=True, verbose_name="图标")
    url = models.CharField(max_length=128, blank=True, null=True, verbose_name="请求路由")
    pid = models.IntegerField(blank=True, null=True, verbose_name="父节点id")
    remark = models.CharField(max_length=128, blank=True, null=True, verbose_name="描述")
    display = models.IntegerField(blank=True, null=True, verbose_name="显隐")

    class Meta:
        db_table = 't_menus'


class SysRole(models.Model):
    """
    角色表
    """
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=32, blank=True, null=True, verbose_name="角色名")
    abbreviation = models.CharField(max_length=32, blank=True, null=True, verbose_name="缩写")
    remark = models.CharField(max_length=128, blank=True, null=True, verbose_name="备注")
    order = models.IntegerField(blank=True, null=True, verbose_name="排序号")

    class Meta:
        db_table = 't_role'


class RoleMenu(models.Model):
    """
    角色菜单关联表
    """
    id = models.AutoField(primary_key=True)
    menu_id = models.IntegerField(default=1, verbose_name="菜单")
    role_id = models.IntegerField(default=1, verbose_name="角色")

    class Meta:
        db_table = 't_role_menu'


class Nest(models.Model):
    """
    机巢信息表
    """
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, verbose_name="机巢名称")
    model = models.CharField(max_length=50, verbose_name="机巢型号", default='')
    nest_sn = models.CharField(max_length=50, unique=True, verbose_name="机巢SN")
    plane_model = models.CharField(max_length=50, verbose_name="飞机型号", default='')
    plane_sn = models.CharField(max_length=50, verbose_name="飞机SN")
    location = models.CharField(max_length=255, verbose_name="机巢位置", default='')
    organization = models.CharField(max_length=255, verbose_name="所属单位", default='')
    longitude = models.FloatField(verbose_name="机巢经度", default=0)
    latitude = models.FloatField(verbose_name="机巢纬度", default=0)
    status = models.IntegerField(verbose_name="机巢状态", default=1)
    owner = models.CharField(verbose_name="维护人", max_length=100, default='')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    last_modify_time = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        db_table = 't_nest'
        verbose_name = "机巢信息"
        verbose_name_plural = verbose_name
        ordering = ['-create_time']  # 按创建时间倒序排列

    def __str__(self):
        return self.name

class Region(models.Model):
    """
    行政区划表
    """
    region_id = models.AutoField(primary_key=True)
    region_name = models.CharField(verbose_name="行政区划名称", max_length=50, default='')
    region_level = models.IntegerField(verbose_name="行政区划级别", default=0)
    region_code = models.CharField(verbose_name="行政区划代码", max_length=50, default='')
    parent_id = models.IntegerField(verbose_name="父级id", default=0)
    parent_name = models.CharField(verbose_name="父级名称", max_length=50, default='')
    parent_code = models.CharField(verbose_name="父级代码", max_length=50, default='')
    longitude = models.FloatField(verbose_name="经度", default=0)
    latitude = models.FloatField(verbose_name="纬度", default=0)
    create_time = models.DateTimeField(auto_now_add=True, null=True, verbose_name='创建时间')

    def __str__(self):
        return self.region_name

    class Meta:
        db_table = 't_region'