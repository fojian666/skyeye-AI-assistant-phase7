import request from "@/api/request";

/**
 * 重定向到登录页面
 */
export function redirectToLogin() {
    const { baseUrl, client_id } = window.config;
    window.location.href = `${baseUrl}/login`;
}

/**
 * 注销用户并重定向到登录页面
 */
export function logout() {
    // 清除本地存储中的 token、refreshToken 和 expires
    localStorage.removeItem('tokens');
    localStorage.removeItem('refreshToken');
    localStorage.removeItem('expires');
    localStorage.removeItem('username');
    localStorage.removeItem('role');
    localStorage.removeItem('county');
    window.location.href = `/login`;
}

export const refreshToken = function (refreshToken, clientId) {
    const params = {
        rst: refreshToken,
        clientId: clientId
    }
    return request({
        url: '/scp-account/oauth/refreshToken',
        method: 'post',
        params
    });
};