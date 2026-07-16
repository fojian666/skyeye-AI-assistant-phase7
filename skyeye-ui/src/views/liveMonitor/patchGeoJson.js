import proj4 from 'proj4';

const PATCH_SOURCE_CRS = 'EPSG:4528';

proj4.defs(PATCH_SOURCE_CRS, '+proj=tmerc +lat_0=0 +lon_0=120 +k=1 +x_0=40500000 +y_0=0 +ellps=GRS80 +units=m +no_defs');

function getFirstCoordinate(coords) {
    if (typeof coords[0] === 'number') {
        return coords;
    }
    return getFirstCoordinate(coords[0]);
}

function isProjectedCoordinate([x, y]) {
    return Math.abs(x) > 180 || Math.abs(y) > 90;
}

function toLeafletLatLng([x, y]) {
    const [lon, lat] = proj4(PATCH_SOURCE_CRS, 'EPSG:4326', [x, y]);
    return [lat, lon];
}

function transformCoords(coords) {
    if (typeof coords[0] === 'number') {
        return toLeafletLatLng(coords);
    }
    return coords.map(transformCoords);
}

export function transformProjectedFeatureToMap(feature) {
    const geometry = JSON.parse(JSON.stringify(feature.geometry));
    delete geometry.bbox;
    const first = getFirstCoordinate(geometry.coordinates || []);
    if (first.length >= 2 && isProjectedCoordinate(first)) {
        if (geometry.type === 'Polygon' || geometry.type === 'MultiPolygon') {
            geometry.coordinates = transformCoords(geometry.coordinates);
        }
    }
    return {
        type: 'Feature',
        geometry,
        properties: feature.properties || {}
    };
}

export function buildPatchPopupHtml(properties) {
    const props = properties || {};
    return [
        props.dkmc ? `<div>地块名称：${props.dkmc}</div>` : '',
        props.tbbh ? `<div>图斑编号：${props.tbbh}</div>` : '',
        props.xzqmc ? `<div>行政区：${props.xzqmc}</div>` : '',
        props.mj != null ? `<div>面积：${props.mj} ㎡</div>` : '',
        props.violation_type ? `<div>违法类型：${props.violation_type}</div>` : '',
        props.overall_label ? `<div>研判结果：${props.overall_label}</div>` : '',
        props.fxsj ? `<div>发现时间：${props.fxsj}</div>` : ''
    ].join('');
}
