import datetime
from django.db import models
from apps.system.models import User


class Resource(models.Model):
    """
    资源表
    """
    id = models.AutoField(primary_key=True)
    name = models.CharField(verbose_name='资源名称', default='', max_length=100, unique=True)
    url = models.CharField(verbose_name='资源地址', default='', max_length=255)
    owner = models.ForeignKey(User, verbose_name='上传人', default='', on_delete=models.CASCADE)
    source_type = models.CharField(verbose_name='资源类型', max_length=20, default='地图服务')
    service_type = models.CharField(verbose_name='服务类型', max_length=20, default='iServer')
    coordinate_system = models.CharField(verbose_name='坐标系', default='', max_length=50)
    center = models.CharField(verbose_name='中心点坐标', max_length=50, default='')
    data_type = models.CharField(verbose_name='数据类型', max_length=50, default='', null=True)
    county = models.CharField(verbose_name='行政区编码', default='', max_length=50)
    datasource_name = models.CharField(verbose_name='数据源名称', default='', max_length=50, null=True)
    datasets_name = models.CharField(verbose_name='数据集名称', default='', max_length=50, null=True)
    create_time = models.DateTimeField(auto_now=True, null=True, verbose_name='创建时间')
    append_time = models.CharField(verbose_name='资源创建时间', default='', max_length=50)
    count = models.IntegerField(verbose_name='图斑数量', default=1, null=True)
    map_url = models.CharField(verbose_name='地图服务地址,地类分割成果服务专用', null=True, max_length=255)
    datasets_count = models.CharField(verbose_name='不同类别对应图斑数量', default='1,2', null=True, max_length=255)
    polygon_color = models.CharField(verbose_name='图斑颜色', default='#fff', null=True, max_length=255)
    polygon_opacity = models.FloatField(verbose_name='图斑透明度', default=0.8, null=True, blank=True)
    polygon_weight = models.IntegerField(verbose_name='图斑宽度', default=2, null=True, blank=True)
    buffer_distance = models.CharField(verbose_name="", default='', max_length=10)
    gis_service_type = models.CharField(verbose_name="GIS服务类型", default='1', max_length=10,
                                        help_text="1:iServer,2:ArcGIS,3:天地图,4:geoserver")
    is_show = models.IntegerField(verbose_name='是否显示', default=1)
    is_show_on_panorama = models.IntegerField(verbose_name='是否显示全景图', default=1)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 't_resource'


class Notify(models.Model):
    """
    通知表
    """
    id = models.AutoField(primary_key=True)
    file_id = models.CharField(verbose_name="图片ID", max_length=100, default='')
    url = models.CharField(verbose_name="图片URL", max_length=500, default='')
    notify_type = models.CharField(verbose_name="通知类型", max_length=100, default='')
    save_path = models.CharField(verbose_name="图片保存路径", max_length=500, default='')
    create_time = models.DateTimeField(auto_now=True, null=True, verbose_name='通知时间')

    def __str__(self):
        return self.file_id

    class Meta:
        db_table = 't_notify'


class Grid(models.Model):
    """
    网格表
    """
    grid_id = models.CharField(verbose_name="网格编号", max_length=50, default='', primary_key=True)
    grid_name = models.CharField(verbose_name="网格名称", max_length=100, default='')
    kml_path = models.CharField(verbose_name="kml文件路径", max_length=500, default='')
    street = models.CharField(verbose_name="街道", max_length=100, default='')
    county = models.CharField(verbose_name="区县", max_length=100, default='')
    count = models.IntegerField(verbose_name="全景点数量", default=0)
    grid_operator = models.ForeignKey(User, verbose_name="网格员", related_name='operator_name', null=True, blank=True,
                                      on_delete=models.PROTECT)
    uploader = models.ForeignKey(User, verbose_name="上传人", related_name='uploader_name', null=True, blank=True,
                                 on_delete=models.PROTECT)
    center_x = models.FloatField(verbose_name="网格中心点x坐标", default=0)
    center_y = models.FloatField(verbose_name="网格中心点y坐标", default=0)
    order = models.IntegerField(verbose_name="排序号", default=1)
    create_time = models.DateTimeField(auto_now=True, null=True, verbose_name='创建时间')

    def __str__(self):
        return self.grid_name

    class Meta:
        db_table = 't_grid'


class Batch(models.Model):
    """
    批次表
    """
    batch_id = models.CharField(verbose_name="批次编号", max_length=50, default='', primary_key=True)
    batch_name = models.CharField(verbose_name="批次名称", max_length=100, default='')
    grid = models.ForeignKey(Grid, verbose_name="关联网格", null=True, blank=True,
                             on_delete=models.PROTECT)
    start_date = models.DateField(verbose_name="开始日期", null=True, blank=True, default=datetime.date.today)
    end_date = models.DateField(verbose_name="结束日期", null=True, blank=True)
    count = models.IntegerField(verbose_name="全景点数量", default=0)
    status = models.IntegerField(verbose_name="状态", default=0)
    operator = models.CharField(verbose_name="操作人", default="", max_length=50)
    year = models.CharField(verbose_name="年", default='2024', max_length=4)
    month = models.CharField(verbose_name="月", default='9', max_length=2)
    order = models.IntegerField(verbose_name="批次", default=1)
    street = models.CharField(verbose_name="街道", default='', max_length=50)
    region = models.CharField(verbose_name="所属区域", default='', null=True, blank=True, max_length=100)
    batch_type = models.IntegerField(verbose_name="批次类型", default=0, help_text="0:固定批次 1:临时批次")
    change_detection = models.IntegerField(verbose_name="是否做变化检测", default=0,
                                           help_text="0：不做变化检测，1：做变化检测")
    create_time = models.DateTimeField(auto_now=True, null=True, verbose_name='创建时间')

    def __str__(self):
        return self.batch_id

    class Meta:
        db_table = 't_batch'


class PointLocation(models.Model):
    """
    全景点位表
    """
    POINT_TYPE = ((0, "临时全景点"), (1, "定制全景点"))
    point_id = models.CharField(verbose_name="全景编号", max_length=50, default='', primary_key=True)
    point_name = models.CharField(verbose_name="全景名称", max_length=50, default='', null=True, blank=True)
    grid = models.ForeignKey(Grid, verbose_name="关联网格", null=True, blank=True,
                             on_delete=models.PROTECT)
    longitude = models.FloatField(verbose_name="经度", default=0)
    latitude = models.FloatField(verbose_name="纬度", default=0)
    point_type = models.IntegerField(verbose_name="点位类型", default=1, help_text="0:临时全景点 1:定制全景点")
    create_time = models.DateTimeField(auto_now=True, null=True, verbose_name='创建时间')

    def __str__(self):
        return self.point_id

    class Meta:
        db_table = 't_point_location'


class Scene(models.Model):
    """
    使用场景表
    """
    scene_id = models.AutoField(primary_key=True, verbose_name='场景ID')
    scene_name = models.CharField(verbose_name="场景名称", default='', max_length=100)
    operator = models.ForeignKey(User, verbose_name="操作用户", on_delete=models.CASCADE, null=True)
    labels = models.TextField(verbose_name="类别")
    create_time = models.DateTimeField(auto_now=True, null=True, verbose_name='创建时间')

    def __str__(self):
        return self.scene_name

    class Meta:
        db_table = 't_scene'


class UploadBatch(models.Model):
    """
    上传表
    """
    id = models.AutoField(primary_key=True)
    batch = models.ForeignKey(Batch, verbose_name="批次", null=True, blank=True, on_delete=models.CASCADE)
    grid_operator = models.CharField(verbose_name="网格员", default='', max_length=50)
    file_path = models.CharField(verbose_name="保存路径", default='', max_length=255)
    count = models.IntegerField(verbose_name="上传数量", default=0)
    status = models.IntegerField(verbose_name="状态", default=0)
    batch_type = models.IntegerField(verbose_name="批次类型", default=0, help_text="0:固定批次 1:临时批次")
    create_time = models.DateTimeField(auto_now=True, null=True, verbose_name='创建时间')

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = 't_upload_batch'


class PanoramaImage(models.Model):
    """
    全景图表
    """
    image_id = models.CharField(verbose_name="图片编号", max_length=50, default='', primary_key=True)
    image_name = models.CharField(verbose_name="图片名称", max_length=100, default='')
    image_path = models.CharField(verbose_name="图片路径", max_length=500, default='')
    upload_batch = models.ForeignKey(UploadBatch, verbose_name="上传批次", null=True, on_delete=models.CASCADE)
    batch = models.ForeignKey(Batch, verbose_name="批次", null=True, blank=True, on_delete=models.CASCADE)
    point = models.ForeignKey(PointLocation, verbose_name="全景点位", null=True, blank=True, on_delete=models.CASCADE)
    longitude = models.FloatField(verbose_name="经度", default=0)
    latitude = models.FloatField(verbose_name="纬度", default=0)
    height = models.FloatField(verbose_name="相对高度", default=0)
    image_width = models.FloatField(verbose_name="像素宽度", default=0)
    image_height = models.FloatField(verbose_name="像素高度", default=0)
    yaw_degree = models.FloatField(verbose_name="偏航角", default=0)
    status = models.IntegerField(verbose_name="状态", default=0, help_text="0:初始化，1:已识别，2：已判读")
    count = models.IntegerField(verbose_name="计数", default=0)
    absolute_height = models.FloatField(verbose_name="绝对高度", default=0)
    cube_resolution = models.IntegerField(verbose_name="立方体贴图分辨率", default=4576)
    max_level = models.IntegerField(verbose_name="最大层级", default=5)
    desc = models.TextField(verbose_name="描述", default="", blank=True, null=True)
    tile_resolution = models.IntegerField(verbose_name="瓦片分辨率", default=512)
    create_time = models.DateTimeField(auto_now=True, null=True, verbose_name='创建时间')
    last_modify_time = models.DateTimeField(auto_now=True, null=True, verbose_name='最后修改时间')

    def __str__(self):
        return self.image_name

    class Meta:
        db_table = 't_panorama_image'


class Clue(models.Model):
    """
    线索表
    """
    clue_id = models.AutoField(verbose_name="线索编号", primary_key=True)
    clue_name = models.CharField(verbose_name="线索名称", max_length=50, default='')
    longitude = models.FloatField(verbose_name="经度", default=0)
    latitude = models.FloatField(verbose_name="纬度", default=0)
    batch = models.ForeignKey(Batch, verbose_name="所属批次", null=True, blank=True,
                              on_delete=models.CASCADE)
    panorama_image = models.ForeignKey(PanoramaImage, verbose_name="所属全景图片", null=True, blank=True,
                                       on_delete=models.CASCADE)
    inspector = models.ForeignKey(User, verbose_name="复核人员", null=True, blank=True,
                                  on_delete=models.CASCADE)
    file_path = models.CharField(verbose_name="线索图片路径", max_length=500, default='')
    center_x = models.FloatField(verbose_name="中心点x", default=0)
    center_y = models.FloatField(verbose_name="中心点y", default=0)
    status = models.IntegerField(verbose_name="线索状态", default=0,
                                 help_text="0:初始化，待审批，1：已审批，无效，2：已审批，待核实，3:已打点 ，-1：已关闭，误检")
    position = models.TextField(verbose_name="方框的位置", default='')
    address = models.CharField(verbose_name="地址", default='', max_length=255)
    score = models.FloatField(verbose_name="概率", default=0.5)
    verification_conclusion = models.TextField(verbose_name="核实结论", default='')
    clue_source = models.CharField(verbose_name="线索来源", default='', max_length=50)
    is_new_clue = models.IntegerField(verbose_name="是否新线索", default=0)
    szdl = models.TextField(verbose_name="所在地类", default='')
    in_not_detection = models.IntegerField(verbose_name="是否在不检测区域", default=1, help_text="0:否，1：是")
    create_time = models.DateTimeField(auto_now_add=True, null=True, verbose_name='创建时间')
    last_modify_time = models.DateTimeField(auto_now=True, null=True, verbose_name='最后修改时间')

    def __str__(self):
        return self.clue_name

    class Meta:
        db_table = 't_clue'


class BufferFile(models.Model):
    """
    文件表
    """
    file_id = models.CharField(verbose_name="文件编号", primary_key=True, max_length=50)
    file_name = models.CharField(verbose_name="文件名称", max_length=50, default='')
    file_type = models.CharField(verbose_name="文件类型", max_length=50, default='')
    file_path = models.CharField(verbose_name="文件路径", max_length=500, default='')
    file_size = models.CharField(verbose_name="文件大小", max_length=50, default='')
    owner = models.CharField(verbose_name="文件拥有者", max_length=50, default='')
    count = models.IntegerField(verbose_name="下载次数", default=0)
    file_extension = models.CharField(verbose_name="文件扩展名", max_length=50, default='')
    desc = models.TextField(verbose_name="文件描述", max_length=500, default='')
    create_time = models.DateTimeField(auto_now_add=True, null=True, verbose_name='创建时间')

    def __str__(self):
        return self.file_name

    class Meta:
        db_table = 't_file'


class VerifyTask(models.Model):
    """
    核实任务表
    """
    task_id = models.AutoField(verbose_name="任务编号", primary_key=True)
    task_name = models.CharField(verbose_name="任务名称", max_length=50, default='')
    file_path = models.CharField(verbose_name="文件路径", max_length=500, default='')
    file_size = models.CharField(verbose_name="文件大小", max_length=50, default='')
    status = models.CharField(verbose_name="任务状态", max_length=50, default='',
                              help_text='待推送、待拍摄、已完成、坐标推送失败、任务停止')
    create_time = models.DateTimeField(auto_now_add=True, null=True, verbose_name='创建时间')

    def __str__(self):
        return self.task_name

    class Meta:
        db_table = 't_verify_task'


class VerifyClue(models.Model):
    """
    核实线索表
    """
    clue_id = models.AutoField(verbose_name="线索编号", primary_key=True)
    longitude = models.FloatField(verbose_name="经度", default=0)
    latitude = models.FloatField(verbose_name="纬度", default=0)
    task = models.ForeignKey(VerifyTask, verbose_name="所属核实任务", null=True, blank=True,
                             on_delete=models.CASCADE)
    record_time = models.DateTimeField(auto_now_add=True, null=True, verbose_name='创建时间')
    division_code = models.CharField(verbose_name="行政区划代码", max_length=50, default='')
    address = models.CharField(verbose_name="地址", max_length=500, default='')
    level = models.CharField(verbose_name="线索等级", max_length=50, default='')
    status = models.CharField(verbose_name="线索状态", max_length=50, default='', help_text='未核实、已核实')

    def __str__(self):
        return self.address

    class Meta:
        db_table = 't_verify_clue'


class PolygonTask(models.Model):
    """
    上传图斑任务
    任务编号，所属街道，状态（待核实、核实中、已关闭），需核实图斑数，已核实图斑数，核实人，操作（查看  关闭）
    """
    id = models.AutoField(primary_key=True)
    task_id = models.CharField(verbose_name="任务编号", max_length=100, default='')
    street = models.CharField(verbose_name="街道", max_length=100, default='')
    status = models.IntegerField(verbose_name="图斑状态", default=0)
    need_verify = models.IntegerField(verbose_name="需核实图斑数", default=0)
    verified = models.IntegerField(verbose_name="已核实图斑数", default=0)
    file_id = models.CharField(verbose_name="文件编号", max_length=50, default='')
    verifier = models.ForeignKey(User, verbose_name="核实人", default=None, on_delete=models.SET_NULL, null=True,
                                 blank=True)
    task_type = models.IntegerField(verbose_name="任务类型", default=0, help_text="0:上传核实图斑 1:上传不检测区域")
    create_person = models.CharField(verbose_name="创建人", default='', null=True, max_length=50)
    create_time = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)
    update_time = models.DateTimeField(verbose_name='更新时间', auto_now=True)

    def __str__(self):
        return self.file_id

    class Meta:
        db_table = 't_polygon_task'
        verbose_name = '上传图斑任务表'
        verbose_name_plural = verbose_name


class PolygonData(models.Model):
    id = models.AutoField(primary_key=True)
    bsm = models.CharField(verbose_name="图斑唯一编号", max_length=100, default='')
    name = models.CharField(verbose_name="图斑名称", max_length=100, default='', null=True, blank=True)
    unit_name = models.CharField(verbose_name="权属单位名称", max_length=100, default='', null=True, blank=True)
    status = models.IntegerField(verbose_name="图斑状态", default=0)
    verify_conclusion = models.TextField(verbose_name="核实结论", default='')
    polygon_task = models.ForeignKey(PolygonTask, verbose_name="图斑任务", on_delete=models.CASCADE)
    polygon = models.TextField(verbose_name="面", default='')
    yaw = models.FloatField(verbose_name="航向角", default=0)
    pitch = models.FloatField(verbose_name="俯仰角", default=0)
    create_time = models.DateTimeField('创建时间', auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 't_polygon_data'
        verbose_name = '上传图斑表'
        verbose_name_plural = verbose_name


class FrameArea(models.Model):
    """
    不检测区域表
    """
    id = models.AutoField(primary_key=True)
    name = models.CharField(verbose_name="图斑名称", max_length=100, default='')
    center_x = models.FloatField(verbose_name='中心点x', null=True, blank=True)
    center_y = models.FloatField(verbose_name='中心点y', null=True, blank=True)
    area = models.FloatField(verbose_name='面积', null=True)
    status = models.IntegerField(verbose_name="状态", default=0)
    area_type = models.IntegerField(verbose_name="区域类型", default=0, help_text="0:不检测区域 1:目标框")
    polygon = models.TextField(verbose_name="图斑面形成的点")
    pixel = models.TextField(verbose_name="图斑像素点形成的面")
    point = models.ForeignKey(PointLocation, on_delete=models.CASCADE, verbose_name='关联全景点位')
    polygon_task = models.ForeignKey(PolygonTask, verbose_name="图斑任务", on_delete=models.PROTECT, null=True,
                                     blank=True)
    create_time = models.DateTimeField('创建时间', auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 't_frame_area'
        verbose_name = '不检测区域面'
        verbose_name_plural = verbose_name


class Route(models.Model):
    """
    航线表
    """
    id = models.AutoField(primary_key=True)
    name = models.CharField(verbose_name="航线名称", max_length=100, default='')
    status = models.IntegerField(verbose_name="状态", default=0)
    camera_size = models.IntegerField(verbose_name="相机尺寸", default=0)
    start_point = models.CharField(verbose_name="起始点", max_length=100, default='')
    end_point = models.CharField(verbose_name="结束点", max_length=100, default='')
    height = models.FloatField(verbose_name='飞行高度', null=True, blank=True)
    route_type = models.CharField(verbose_name="航线类型", max_length=100, default='', help_text='人工选点，算法规划')
    file_id = models.CharField(verbose_name="文件id", default='', max_length=100)
    lines = models.TextField(verbose_name="航线数据", default='')
    create_time = models.DateTimeField('创建时间', auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 't_route'
        verbose_name = '航线表'
        verbose_name_plural = verbose_name


class BatchResource(models.Model):
    """
    批次线索关联业务数据资源表
    """
    id = models.AutoField(primary_key=True)
    batch = models.ForeignKey(Batch, verbose_name="批次", on_delete=models.CASCADE)
    resource = models.ForeignKey(Resource, verbose_name="资源", on_delete=models.CASCADE)
    create_time = models.DateTimeField('创建时间', auto_now_add=True)

    def __str__(self):
        return self.batch.batch_name

    class Meta:
        db_table = 't_batch_resource'
        verbose_name = '批次关联资源表'
        verbose_name_plural = verbose_name


class PlotRecord(models.Model):
    """
    标绘记录表
    """
    id = models.AutoField(primary_key=True)
    color = models.CharField(verbose_name="颜色", max_length=50, default='')
    transparent = models.CharField(verbose_name="透明度", max_length=50, default='')
    plot_type = models.CharField(verbose_name="标绘类型", max_length=50, default='')
    plot_name = models.CharField(verbose_name="名称", max_length=50, default='')
    plot_status = models.IntegerField(verbose_name="状态", default=0)
    plot_desc = models.CharField(verbose_name="描述", max_length=255, default='', null=True, blank=True)
    line_color = models.CharField(verbose_name="线颜色", max_length=50, default='')
    line_width = models.CharField(verbose_name="线宽度", max_length=50, default='')
    clue = models.ForeignKey(Clue, verbose_name="线索", on_delete=models.CASCADE)
    clue_name = models.CharField(verbose_name="线索名称", max_length=50, default='')
    image_id = models.CharField(verbose_name="图片ID", max_length=100, default='')
    create_person = models.CharField(verbose_name="创建人", max_length=50, default='')
    point_name = models.CharField(verbose_name="点位名称", max_length=50, default='')
    point_id = models.CharField(verbose_name="点位ID", max_length=50, default='')
    geometry = models.TextField(verbose_name="几何信息", default='')
    order_index = models.IntegerField(verbose_name="排序", default=0)
    plot_area = models.FloatField(verbose_name='面积', null=True, blank=True)
    create_time = models.DateTimeField('创建时间', auto_now_add=True)

    def __str__(self):
        return self.plot_name

    class Meta:
        db_table = 't_plot_record'


class FlyOrder(models.Model):
    """
    订单表
    """
    id = models.AutoField(primary_key=True)
    order_name = models.CharField(verbose_name="订单名称", max_length=100, default='')
    data_type = models.CharField(verbose_name="数据类型", max_length=100, default='')
    organization = models.CharField(verbose_name="所属单位", max_length=255, default='')
    collect_type = models.CharField(verbose_name="采集方式", default='', max_length=100)
    create_person = models.CharField(verbose_name="创建人", default='', max_length=100)
    status = models.IntegerField(verbose_name="订单状态", default=0)
    county = models.CharField(verbose_name="县区", default='', max_length=100)
    route = models.ForeignKey(Route, on_delete=models.PROTECT, verbose_name="关联航线")
    collect_time = models.DateField(verbose_name='采集时间', default=datetime.datetime.now())
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    class Meta:
        db_table = 't_fly_order'
        verbose_name = "订单表"
        verbose_name_plural = verbose_name
        ordering = ['-create_time']  # 按创建时间倒序排列

    def __str__(self):
        return self.order_name


class SupervisionProject(models.Model):
    """
    监管项目表
    """
    id = models.AutoField(primary_key=True)
    data_type = models.CharField(verbose_name="数据类型", max_length=100, default='')
    count = models.IntegerField(verbose_name="监管项目数量", default='')
    create_person = models.CharField(verbose_name="创建人", default='', max_length=100)
    status = models.IntegerField(verbose_name="订单状态", default=0)
    county = models.CharField(verbose_name="县区", default='', max_length=100)
    collect_time = models.DateField(verbose_name='采集时间', default=datetime.datetime.now())
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    class Meta:
        db_table = 't_supervision_project'
        verbose_name = "监管项目表"
        verbose_name_plural = verbose_name
        ordering = ['-create_time']  # 按创建时间倒序排列

    def __str__(self):
        return str(self.id)


class SupervisionProjectRoute(models.Model):
    """
    监管项目航线关联表
    """
    id = models.AutoField(primary_key=True)
    supervision_project_id = models.IntegerField(verbose_name="监管项目")
    route_id = models.IntegerField(verbose_name="航线")
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    class Meta:
        db_table = 't_supervision_project_route'
        verbose_name = "监管项目航线关联表"
        verbose_name_plural = verbose_name
        ordering = ['-create_time']  # 按创建时间倒序排列

    def __str__(self):
        return str(self.id)


class SupervisionProjectPolygon(models.Model):
    """
    监管项目图斑
    """
    id = models.AutoField(primary_key=True)
    supervision_project_id = models.IntegerField(verbose_name="监管项目")
    polygon = models.TextField(verbose_name="图斑", default='')
    latitude = models.FloatField(verbose_name="纬度", default=0)
    longitude = models.FloatField(verbose_name="经度", default=0)
    polygon_type = models.CharField(verbose_name="图斑类型", default='3', max_length=100)  # 1：临时用地恢复 2：山水工程 3:建设项目
    construction_desc = models.TextField(verbose_name="建设描述", default='')
    color_desc = models.TextField(verbose_name="颜色描述", default='')
    point_id = models.CharField(verbose_name="关联全景点", default='', max_length=100, null=True, blank=True)
    status = models.IntegerField(verbose_name="状态", default=0)
    is_del = models.IntegerField(verbose_name='是否删除', default=0)
    create_person = models.CharField(verbose_name="创建人", default='', max_length=100)
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    update_time = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        db_table = 't_supervision_project_polygon'
        verbose_name = "监管项目图斑表"
        verbose_name_plural = verbose_name
        ordering = ['-create_time']  # 按创建时间倒序排列

    def __str__(self):
        return str(self.id)


class SupervisionPolygonVertical(models.Model):
    """
    监管项目图斑俯视图
    """
    id = models.AutoField(primary_key=True)
    polygon_id = models.IntegerField(verbose_name="图斑ID", default=0)
    vertical_view_id = models.IntegerField(verbose_name="俯视图ID", default=0)
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    update_time = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        db_table = 't_supervision_polygon_vertical'
        verbose_name = "监管项目图斑表"
        verbose_name_plural = verbose_name
        ordering = ['-create_time']  # 按创建时间倒序排列

    def __str__(self):
        return str(self.id)
