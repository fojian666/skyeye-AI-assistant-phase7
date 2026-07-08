import {
  TASK_TYPE,
  filterMockTempLandRestoreTable,
  filterMockMountainWaterTable,
  filterMockConstructionTable,
  MOCK_TEMP_LAND_RESTORE_TABLE,
  MOCK_MOUNTAIN_WATER_TABLE,
  MOCK_CONSTRUCTION_TABLE,
} from '@/views/taskManagementModule/mock/taskTable';
import {
  filterMockTempLandRestoreDetail,
  filterMockMountainWaterDetail,
  filterMockConstructionDetail,
  getMockTaskListTotalTodoCount,
} from '@/views/taskManagementModule/mock/taskList';
import { getMockVerticalViewsByPointId } from '@/views/taskManagementModule/mock/topViewList';
import nestImg from '@/assets/images/nest2.png';
import {
  MOCK_TEMP_LAND_RESTORE_DETAIL,
  MOCK_MOUNTAIN_WATER_DETAIL,
  MOCK_CONSTRUCTION_DETAIL,
} from '@/views/taskManagementModule/mock/taskList';
import { DATA_TYPE_TO_TASK_TYPE, TASK_TYPE_DATA_TYPE_MAP } from '@/api/taskMgmtApi';
import { cardToPolygon } from '@/views/taskManagementModule/utils/projectListAdapter';

const MOCK_DELAY_MS = 200;

function delay(ms = MOCK_DELAY_MS) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function buildListResponse(listResult) {
  return {
    code: 0,
    data: listResult.data,
    total: listResult.total,
    message: 'success',
  };
}

function buildDetailResponse(cards) {
  return {
    code: 0,
    data: {
      cards,
      total_todo_count: getMockTaskListTotalTodoCount(cards),
    },
    message: 'success',
  };
}

/** 模拟：临时用地恢复任务列表 */
export async function mockGetTempLandRestoreTaskListApi(params = {}) {
  await delay();
  const { taskId = '', pageIndex = 1, pageSize = 10 } = params;
  return buildListResponse(filterMockTempLandRestoreTable(taskId, pageIndex, pageSize));
}

/** 模拟：山水工程项目任务列表 */
export async function mockGetMountainWaterTaskListApi(params = {}) {
  await delay();
  const { taskId = '', pageIndex = 1, pageSize = 10 } = params;
  return buildListResponse(filterMockMountainWaterTable(taskId, pageIndex, pageSize));
}

/** 模拟：建设项目任务列表 */
export async function mockGetConstructionTaskListApi(params = {}) {
  await delay();
  const { taskId = '', pageIndex = 1, pageSize = 10 } = params;
  return buildListResponse(filterMockConstructionTable(taskId, pageIndex, pageSize));
}

/** 模拟：临时用地恢复任务详情 */
export async function mockGetTempLandRestoreTaskDetailApi(params = {}) {
  await delay();
  const cards = filterMockTempLandRestoreDetail(params.taskId);
  return buildDetailResponse(cards);
}

/** 模拟：山水工程项目任务详情 */
export async function mockGetMountainWaterTaskDetailApi(params = {}) {
  await delay();
  const cards = filterMockMountainWaterDetail(params.taskId);
  return buildDetailResponse(cards);
}

/** 模拟：建设项目任务详情 */
export async function mockGetConstructionTaskDetailApi(params = {}) {
  await delay();
  const cards = filterMockConstructionDetail(params.taskId);
  return buildDetailResponse(cards);
}

function tableRowToProjectItem(row) {
  return {
    id: row.id,
    dataType: TASK_TYPE_DATA_TYPE_MAP[row.task_type],
    count: row.total_count != null ? row.total_count : 0,
    createPerson: row.verifier || '测试用户',
    status: row.status,
    county: row.street || '',
    collectTime: row.collectTime || '2026-06-16 09:00:00',
    createTime: row.createTime || '2026-06-16 09:00:00',
  };
}

function getMockDetailByTaskType(taskType, taskId) {
  if (taskType === TASK_TYPE.MOUNTAIN_WATER) {
    return filterMockMountainWaterDetail(taskId);
  }
  if (taskType === TASK_TYPE.CONSTRUCTION) {
    return filterMockConstructionDetail(taskId);
  }
  return filterMockTempLandRestoreDetail(taskId);
}

function findMockTableRowById(id) {
  const all = [
    ...MOCK_TEMP_LAND_RESTORE_TABLE,
    ...MOCK_MOUNTAIN_WATER_TABLE,
    ...MOCK_CONSTRUCTION_TABLE,
  ];
  return all.find(
    (item) => String(item.id) === String(id) || item.task_id === String(id)
  );
}

/** 模拟：监管项目列表/详情统一接口 */
export async function mockGetSupervisionProjectListApi(params = {}) {
  await delay();
  const {
    pageIndex = 1,
    pageSize = 10,
    id,
    dataType = 1,
    taskId,
  } = params;
  const searchId = id != null && id !== '' ? id : taskId;

  if (searchId != null && searchId !== '') {
    const row = findMockTableRowById(searchId);
    const taskType = row
      ? row.task_type
      : DATA_TYPE_TO_TASK_TYPE[dataType] || TASK_TYPE.TEMP_LAND_RESTORE;
    const legacyTaskId = row ? row.task_id : String(searchId);
    const cards = getMockDetailByTaskType(taskType, legacyTaskId);
    const polygons = cards.map(cardToPolygon).filter(Boolean);
    const start = (pageIndex - 1) * pageSize;
    const pagedPolygons = polygons.slice(start, start + pageSize);
    return {
      code: 0,
      data: {
        id: row ? row.id : Number(searchId) || searchId,
        dataType: row ? TASK_TYPE_DATA_TYPE_MAP[row.task_type] : dataType,
        count: row ? row.total_count : polygons.length,
        todo_count: row ? row.todo_count : polygons.length,
        createPerson: row ? row.verifier : '测试用户',
        status: row ? row.status : 0,
        county: row ? row.street : '',
        collectTime: '2026-06-16 09:00:00',
        createTime: '2026-06-16 09:00:00',
        polygons: pagedPolygons,
        routes: [],
      },
      total: polygons.length,
      message: 'success',
    };
  }

  let listResult;
  const legacyTaskId = '';
  if (dataType === TASK_TYPE_DATA_TYPE_MAP[TASK_TYPE.MOUNTAIN_WATER]) {
    listResult = filterMockMountainWaterTable(legacyTaskId, pageIndex, pageSize);
  } else if (dataType === TASK_TYPE_DATA_TYPE_MAP[TASK_TYPE.CONSTRUCTION]) {
    listResult = filterMockConstructionTable(legacyTaskId, pageIndex, pageSize);
  } else {
    listResult = filterMockTempLandRestoreTable(legacyTaskId, pageIndex, pageSize);
  }

  const data = listResult.data.map(tableRowToProjectItem);
  return {
    code: 0,
    data,
    total: listResult.total,
    count1: filterMockTempLandRestoreTable(legacyTaskId, 1, 9999).total,
    count2: filterMockMountainWaterTable(legacyTaskId, 1, 9999).total,
    count3: filterMockConstructionTable(legacyTaskId, 1, 9999).total,
    message: 'success',
  };
}

/** 模拟：监管图斑详情（含俯视图） */
function resolveMockDetailPointId(polygonId) {
  const allPoints = [
    ...MOCK_TEMP_LAND_RESTORE_DETAIL,
    ...MOCK_MOUNTAIN_WATER_DETAIL,
    ...MOCK_CONSTRUCTION_DETAIL,
  ];
  const matched = allPoints.find(
    (item) => String(item.id) === String(polygonId)
      || String(item.pointId) === String(polygonId)
      || String(item.point_id) === String(polygonId)
  );
  return matched ? (matched.pointId || matched.point_id) : 'mock_point_ls001';
}

export function getMockPanoramaListByPointId(pointId) {
  const allPoints = [
    ...MOCK_TEMP_LAND_RESTORE_DETAIL,
    ...MOCK_MOUNTAIN_WATER_DETAIL,
    ...MOCK_CONSTRUCTION_DETAIL,
  ];
  const matched = allPoints.filter(
    (item) => String(item.pointId) === String(pointId) || String(item.point_id) === String(pointId)
  );
  const source = matched.length > 0 ? matched : [allPoints[0]];
  return source.map((item, index) => ({
    ...item,
    pointId: item.pointId || item.point_id,
    batchName: item.batchId ? `批次${index + 1}` : `批次${index + 1}`,
    imageId: item.imageId,
    batchId: item.batchId,
    latitude: item.latitude != null ? item.latitude : item.lat,
    longitude: item.longitude != null ? item.longitude : item.lon,
    yawDegree: item.yawDegree || 0,
    imageName: item.imageName,
  }));
}

/** 模拟：全景点位多期全景图 */
export async function mockGetPanoramaImageApi(data = {}) {
  await delay();
  const list = getMockPanoramaListByPointId(data.pointId);
  return {
    code: 0,
    data: list,
    message: 'success',
  };
}

export async function mockGetSupervisionPolygonListApi(params = {}) {
  await delay();
  const {
    pageIndex = 1,
    pageSize = 10,
    id,
    supervisionProjectId,
    dataType = 1,
  } = params;
  const projectId = supervisionProjectId != null && supervisionProjectId !== ''
    ? supervisionProjectId
    : id;

  if (id != null && id !== '' && (supervisionProjectId == null || supervisionProjectId === '')) {
    const row = findMockTableRowById(id);
    const taskType = row
      ? row.task_type
      : DATA_TYPE_TO_TASK_TYPE[dataType] || TASK_TYPE.TEMP_LAND_RESTORE;
    const legacyTaskId = row ? row.task_id : String(id);
    const cards = getMockDetailByTaskType(taskType, legacyTaskId);
    const polygon = cardToPolygon(cards[0]);
    return {
      code: 0,
      data: polygon ? [polygon] : [],
      total: polygon ? 1 : 0,
      message: 'success',
    };
  }

  const row = findMockTableRowById(projectId);
  const taskType = row
    ? row.task_type
    : DATA_TYPE_TO_TASK_TYPE[dataType] || TASK_TYPE.TEMP_LAND_RESTORE;
  const legacyTaskId = row ? row.task_id : String(projectId);
  const cards = getMockDetailByTaskType(taskType, legacyTaskId);
  const polygons = cards.map(cardToPolygon).filter(Boolean);
  const start = (pageIndex - 1) * pageSize;
  return {
    code: 0,
    data: polygons.slice(start, start + pageSize),
    total: polygons.length,
    message: 'success',
  };
}

export async function mockGetSupervisionPolygonDetailApi(params = {}) {
  await delay();
  const polygonId = params.id || params.polygonId;
  const verticalViews = getMockVerticalViewsByPointId(polygonId);
  const pointId = resolveMockDetailPointId(polygonId);
  return {
    code: 0,
    data: {
      verticalViews,
      pointId,
      project: {
        id: 6,
        dataType: '1',
        count: 5,
        county: '无锡市(320200)',
        fcw: 5,
        jj: 2,
        wd: 8,
        status: 0,
        createPerson: 'WXSAdmin',
        collectTime: '2026-06-17',
        createTime: '2026-06-17 16:11:45',
      },
      construction_desc: 'AI 检测到图斑范围内存在防尘网及工程机械，建议人工复核',
      tag: '防尘网 5 | 工程机械 2 | 围挡 8',
      imagePath: nestImg,
    },
    message: 'success',
  };
}

/** 模拟：监管图斑全景坐标计算（pitch/yaw 顶点） */
export async function mockCalculatePanoramaApi(data = {}) {
  await delay();
  return {
    code: 0,
    data: {
      pitch: -5,
      yaw: 10,
      points: [
        [-8, -15],
        [-8, 15],
        [5, 15],
        [5, -15],
      ],
    },
    message: 'success',
  };
}

const MOCK_TASK_LIST_API_MAP = {
  [TASK_TYPE.TEMP_LAND_RESTORE]: mockGetTempLandRestoreTaskListApi,
  [TASK_TYPE.MOUNTAIN_WATER]: mockGetMountainWaterTaskListApi,
  [TASK_TYPE.CONSTRUCTION]: mockGetConstructionTaskListApi,
};

const MOCK_TASK_DETAIL_API_MAP = {
  [TASK_TYPE.TEMP_LAND_RESTORE]: mockGetTempLandRestoreTaskDetailApi,
  [TASK_TYPE.MOUNTAIN_WATER]: mockGetMountainWaterTaskDetailApi,
  [TASK_TYPE.CONSTRUCTION]: mockGetConstructionTaskDetailApi,
};

export function getMockTaskListApiByType(taskType) {
  return MOCK_TASK_LIST_API_MAP[taskType] || mockGetTempLandRestoreTaskListApi;
}

export function getMockTaskDetailApiByType(taskType) {
  return MOCK_TASK_DETAIL_API_MAP[taskType] || mockGetTempLandRestoreTaskDetailApi;
}
