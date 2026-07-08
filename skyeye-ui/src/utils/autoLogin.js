import { getLoginCheckApi, getPublicKeyApi } from '@/api/commonApi';

function encodePwd(plainText, publicKey, offset = 18) {
    let result = '';
    const mixStr = plainText + '|' + publicKey;
    for (let i = 0; i < mixStr.length; i++) {
        const code = mixStr.charCodeAt(i);
        result += String.fromCharCode(code + offset);
    }
    result = result.split('').reverse().join('');
    return btoa(result);
}

/**
 * 使用配置账号静默登录（用于大屏等免登录入口）
 */
export async function performAutoLogin(credentials) {
    const config = window.config?.overviewAutoLogin || {};
    const username = credentials?.username || config.username || 'WXSAdmin';
    const password = credentials?.password || config.password || 'WXSAdmin)OKM';

    localStorage.removeItem('tokens');
    localStorage.removeItem('username');
    localStorage.removeItem('role');

    const keyRes = await getPublicKeyApi();
    const publicKey = keyRes?.data?.public_key;
    if (!publicKey) {
        throw new Error('获取公钥失败');
    }

    const res = await getLoginCheckApi({
        username,
        password: encodePwd(password, publicKey)
    });

    if (res.code !== 0) {
        throw new Error(res.msg || '自动登录失败');
    }

    localStorage.setItem('username', username);
    localStorage.setItem('role', res.role);
    localStorage.setItem('tokens', res.tokens);
    localStorage.setItem('lastClickTime', String(new Date().getTime()));

    return res;
}
