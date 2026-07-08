/**
 * 监管项目列表接口响应适配
 */

function normalizePolygonField(polygon) {
    if (!polygon) return null;
    if (typeof polygon === 'string') {
        try {
            return JSON.parse(polygon);
        } catch (e) {
            return null;
        }
    }
    return polygon;
}

export function parseProjectListData(data) {
    if (!data) return [];
    if (Array.isArray(data)) return data;
    if (Array.isArray(data.list)) return data.list;
    if (data.id != null) return [data];
    return [];
}

export function adaptProjectListItem(item) {
    if (!item) return null;
    const count = item.count != null ? item.count : 0;
    return {
        id: item.id,
        task_id: String(item.id),
        dataType: item.dataType,
        total_count: count,
        done_count: item.done_count != null ? item.done_count : count,
        todo_count: item.todo_count != null ? item.todo_count : 0,
        street: item.county || item.street || '',
        county: item.county || '',
        city: item.city || '',
        polygonName: item.polygonName || '',
        verifier: item.createPerson || item.verifier || '',
        createPerson: item.createPerson || '',
        status: item.status,
        hasPic: item.hasPic || '',
        collectTime: item.collectTime || '',
        createTime: item.createTime || ''
    };
}

export function adaptProjectList(data) {
    return parseProjectListData(data).map(adaptProjectListItem).filter(Boolean);
}

export function adaptPolygonToCard(polygon, projectId, dataType) {
    if (!polygon) return null;
    const pointId = polygon.pointId || polygon.point_id || polygon.id;
    const todoCount = polygon.todoCount != null ? polygon.todoCount : polygon.todo_count || 0;
    const doneCount = polygon.doneCount != null ? polygon.doneCount : polygon.done_count || 0;
    const pid = projectId != null ? projectId : polygon.supervisionProjectId;
    return {
        id: polygon.id,
        taskId: String(pid),
        supervisionProjectId: polygon.supervisionProjectId != null ? polygon.supervisionProjectId : pid,
        dataType,
        taskName: polygon.polygonType || polygon.taskName || polygon.pointName || polygon.name || `图斑${polygon.id}`,
        pointName: polygon.polygonType || polygon.pointName || polygon.name || `图斑${polygon.id}`,
        polygonType: polygon.polygonType || '',
        pointId,
        point_id: pointId,
        latitude: polygon.latitude != null ? polygon.latitude : polygon.lat,
        longitude: polygon.longitude != null ? polygon.longitude : polygon.lon,
        lat: polygon.lat != null ? polygon.lat : polygon.latitude,
        lon: polygon.lon != null ? polygon.lon : polygon.longitude,
        polygon: normalizePolygonField(polygon.polygon),
        constructionDesc: polygon.constructionDesc || '',
        colorDesc: polygon.colorDesc || '',
        status: polygon.status != null ? polygon.status : 0,
        createPerson: polygon.createPerson || '',
        createTime: polygon.createTime || '',
        updateTime: polygon.updateTime || '',
        height: polygon.height != null ? polygon.height : 100,
        yawDegree: polygon.yawDegree || 0,
        imageName: polygon.imageName || '',
        imageId: polygon.imageId || '',
        batchId: polygon.batchId || '',
        street: polygon.street || polygon.county || '',
        verticalCount: polygon.verticalCount != null ? polygon.verticalCount : polygon.vertical_count != null ? polygon.vertical_count : 0,
        doneCount,
        todoCount,
        aiResult: polygon.aiResult || {},
        plotStats: polygon.plotStats || {
            total_count: todoCount + doneCount,
            todo_count: todoCount,
            done_count: doneCount,
            status: polygon.status != null ? polygon.status : 0
        }
    };
}

export function cardToPolygon(card) {
    if (!card) return null;
    return {
        id: card.pointId || card.point_id,
        pointId: card.pointId || card.point_id,
        pointName: card.pointName || card.taskName,
        name: card.pointName || card.taskName,
        imageName: card.imageName,
        imageId: card.imageId,
        street: card.street,
        county: card.street,
        createTime: card.createTime,
        status: card.status,
        doneCount: card.doneCount,
        todoCount: card.todoCount,
        done_count: card.doneCount,
        todo_count: card.todoCount,
        yawDegree: card.yawDegree,
        lat: card.lat,
        lon: card.lon,
        latitude: card.latitude || card.lat,
        longitude: card.longitude || card.lon,
        height: card.height,
        verticalCount: card.verticalCount,
        aiResult: card.aiResult,
        plotStats: card.plotStats
    };
}

export function adaptProjectDetail(data, projectId) {
    if (!data) {
        return { cards: [], routes: [], totalCount: 0 };
    }

    const detail = Array.isArray(data) ? data[0] || {} : data;
    const polygons = Array.isArray(detail.polygons) ? detail.polygons : [];
    const routes = detail.routes || [];

    const pid =
        projectId != null && projectId !== ''
            ? projectId
            : detail.supervisionProjectId || detail.id || (polygons[0] && polygons[0].supervisionProjectId);
    const dataType = detail.dataType || (polygons[0] && polygons[0].dataType);

    const cards = polygons.map((p) => adaptPolygonToCard(p, pid, dataType)).filter(Boolean);

    return { cards, routes, totalCount: cards.length };
}

export function parsePolygonListData(data) {
    if (!data) return [];
    if (Array.isArray(data)) return data;
    if (Array.isArray(data.list)) return data.list;
    if (data.id != null) return [data];
    return [];
}

export function adaptPolygonList(data, projectId, dataType) {
    return parsePolygonListData(data)
        .map((p) => adaptPolygonToCard(p, projectId, dataType != null ? dataType : p.dataType))
        .filter(Boolean);
}

export function adaptPolygonDetail(data, projectId) {
    const item = parsePolygonListData(data)[0];
    if (!item) return null;
    const pid = projectId || item.supervisionProjectId;
    return adaptPolygonToCard(item, pid, item.dataType);
}
