/**
 * ==============================================================================
 * SMOOTH NUMBER COUNTER ANIMATION (COUNT-UP) - FIXED & ACCURATE
 * ==============================================================================
 * Accurately parses integers, floats, and percentages without stripping decimals.
 */

function parseMetric(text) {
    if (!text) return null;
    const trimmed = text.trim();
    if (!trimmed || trimmed === '-' || trimmed === 'N/A') return null;

    const isPercent = trimmed.endsWith('%');
    // Extract first valid numeric part (supporting both integer and decimal e.g. 70, 70.2, 99.5)
    const cleanStr = trimmed.replace('%', '').trim().replace(/,/g, '');
    const match = cleanStr.match(/^[0-9]+(\.[0-9]+)?/);
    if (!match) return null;

    const num = parseFloat(match[0]);
    if (isNaN(num) || num <= 0) return null;

    const isDecimal = match[0].includes('.');
    const decimals = isDecimal ? match[0].split('.')[1].length : 0;

    return {
        value: num,
        isPercent: isPercent,
        isDecimal: isDecimal,
        decimals: decimals
    };
}

function animateValue(obj, start, end, duration, isPercent, isDecimal, decimals) {
    if (!obj || isNaN(end)) return;
    let startTimestamp = null;
    const step = (timestamp) => {
        if (!startTimestamp) startTimestamp = timestamp;
        const progress = Math.min((timestamp - startTimestamp) / duration, 1);
        const easeOut = 1 - Math.pow(1 - progress, 3);
        const current = easeOut * (end - start) + start;

        const formatted = isDecimal
            ? current.toFixed(decimals)
            : Math.floor(current).toLocaleString('id-ID');

        obj.textContent = isPercent ? `${formatted}%` : formatted;

        if (progress < 1) {
            window.requestAnimationFrame(step);
        } else {
            const finalFormatted = isDecimal
                ? end.toFixed(decimals)
                : end.toLocaleString('id-ID');
            obj.textContent = isPercent ? `${finalFormatted}%` : finalFormatted;
        }
    };
    window.requestAnimationFrame(step);
}

document.addEventListener('DOMContentLoaded', () => {
    // Select KPI cards and metric values
    const metricElements = document.querySelectorAll(
        '.analytics-card-value, #stat-total-input, #stat-success, #stat-failed, #stat-pending, #distribution-rate-text'
    );

    metricElements.forEach((el) => {
        const rawText = el.textContent.trim();
        const parsed = parseMetric(rawText);

        if (parsed && parsed.value > 0) {
            animateValue(
                el,
                0,
                parsed.value,
                800,
                parsed.isPercent,
                parsed.isDecimal,
                parsed.decimals
            );
        }
    });
});
