(function () {
    const registry = new Map();

    function toNumber(value) {
        const num = Number(value);
        return Number.isFinite(num) ? num : null;
    }

    function clamp(value, min, max) {
        return Math.max(min, Math.min(max, value));
    }

    function normalize(value, min, max) {
        if (!Number.isFinite(value)) return 0;
        if (!Number.isFinite(min) || !Number.isFinite(max) || min === max) return clamp(value, 0, 100);
        const ratio = ((value - min) / (max - min)) * 100;
        return clamp(ratio, 0, 100);
    }

    function register(type, factory) {
        registry.set(type, factory);
    }

    function create(type, context) {
        const factory = registry.get(type) || registry.get("line");
        return factory(context);
    }

    function list() {
        return Array.from(registry.keys());
    }

    function chartFactory(type, areaFill) {
        return function (context) {
            const container = context.container;
            container.innerHTML = "";
            const canvas = document.createElement("canvas");
            container.appendChild(canvas);

            const chart = new Chart(canvas, {
                type,
                data: {
                    labels: [],
                    datasets: [
                        {
                            label: context.label,
                            data: [],
                            borderColor: context.color,
                            backgroundColor: type === "bar" ? context.color + "66" : context.color + "22",
                            fill: areaFill,
                            tension: type === "bar" ? 0 : 0.3,
                            borderWidth: 2,
                        },
                    ],
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false } },
                },
            });

            return {
                setHistory(points) {
                    chart.data.labels = points.map((p) => p.label);
                    chart.data.datasets[0].data = points.map((p) => p.value);
                    chart.update();
                },
                setLatest(value) {
                    const num = toNumber(value);
                    if (num === null) return;

                    const nowLabel = new Date().toLocaleTimeString("zh-TW", { hour12: false });
                    chart.data.labels.push(nowLabel);
                    chart.data.datasets[0].data.push(num);

                    if (chart.data.labels.length > 120) {
                        chart.data.labels.shift();
                        chart.data.datasets[0].data.shift();
                    }

                    chart.update("none");
                },
                destroy() {
                    chart.destroy();
                },
            };
        };
    }

    function gaugeFactory(context) {
        const container = context.container;
        container.innerHTML = "";

        const wrap = document.createElement("div");
        wrap.className = "widget-gauge-wrap";

        const canvas = document.createElement("canvas");
        const center = document.createElement("div");
        center.className = "widget-gauge-center";
        center.innerHTML = "--";

        wrap.appendChild(canvas);
        wrap.appendChild(center);
        container.appendChild(wrap);

        const chart = new Chart(canvas, {
            type: "doughnut",
            data: {
                labels: ["value", "remaining"],
                datasets: [
                    {
                        data: [0, 100],
                        backgroundColor: [context.color, "#dfe5ef"],
                        borderWidth: 0,
                        circumference: 180,
                        rotation: 270,
                    },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false }, tooltip: { enabled: false } },
            },
        });

        function update(value) {
            const num = toNumber(value);
            if (num === null) return;
            const percent = normalize(num, context.minValue, context.maxValue);
            chart.data.datasets[0].data = [percent, 100 - percent];
            chart.update("none");
            center.innerHTML = `${num.toFixed(2)}<small>${context.unit || ""}</small>`;
        }

        return {
            setHistory(points) {
                if (!points.length) return;
                update(points[points.length - 1].value);
            },
            setLatest(value) {
                update(value);
            },
            destroy() {
                chart.destroy();
            },
        };
    }

    function progressFactory(context) {
        const container = context.container;
        container.innerHTML = `
            <div class="widget-progress-wrap">
                <div class="widget-progress-label">${context.label}</div>
                <div class="progress" style="height: 18px;">
                    <div class="progress-bar" role="progressbar" style="width: 0%; background: ${context.color};"></div>
                </div>
                <div class="widget-progress-value">--</div>
            </div>
        `;

        const bar = container.querySelector(".progress-bar");
        const text = container.querySelector(".widget-progress-value");

        function update(value) {
            const num = toNumber(value);
            if (num === null) return;
            const percent = normalize(num, context.minValue, context.maxValue);
            bar.style.width = `${percent}%`;
            text.textContent = `${num.toFixed(2)} ${context.unit || ""}`;
        }

        return {
            setHistory(points) {
                if (!points.length) return;
                update(points[points.length - 1].value);
            },
            setLatest(value) {
                update(value);
            },
            destroy() {
                container.innerHTML = "";
            },
        };
    }

    register("line", chartFactory("line", false));
    register("bar", chartFactory("bar", false));
    register("area", chartFactory("line", true));
    register("gauge", gaugeFactory);
    register("progress", progressFactory);

    window.DashboardWidgets = { register, create, list };
})();
