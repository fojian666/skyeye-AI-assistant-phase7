import cookies from 'js-cookie';

export function sphericalToScreen(viewer, pitch, yaw, canvas) {
    const currentPitch = viewer.getPitch();
    const currentYaw = viewer.getYaw();
    const currentHfov = viewer.getHfov();
    const currentRoll = 0;
    var hsPitchSin = Math.sin((pitch * Math.PI) / 180),
        hsPitchCos = Math.cos((pitch * Math.PI) / 180),
        configPitchSin = Math.sin((currentPitch * Math.PI) / 180),
        configPitchCos = Math.cos((currentPitch * Math.PI) / 180),
        yawCos = Math.cos(((-yaw + currentYaw) * Math.PI) / 180);
    var z = hsPitchSin * configPitchSin + hsPitchCos * yawCos * configPitchCos;
    if (z <= 0) {
        z = -z;
    }
    var yawSin = Math.sin(((-yaw + currentYaw) * Math.PI) / 180),
        hfovTan = Math.tan((currentHfov * Math.PI) / 360);
    var canvasWidth = canvas.clientWidth,
        canvasHeight = canvas.clientHeight;
    var coord = [
        ((-canvasWidth / hfovTan) * yawSin * hsPitchCos) / z / 2,
        ((-canvasWidth / hfovTan) * (hsPitchSin * configPitchCos - hsPitchCos * yawCos * configPitchSin)) / z / 2
    ];
    // Apply roll
    var rollSin = Math.sin((currentRoll * Math.PI) / 180),
        rollCos = Math.cos((currentRoll * Math.PI) / 180);
    coord = [coord[0] * rollCos - coord[1] * rollSin, coord[0] * rollSin + coord[1] * rollCos];
    // Apply transform
    coord[0] += canvasWidth / 2;
    coord[1] += canvasHeight / 2;
    return coord;
}
export function isPointInView(viewer, pitch, yaw, canvas) {
    // 获取当前视角参数
    var currentPitch = viewer.getPitch(); // 当前俯仰角
    var currentYaw = viewer.getYaw(); // 当前偏航角
    var currentHfov = viewer.getHfov(); // 当前水平视场角
    var canvasWidth = canvas.clientWidth,
        canvasHeight = canvas.clientHeight;

    var yawDiff = Math.abs(yaw - currentYaw);
    if (yawDiff > 180) {
        yawDiff = 360 - yawDiff;
    }
    var halfYaw = currentHfov / 2;
    if (yawDiff > halfYaw) {
        return false;
    }

    // 计算当前pitch边界
    var halfVfov = (currentHfov * canvasHeight) / canvasWidth;
    var minPitch = currentPitch - halfVfov;
    var maxPitch = currentPitch + halfVfov;

    // 判断目标点的俯仰角是否在当前视角范围内
    if (pitch < minPitch || pitch > maxPitch) {
        return false;
    }
    return true;
}

export function updateZoomButtonsState(viewer, minHfovValue, maxHfovValue) {
    const currentHfov = viewer.getHfov(); // 获取当前水平视场角
    const minHfov = minHfovValue; // 最小水平视场角
    const maxHfov = maxHfovValue; // 最大水平视场角
    const container = viewer.getContainer ? viewer.getContainer() : document.getElementById('panoramaContainer');
    if (!container) return;
    const zoomInBtn = container.querySelector('.pnlm-zoom-in');
    const zoomOutBtn = container.querySelector('.pnlm-zoom-out');
    // 处理“放大”按钮：达到最大视场角时，添加禁用样式和行为限制
    if (zoomInBtn) {
        const isDisabled = currentHfov <= minHfov;
        zoomInBtn.classList.toggle('disabled', isDisabled);
    }
    // 处理“缩小”按钮：达到最小视场角时，添加禁用样式和行为限制
    if (zoomOutBtn) {
        const isDisabled = currentHfov >= maxHfov;
        zoomOutBtn.classList.toggle('disabled', isDisabled);
    }
}
