import cookies from 'js-cookie';
import icon from 'leaflet/dist/images/marker-icon.png';

/**
 * JSON对象中的字符串去除空格
 * @param obj JSON对象
 * @return 属性去除空格的 JSON 对象
 */
export function objectTrim(obj) {
    for (const key in obj) {
        if (typeof obj[key] === 'string') obj[key] = obj[key].trim();
    }
}

// =======================================================================================
// Cookie操作：httpOnly的cookie, js拿不到。spring-security返回的"自动登录"cookie, js无法拿到。
export function setCookie(key, value, args) {
    cookies.set(key, value, args);
}

export function getCookie(key) {
    return cookies.get(key);
}

export function removeCookie(key, args) {
    cookies.remove(key, args);
}

// =======================================================================================
// 网络操作

/**
 * 判断该用户是否登录了（自动登录）, 需要携带自动登录的cookie
 */

// 计算平面坐标系地图分辨率
export function calcResolution(arr) {
    const resolution = [];
    arr.forEach((item) => {
        resolution.push(0.0254 / 96 / item);
    });
    return resolution;
}

export function arrayToTree(array, pid) {
    let result = [];
    array.forEach((item) => {
        if (item.pid == pid) {
            item.children = arrayToTree(array, item.id);
            result.push(item);
        }
    });
    return result;
}

let lineBarDRAWLAYERS = [];
let polygonBarDRAWLAYERS = [];
let pointMarker = null;
let pointMarkerArr = [];
let lineMarker = null;
let lineMarkerArr = [];
let polygonMarker = null;
let polygonMarkerArr = [];
/** 测面积过程中未完成的多边形图层（未右键结束前） */
let activeMeasurePolygon = null;

function offMeasureMapEvents(map) {
    if (!map) {
        return;
    }
    map.off('mousedown');
    map.off('mousemove');
    map.off('dblclick');
    map.off('contextmenu');
    if (map.getContainer()) {
        map.getContainer().style.cursor = '';
    }
}

// 画点；decimalPlaces 可选，指定经纬度弹窗保留小数位数
export function drawPoint(map, decimalPlaces) {
    const decimals = typeof decimalPlaces === 'number' ? decimalPlaces : window.config.projectCity === 'tangshan' ? 6 : 2;
    var DRAWING = false; //是否正在绘制
    map.getContainer().style.cursor = 'crosshair';
    map.on('click', (e) => {
        DRAWING = true; //是否正在绘制
        pointMarker = new L.Marker(e.latlng, {
            draggable: false, // 允许点位拖拽
            icon: L.icon({
                iconUrl: icon,
                iconSize: [24, 40] // 图片大小
            })
        });
        map.addLayer(pointMarker);
        pointMarker.bindPopup(`坐标：[${e.latlng.lng.toFixed(decimals)}, ${e.latlng.lat.toFixed(decimals)}]`).openPopup();
        pointMarkerArr.push(pointMarker);
        if (DRAWING) {
            DRAWING = false;
            //移除事件
            map.off('click');
            map.getContainer().style.cursor = '';
        }
    });
}

// 测量距离
export function measureDistance(map) {
    let DRAWING = false; //是否正在绘制
    let MEASURERESULT = 0; //测量结果
    let DRAWMOVEPOLYLINE = null; //绘制过程中的折线
    let DRAWPOLYLINEPOINTS = []; //绘制的折线的节点集
    let distance = 0;
    map.getContainer().style.cursor = 'crosshair';
    const shapeOptions = {
        color: '#F54124',
        weight: 5,
        opacity: 0.8,
        fill: false,
        clickable: true
    };
    //绘制的折线
    let DRAWPOLYLINE = new L.Polyline([], shapeOptions); // 绘制的折线
    //地图上添加折线
    map.addLayer(DRAWPOLYLINE);
    //设置地图的鼠标按下事件
    map.on('mousedown', (e) => {
        DRAWING = true; //是否正在绘制
        DRAWPOLYLINEPOINTS.push(e.latlng); //绘制的折线的节点集
        //测量结果加上距离上个点的距离
        if (DRAWPOLYLINEPOINTS.length > 1) {
            MEASURERESULT += e.latlng.distanceTo(DRAWPOLYLINEPOINTS[DRAWPOLYLINEPOINTS.length - 2]);
        }

        //绘制的折线添加进集合
        DRAWPOLYLINE.addLatLng(e.latlng);
        //地图添加鼠标移动事件
        map.on('mousemove', (e) => {
            if (DRAWING) {
                //是否正在绘制
                //将上次的移除
                if (DRAWMOVEPOLYLINE != undefined && DRAWMOVEPOLYLINE != null) {
                    //绘制过程中的折线
                    map.removeLayer(DRAWMOVEPOLYLINE);
                }
                //获取上个点坐标
                let prevPoint = DRAWPOLYLINEPOINTS[DRAWPOLYLINEPOINTS.length - 1];
                //绘制最后一次的折线
                DRAWMOVEPOLYLINE = new L.Polyline([prevPoint, e.latlng], shapeOptions);
                //添加到地图
                map.addLayer(DRAWMOVEPOLYLINE);
                //累加距离
                distance = MEASURERESULT + e.latlng.distanceTo(DRAWPOLYLINEPOINTS[DRAWPOLYLINEPOINTS.length - 1]);
            }
        });
    });

    //设置地图的双击事件
    map.on('contextmenu', (e) => {
        map.getContainer().style.cursor = '';
        /*显示两点距离*/
        //之前的距离加上最后一次的距离
        distance = MEASURERESULT + e.latlng.distanceTo(DRAWPOLYLINEPOINTS[DRAWPOLYLINEPOINTS.length - 1]);
        //添加一个标记
        lineMarker = new L.Marker(e.latlng, {
            draggable: false,
            icon: L.icon({
                iconUrl: icon,
                iconSize: [20, 30] // 图片大小
            })
        });
        //地图上添加标记
        map.addLayer(lineMarker);
        //标记绑定弹窗显示
        // lineMarker.bindPopup((distance / 1000).toFixed(2) + '公里').openPopup();
        if (window.config.projectCity == 'tangshan') {
            if (distance < 1000) {
                lineMarker.bindPopup(distance.toFixed(2) + '米').openPopup();
            } else {
                lineMarker.bindPopup((distance / 1000).toFixed(2) + '公里').openPopup();
            }
        } else {
            lineMarker.bindPopup((distance / 1000).toFixed(2) + '公里').openPopup();
        }

        lineMarkerArr.push(lineMarker);
        if (DRAWING) {
            //清除上次的
            if (DRAWMOVEPOLYLINE != undefined && DRAWMOVEPOLYLINE != null) {
                map.removeLayer(DRAWMOVEPOLYLINE);
                DRAWMOVEPOLYLINE = null;
            }
            lineBarDRAWLAYERS.push(DRAWPOLYLINE);
            DRAWPOLYLINEPOINTS = [];
            DRAWING = false;
            //移除事件
            map.off('mousedown');
            map.off('mousemove');
            map.off('dblclick');
            map.off('contextmenu');
        }
    });
}

export function clearGraphical(map) {
    offMeasureMapEvents(map);
    pointMarkerArr.forEach((item) => {
        map.removeLayer(item);
    });
    pointMarkerArr = [];
    lineBarDRAWLAYERS.forEach((item) => {
        map.removeLayer(item);
    });
    lineBarDRAWLAYERS = [];
    lineMarkerArr.forEach((item) => {
        map.removeLayer(item);
    });
    lineMarkerArr = [];
    polygonBarDRAWLAYERS.forEach((item) => {
        map.removeLayer(item);
    });
    polygonBarDRAWLAYERS = [];
    polygonMarkerArr.forEach((item) => {
        map.removeLayer(item);
    });
    polygonMarkerArr = [];
    if (activeMeasurePolygon) {
        map.removeLayer(activeMeasurePolygon);
        activeMeasurePolygon = null;
    }
}

// 画多边形，测量面积（右键结束）
export function measureArea(map) {
    offMeasureMapEvents(map);
    if (activeMeasurePolygon) {
        map.removeLayer(activeMeasurePolygon);
        activeMeasurePolygon = null;
    }

    var DRAWING = false; //是否正在绘制
    var DRAWPOLYGON; //绘制的面
    var DRAWMOVEPOLYGON; //绘制过程中的面
    var DRAWPOLYGONPOINTS = []; //绘制的面的节点集

    var shapeOptions = {
        color: '#F54124',
        weight: 5,
        opacity: 0.8,
        fill: true,
        fillColor: null,
        fillOpacity: 0.2,
        clickable: true
    };
    map.getContainer().style.cursor = 'crosshair';
    //地图添加鼠标按下事件
    map.on('mousedown', (e) => {
        DRAWING = true;
        DRAWPOLYGONPOINTS.push(e.latlng);
        DRAWPOLYGON.addLatLng(e.latlng);
    });
    //地图添加鼠标移动事件
    map.on('mousemove', (e) => {
        if (DRAWING) {
            //清除上次数据
            if (DRAWMOVEPOLYGON != undefined && DRAWMOVEPOLYGON != null) {
                map.removeLayer(DRAWMOVEPOLYGON);
            }
            var prevPoint = DRAWPOLYGONPOINTS[DRAWPOLYGONPOINTS.length - 1];
            var firstPoint = DRAWPOLYGONPOINTS[0];
            DRAWMOVEPOLYGON = new L.Polygon([firstPoint, prevPoint, e.latlng], shapeOptions);
            map.addLayer(DRAWMOVEPOLYGON);
        }
    });

    map.on('contextmenu', (e) => {
        if (!DRAWING) {
            offMeasureMapEvents(map);
            return;
        }

        var tempPoints = DRAWPOLYGONPOINTS.slice();
        tempPoints.push(e.latlng);

        var pointsCount = tempPoints.length;
        var distance = 0;
        if (pointsCount > 2) {
            var area = 0.0;
            var d2r = Math.PI / 180;
            for (var i = 0; i < pointsCount; i++) {
                var p1 = tempPoints[i];
                var p2 = tempPoints[(i + 1) % pointsCount];
                area += (p2.lng - p1.lng) * d2r * (2 + Math.sin(p1.lat * d2r) + Math.sin(p2.lat * d2r));
            }
            distance = Math.abs((area * 6378137.0 * 6378137.0) / 2.0);

            polygonMarker = new L.Marker(e.latlng, {
                draggable: false,
                icon: L.icon({
                    iconUrl: icon,
                    iconSize: [20, 30]
                })
            });
            map.addLayer(polygonMarker);
            if (window.config.projectCity == 'tangshan') {
                let areaMu = (distance / 666.6667).toFixed(2);
                polygonMarker.bindPopup('总面积：' + distance.toFixed(2) + '平方米（' + areaMu + '亩）').openPopup();
            } else {
                polygonMarker.bindPopup('总面积：' + distance.toFixed(2) + '平方米').openPopup();
            }
            polygonMarkerArr.push(polygonMarker);
        }

        if (DRAWMOVEPOLYGON != undefined && DRAWMOVEPOLYGON != null) {
            map.removeLayer(DRAWMOVEPOLYGON);
            DRAWMOVEPOLYGON = null;
        }
        if (pointsCount > 2) {
            polygonBarDRAWLAYERS.push(DRAWPOLYGON);
        } else {
            map.removeLayer(DRAWPOLYGON);
        }
        activeMeasurePolygon = null;
        DRAWPOLYGONPOINTS = [];
        DRAWING = false;
        offMeasureMapEvents(map);
    });

    DRAWPOLYGON = new L.Polygon([], shapeOptions);
    map.addLayer(DRAWPOLYGON);
    activeMeasurePolygon = DRAWPOLYGON;
}

export function formatDate(date) {
    return new Date(date)
        .toLocaleDateString('zh-CN', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit'
        })
        .replace(/\//g, '-');
}

//菜单树状结构对接公共接口，增加对应的参数
export function traverseList(list) {
    // 遍历列表中的每个元素
    for (let item of list) {
        item.caption = item.name;
        item.display = item.enabled;
        item.order = item.sequenceNumber;
        if (!item.url) {
            item.url = item.children[0].url;
            if (!item.children[0].url) {
                item.url = item.children[0].children[0].url;
            }
        }
        if (item.children) {
            traverseList(item.children);
        }
    }
}

export function getCheckedTree(data) {
    function filterChecked(nodes) {
        return nodes
            .filter((node) => node.checked)
            .map((node) => {
                const newNode = { ...node };
                if (node.children && node.children.length > 0) {
                    const filteredChildren = filterChecked(node.children);
                    if (filteredChildren.length > 0) {
                        newNode.children = filteredChildren;
                    } else {
                        delete newNode.children;
                    }
                }
                return newNode;
            });
    }

    return filterChecked(data);
}

export function findNodeWithPath(node, path) {
    if (node.url === path) {
        return true;
    }
    if (node.children && node.children.length > 0) {
        for (let child of node.children) {
            const result = findNodeWithPath(child, path);
            if (result) {
                return true;
            }
        }
    }
    return false;
}

// 递归检查树结构路径权限
export function checkMenuPermission(menuTree, targetPath) {
    for (const node of menuTree) {
        if (node.url === targetPath) {
            return true;
        }
        if (node.children && node.children.length) {
            if (checkMenuPermission(node.children, targetPath)) {
                return true;
            }
        }
    }
    return false;
}

export function subPage(targetPath, fromPath) {
    if (targetPath.startsWith('/panoramic-detection/verifyClue') && fromPath === '/panoramic-detection/task-management') {
        return true;
    } else if (targetPath.startsWith('/pattern-verifiy/map_overview') && fromPath === '/pattern-verifiy/task_management') {
        return true;
    }
    return false;
}

/**
 * 将图像中的角度坐标转换为经纬度坐标
 * @param {number} lat - 基准纬度
 * @param {number} lon - 基准经度
 * @param {number} h - 高度（米）
 * @param {number} yaw - 偏航角（度）
 * @param {number} pitch - 俯仰角（度）
 * @param {number} north_offset - 北向偏移（度）
 * @returns {Array} 包含最终纬度和经度的数组 [final_lat, final_lon]
 */
export function imageToLatLon(lat, lon, h, yaw, pitch, north_offset) {
    // 将角度转换为弧度的工具函数
    const toRadians = (degrees) => degrees * (Math.PI / 180);

    // 将 yaw 和 pitch 转换为弧度
    const yawRad = toRadians(Number(yaw) + Number(north_offset));
    const pitchRad = toRadians(90 - Math.abs(pitch));

    let deltaLat = 0;
    let deltaLon = 0;

    // 计算D时需要考虑 pitch 的范围
    if (pitch !== -90 && pitch !== 90) {
        // 计算到目标点的水平距离
        const horizontalDistance = h * Math.tan(pitchRad);

        const dE = horizontalDistance * Math.sin(yawRad);
        const dN = horizontalDistance * Math.cos(yawRad);

        const R = 6378137; // 地球半径（米）
        deltaLat = (dN / R) * (180 / Math.PI);
        deltaLon = (dE / (R * Math.cos(toRadians(lat)))) * (180 / Math.PI);
    }

    const finalLat = lat + deltaLat;
    const finalLon = lon + deltaLon;
    return [finalLat, finalLon];
}
/**
 * 将经纬度坐标转换为球面坐标（相对无人机）
 * @param {number} lat - 目标点纬度
 * @param {number} lon - 目标点经度
 * @param {number} alt - 目标点高度
 * @param {number} refLat - 参考点（无人机）纬度
 * @param {number} refLon - 参考点（无人机）经度
 * @param {number} refAlt - 参考点（无人机）高度
 * @returns {Array} 球面坐标 [x, y, z]
 */
export function geodeticToSpherical(lat, lon, alt, refLat, refLon, refAlt) {
    // 转换为弧度
    const toRadians = (deg) => deg * (Math.PI / 180);
    const latRad = toRadians(lat);
    const lonRad = toRadians(lon);
    const refLatRad = toRadians(refLat);
    const refLonRad = toRadians(refLon);

    // 计算大圆距离
    const d = calculateDistance(refLat, refLon, lat, lon);

    // 计算方向（航向角）
    const deltaLon = lonRad - refLonRad;
    const y = Math.sin(deltaLon) * Math.cos(latRad);
    const x = Math.cos(refLatRad) * Math.sin(latRad) - Math.sin(refLatRad) * Math.cos(latRad) * Math.cos(deltaLon);
    const bearing = Math.atan2(y, x);

    // 计算球面坐标
    const xCoord = d * Math.cos(bearing);
    const yCoord = d * Math.sin(bearing);
    const zCoord = alt - refAlt;

    return [xCoord, yCoord, zCoord];
}

/**
 * 计算每个点相对于无人机的偏航角(yaw)和俯仰角(pitch)
 * @param {number} lat - 目标点纬度
 * @param {number} lon - 目标点经度
 * @param {number} h - 目标点高度
 * @param {number} droneLat - 无人机纬度
 * @param {number} droneLon - 无人机经度
 * @param {number} droneAlt - 无人机高度
 * @param {number} northOffset - 北向偏移
 * @returns {Array} 包含偏航角和俯仰角的数组 [yaw, pitch]
 */
export function latLonToYawPitch(lat, lon, h, droneLat, droneLon, droneAlt, northOffset) {
    const [x, y, z] = geodeticToSpherical(lat, lon, h, droneLat, droneLon, droneAlt);

    // 计算方位角，并调整范围到[-180, 180]
    let yaw = (Math.atan2(y, x) * 180) / Math.PI - northOffset;
    if (yaw < -180) {
        yaw += 360;
    } else if (yaw > 180) {
        yaw -= 360;
    }

    // 计算俯仰角
    const pitch = (Math.atan2(z, Math.sqrt(x ** 2 + y ** 2)) * 180) / Math.PI;

    return [yaw, pitch];
}
/**
 * 计算两点经纬度之间的距离（米）
 * 使用Haversine公式
 */
export function calculateDistance(lat1, lon1, lat2, lon2) {
    const R = 6371000; // 地球半径（米）
    // 角度转弧度
    const toRadians = (deg) => deg * (Math.PI / 180);
    const radLat1 = toRadians(lat1);
    const radLon1 = toRadians(lon1);
    const radLat2 = toRadians(lat2);
    const radLon2 = toRadians(lon2);
    // 计算经纬度差值
    const deltaLat = radLat2 - radLat1;
    const deltaLon = radLon2 - radLon1;
    // Haversine公式
    const a =
        Math.sin(deltaLat / 2) * Math.sin(deltaLat / 2) + Math.cos(radLat1) * Math.cos(radLat2) * Math.sin(deltaLon / 2) * Math.sin(deltaLon / 2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    return R * c; // 距离（米）
}

/**
 * 将单点坐标规范为 Leaflet 使用的 [纬度, 经度]。
 * 纬度绝对值不超过 90；若首项 > 90 则判定为 [经度, 纬度] 并交换。
 */
export function normalizeLatLngPoint(point) {
    if (!Array.isArray(point) || point.length < 2) return point;
    const first = Number(point[0]);
    const second = Number(point[1]);
    if (Number.isNaN(first) || Number.isNaN(second)) return point;
    if (Math.abs(first) > 90 && Math.abs(second) <= 90) {
        return [second, first];
    }
    return [first, second];
}

/**
 * 批量规范坐标列表为 [纬度, 经度]
 */
export function normalizeLatLngList(points) {
    if (!Array.isArray(points)) return [];
    const result = [];
    for (let i = 0; i < points.length; i++) {
        result.push(normalizeLatLngPoint(points[i]));
    }
    return result;
}

/**
 * 计算多个经纬度点的总距离
 * @param {Array} points - 点数组，每个点格式为 [纬度, 经度]
 * @returns {number} 总距离（米）
 */
export function calculateTotalDistance(points) {
    let MEASURERESULT = 0; //测量结果
    for (let i = 0; i < points.length - 1; i++) {
        MEASURERESULT += points[i].distanceTo(points[i + 1]);
    }
    return MEASURERESULT;
}

export function calculateTotalArea(points) {
    //计算面积
    var pointsCount = points.length,
        area = 0.0,
        d2r = Math.PI / 180,
        p1,
        p2;
    if (pointsCount > 2) {
        for (var i = 0; i < pointsCount; i++) {
            p1 = points[i];
            p2 = points[(i + 1) % pointsCount];
            area += (p2.lng - p1.lng) * d2r * (2 + Math.sin(p1.lat * d2r) + Math.sin(p2.lat * d2r));
        }
        var allarea = Math.abs((area * 6378137.0 * 6378137.0) / 2.0);
    }
    return allarea;
}

// onFinish 回调参数，用于绘制结束后返回结果
export function drawPolygon(map, shapeOptions, onFinish) {
    let DRAWING = false; // 是否正在绘制
    let DRAWPOLYGON; // 最终绘制的多边形
    let DRAWMOVEPOLYGON; // 绘制过程中的临时多边形
    let DRAWPOLYGONPOINTS = []; // 绘制过程中收集的顶点

    // 设置鼠标样式为十字光标
    map.getContainer().style.cursor = 'crosshair';

    // 初始化最终多边形图层
    DRAWPOLYGON = new L.Polygon([], shapeOptions);
    map.addLayer(DRAWPOLYGON);

    // 1. 鼠标按下：添加顶点
    map.on('mousedown', (e) => {
        if (e.originalEvent.button !== 0) return; //右键处理的不放进去
        DRAWING = true;
        // const point = { lat: e.latlng.lat, lng: e.latlng.lng }; // 格式化坐标
        const point = [e.latlng.lat, e.latlng.lng]; // 格式化坐标
        DRAWPOLYGONPOINTS.push(point); // 收集顶点
        DRAWPOLYGON.addLatLng(e.latlng); // 添加到最终多边形
    });

    // 2. 鼠标移动：实时绘制临时多边形
    map.on('mousemove', (e) => {
        if (!DRAWING) return; // 未绘制状态不处理

        // 清除上一次的临时多边形
        if (DRAWMOVEPOLYGON && map.hasLayer(DRAWMOVEPOLYGON)) {
            map.removeLayer(DRAWMOVEPOLYGON);
        }

        // 至少有一个顶点才绘制临时多边形
        if (DRAWPOLYGONPOINTS.length >= 1) {
            const lastPoint = DRAWPOLYGONPOINTS[DRAWPOLYGONPOINTS.length - 1];
            const tempLatLngs = [
                ...DRAWPOLYGONPOINTS.map((p) => L.latLng(p[0], p[1])), // 已选顶点
                e.latlng // 当前鼠标位置（临时顶点）
            ];
            // 创建临时多边形并添加到地图
            DRAWMOVEPOLYGON = new L.Polygon(tempLatLngs, shapeOptions);
            map.addLayer(DRAWMOVEPOLYGON);
        }
    });

    // 3. 右击结束绘制（核心：触发回调返回结果）
    map.on('contextmenu', (e) => {
        if (!DRAWING) return; // 未绘制状态不处理

        // 恢复鼠标样式
        map.getContainer().style.cursor = '';

        // 清除临时多边形
        if (DRAWMOVEPOLYGON && map.hasLayer(DRAWMOVEPOLYGON)) {
            map.removeLayer(DRAWMOVEPOLYGON);
            DRAWMOVEPOLYGON = null;
        }

        // 收集最终顶点（包含右击结束时的点）
        const finalPoints = [...DRAWPOLYGONPOINTS];

        // 保存最终多边形到图层列表
        // polygonBarDRAWLAYERS.push(DRAWPOLYGON);

        // 重置绘制状态
        DRAWING = false;
        DRAWPOLYGONPOINTS = [];

        // 移除绘制相关事件（防止重复触发）
        map.off('mousedown');
        map.off('mousemove');
        map.off('contextmenu');

        // 关键：通过回调返回最终顶点列表
        if (typeof onFinish === 'function') {
            const tempfinalPoints = finalPoints.map((item) => {
                return L.latLng(item[0], item[1]);
            });
            const allArea = calculateTotalArea(tempfinalPoints);
            onFinish(finalPoints, DRAWPOLYGON, (allArea / 666.6667).toFixed(2));
        }
    });
}

export function formatCurrentTime() {
    const now = new Date();
    const year = now.getFullYear();
    // 月份从 0 开始，所以要 +1
    const month = (now.getMonth() + 1).toString().padStart(2, '0');
    const day = now.getDate().toString().padStart(2, '0');
    const hour = now.getHours().toString().padStart(2, '0');
    const minute = now.getMinutes().toString().padStart(2, '0');
    const second = now.getSeconds().toString().padStart(2, '0');
    // 这里如果需要秒可以继续处理 getSeconds()
    return `${year}-${month}-${day} ${hour}:${minute}:${second}`;
}
export function judgeInnerOrutside() {
    const currntUrl = window.location.href;
    const urlObj = new URL(currntUrl);
    const hostWithPort = urlObj.host;
    var outside = 0;
    if (hostWithPort === window.config.outerIp) {
        outside = 1;
    }
    return outside;
}

export function judgeInnerOrutsideAndIserver() {
    const currntUrl = window.location.href;
    const urlObj = new URL(currntUrl);
    const hostWithPort = urlObj.host;
    var outside = 0;
    var iserverAdress = window.config.iserverAdress;
    if (hostWithPort === window.config.outerIp) {
        outside = 1;
        iserverAdress = window.config.outerIserverAdress;
    }
    return iserverAdress;
}

export function judgeInnerOrutsideAndgridSampleUrl() {
    const currntUrl = window.location.href;
    const urlObj = new URL(currntUrl);
    const hostWithPort = urlObj.host;
    var outside = 0;
    var gridSampleUrl = window.config.gridSampleUrl;
    if (hostWithPort === window.config.outerIp) {
        outside = 1;
        gridSampleUrl = window.config.outerGridSampleUrl;
    }
    return gridSampleUrl;
}

export function judgeInnerOrutsideAndPointSampleUrl() {
    const currntUrl = window.location.href;
    const urlObj = new URL(currntUrl);
    const hostWithPort = urlObj.host;
    var outside = 0;
    var pointSampleUrl = window.config.pointSampleUrl;
    if (hostWithPort === window.config.outerIp) {
        outside = 1;
        pointSampleUrl = window.config.outerPointSampleUrl;
    }
    return pointSampleUrl;
}
