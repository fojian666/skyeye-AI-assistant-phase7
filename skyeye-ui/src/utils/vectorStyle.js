import { normalizeHexColor } from '@/utils/colorHex';

const DEFAULTS = {
    color: '#FF0000',
    weight: 2,
    opacity: 1
};

function parseVectorStyle(node) {
    const colorRaw = node.polygon_color ?? node.polygonColor;
    const weightRaw = node.polygon_weight ?? node.polygonWeight;
    const opacityRaw = node.polygon_opacity ?? node.polygonOpacity;

    const color = colorRaw ? normalizeHexColor(colorRaw) || DEFAULTS.color : DEFAULTS.color;
    const weight = weightRaw != null && !Number.isNaN(Number(weightRaw)) ? Number(weightRaw) : DEFAULTS.weight;
    const opacity =
        opacityRaw != null && !Number.isNaN(Number(opacityRaw))
            ? Math.min(1, Math.max(0, Number(opacityRaw)))
            : DEFAULTS.opacity;

    return { color, weight, opacity };
}

export function getLeafletVectorStyle(node) {
    const { color, weight, opacity } = parseVectorStyle(node);
    return {
        color,
        weight,
        opacity,
        fillOpacity: 0
    };
}

export function getCesiumVectorStyle(node) {
    const { color, weight, opacity } = parseVectorStyle(node);
    return {
        strokeColorHex: color,
        strokeWidth: weight,
        strokeAlpha: opacity
    };
}
