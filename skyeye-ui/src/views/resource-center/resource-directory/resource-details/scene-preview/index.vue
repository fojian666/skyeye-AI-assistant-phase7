<template>
    <a-modal v-model="visible" :dialog-style="{ top: '10vh' }" title="场景预览" width="80vw">
        <div id="map" style="margin: 0 auto; width: 100%; height: 100%"></div>
    </a-modal>
</template>

<script>
import { calcResolution } from '@/utils/utils';
import { TiledMapLayer, GetFeaturesBySQLParameters, FeatureService } from '@supermap/iclient-leaflet';

import { getResourceByIdApi } from '@/api/commonApi';
export default {
    data() {
        return {
            url: '',
            coordinate_system: '',
            center: null,
            zoom: 11,
            visible: false,
            source_id: 0,
            proj: ''
        };
    },
    methods: {
        open(obj) {
            this.source_id = obj.source_id;
            this.visible = true;
            this.getTaskById();
        },
        async getTaskById() {
            const res = await getResourceByIdApi(this.source_id);
            if (res.code === 0) {
                const dataObj = res.data;
                this.url = dataObj.url;
                this.coordinate_system = dataObj.coordinateSystem;
                this.center = dataObj.center;
                this.initMap();
            }
        },
        initMap() {
            let projs = {
                4528: '',
                4549: '+proj=tmerc +lat_0=0 +lon_0=120 +k=1 +x_0=500000 +y_0=0 +ellps=GRS80 +units=m +no_defs \n'
            };
            this.axios.get(this.url + '.json', { withCredentials: false }).then((res) => {
                const serveData = res.data;
                const minX = serveData.bounds.left.toFixed(2);
                const minY = serveData.bounds.bottom.toFixed(2);
                const maxX = serveData.bounds.right.toFixed(2);
                const maxY = serveData.bounds.top.toFixed(2);
                let transCenter = {};
                let crs = {};
                if (this.coordinate_system === '4326' || this.coordinate_system === '4490') {
                    crs = L.CRS.EPSG4326;
                    this.center = eval(this.center);
                } else if (this.coordinate_system === '3857') {
                    crs = L.Proj.CRS('EPSG:3857', {
                        resolutions: calcResolution(serveData.visibleScales),
                        bounds: L.bounds([parseFloat(minX), parseFloat(maxY)], [parseFloat(maxX), parseFloat(minY)]),
                        origin: [parseFloat(minX), parseFloat(minY)]
                    });
                    transCenter = crs.unproject(L.point((parseFloat(minX) + parseFloat(maxX)) / 2, (parseFloat(maxY) + parseFloat(minY)) / 2));

                    this.center = [transCenter.lat, transCenter.lng];
                } else {
                    const EPSG = 'EPSG:' + this.coordinate_system;
                    // proj4.defs(EPSG, this.proj)
                    crs = L.Proj.CRS(EPSG, {
                        resolutions: calcResolution(serveData.visibleScales),
                        bounds: L.bounds([parseFloat(minX), parseFloat(maxY)], [parseFloat(maxX), parseFloat(minY)]),
                        origin: [parseFloat(minX), parseFloat(minY)]
                    });
                    transCenter = crs.unproject(L.point((parseFloat(minX) + parseFloat(maxX)) / 2, (parseFloat(maxY) + parseFloat(minY)) / 2));

                    this.center = [transCenter.lat, transCenter.lng];
                }
                const map = L.map('map', {
                    crs: crs,
                    center: this.center,
                    maxZoom: 18,
                    zoom: this.zoom,
                    attributionControl: false,
                    logoControl: false
                });
                new TiledMapLayer(this.url).addTo(map);
            });
        }
    }
};
</script>

<style scoped>
::v-deep(.ant-modal-body) {
    height: 76vh;
    padding: 6px;
}
::v-deep(.ant-modal-footer) {
    display: none;
}
</style>
