document.addEventListener('DOMContentLoaded', function() {
    initResultsToggle();
    initFormLoading();
    initGeneCards();
});

function initResultsToggle() {
    const resultsContainer = document.getElementById('resultsContainer');
    const uploadContainer = document.getElementById('uploadContainer');
    if (resultsContainer && resultsContainer.classList.contains('active')) {
        if (uploadContainer) uploadContainer.style.display = 'none';
        resultsContainer.style.display = 'block';
    }
}

function initFormLoading() {
    const form = document.getElementById('predictionForm');
    const submitBtn = document.getElementById('submitBtn');
    const overlay = document.getElementById('loadingOverlay');
    if (form && submitBtn && overlay) {
        form.addEventListener('submit', function(e) {
            const fileInput = form.querySelector('input[name="file"]');
            if (!fileInput || !fileInput.files.length) {
                e.preventDefault();
                alert('Пожалуйста, выберите файл');
                return;
            }
            overlay.classList.add('active');
            submitBtn.disabled = true;
            submitBtn.textContent = 'Обработка...';
        });
    }
}

function initGeneCards() {
    const genesPreview = document.querySelector('.genes-preview');
    if (!genesPreview) return;
    const geneCards = genesPreview.querySelectorAll('.gene-card');

    document.querySelectorAll('.gene-trigger').forEach(trigger => {
        trigger.addEventListener('click', function(e) {
            e.preventDefault();
            genesPreview.style.display = 'flex';
            const name = this.getAttribute('data-name');
            geneCards.forEach(card => {
                if (name === card.getAttribute('data-target')) card.classList.add('active');
            });
            document.body.style.overflow = 'hidden';
        });
    });

    genesPreview.addEventListener('click', function(e) {
        if (e.target === genesPreview) closeGeneModal(genesPreview, geneCards);
    });

    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && genesPreview.style.display === 'flex') closeGeneModal(genesPreview, geneCards);
    });
}

function closeGeneModal(genesPreview, geneCards) {
    geneCards.forEach(card => card.classList.remove('active'));
    genesPreview.style.display = 'none';
    document.body.style.overflow = '';
}

function resetToUpload() {
    const resultsContainer = document.getElementById('resultsContainer');
    const uploadContainer = document.getElementById('uploadContainer');
    if (resultsContainer) {
        resultsContainer.style.display = 'none';
        resultsContainer.classList.remove('active');
    }
    if (uploadContainer) uploadContainer.style.display = 'block';
    window.scrollTo({ top: 0, behavior: 'smooth' });
}
let genesChartMainInstance = null;

document.addEventListener('DOMContentLoaded', function () {
    initGenesChart();
});

function initGenesChart() {
    const triggers = document.querySelectorAll('.gene-trigger');
    const canvas = document.getElementById('genesChartMain');

    if (!canvas || triggers.length === 0) return;

    const genesData = {};

    triggers.forEach(el => {
        const gene = el.getAttribute('data-gene');
        let value = el.getAttribute('data-shap');

        if (!value) return;

        value = value.replace(',', '.');
        value = Math.abs(Number(value));

        if (!isNaN(value)) {
            genesData[gene] = value;
        }
    });

    const entries = Object.entries(genesData)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 10);

    if (entries.length === 0) return;

    const labels = entries.map(e => e[0]);
    const values = entries.map(e => e[1]);

    const total = values.reduce((a, b) => a + b, 0);
    if (total === 0) return;

    const colors = labels.map((_, i) => {
        const hue = 220 + (i * 12) % 100;
        return `hsl(${hue}, 70%, 60%)`;
    });

    if (genesChartMainInstance) {
        genesChartMainInstance.destroy();
    }

    genesChartMainInstance = new Chart(canvas, {
        type: 'doughnut',
        data: {
            labels,
            datasets: [{
                data: values,
                backgroundColor: colors,
                borderWidth: 2,
                borderColor: '#fff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '55%',
            plugins: {
                legend: {
                    position: 'bottom',
                    onClick: null
                },
                tooltip: {
                    callbacks: {
                        label: function (ctx) {
                            const val = ctx.parsed;
                            const pct = ((val / total) * 100).toFixed(1);
                            return `${ctx.label}: ${val.toFixed(4)} (${pct}%)`;
                        }
                    }
                }
            }
        }
    });
}
