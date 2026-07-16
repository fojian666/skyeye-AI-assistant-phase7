import 'babel-polyfill';
import 'promise-polyfill';
import Vue from 'vue';
import App from './App.vue';
import router from './router';
import store from './store';
import panZoom from 'vue-panzoom';
import Antd from 'ant-design-vue';
import 'ant-design-vue/dist/antd.css';
import moment from 'moment';
import './utils/authUtil';
import './css/theme/cyber-tokens.css';
import './css/theme/base.css';
import './less/fonts.css';
import './assets/css/table/common.css';
import './assets/css/table/primary-color.css';
// 1. 引入 Leaflet 核心库
import 'leaflet';
import 'leaflet/dist/leaflet.css'; // 引入 Leaflet CSS

// 2. 引入 iClient-Leaflet 插件（必须在 Leaflet 之后引入）
import '@supermap/iclient-leaflet';
import '@supermap/iclient-leaflet/dist/iclient-leaflet.css';

// 3. 修复 Leaflet 图标路径问题
import L from 'leaflet';
delete L.Icon.Default.prototype._getIconUrl; // 删除默认图标路径

L.Icon.Default.mergeOptions({
    iconRetinaUrl: require('leaflet/dist/images/marker-icon-2x.png'),
    iconUrl: require('leaflet/dist/images/marker-icon.png'),
    shadowUrl: require('leaflet/dist/images/marker-shadow.png')
});

// 4. 确保全局 L 对象可用
window.L = L;
window.L.supermap = L.supermap;
import ElementUI from 'element-ui';
import 'element-ui/lib/theme-chalk/index.css';
import { Message, MessageBox } from 'element-ui';
//定义一个新的Message方法，多传入一个offset参数
const $message = (options) => {
    return Message({
        ...options,
        offset: 100
    });
};

//重写方法,将offset写入options
['success', 'warning', 'info', 'error'].forEach((type) => {
    $message[type] = (options) => {
        if (typeof options === 'string') {
            options = {
                message: options,
                offset: 100
            };
            options.type = type;
        }

        return Message(options);
    };
});
Vue.use(panZoom);
Vue.use(Antd);
Vue.use(ElementUI, { size: 'small' });
Vue.prototype.$message = $message;
Vue.prototype.$confirm = MessageBox.confirm;
Vue.prototype.$moment = moment;
Vue.prototype.$map = { _leaflet_id: -1 };

import VueLazyLoad from 'vue-lazyload';
Vue.use(VueLazyLoad, {
    preLoad: 1,
    attempt: 2
});

import 'vue-virtual-scroller/dist/vue-virtual-scroller.css';
import VueVirtualScroller from 'vue-virtual-scroller';
// 引入图标库样式
import './assets/iconfont/iconfont.css';

import './css/index.scss';
import axios from 'axios';
import VueAxios from 'vue-axios';
//允许携带cookie
axios.defaults.withCredentials = true;
axios.prototype.$axios = axios;
Vue.use(VueAxios, axios);
Vue.use(VueVirtualScroller);

Vue.config.productionTip = false;

import VueTreeList from 'vue-tree-list';
Vue.use(VueTreeList);

new Vue({
    router,
    store,
    render: (h) => h(App)
}).$mount('#app');
