import proj4 from 'proj4';

const WGS84_DEF = '+proj=longlat +datum=WGS84 +no_defs +type=crs';

function get4528Epsg() {
  return (window.config && window.config.baseMap4528Epsg) || 'EPSG:4528';
}

function get4528Proj() {
  return (
    (window.config && window.config.baseMap4528Proj) ||
    '+proj=tmerc +lat_0=0 +lon_0=120 +k=1 +x_0=40500000 +y_0=0 +ellps=GRS80 +units=m +no_defs +type=crs'
  );
}

function ensureProjDefs() {
  proj4.defs('EPSG:4326', WGS84_DEF);
  const epsg = get4528Epsg();
  proj4.defs(epsg, get4528Proj());
  return epsg;
}

/** 是否为 WGS84 经纬度（度） */
export function isWgs84LatLng(latitude, longitude) {
  const lat = Number(latitude);
  const lng = Number(longitude);
  if (Number.isNaN(lat) || Number.isNaN(lng)) return false;
  return Math.abs(lat) <= 90 && Math.abs(lng) <= 180;
}

/**
 * 转为 Leaflet LatLng 用的 [lat, lng]（度）。
 * 接口字段 latitude=北向Y、longitude=东向X；若为 EPSG:4528 米制则转为 WGS84。
 */
export function toMapLatLng(latitude, longitude) {
  const lat = Number(latitude);
  const lng = Number(longitude);
  if (Number.isNaN(lat) || Number.isNaN(lng)) {
    return [latitude, longitude];
  }
  if (isWgs84LatLng(lat, lng)) {
    return [lat, lng];
  }
  const epsg = ensureProjDefs();
  const [lonDeg, latDeg] = proj4(epsg, 'EPSG:4326', [lng, lat]);
  return [latDeg, lonDeg];
}

export function toMapLatLngFromPoint(point) {
  if (!point) return null;
  return toMapLatLng(point.latitude, point.longitude);
}

/** WGS84 经纬度，供 Cesium.Cartesian3.fromDegrees(lon, lat) 使用 */
export function toCesiumLonLat(latitude, longitude) {
  const [lat, lng] = toMapLatLng(latitude, longitude);
  return { lat, lon: lng };
}

/** Leaflet 点击 WGS84 度 → 接口字段（latitude=北向Y、longitude=东向X，EPSG:4528 米） */
export function fromMapLatLngToApiCoords(lat, lng) {
  const latDeg = Number(lat);
  const lngDeg = Number(lng);
  if (Number.isNaN(latDeg) || Number.isNaN(lngDeg)) {
    return { latitude: lat, longitude: lng };
  }
  const epsg = ensureProjDefs();
  const [x, y] = proj4('EPSG:4326', epsg, [lngDeg, latDeg]);
  return { latitude: y, longitude: x };
}
