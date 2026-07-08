def parse_json_request(request):
    """解析 JSON 格式的请求体（POST/PUT 请求用）"""
    try:
        return json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({
            'code': 400,
            'msg': '请求数据格式错误（需 JSON 格式）',
            'data': None
        }, status=400)

def paginate_queryset(queryset, request):
    """原生分页实现：page=页码，size=每页条数"""
    # 获取分页参数（默认 page=1，size=10）
    page = int(request.GET.get('page', 1))
    size = int(request.GET.get('size', 10))
    size = min(size, 100)  # 限制最大每页 100 条

    # 计算偏移量
    offset = (page - 1) * size
    total = queryset.count()  # 总记录数
    paginated_data = queryset[offset:offset + size]  # 分页后的数据

    return {
        'records': list(paginated_data.values()),  # 转为字典列表
        'total': total
    }

def validate_region_data(data, is_update=False):
    """验证区域数据（新增/编辑通用）"""
    errors = []

    # 必填字段验证（新增时必须，编辑时可选）
    required_fields = ['region_name', 'region_code', 'longitude', 'latitude']
    if not is_update:
        for field in required_fields:
            if not data.get(field):
                errors.append(f'{field} 为必填项')
    else:
        # 编辑时至少传一个字段
        if not any([data.get(field) for field in required_fields + ['parent_id']]):
            errors.append('至少需传递一个修改字段')

    # 经纬度范围验证
    if data.get('longitude') is not None:
        try:
            lon = float(data['longitude'])
            if not (-180 <= lon <= 180):
                errors.append('经度范围必须在 -180 到 180 之间')
        except (ValueError, TypeError):
            errors.append('经度必须为数字')

    if data.get('latitude') is not None:
        try:
            lat = float(data['latitude'])
            if not (-90 <= lat <= 90):
                errors.append('纬度范围必须在 -90 到 90 之间')
        except (ValueError, TypeError):
            errors.append('纬度必须为数字')

    # 父级 ID 验证（必须为整数）
    if data.get('parent_id') is not None:
        try:
            parent_id = int(data['parent_id'])
            if parent_id < 0:
                errors.append('父级 ID 不能为负数')
        except (ValueError, TypeError):
            errors.append('父级 ID 必须为整数')

    return errors