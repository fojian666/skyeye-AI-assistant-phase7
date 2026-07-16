import request from './request';
import { TASK_TYPE } from '@/views/taskManagementModule/mock/taskTable';

/** 后端接口未就绪前使用模拟接口，就绪后改为 false */
export const TASK_MGMT_USE_MOCK = false;

/** 前端任务类型 -> 监管项目 dataType */
export const TASK_TYPE_DATA_TYPE_MAP = {
    [TASK_TYPE.TEMP_LAND_RESTORE]: 1,
    [TASK_TYPE.MOUNTAIN_WATER]: 2,
    [TASK_TYPE.CONSTRUCTION]: 3
};

/** 监管项目 dataType -> 前端任务类型 */
export const DATA_TYPE_TO_TASK_TYPE = {
    1: TASK_TYPE.TEMP_LAND_RESTORE,
    2: TASK_TYPE.MOUNTAIN_WATER,
    3: TASK_TYPE.CONSTRUCTION
};

/**
 * 监管项目列表/详情统一接口
 * @param {Object} data - pageIndex, pageSize, id, dataType, county, status
 */
export const getSupervisionProjectListApi = (data) => {
    return request({
        url: '/api/panorama/supervision/project/list',
        method: 'POST',
        data
    });
};

/**
 * 构建监管项目列表请求参数
 */
export function buildSupervisionProjectListParams({ pageIndex = 1, pageSize = 10, id, taskType, county, status, taskId } = {}) {
    const params = {
        pageIndex,
        pageSize
    };
    if (id != null && id !== '') {
        params.id = id;
    } else if (taskId) {
        params.id = taskId;
    }
    if (taskType && TASK_TYPE_DATA_TYPE_MAP[taskType] != null) {
        params.dataType = TASK_TYPE_DATA_TYPE_MAP[taskType];
    }
    if (county) {
        params.county = county;
    }
    if (status != null && status !== '') {
        params.status = status;
    }
    return params;
}

/** 监管图斑列表/详情 */
export const getSupervisionPolygonListApi = (data) => {
    return request({
        url: '/api/panorama/supervision/polygon/list',
        method: 'POST',
        data
    });
};

/** 构建监管图斑列表请求参数 */
export function buildSupervisionPolygonListParams({ pageIndex = 1, pageSize = 1, id, supervisionProjectId, polygonType } = {}) {
    const params = { pageIndex, pageSize };
    if (id != null && id !== '') {
        params.id = id;
    }
    if (supervisionProjectId != null && supervisionProjectId !== '') {
        params.supervisionProjectId = supervisionProjectId;
    }
    if (polygonType) {
        params.polygonType = polygonType;
    }
    return params;
}

/** 新增监管项目（multipart/form-data：dataType + file） */
export const addSupervisionProjectApi = (formData) => {
    return request({
        url: '/api/panorama/supervision/project/add',
        method: 'POST',
        data: formData,
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 120000
    });
};

/** 删除监管项目：单条传 id，多条传 ids */
export const deleteSupervisionProjectApi = (data) => {
    return request({
        url: '/api/panorama/supervision/project/del',
        method: 'POST',
        data
    });
};

/** 临时用地恢复 - 任务列表 */
export const getTempLandRestoreTaskListApi = (data) => {
    return request({
        url: '/api/task-mgmt/temp-land-restore/list',
        method: 'POST',
        data
    });
};

/** 山水工程项目 - 任务列表 */
export const getMountainWaterTaskListApi = (data) => {
    return request({
        url: '/api/task-mgmt/mountain-water/list',
        method: 'POST',
        data
    });
};

/** 建设项目 - 任务列表 */
export const getConstructionTaskListApi = (data) => {
    return request({
        url: '/api/task-mgmt/construction/list',
        method: 'POST',
        data
    });
};

/** 临时用地恢复 - 任务详情点位列表 */
export const getTempLandRestoreTaskDetailApi = (data) => {
    return request({
        url: '/api/task-mgmt/temp-land-restore/detail',
        method: 'POST',
        data
    });
};

/** 山水工程项目 - 任务详情点位列表 */
export const getMountainWaterTaskDetailApi = (data) => {
    return request({
        url: '/api/task-mgmt/mountain-water/detail',
        method: 'POST',
        data
    });
};

/** 建设项目 - 任务详情点位列表 */
export const getConstructionTaskDetailApi = (data) => {
    return request({
        url: '/api/task-mgmt/construction/detail',
        method: 'POST',
        data
    });
};

const TASK_LIST_API_MAP = {
    [TASK_TYPE.TEMP_LAND_RESTORE]: getTempLandRestoreTaskListApi,
    [TASK_TYPE.MOUNTAIN_WATER]: getMountainWaterTaskListApi,
    [TASK_TYPE.CONSTRUCTION]: getConstructionTaskListApi
};

const TASK_DETAIL_API_MAP = {
    [TASK_TYPE.TEMP_LAND_RESTORE]: getTempLandRestoreTaskDetailApi,
    [TASK_TYPE.MOUNTAIN_WATER]: getMountainWaterTaskDetailApi,
    [TASK_TYPE.CONSTRUCTION]: getConstructionTaskDetailApi
};

export function getTaskListApiByType(taskType) {
    return TASK_LIST_API_MAP[taskType] || getTempLandRestoreTaskListApi;
}

export function getTaskDetailApiByType(taskType) {
    return TASK_DETAIL_API_MAP[taskType] || getTempLandRestoreTaskDetailApi;
}

/** 监管图斑详情（含俯视图） */
export const getSupervisionPolygonDetailApi = (data) => {
    return request({
        url: '/api/panorama/supervision/polygon/detail',
        method: 'POST',
        data
    });
};

/** 构建监管图斑详情请求参数 */
export function buildSupervisionPolygonDetailParams({ id, polygonId } = {}) {
    const params = {};
    if (id != null && id !== '') {
        params.id = id;
    } else if (polygonId != null && polygonId !== '') {
        params.polygonId = polygonId;
    }
    return params;
}
