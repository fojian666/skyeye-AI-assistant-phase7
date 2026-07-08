import { TASK_TYPE } from '@/views/taskManagementModule/mock/taskTable';

function buildAiResult(judgment, confidence, summary) {
  return { judgment, confidence, summary };
}

function buildPlotStats(todoCount, doneCount, status) {
  const total = todoCount + doneCount;
  return {
    total_count: total,
    todo_count: todoCount,
    done_count: doneCount,
    status,
  };
}

export const MOCK_TEMP_LAND_RESTORE_DETAIL = [
  {
    taskId: 'LS001',
    task_type: TASK_TYPE.TEMP_LAND_RESTORE,
    taskName: '临时用地恢复任务1',
    pointName: '临时用地恢复任务1',
    imageName: 'IMG_LS001.jpg',
    imageId: 'mock_image_ls001',
    pointId: 'mock_point_ls001',
    point_id: 'mock_point_ls001',
    batchId: 'mock_batch_ls001',
    street: '玄武区梅园新村街道',
    createTime: '2026-06-16 09:00:00',
    status: 0,
    doneCount: 3,
    todoCount: 2,
    yawDegree: 120,
    lat: 32.0603,
    lon: 118.7969,
    latitude: 32.0603,
    longitude: 118.7969,
    height: 120,
    aiResult: buildAiResult('疑似占用耕地', 0.92, 'AI 检测到图斑范围内存在建设痕迹，建议人工复核'),
    plotStats: buildPlotStats(2, 3, 0),
  },
  {
    taskId: 'LS002',
    task_type: TASK_TYPE.TEMP_LAND_RESTORE,
    taskName: '临时用地恢复任务2',
    pointName: '临时用地恢复任务2',
    imageName: 'IMG_LS002.jpg',
    imageId: 'mock_image_ls002',
    pointId: 'mock_point_ls002',
    point_id: 'mock_point_ls002',
    batchId: 'mock_batch_ls002',
    street: '秦淮区夫子庙街道',
    createTime: '2026-06-16 10:30:00',
    status: 1,
    doneCount: 5,
    todoCount: 1,
    yawDegree: 90,
    lat: 32.0201,
    lon: 118.7889,
    aiResult: buildAiResult('未占用耕地', 0.88, 'AI 判读图斑范围内以植被覆盖为主，无明显建设活动'),
    plotStats: buildPlotStats(1, 5, 1),
  },
];

export const MOCK_MOUNTAIN_WATER_DETAIL = [
  {
    taskId: 'SS001',
    task_type: TASK_TYPE.MOUNTAIN_WATER,
    taskName: '山水工程项目1',
    pointName: '山水工程项目1',
    imageName: 'IMG_SS001.jpg',
    imageId: 'mock_image_ss001',
    pointId: 'mock_point_ss001',
    point_id: 'mock_point_ss001',
    batchId: 'mock_batch_ss001',
    street: '建邺区江东街道',
    createTime: '2026-06-16 11:15:00',
    status: 2,
    doneCount: 8,
    todoCount: 0,
    yawDegree: 45,
    lat: 32.0042,
    lon: 118.7312,
    aiResult: buildAiResult('工程进度正常', 0.95, 'AI 判读山水工程区域施工符合规划范围'),
    plotStats: buildPlotStats(0, 8, 2),
  },
  {
    taskId: 'SS002',
    task_type: TASK_TYPE.MOUNTAIN_WATER,
    taskName: '山水工程项目2',
    pointName: '山水工程项目2',
    imageName: 'IMG_SS002.jpg',
    imageId: 'mock_image_ss002',
    pointId: 'mock_point_ss002',
    point_id: 'mock_point_ss002',
    batchId: 'mock_batch_ss002',
    street: '鼓楼区湖南路街道',
    createTime: '2026-06-16 14:00:00',
    status: 0,
    doneCount: 2,
    todoCount: 4,
    yawDegree: 200,
    lat: 32.0705,
    lon: 118.7698,
    aiResult: buildAiResult('疑似超范围施工', 0.86, 'AI 检测到施工范围超出备案边界，需进一步核实'),
    plotStats: buildPlotStats(4, 2, 0),
  },
];

export const MOCK_CONSTRUCTION_DETAIL = [
  {
    taskId: 'JS001',
    task_type: TASK_TYPE.CONSTRUCTION,
    taskName: '建设项目1',
    pointName: '建设项目1',
    imageName: 'IMG_JS001.jpg',
    imageId: 'mock_image_js001',
    pointId: 'mock_point_js001',
    point_id: 'mock_point_js001',
    batchId: 'mock_batch_js001',
    street: '栖霞区仙林街道',
    createTime: '2026-06-16 16:45:00',
    status: 1,
    doneCount: 6,
    todoCount: 3,
    yawDegree: 270,
    lat: 32.0987,
    lon: 118.9123,
    aiResult: buildAiResult('疑似违法建设', 0.91, 'AI 检测到未批先建嫌疑，建议现场核查'),
    plotStats: buildPlotStats(3, 6, 1),
  },
  {
    taskId: 'JS002',
    task_type: TASK_TYPE.CONSTRUCTION,
    taskName: '建设项目2',
    pointName: '建设项目2',
    imageName: 'IMG_JS002.jpg',
    imageId: 'mock_image_js002',
    pointId: 'mock_point_js002',
    point_id: 'mock_point_js002',
    batchId: 'mock_batch_js002',
    street: '雨花台区铁心桥街道',
    createTime: '2026-06-16 17:30:00',
    status: 0,
    doneCount: 4,
    todoCount: 2,
    yawDegree: 150,
    lat: 31.9889,
    lon: 118.7654,
    aiResult: buildAiResult('手续齐全', 0.93, 'AI 判读建设项目与审批范围一致，手续材料匹配'),
    plotStats: buildPlotStats(2, 4, 0),
  },
];

export function getMockTaskListTotalTodoCount(list) {
  return list.reduce((sum, item) => sum + (item.todoCount || 0), 0);
}

function withMapCoords(item) {
  return {
    ...item,
    latitude: item.latitude != null ? item.latitude : item.lat,
    longitude: item.longitude != null ? item.longitude : item.lon,
    height: item.height != null ? item.height : 100,
  };
}

function filterDetailList(list, taskId) {
  let result;
  if (!taskId) {
    result = list.slice(0, 1);
  } else {
    const matched = list.filter(
      (item) => item.taskId === taskId || item.taskId === String(taskId)
    );
    result = matched.length > 0 ? matched : list.slice(0, 1);
  }
  return result.map(withMapCoords);
}

export function filterMockTempLandRestoreDetail(taskId) {
  return filterDetailList(MOCK_TEMP_LAND_RESTORE_DETAIL, taskId);
}

export function filterMockMountainWaterDetail(taskId) {
  return filterDetailList(MOCK_MOUNTAIN_WATER_DETAIL, taskId);
}

export function filterMockConstructionDetail(taskId) {
  return filterDetailList(MOCK_CONSTRUCTION_DETAIL, taskId);
}
