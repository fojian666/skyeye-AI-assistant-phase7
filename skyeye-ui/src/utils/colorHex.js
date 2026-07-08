const HEX_COLOR_RE = /^#([0-9A-Fa-f]{3}|[0-9A-Fa-f]{6})$/;

export function isValidHexColor(value) {
    return HEX_COLOR_RE.test(String(value || '').trim());
}

export function normalizeHexColor(value) {
    const trimmed = String(value || '').trim();
    if (!isValidHexColor(trimmed)) {
        return '';
    }
    if (trimmed.length === 4) {
        const r = trimmed[1];
        const g = trimmed[2];
        const b = trimmed[3];
        return `#${r}${r}${g}${g}${b}${b}`.toUpperCase();
    }
    return trimmed.toUpperCase();
}
