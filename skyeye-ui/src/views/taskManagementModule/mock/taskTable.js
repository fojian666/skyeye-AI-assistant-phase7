/** 任务管理模块 - 列表页测试数据（接口未就绪时使用） */
export const TASK_TYPE = {
    TEMP_LAND_RESTORE: 'temp_land_restore',
    MOUNTAIN_WATER: 'mountain_water',
    CONSTRUCTION: 'construction'
};

export const MOCK_TEMP_LAND_RESTORE_TABLE = [
    {
        id: 1,
        task_id: 'LS001',
        task_type: TASK_TYPE.TEMP_LAND_RESTORE,
        street: '玄武区梅园新村街道',
        status: 0,
        todo_count: 2,
        done_count: 3,
        total_count: 5,
        verifier: '测试用户'
    },
    {
        id: 2,
        task_id: 'LS002',
        task_type: TASK_TYPE.TEMP_LAND_RESTORE,
        street: '秦淮区夫子庙街道',
        status: 1,
        todo_count: 1,
        done_count: 5,
        total_count: 6,
        verifier: '测试用户'
    }
];

export const MOCK_MOUNTAIN_WATER_TABLE = [
    {
        id: 3,
        task_id: 'SS001',
        task_type: TASK_TYPE.MOUNTAIN_WATER,
        street: '建邺区江东街道',
        status: 2,
        todo_count: 0,
        done_count: 8,
        total_count: 8,
        verifier: '测试用户'
    },
    {
        id: 4,
        task_id: 'SS002',
        task_type: TASK_TYPE.MOUNTAIN_WATER,
        street: '鼓楼区湖南路街道',
        status: 0,
        todo_count: 4,
        done_count: 2,
        total_count: 6,
        verifier: '测试用户'
    }
];

export const MOCK_CONSTRUCTION_TABLE = [
    {
        id: 5,
        task_id: 'JS001',
        task_type: TASK_TYPE.CONSTRUCTION,
        street: '栖霞区仙林街道',
        status: 1,
        todo_count: 3,
        done_count: 6,
        total_count: 9,
        verifier: '测试用户'
    },
    {
        id: 6,
        task_id: 'JS002',
        task_type: TASK_TYPE.CONSTRUCTION,
        street: '雨花台区铁心桥街道',
        status: 0,
        todo_count: 2,
        done_count: 4,
        total_count: 6,
        verifier: '测试用户'
    }
];

function paginateList(list, taskId, pageIndex = 1, pageSize = 10) {
    let filtered = list;
    if (taskId) {
        filtered = filtered.filter((item) => item.task_id.includes(taskId));
    }
    const start = (pageIndex - 1) * pageSize;
    return {
        data: filtered.slice(start, start + pageSize),
        total: filtered.length
    };
}

export function filterMockTempLandRestoreTable(taskId, pageIndex, pageSize) {
    return paginateList(MOCK_TEMP_LAND_RESTORE_TABLE, taskId, pageIndex, pageSize);
}

export function filterMockMountainWaterTable(taskId, pageIndex, pageSize) {
    return paginateList(MOCK_MOUNTAIN_WATER_TABLE, taskId, pageIndex, pageSize);
}

export function filterMockConstructionTable(taskId, pageIndex, pageSize) {
    return paginateList(MOCK_CONSTRUCTION_TABLE, taskId, pageIndex, pageSize);
}
