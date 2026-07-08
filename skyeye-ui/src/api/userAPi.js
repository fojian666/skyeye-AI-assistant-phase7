import request from '@/api/request';

export const getCurrentUser = () => {
    return request({
        url: `/api/system/user/current-user`,
        method: 'get'
    });
};

export const postLoginByCodeApi = (data) => {
    return request({
        url: `/api/system/user/temp-login`,
        method: 'post',
        data,
    })
};
