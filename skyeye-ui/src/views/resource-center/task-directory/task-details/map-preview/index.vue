<template>
  <a-modal
    v-model="visible"
    :dialog-style="{ top: '10vh' }"
    title="地图预览"
    width="80vw"
  >
    <div id="map" style="margin: 0 auto; width: 100%; height: 100%"></div>
  </a-modal>
</template>

<script>
import { calcResolution, arcMapDisplay } from '@/utils/utils';
import {getTaskInfoByIdApi} from '@/api/commonApi';
export default {
  data() {
    return {
      url: '',
      next_url: '',
      center: null,
      coordinate_system: '',
      proj: '',
      zoom: 11,
      visible: false,
      task_id: 0,
      preview_type: '',
      layer: {},
      crs: {}
    };
  },
  computed: {
    map() {
      if (this.$map._leaflet_id === -1) {
        this.$map = L.map('map', {
          crs: this.crs,
          center: this.center,
          maxZoom: 18,
          zoom: this.zoom,
          attributionControl: false,
          logoControl: false
        });
      }
    }
  },
  methods: {
    open(obj) {
      this.task_id = obj.task_id;
      this.preview_type = obj.preview_type;
      this.visible = true;
      this.getTaskById();
    },
   async getTaskById() {
      const res = await getTaskInfoByIdApi(this.task_id);
      if (res.code === 0) {
        this.dataObj = res.data;
        if (this.dataObj.nextImage && this.dataObj.nextImage.url && this.dataObj.nextImage.url.includes('arcgis') ||
            this.dataObj.path && this.dataObj.path.url && this.dataObj.path.url.includes('arcgis') ||
            this.dataObj.mapUrl && this.dataObj.mapUrl.includes('arcgis') ||
            this.dataObj.prevImage && this.dataObj.prevImage.url && this.dataObj.prevImage.url.includes('arcgis')) {
            this.initArcMap();
        } else {
          this.center = this.dataObj.center;
          if (this.dataObj.taskType === '地类变化') {
            this.coordinate_system = this.dataObj.prevImage && this.dataObj.prevImage.coordinateSystem;
            this.proj = this.dataObj.prevImage && this.dataObj.prevImage.proj;
          } else {
            this.coordinate_system = this.dataObj.path.coordinateSystem;
            this.proj = this.dataObj.path.proj;
          }
          this.initMap();
        }
      }
      // const params = { task_id: this.task_id };
      // this.axios
      //   .get(config.BASE_URL + 'common/get_task_by_id', { params })
      //   .then((res) => {
      //     this.dataObj = res.data;
      //     if (this.dataObj.next_image.url && this.dataObj.next_image.url.includes('arcgis') || this.dataObj.path.url && this.dataObj.path.url.includes('arcgis') || this.dataObj.map_url && this.dataObj.map_url.includes('arcgis') || this.dataObj.prev_image.url && this.dataObj.prev_image.url.includes('arcgis')) {
      //       this.initArcMap();
      //     } else {
      //       this.center = this.dataObj.center;
      //       if (this.dataObj.task_type === '地类变化') {
      //         this.coordinate_system = this.dataObj.prev_image.coordinate_system;
      //         this.proj = this.dataObj.prev_image.proj;
      //       } else {
      //         this.coordinate_system = this.dataObj.path.coordinate_system;
      //         this.proj = this.dataObj.path.proj;
      //       }
      //       this.initMap();
      //     }
      //   });
    },
    initMap() {
      if (this.preview_type === '前景影像') {
        this.url = this.dataObj.prevImage && this.dataObj.prevImage.url;
      } else if (this.preview_type === '后景影像') {
        this.url = this.dataObj.nextImage && this.dataObj.nextImage.url;
      } else if (this.preview_type === '成果切片服务') {
        this.url = this.dataObj.mapUrl;
      } else {
        this.url = this.dataObj.path.url;
      }
      this.axios
        .get(this.url + '.json', { withCredentials: false })
        .then((res) => {
          const serveData = res.data;
          const minX = serveData.bounds.left.toFixed(2);
          const minY = serveData.bounds.bottom.toFixed(2);
          const maxX = serveData.bounds.right.toFixed(2);
          const maxY = serveData.bounds.top.toFixed(2);
          let transCenter = {};
          if (this.coordinate_system === '4326' || this.coordinate_system === '4490') {
            this.crs = L.CRS.EPSG4326;
            this.center = eval(this.center);
          } else if (this.coordinate_system === '3857') {
            this.crs = L.Proj.CRS('EPSG:3857', {
              resolutions: calcResolution(serveData.visibleScales),
              bounds: L.bounds(
                [parseFloat(minX), parseFloat(maxY)],
                [parseFloat(maxX), parseFloat(minY)]
              ),
              origin: [parseFloat(minX), parseFloat(minY)]
            });
            transCenter = this.crs.unproject(
              L.point(
                (parseFloat(minX) + parseFloat(maxX)) / 2,
                (parseFloat(maxY) + parseFloat(minY)) / 2
              )
            );
            this.center = [transCenter.lat, transCenter.lng];
          } else {
            const EPSG = 'EPSG:' + this.coordinate_system;
            proj4.defs(EPSG, this.proj);
            this.crs = L.Proj.CRS(EPSG, {
              resolutions: calcResolution(serveData.visibleScales),
              bounds: L.bounds(
                  [parseFloat(minX), parseFloat(maxY)],
                  [parseFloat(maxX), parseFloat(minY)]
              ),
              origin: [parseFloat(minX), parseFloat(minY)]
            });
            transCenter = this.crs.unproject(
                L.point(
                    (parseFloat(minX) + parseFloat(maxX)) / 2,
                    (parseFloat(maxY) + parseFloat(minY)) / 2
                )
            );
            this.center = [transCenter.lat, transCenter.lng];
          }
          if (this.layer._zoomAnimated) {
            this.$map.removeLayer(this.layer);
          }
          // this.map = L.map('map', {
          //   crs: crs,
          //   center: this.center,
          //   maxZoom: 18,
          //   zoom: this.zoom,
          //   attributionControl: false,
          //   logoControl: false
          // });
          this.map;
          this.layer = L.supermap.tiledMapLayer(this.url);
          this.layer.addTo(this.$map);
        });
    },
    initArcMap() {
      if (this.preview_type === '前景影像') {
        this.url = this.dataObj.prevImage && this.dataObj.prevImage.url;
      } else if (this.preview_type === '后景影像') {
        this.url = this.dataObj.nextImage && this.dataObj.nextImage.url;
      } else if (this.preview_type === '成果切片服务') {
        this.url = this.dataObj.mapUrl;
      } else {
        this.url = this.dataObj.path.url;
      }
      arcMapDisplay(this.url, 'map', 11);
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
