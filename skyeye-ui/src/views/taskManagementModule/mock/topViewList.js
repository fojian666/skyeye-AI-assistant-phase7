import nestImg from '@/assets/images/nest2.png';

const DEFAULT_BOUNDS = [
    [118.99606296831247, 31.38533032058644],
    [118.99257103168753, 31.383063679413556]
];

function createVerticalView(pointId, index, format) {
    const num = String(index + 1).padStart(2, '0');
    return {
        id: index + 1,
        dataName: `DJI_mock_${pointId}_${num}.${format}`,
        fileId: `${pointId}_file_${num}`,
        path: nestImg,
        latitude: 31.384197,
        longitude: 118.994317,
        bounds: DEFAULT_BOUNDS,
        county: '南京市(320100)',
        fileSize: 5193728,
        collectTime: '2026-06-17 18:13:16',
        createTime: '2026-06-17 18:13:16',
        relationId: 1
    };
}

/** 按 pointId 生成 mock verticalViews（每组 3-4 张） */
const MOCK_VERTICAL_VIEW_MAP = {
    mock_point_ls001: [
        createVerticalView('mock_point_ls001', 0, 'jpg'),
        createVerticalView('mock_point_ls001', 1, 'png'),
        createVerticalView('mock_point_ls001', 2, 'jpg'),
        createVerticalView('mock_point_ls001', 3, 'png')
    ],
    mock_point_ls002: [
        createVerticalView('mock_point_ls002', 0, 'jpg'),
        createVerticalView('mock_point_ls002', 1, 'jpg'),
        createVerticalView('mock_point_ls002', 2, 'png')
    ],
    mock_point_ss001: [
        createVerticalView('mock_point_ss001', 0, 'png'),
        createVerticalView('mock_point_ss001', 1, 'jpg'),
        createVerticalView('mock_point_ss001', 2, 'png'),
        createVerticalView('mock_point_ss001', 3, 'jpg')
    ],
    mock_point_ss002: [
        createVerticalView('mock_point_ss002', 0, 'jpg'),
        createVerticalView('mock_point_ss002', 1, 'png'),
        createVerticalView('mock_point_ss002', 2, 'jpg')
    ],
    mock_point_js001: [
        createVerticalView('mock_point_js001', 0, 'jpg'),
        createVerticalView('mock_point_js001', 1, 'png'),
        createVerticalView('mock_point_js001', 2, 'jpg'),
        createVerticalView('mock_point_js001', 3, 'png'),
        createVerticalView('mock_point_js001', 4, 'jpg')
    ],
    mock_point_js002: [
        createVerticalView('mock_point_js002', 0, 'png'),
        createVerticalView('mock_point_js002', 1, 'jpg'),
        createVerticalView('mock_point_js002', 2, 'png')
    ]
};

const DEFAULT_POINT_ID = 'mock_point_ls001';

export function getMockVerticalViewsByPointId(pointId) {
    if (pointId && MOCK_VERTICAL_VIEW_MAP[pointId]) {
        return MOCK_VERTICAL_VIEW_MAP[pointId];
    }
    return MOCK_VERTICAL_VIEW_MAP[DEFAULT_POINT_ID];
}

/** @deprecated 兼容旧 mock，请使用 getMockVerticalViewsByPointId */
export function getMockTopViewListByPointId(pointId) {
    return getMockVerticalViewsByPointId(pointId);
}
