window.DashboardPrefs = (() => {
    const PREFIX = 'esp_iot_dash_';

    function load(key, fallback) {
        try {
            const value = localStorage.getItem(PREFIX + key);
            if (!value) return fallback;
            return JSON.parse(value);
        } catch (err) {
            console.warn('[prefs] load failed', err);
            return fallback;
        }
    }

    function save(key, value) {
        try {
            localStorage.setItem(PREFIX + key, JSON.stringify(value));
        } catch (err) {
            console.warn('[prefs] save failed', err);
        }
    }

    function clear(key) {
        localStorage.removeItem(PREFIX + key);
    }

    return { load, save, clear };
})();
