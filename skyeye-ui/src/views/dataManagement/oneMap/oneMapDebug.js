/** 南京市区测试全景点（玄武湖附近），用于接口无数据时的地图联调 */
export const NANJING_TEST_PANORAMA_POINT = {
    pointId: 'nj_test_panorama_001',
    pointName: '南京测试全景点',
    latitude: 32.0707,
    longitude: 118.7969,
    panoramaImageCount: 1,
    latestTime: '2026-07-03',
    gridOperator: '测试',
    address: '南京市玄武区',
    pointType: '0'
};

/**
 * 是否为临时全景点。
 * 仅字符串 '1' 视为临时点；接口常返回数字 1 表示正式全景点（与任务管理里 pointType===0 的语义不同）。
 */
export function isTempPanoramaPoint(item) {
    return item != null && item.pointType === '1';
}

export function mergeNanjingTestPanoramaPoint(panoramaList) {
    const cfg = window.config && window.config.oneMapTestPanorama;
    const enabled = cfg == null ? true : cfg.enabled !== false;
    if (!enabled) {
        return panoramaList || [];
    }
    const testPoint = cfg && cfg.point ? cfg.point : NANJING_TEST_PANORAMA_POINT;
    const list = [...(panoramaList || [])];
    const exists = list.some(
        (p) =>
            p.pointId === testPoint.pointId ||
            (Number(p.latitude) === Number(testPoint.latitude) && Number(p.longitude) === Number(testPoint.longitude))
    );
    if (!exists) {
        list.unshift({ ...testPoint });
    }
    return list;
}
