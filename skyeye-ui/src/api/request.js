import axios from 'axios';
import { Message } from 'element-ui';
import router from '@/router';

function isUnauthorizedCode(code) {
    return code === 405 || code === '405';
}

function canAutoLoginOnCurrentRoute() {
    const route = router.currentRoute;
    if (!route || !route.matched) return false;
    return route.matched.some((record) => record.meta.autoLogin)
        && window.config?.overviewAutoLogin?.enabled !== false;
}

function handleUnauthorized(data) {
    localStorage.removeItem('username');
    localStorage.removeItem('tokens');
    localStorage.removeItem('role');
    if (!canAutoLoginOnCurrentRoute()) {
        Message.error('登录失效，请重新登录！');
        router.push({ name: 'login' });
    }
    return Promise.reject(data || { code: 405, msg: '登录失效' });
}

function isBlobResponse(response) {
    const responseType = response.config && response.config.responseType;
    return responseType === 'blob' || response.data instanceof Blob;
}

const axiosInstance = axios.create({
    timeout: 90000,
    withCredentials: true
});

axiosInstance.interceptors.request.use(
    (config) => {
        const tokens = localStorage.getItem('tokens');
        if (tokens) {
            config.headers.Authorization = `Bearer ${tokens}`;
        }
        config.headers['Content-Type'] =
            config.headers['Content-Type'] || 'application/json';
        return config;
    },
    (error) => Promise.reject(error)
);

axiosInstance.interceptors.response.use(
    (response) => {
        if (isBlobResponse(response)) {
            return response.data;
        }

        const data = response.data;
        if (data && isUnauthorizedCode(data.code)) {
            return handleUnauthorized(data);
        }
        return data;
    },
    (err) => {
        const data = err.response && err.response.data;

        if (data && isUnauthorizedCode(data.code)) {
            return handleUnauthorized(data);
        }

        const msg = (data && (data.msg || data.message))
            || err.message
            || '请求失败，请稍后重试';
        Message.error(msg);
        return Promise.reject(err);
    }
);

export default axiosInstance;
