// commonApi.js

import request from './request'; // 导入我们之前定义的axios实例

/**
 * @description 获取菜单信息
 */
export const getSysMenuListApi = () => {
    return request({
        url: `/api/system/menu_list`,
        method: 'get'
    });
};
/**
 * @description 获取枚举(不认证)
 */
export const getEnumOptionApi = (data) => {
    return request({
        url: `/api/system/get-dict-by-type?dict_type=${data}`,
        method: 'get'
    });
};
/**
 * @description 获取加密公钥
 */
export const getPublicKeyApi = (data) => {
    return request({
        url: `/api/system/get-public-key`,
        method: 'get'
    });
};
/**
 * @description 获取用户信息
 */
export const getUserListApi = (data) => {
    return request({
        url: '/api/system/user/list',
        method: 'post',
        data
    });
};
/**
 * @description 分配角色
 */
export const postUserRoleApi = (data) => {
    return request({
        url: '/api/system/user_role_relation',
        method: 'post',
        data
    });
};
/**
 * @description 监听用户状态改变 停用用户
 */
export const postUserStatusApi = (data) => {
    return request({
        url: '/api/system/user-status/edit',
        method: 'post',
        data
    });
};

/**
 * @description 新增用户信息
 */
export const postUserDataApi = (data) => {
    return request({
        url: '/api/system/user/add',
        method: 'post',
        data
    });
};
/**
 * @description 删除用户信息
 */
export const deleteUserDataApi = (data) => {
    return request({
        url: '/api/system/user/del',
        method: 'post',
        data
    });
};
/**
 * @description 修改用户信息
 */
export const putUserDataApi = (data) => {
    return request({
        url: '/api/system/user/edit',
        method: 'post',
        data
    });
};
/**
 * @description 获取首页信息
 */
export const getInfoApi = () => {
    return request({
        url: '/api/system/get_info',
        method: 'get'
    });
};
/**
 * @description 用户登录校验
 */
export const getLoginCheckApi = (data) => {
    return request({
        url: '/api/system/login_check',
        method: 'post',
        data
    });
};
/**
 * @description 获取任务列表
 */
export const getTaskListApi = (data) => {
    return request({
        url: '/lais/site/inspection/task/get-task-by-conditions',
        method: 'post',
        data
    });
};
/**
 * @description 根据id删除目标检测任务
 */
export const deleteOdImageApi = (task_id) => {
    return request({
        url: `/common/task_del/${task_id}`,
        method: 'delete'
    });
};
/**
 * @description 获取全景任务列表
 */
export const getTaskDataListApi = (data) => {
    return request({
        url: '/common/task_data',
        method: 'post',
        data
    });
};
/**
 * @description 根据id删除全景任务
 */
export const deletePanoramaImageApi = (data) => {
    return request({
        url: `/common/panorama_task_del`,
        method: 'post',
        data
    });
};
/**
 * @description 获取角色相关信息
 */
export const getRoleDataApi = (data) => {
    return request({
        url: `/api/system/role_operation?name=${data}`,
        method: 'get'
    });
};
/**
 * @description 新增角色相关信息
 */
export const postRoleDataApi = (data) => {
    return request({
        url: `/api/system/role_operation`,
        method: 'post',
        data
    });
};
/**
 * @description 修改角色相关信息
 */
export const putRoleDataApi = (data) => {
    return request({
        url: '/api/system/role_operation',
        method: 'put',
        data
    });
};
/**
 * @description 删除角色相关信息
 */
export const deleteRoleDataApi = (data) => {
    return request({
        url: '/api/system/role_operation',
        method: 'delete',
        data
    });
};
/**
 * @description 查询关联用户信息
 */
export const getUserRoleDataApi = () => {
    return request({
        url: '/api/system/user_related',
        method: 'get'
    });
};
/**
 * @description 用户角色信息关联
 */
export const postUserRoleDataApi = (data) => {
    return request({
        url: '/api/system/user_related',
        method: 'post',
        data
    });
};
/**
 * @description 用户角色信息关联
 */
export const UserRoleDataUnrelatedApi = (data) => {
    return request({
        url: '/api/system/user_related',
        method: 'post',
        data
    });
};
/**
 * @description 菜单角色信息关联
 */
export const getMenuRoleDataApi = (id) => {
    return request({
        url: `/api/system/menu_related?id=${id}`,
        method: 'get'
    });
};
/**
 * @description 菜单角色信息关联
 */
export const postMenuRoleDataApi = (data) => {
    return request({
        url: `/api/system/menu_related`,
        method: 'post',
        data: data
    });
};
/**
 * @description 日志信息获取
 */
export const getLogDataApi = (data) => {
    return request({
        url: `/scp-manage/rest/v1/log/business/page?conditions=${data.conditions}&page=${data.page}&limit=${data.limit}&principal=${data.userName}&begin=&end=`,
        method: 'get'
    });
};
/**
 * @description 菜单信息获取
 */
export const getMenuDataApi = (data) => {
    return request({
        url: `/api/system/menu_operation?caption=${data}`,
        method: 'get'
    });
};
/**
 * @description 删除菜单信息
 */
export const deleteMenuDataApi = (data) => {
    return request({
        url: `/scp-account/rest/v1/modules/${data.id}`,
        method: 'post',
        data
    });
};
/**
 * @description 新增菜单信息
 */
export const postMenuDataApi = (data) => {
    return request({
        url: `/api/system/menu_operation`,
        method: 'post',
        data
    });
};
/**
 * @description 修改菜单信息
 */
export const putMenuDataApi = (data) => {
    return request({
        url: `/api/system/menu_operation`,
        method: 'put',
        data
    });
};
/**
 * @description 下载接口
 */
export const getDownloadFileApi = (data) => {
    return request({
        url: `/scp-storage/ui/v1/storage/yunpan/file/download?id=${data}`,
        method: 'get',
        responseType: 'blob'
    });
};

/**
 * @description 航线下载接口
 */
export const getDownloadRouteFileApi = (data) => {
    return request({
        url: `/api/panorama/file/download/${data}`,
        method: 'get',
        responseType: 'blob'
    });
};

/**
 * @description 获取图片的长和宽
 */
export const getShapeApi = (id) => {
    return request({
        url: `/common/get_shape?task_id=${id}`,
        method: 'get'
    });
};

/**
 * @description 体验中心新增目标检测点
 */
export const postLabelDataApi = (data) => {
    return request({
        url: `/common/label_data`,
        method: 'post',
        data
    });
};
/**
 * @description 新增目标检测点
 */
export const postClueInfoApi = (data) => {
    return request({
        url: `/api/panorama/clue/objectives`,
        method: 'post',
        data
    });
};
/**
 * @description 查询检测结果
 */
export const getAlarmsListApi = (id) => {
    return request({
        url: `/common/get_alarms_list?task_id=${id}`,
        method: 'get'
    });
};

/**
 * @description 根据ID删除图斑
 */
export const deleteAlarmsByIdApi = (data) => {
    return request({
        url: `/common/alarms_delete`,
        method: 'post',
        data
    });
};
/**
 * @description 根据ID判断线索
 */
export const changeClueByIdApi = (data) => {
    return request({
        url: `/api/panorama/clue/clue_status`,
        method: 'post',
        data
    });
};
/**
 * @description 根据ID查询图斑
 */
export const getAlarmsByIdApi = (id) => {
    return request({
        url: `/common/get_alarms_by_id?id=${id}`,
        method: 'get'
    });
};

/**
 * @description 获取字典类型数据
 */
export const getDictTypeListApi = (data) => {
    return request({
        url: `/api/system/dict-type/list`,
        method: 'post',
        data
    });
};
/**
 * @description 新增字典类型数据
 */
export const postDictTypeDataApi = (data) => {
    return request({
        url: `/api/system/dict-type/add`,
        method: 'post',
        data
    });
};
/**
 * @description 修改字典类型数据
 */
export const putDictTypeDataApi = (data) => {
    return request({
        url: '/api/system/dict-type/edit',
        method: 'post',
        data
    });
};
/**
 * @description 删除字典类型数据
 */
export const deleteDictTypeDataApi = (data) => {
    return request({
        url: '/api/system/dict-type/del',
        method: 'post',
        data
    });
};
/**
 * @description 获取字典数据
 */
export const getDictDataListApi = (data) => {
    return request({
        url: `/api/system/dict-data/list`,
        method: 'post',
        data
    });
};
/**
 * @description 新增字典数据
 */
export const postDictDataApi = (data) => {
    return request({
        url: `/api/system/dict-data/add`,
        method: 'post',
        data
    });
};
/**
 * @description 修改字典数据
 */
export const putDictDataApi = (data) => {
    return request({
        url: `/api/system/dict-data/edit`,
        method: 'post',
        data
    });
};
/**
 * @description 删除字典数据
 */
export const deleteDictDataApi = (data) => {
    return request({
        url: `/api/system/dict-data/del`,
        method: 'post',
        data
    });
};
/**
 * @description  获取模型列表
 */
export const getModelLists = (data) => {
    return request({
        url: `/lais/site/inspection/models/get-models-by-conditions`,
        method: 'post',
        data
    });
};

/**
 * @description  根据id查询模型
 */
export const getModelDetail = (id) => {
    return request({
        url: `/model/model/${id}`,
        method: 'get'
    });
};

/**
 * @description  获取服务器下的文件夹
 */
export const getFileFolder = () => {
    return request({
        url: '/system/server_path',
        method: 'get'
    });
};

/**
 * @description  获取统计数据
 */
export const getResourceData = () => {
    return request({
        url: '/api/system/sourceOverview',
        method: 'get'
    });
};
/**
 * @description  获取体验页面数据
 */
export const getExperienceData = () => {
    return request({
        url: '/common/experience_data',
        method: 'get'
    });
};

/**
 * @description  获取网格数据表格
 */
export const getGridData = (data) => {
    return request({
        url: `/api/panorama/grid/list`,
        method: 'post',
        data
    });
};
/**
 * @description  上传网格
 */
export const uploadGridData = (data) => {
    return request({
        url: `/api/panorama/grid/add`,
        method: 'post',
        data
    });
};
/**
 * @description 根据网格编号删除网格数据
 */
export const deleteGridByIdApi = (data) => {
    return request({
        url: `/api/panorama/grid/del`,
        method: 'post',
        data
    });
};
/**
 * @description  三维瓦片（3DTiles）列表
 */
export const get3dtilesListApi = () => {
    return request({
        url: `/api/resource/3dtiles-list`,
        method: 'get'
    });
};
/*进行任务管理查询*/
export const getTaskManageTable = (data) => {
    return request({
        url: '/api/panorama/batch/list',
        method: 'post',
        data
    });
};
// 获取区域选择级联数据
export const getRegionOptions = () => {
    return request({
        url: '/api/system/region/get-region-tree-by-user',
        method: 'post'
    });
};
// 注册数据时行政区 选择
export const getRegionInfoListApi = () => {
    return request({
        url: '/api/system/region/region-info-list',
        method: 'get'
    });
};
export const getRegionTreeByUser = () => {
    return request({
        url: '/api/system/region/get-region-tree-by-user',
        method: 'post'
    });
};

//添加批次任务
export const addBatchTask = (data) => {
    return request({
        url: '/api/panorama/batch/add',
        method: 'post',
        data
    });
};
/**
 * @description 获取全景点坐标
 */
export const getPanoramaPointApi = () => {
    return request({
        url: `/api/panorama/panorama-point/get-pointlocation`,
        method: 'post'
    });
};
/**
 * @description 根据经纬度查询最近的全景点
 */
export const getNearestPanoramaPointApi = (data) => {
    return request({
        url: `/api/panorama/panorama-point/nearest`,
        method: 'post',
        data
    });
};
/**
 * @description 根据行政区获取全景点坐标
 */
export const getPanoramaPointByCountryApi = (data) => {
    return request({
        url: `/api/resource/point-location/list`,
        method: 'post',
        data
    });
};
/**
 * @description 获取全景检测页面加载数据
 */
export const getMainDetectionApi = () => {
    return request({
        url: `/api/panorama/main_detection`,
        method: 'get'
    });
};

/**
 * @description  获取地图总览数据
 */
export const getOverViewData = () => {
    return request({
        url: '/api/panorama/map_view_info',
        method: 'post'
    });
};

/**
 * @description  获取线索数据
 */
export const getClueData = (data) => {
    return request({
        url: '/api/panorama/clue/list',
        method: 'post',
        data
    });
};
/**
 * @description 根据批次ID获取批次信息
 */
export const getMainDetectionByBatchIdApi = (data) => {
    return request({
        url: `/api/panorama/main_detection?batchId=${data}`,
        method: 'get'
    });
};
/**
 * @description  获取线索数据(线索总览，仅包含疑似，有效，待审核数据)
 */
export const getClueOverViewData = (data) => {
    return request({
        url: '/api/panorama/map_view_clue_list',
        method: 'post',
        data
    });
};

/**
 * @description 下载网格kml
 */
export const getDownloadPanoramaPointApi = (data) => {
    return request({
        url: `/api/panorama/grid/kml_download?kmlPath=${data}`,
        method: 'get',
        responseType: 'blob'
    });
};
/**
 * @description 下载信息反馈数据
 */
export const getDownloadAnalysisInfoApi = (data) => {
    return request({
        url: `/api/panorama/upload-batch/down_detection_log/${data}`,
        method: 'get',
        responseType: 'blob'
    });
};
// 获取当前页线索核实全景点列表
export const getCurrentPageVerifyClueQuanjingPointsApi = (data) => {
    return request({
        url: `/api/panorama/panorama_image_by_params`,
        method: 'POST',
        data
    });
};
//根据批次获取所有的全景图信息
export const getAllPanoramaImageByBatchIdApi = (data) => {
    return request({
        url: `/api/panorama/panorama_image_all`,
        method: 'post',
        data
    });
};

//获取多期对比
export const getOnePointMultiComInfoApi = (data) => {
    return request({
        url: `/api/panorama/panorama_image_sibling?panorama_image_id=${data}`,
        method: 'get'
    });
};

//获取线索核实线索点信息
export const getOneQuanjingPointClueInfoApi = (data) => {
    return request({
        url: `/api/panorama/clue/get_clue_by_panorama_image_id?panorama_image_id=${data}`,
        method: 'get'
    });
};

//根据线索点id查看
export const queryCluesDataApi = (clue_id) => {
    return request({
        url: `/api/panorama/clue/get_clue_data_by_id?clue_id=${clue_id}`,
        method: 'get'
    });
};

/**
 * @description  全景检测接口
 */
export const postPanoramaDetectionApi = (data) => {
    return request({
        url: '/api/panorama/main_detection',
        method: 'post',
        // timeout:0,
        data
    });
};

/**
 * @description  全景上传管理页面获取表格数据
 */
export const getUploadBatchData = (data) => {
    return request({
        url: '/api/panorama/upload_batch/list',
        method: 'post',
        data
    });
};

/**
 * @description  新增场景
 */
export const addSceneData = (data) => {
    return request({
        url: '/api/panorama/scene/add',
        method: 'post',
        data
    });
};

/**
 * @description  获取场景数据
 */
export const getSceneData = (data) => {
    return request({
        url: '/api/panorama/scene/list',
        method: 'post',
        data
    });
};
/**
 * @description  编辑场景数据
 */
export const editSceneData = (data) => {
    return request({
        url: '/api/panorama/scene/edit',
        method: 'post',
        data
    });
};

/**
 * @description 根据场景编号删除场景表格数据
 */
export const deleteSceneByIdApi = (data) => {
    return request({
        url: `/api/panorama/scene/del`,
        method: 'post',
        data
    });
};

/**
 * @description  报告页面获取批次和场景信息
 */
export const getReportOverview = () => {
    return request({
        url: '/api/report/report_params',
        method: 'post'
    });
};

/**
 * @description  获取报告数据
 */
export const getReportData = (data) => {
    return request({
        url: '/api/report/report_list',
        method: 'post',
        data
    });
};
/**
 * @description  获取批次报告数据
 */
export const getBatchReportData = (data) => {
    return request({
        url: '/api/report/batch_report',
        method: 'post',
        data
    });
};
/**
 * @description  新增报告
 */
export const addReportData = (data) => {
    return request({
        url: '/api/report/report_generate',
        method: 'post',
        data
    });
};
/**
 * @description  报告下载
 */
export const downloadReportData = (data) => {
    return request({
        url: `/api/report/download/${data}`,
        method: 'get',
        responseType: 'blob'
    });
};

/**
 * @description 根据报告编号删除报告
 */
export const deleteReportByIdApi = (data) => {
    return request({
        url: `/api/report/report_delete`,
        method: 'post',
        data
    });
};

/**
 * @description  获取上传进度信息filepload
 */
export const getUploadProgress = () => {
    return request({
        url: `/api/panorama/interpretation_progress`,
        method: 'get'
    });
};

/**
 * @description 根据上传编号删除全景上传表格数据
 */
export const deleteUploadByIdApi = (data) => {
    return request({
        url: `/api/panorama/upload_batch/del`,
        method: 'post',
        data
    });
};


/**
 * @description  获取已经上传的全景点位
 */
export const getUploadPoint = (data) => {
    return request({
        url: `/lais/site/inspection/panorama_view/point_list_by_batch?batchId=${data}`,
        method: 'get'
    });
};

//提交复核
export const submitReviewApi = (data) => {
    return request({
        url: `/api/panorama/panorama_image/review`,
        method: 'post',
        data
    });
};


//删除任务
export const batchDeleteTaskApi = (data) => {
    return request({
        url: `/api/panorama/batch/del`,
        method: 'post',
        data
    });
};

//获取home页大屏信息
export const getHomeScreenDataApi = () => {
    return request({
        url: `/api/panorama/info`,
        method: 'get'
    });
};

//提交重新修改的点位坐标
export const submitCorrectPointApi = (data) => {
    return request({
        url: `/api/panorama/clue-location`,
        method: 'post',
        data
    });
};

//获取首页大屏的八个数据信息
export const getDataInfoApi = () => {
    return request({
        url: `/api/panorama/data_info`,
        method: 'get'
    });
};

//获取对应全景点位对应的多期图片
export const getPanoramaImageApi = (data) => {
    return request({
        url: `/api/panorama/panorama_image_by_point_id`,
        method: 'post',
        data
    });
};
export const getResourceListsApi = (data) => {
    return request({
        url: `/api/resource/resources/list`,
        method: 'post',
        data
    });
};
/**
 * @description  资源注册
 */
export const postResourceApi = (data) => {
    return request({
        url: `/api/resource/resources/add`,
        method: 'post',
        data
    });
};
/**
 * @description  资源删除
 */
export const deleteResourceApi = (data) => {
    return request({
        url: `/api/resource/resources/del`,
        method: 'post',
        data
    });
};

/**
 * @description  根据ID获取资源信息
 */
export const getResourceByIdApi = (data) => {
    return request({
        url: `/api/resource/resource_one?resource_id=${data}`,
        method: 'get'
    });
};
/**
 * @description  根据ID修改资源信息
 */
export const postResourceByIdApi = (data) => {
    return request({
        url: `/api/resource/resources/edit`,
        method: 'post',
        data
    });
};

//任务管理
// 地类变化  地类分割注册
export const postRegisterTask = (data) => {
    return request({
        url: `/api/interpretation/interpretation-task/add`,
        method: 'post',
        data
    });
};

//获取资源
export const getAllTaskResources = () => {
    return request({
        url: `/api/interpretation/interpretation-task/resource_list`,
        method: 'get'
    });
};

//地类变化任务 地类分割任务
export const getTaskListsApi = (data) => {
    return request({
        url: `/api/interpretation/interpretation-task-result/list`,
        method: 'post',
        data
    });
};
//删除 地类变化任务 地类分割任务
export const deleteTaskByIds = (data) => {
    return request({
        url: `/api/interpretation/interpretation-task-result/del`,
        method: 'post',
        data
    });
};
//查看任务详情
export const getTaskInfoByIdApi = (id) => {
    return request({
        url: `/api/interpretation/interpretation-task-result/get_result/${id}`,
        method: 'get'
    });
};

//任务详情更新
export const updateTaskByIdApi = (data) => {
    return request({
        url: `/lais/site/inspection/interpretation_task_result/update_result`,
        method: 'post',
        data
    });
};

export const getMapInfoApi = () => {
    return request({
        url: `/api/system/map_info`,
        method: 'get'
    });
};

export const upLoadExcelApi = (formData) => {
    return request({
        url: `/common/files`,
        method: 'post',
        headers: {
            'content-type': 'application/x-www-form-urlencoded',
            Authorization: 'Bearer ' + localStorage.getItem('tokens')
        },
        formData
    });
};

export const verifyClueApi = (data) => {
    return request({
        url: `/common/verify_clue`,
        method: 'post',
        data
    });
};

export const getClueVerifyTableApi = (data) => {
    return request({
        url: `/common/verify_task`,
        method: 'post',
        data
    });
};

export const verifyClueByTaskIDApi = (data) => {
    return request({
        url: `/common/verify_clue_list`,
        method: 'post',
        data
    });
};

export const addMarkerApi = (data) => {
    return request({
        url: `/common/verify_clue_add`,
        method: 'post',
        data
    });
};

export const deleteMarkerApi = (data) => {
    return request({
        url: `/common/verify_clue_delete`,
        method: 'post',
        data
    });
};

export const getVerifyTaskParamsApi = () => {
    return request({
        url: `/common/verify_task_params`,
        method: 'get'
    });
};
/**
 * @description 根据id删除全景任务
 */
export const deleteProjectApi = (data) => {
    return request({
        url: `/common/project_delete`,
        method: 'post',
        data
    });
};
/**
 * @description 查询项目
 */
export const postProjectApi = (data) => {
    return request({
        url: `/common/project`,
        method: 'post',
        data
    });
};

export const getFlyHistoryTreeListApi = (data) => {
    return request({
        url: `/common/get_video`,
        method: 'get',
        params: {
            pageNum: data.pageNum,
            pageSize: data.pageSize
        },
        timeout: 20000
    });
};

export const saveRoutePlanApi = (data) => {
    return request({
        url: `/api/route/routes/add`,
        method: 'post',
        data,
        timeout: 500000000
    });
};

export const saveMultiAircraftRoutePlanApi = (data) => {
    return request({
        url: `/api/route/route_plan_async`,
        method: 'post',
        data,
        timeout: 600000
    });
};

/**
 * @description 新增不检测区域
 */
export const postFrameAreaApi = (data) => {
    return request({
        url: `/api/panorama/frame_area/add`,
        method: 'post',
        data
    });
};

/**
 * @description 获取不检测区域列表
 */
export const getFrameAreaListApi = (data) => {
    return request({
        url: `/api/panorama/frame_area/list`,
        method: 'post',
        data
    });
};

/**
 * @description 根据id删除不检测区域
 */
export const deleteFrameAreaApi = (data) => {
    return request({
        url: `/api/panorama/frame_area/del`,
        method: 'post',
        data
    });
};

export const getRouteListApi = (data) => {
    return request({
        url: `/api/route/routes/list`,
        method: 'post',
        data
    });
};

export const getRouteMapDetailApi = (fileId) => {
    return request({
        url: `/api/route/routes/map-detail/${fileId}`,
        method: 'get'
    });
};

export const deleteKmzfileApi = (data) => {
    return request({
        url: `/api/route/routes/del`,
        method: 'post',
        data
    });
};

export const batchDeleteRoutePlansApi = (fileIds) => {
    return request({
        url: `/api/route/routes/batch-delete`,
        method: 'post',
        data: { fileIds }
    });
};

// 获取无人机飞行轨迹
export const getFlyTraceApi = (data) => {
    return request({
        url: `/common/get_uav_fly_track`,
        method: 'post',
        data
    });
};

export const upLoadShpApi = (data) => {
    return request({
        url: `/api/route/routes/upload`,
        method: 'post',
        data,
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 300000
    });
};

export const filterParcelsByRangeApi = (data) => {
    return request({
        url: `/api/route/routes/filter-parcels`,
        method: 'post',
        data,
        timeout: 600000
    });
};

export const getRouteJobStatusApi = (jobId) => {
    return request({
        url: `/api/route/jobs/${jobId}`,
        method: 'get',
        timeout: 30000
    });
};

export const downloadExcludedParcelsApi = (jobId) => {
    return request({
        url: `/api/route/jobs/${jobId}/excluded-parcels`,
        method: 'get',
        responseType: 'blob',
        timeout: 600000
    });
};

export const viewPlanApi = (id, type) => {
    return request({
        url: `/api/route/routes/view-plan/${id}?type=${type}`,
        method: 'get'
    });
};

export const getUavInfoApi = () => {
    return request({
        url: `/api/resource/uav-info/list`,
        method: 'post'
    });
};

export const getLogsInfoApi = (data) => {
    return request({
        url: `/api/system/logs_search`,
        method: 'post',
        data
    });
};
export const postInformationPush = (data) => {
    return request({
        url: `/api/panorama/information_push`,
            method: 'post',
            data
        });
    };

    export const deleteTaskApi = (data) => {
        return request({
            url: `/api/panorama/polygon-task/del`,
            method: 'post',
            data
        });
    };

    export const exportPolygon = (data) => {
        return request({
        url: `/lais/site/inspection/polygon-task/export_polygon?id=${data}`,
        method: 'get',
        responseType: 'blob'
    });
};

/**
 * @description 获取一张图数据
 */
export const getOneMapApi = (data) => {
    return request({
        url: `/api/resource/resources/get_resources_on_one_map`,
        method: 'post',
        data: data
    });
};
/**
 * @description 根据全景点ID获取不检测区域数据
 */
export const getFrameAreaByPointIdApi = (data) => {
    return request({
        url: `/api/panorama/frame-area/get-upload-areas`,
        method: 'post',
        data: data
    });
};

//保存全景航线
export const savePanoramicPointPlanApi = (data) => {
    return request({
        url: `/api/route/panoramic_point/add`,
        method: 'post',
        data,
        timeout: 50000
    });
};
//修改全景点位置
export const modifyPanoramicPointApi = (data) => {
    return request({
        url: `/common/modify_panoramic_point`,
        method: 'post',
        data
    });
};

export const patternVerifiTableApi = (data) => {
    return request({
        url: `/api/panorama/polygon-task/list`,
        method: 'post',
        data
    });
};
export const addFrameAreaDataApi = (data) => {
    return request({
        url: `/api/panorama/frame_area/upload`,
        method: 'post',
        data
    });
};
export const uploadPolygonTaskApi = (data) => {
    return request({
        url: `/api/panorama/polygon-task/add`,
        method: 'post',
        data
    });
};

//获取图斑数据通过task_id
export const getPatternDataByTaskIdApi = (data) => {
    return request({
        url: `/api/panorama/polygon-data/list`,
        method: 'post',
        data
    });
};
//修改图斑状态
export const modifyPatternStatusApi = (data) => {
    return request({
        url: `/api/panorama/polygon-data/update-data-status`,
        method: 'post',
        data
    });
};
//修改图斑核实结论
export const modifyPatternConclusionApi = (data) => {
    return request({
        url: `/api/panorama/polygon-data/verify`,
        method: 'post',
        data
    });
};
//线索录入
export const clueEntryApi = (data) => {
    return request({
        url: `/api/panorama/clue/clue-entry`,
        method: 'post',
        data
    });
};

/**
 * @description 根据线索总览中的数据
 */
export const getClueOverviewApi = (data) => {
    return request({
        url: `/api/panorama/clue/list`,
        method: 'post',
        data
    });
};
//获取机巢信息
export const getNestInfoApi = () => {
    return request({
        url: `/api/system/nest/all`,
        method: 'post'
    });
};
//新增机巢
export const addNestApi = (data) => {
    return request({
        url: `/api/system/nest/add`,
        method: 'post',
        data
    });
};
//获取机巢表格信息
export const getNestTableApi = (data) => {
    return request({
        url: `/api/system/nest/list`,
        method: 'post',
        data
    });
};
//获取机巢表格信息
export const deleteTableDataApi = (data) => {
    return request({
        url: `/api/system/nest/del`,
        method: 'post',
        data
    });
};

// 批量导入机巢 Excel
export const importNestExcelApi = (data) => {
    return request({
        url: `/api/system/nest/import`,
        method: 'post',
        data,
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 120000
    });
};

/**
 * @description 获取区域数据
 */
export const getRegionDataApi = () => {
    return request({
        url: `/api/resource/region_data`,
        method: 'get'
    });
};



/**
 * @description 获取系统名字
 */
export const getSystemNameApi = () => {
    return request({
        url: `/api/system/system-name`,
        method: 'get'
    });
};
/**
 * @description 根据区域网格id查询全景点数据
 */
export const getPanoramaByGridApi = (data) => {
    return request({
        url: `/api/resource/query_data_by_grid_id`,
        method: 'post',
        data
    });
};

//获取统计大屏6个数字
export const getClueStatisDataApi = () => {
    return request({
        url: `/lais/site/inspection/analyze/data_analysis`,
        method: 'get'
    });
};
export const getVillageListApi = () => {
    return request({
        url: `/lais/site/inspection/analyze/village_list`,
        method: 'get'
    });
};
export const statisticsIllegalCluesApi = () => {
    return request({
        url: `/lais/site/inspection/analyze/statistics_illegal_clues`,
        method: 'get'
    });
};
export const getClueConfirmedTableApi = (data) => {
    return request({
        url: `/lais/site/inspection/analyze/clue_confirmed`,
        method: 'post',
        data
    });
};

// 修改密码
export const modifyPassword = (data) => {
    return request({
        url: `/scp-account/config/v1/users/reset/enc-password`,
        method: 'post',
        data
    });
};

export const modifyNestInfoApi = (data) => {
    return request({
        url: `/api/panorama/nest/edit`,
        method: 'post',
        data
    });
};
/**
 * @description 获取小地图组件数据
 */
export const getSmallMapApi = () => {
    return request({
        url: `/api/panorama/resources/get_business_data`,
        method: 'get'
    });
};
//根据批次ID获取批次信息
export const getBatchInfoByIdApi = (pk_id) => {
    return request({
        url: `/api/panorama/batch/get-batch-by-id?batch_id=${pk_id}`,
        method: 'get',
    });
};
//获取指定范围内的耕地
export const getPointBufferGDApi = (data) => {
    return request({
        url: `/api/panorama/get_buffer_gd?panorama_image_id=${data}`,
        method: 'get',

    });
};
//获取服务列表
export const getBufferLayerApi = () => {
    return request({
        url: `/api/resource/get-buffer-list`,
        method: 'get',
    });
};
//请求后台获取服务图斑
export const getPointBufferLayerApi = (data) => {
    return request({
        url: `/api/panorama/get_buffer_gd?panorama_image_id=${data.panorama_image_id}&resource_id=${data.resource_id}`,
        method: 'get',
    });
};

//获取绘制的目标线索列表
export const getTargetAreaListApi = (data) => {
    return request({
        url: `/common/get_target_area_list`,
        method: 'post',
        data
    });
};

//删除目标线索
export const deleteTargetClueApi = (data) => {
    return request({
        url: `/common/target_area_clue_delete`,
        method: 'post',
        data
    });
};
export const calculatePanoramaApi = (data) => {
    return request({
        url: `/api/panorama/polygon-data/calculate_panorama`,
        method: 'post',
        data
    });
};

// 根据id修改图斑核实任务的状态
export const postPolygonTaskStatusApi = (data) => {
    return request({
        url: `/lais/site/inspection/polygon-task/update-polygon-task-status-by-id/${data}`,
        method: 'post',
        data
    });
};
/**
 * @description  判断图斑核实是否都处理完成
 */
export const JudgeClueApi = (data) => {
    return request({
        url: `/api/panorama/polygon-data/judge_clue?taskId=${data}`,
        method: 'get'
    });
};

/**
 * @description  获取变化检测数据
 */
export const getLandChangeTaskApi = (data) => {
    return request({
        url: `/lais/site/inspection/polygon-data/judge_clue?taskId=${data}`,
        method: 'get'
    });
};
/**
 * @description  多元数据页面文件上传接口
 */
export const uploadFileApi = (data) => {
    return request({
        url: `/api/resource/multivariate-data/files_upload`,
        method: 'post',
        data
    });
};
/**
 * @description  多元数据页面文件上传接口
 */
export const addMultivariateDataApi = (data) => {
    return request({
        url: `/api/resource/multivariate-data/add`,
        method: 'post',
        data
    });
};
/**
 * @description  机巢数据获取接口
 */
export const getNestDataApi = () => {
    return request({
        url: `/api/resource/nest/list`,
        method: 'post',
    });
};
/**
 * @description  多元数据获取接口
 */
export const getMultDataApi = (data) => {
    return request({
        url: `/api/resource/multivariate-data/list`,
        method: 'post',
        data
    });
};
/**
 * @description  多元数据字典获取接口
 */
export const getMultDataDictApi = (data) => {
    return request({
        url: `/api/system/multivariate_data/dict`,
        method: 'get',
        data
    });
};
/**
 * @description  多元数据删除接口
 */
export const deleteMultDataApi = (data) => {
    return request({
        url: `/api/resource/multivariate-data/del`,
        method: 'post',
        data
    });
};

/**
 * @description  俯视图数据获取接口
 */
export const getTopViewDataApi = (data) => {
    return request({
        url: `/api/resource/top-view/list`,
        method: 'post',
        data
    });
};
/**
 * @description  获取时间轴数据
 */
export const getTimeAxisDataApi = () => {
    return request({
        url: `/api/resource/get_time_axis`,
        method: 'get',
    });
};

//获取解译结果展示卡片
export const getInterpretationResultByApi = (data) => {
    return request({
        url: `/api/interpretation/interpretation-task-result/fetch_task_fronted`,
        method: 'post',
        data
    });
};
//获取解译结果右侧统计展示
export const getStaticInfoApi = () => {
    return request({
        url: `/api/interpretation/interpretation-task-result/get_stat_info`,
        method: 'get',
    });
};

//获取展示详情数据
export const getDetailResultApi = (id) => {
    return request({
        url: `/api/interpretation/interpretation-task-result/get_detail_result/${id}`,
        method: 'get',
    });
};

//获取模型列表
export const getModelListApi = () => {
    return request({
        url: `/lais/site/inspection/interpretation_task/get_models`,
        method: 'get',
    });
};

//获取服务器文件列表
export const getServerPathApi = () => {
    return request({
        url: `/lais/site/inspection/interpretation_task/get_server_paths`,
        method: 'get',
    });
};

//获取解译任务状态和进度
export const getProcessStatusApi = (id) => {
    return request({
        url: `/lais/site/inspection/interpretation_task/get_process_status/${id}`,
        method: 'get',
    });
};

//新增解译任务
export const addInterpretationTaskApi = (data) => {
    return request({
        url: `/lais/site/inspection/interpretation_task/add_task`,
        method: 'post',
        data
    });
};

//获取redis数量
export const getRedisCountApi = () => {
    return request({
        url: `/lais/site/inspection/interpretation_task/get_redis_count`,
        method: 'get',
    });
};
//获取gpu信息
export const getGpuFreeMemoryApi = () => {
    return request({
        url: `/lais/site/inspection/interpretation_task/get_gpu_free_memory`,
        method: 'get',
    });
};
//数据验证
export const dataVerifyApi = (data) => {
    return request({
        url: `/lais/site/inspection/interpretation_task/data_verify`,
        method: 'post',
        data
    });
};

//批量删除解译任务
export const batchDeleteInterpretationTaskApi = (data) => {
    return request({
        url: `/lais/site/inspection/interpretation_task/delete_task?ids=${data}`,
        method: 'get',
    });
};

//获取解译任务表格
export const getTableDataApi = (data) => {
    return request({
        url: `/lais/site/inspection/interpretation_task/get_task_by_conditions`,
        method: 'post',
        data
    });
};

//任务终止
export const taskStopApi = (data) => {
    return request({
        url: `/lais/site/inspection/interpretation_task/task_stop/${data}`,
        method: 'get',
    });
};
//下载文件
export const downloadFileApi = (data) => {
    return request({
        url: `/lais/site/inspection/interpretation_task/download_result/${data}`,
        method: 'get'
    });
};
//获取自动创建批次
export const getAutoCreateBatchApi = () => {
    return request({
        url: `/api/panorama/batch/temp-detection-batch-data`,
        method: 'get'
    });
};

// 批次状态改为核实中
export const changeBatchToHszApi = (data) => {
    return request({
        url: `/api/panorama/batch/change-status`,
        method: 'post',
        data
    });
};
// 批次状态改为核实中
export const exportBatchShpApi = (data) => {
    return request({
        url: `/api/panorama/batch/export-shp`,
        method: 'post',
        data
    });
};

//临时上传批次
export const tempAddUploadBatchApi = (data) => {
    return request({
        url: `/api/panorama/temp_main_detection`,
        method: 'post',
        data
    });
};

//获取指定时间内的航片
export const getTimePhotoApi = (data) => {
    return request({
        url: `/api/resource/flight_view_task`,
        method: 'post',
        data
    });
};

export const getDownloadAiResultApi = (data) => {
    return request({
        url: `/api/panorama/file/download/${data}`,
        method: 'get',
        responseType: 'blob'
    });
};

export const getRegionListApi = (data) => {
    return request({
        url: `/api/system/regions/list`,
        method: 'post',
        data
    });
};

export const addRegionApi = (data) => {
    return request({
        url: `/api/system/regions/add`,
        method: 'post',
        data
    });
};

export const editRegionApi = (data) => {
    return request({
        url: `/api/system/regions/edit`,
        method: 'post',
        data
    });
};

export const deleteRegionApi = (data) => {
    return request({
        url: `/api/system/regions/del`,
        method: 'post',
        data
    });
};
//获取父级区划
export const getParentRegionApi = (data) => {
    return request({
        url: `/api/system/region/parent?region_level=${data}`,
        method: 'get',
    });
};
//新增标注
export const addPlotApi = (data) => {
    return request({
        url: `/api/panorama/plot/add-plot`,
        method: 'post',
        data
    });
};
//查询全景图关联标注
export const getPlotByImageApi = (id) => {
    return request({
        url: `/api/panorama/plot/get-plot-by-image-id?id=${id}`,
        method: 'get'
    });
};
//查询线索关联标注
export const getPlotByClueApi = (id) => {
    return request({
        url: `/api/panorama/plot/get-plot-by-clue?id=${id}`,
        method: 'get'
    });
};
// 查询标注详情
export const getPlotDetailApi = (id) => {
    return request({
        url: `/api/panorama/plot/get-plot-by-id?id=${id}`,
        method: 'get'
    });
};

//标绘更新
export const updatePlotApi = (data) => {
    return request({
        url: `/api/panorama/plot/update-plot`,
        method: 'post',
        data
    });
};
//标绘删除
export const deletePlotApi = (data) => {
    return request({
        url: `/api/panorama/plot/delete-plot`,
        method: 'post',
        data
    });
};
//标绘分页查询
export const getPlotByConditionsApi = (data) => {
    return request({
        url: `/api/panorama/plot/get-plot-by-conditions`,
        method: 'post',
        data
    });
};
//生成excel
export const generatePlotExcelApi = (data) => {
    return request({
        url: `/api/panorama/plot/generate-excel`,
        method: 'post',
        data
    });
};
//下载标注excel
export const DownloadPlotExcelApi = (data) => {
    return request({
        url: `/api/panorama/plot/download-excel?file_id=${data}`,
        method: 'get',
        responseType: 'blob'
    });
};
//获取视频识别任务
export const getVideoTaskListApi = (data) => {
    return request({
        url: `/api/resource/video/list`,
        method: 'post',
        data
    });
};
/**
 * @description 获取实时视频流信息（含 httpUrl 拉流地址）
 */
export const getLiveStreamInfoApi = (data) => {
    return request({
        url: `/api/resource/live-stream/info`,
        method: 'post',
        data
    });
};
//获取订单数据API
export const getOrderListApi = (data) => {
    return request({
        url: `/api/panorama/order/list`,
        method: 'post',
        data
    });
};
//新增订单数据API
export const postOrderInfoApi = (data) => {
    return request({
        url: `/api/panorama/order/add`,
        method: 'post',
        data
    });
};
