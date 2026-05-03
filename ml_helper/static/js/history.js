// ===== ГЛОБАЛЬНАЯ ПЕРЕМЕННАЯ ДЛЯ ДИАГРАММЫ =====
let genesChartInstance = null;

// ===== ИНИЦИАЛИЗАЦИЯ ОБРАБОТЧИКОВ =====
document.addEventListener('DOMContentLoaded', function() {
    const modal = document.getElementById('predictionModal');
    if (modal) {
        modal.addEventListener('click', function(e) {
            if (e.target === this) closePredictionModal();
        });
    }
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && modal && modal.style.display === 'flex') {
            closePredictionModal();
        }
    });
});

// ===== ФУНКЦИЯ ОТРИСОВКИ ДИАГРАММЫ =====
function renderGenesPieChart(genesDict) {
    const ctx = document.getElementById('genesChart');
    if (!ctx) return;
    
    // Уничтожаем старую диаграмму
    if (genesChartInstance) {
        genesChartInstance.destroy();
    }
    
    // Подготовка данных: топ-10 генов по важности
    const entries = Object.entries(genesDict)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 10);
    
    const labels = entries.map(([gene]) => gene);
    const values = entries.map(([, value]) => value);
    
    // Цвета: градиент от синего к фиолетовому
    const colors = labels.map((_, i) => {
        const hue = 220 + (i * 12) % 100;
        return `hsl(${hue}, 70%, 60%)`;
    });
    
    genesChartInstance = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: values,
                backgroundColor: colors,
                borderColor: '#ffffff',
                borderWidth: 2,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,

            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        font: { size: 11 },
                        padding: 12,
                    },
                    onClick: null
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.parsed || 0;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const pct = total > 0 ? ((value / total) * 100).toFixed(1) : 0;
                            return `${label}: ${value.toFixed(4)} (${pct}%)`;
                        }
                    }
                }
            },
            cutout: '50%'
        }
    });
}

// ===== ОТКРЫТИЕ МОДАЛЬНОГО ОКНА =====
function openPredictionModal(predictionId) {
    fetch(`/api/prediction/${predictionId}/`)
        .then(res => {
            if (!res.ok) throw new Error('Network response was not ok');
            return res.json();
        })
        .then(data => {
            // Метаданные
            document.getElementById('modalPatient').textContent = data.patient_id || '—';
            document.getElementById('modalDate').textContent = new Date(data.created_at).toLocaleString('ru-RU');
            document.getElementById('modalFile').textContent = data.input_file_name || '—';
            document.getElementById('modalId').textContent = data.id;

            // Основной результат
            document.getElementById('modalTitle').textContent = `Детали: ${data.predicted_label}`;
            document.getElementById('modalLabel').textContent = data.predicted_label;
            document.getElementById('modalConfidence').textContent = `${data.confidence.toFixed(1)}%`;
            document.getElementById('modalProbFill').style.width = `${data.confidence}%`;

            // Альтернативы
            const altBlock = document.getElementById('modalAlternativesBlock');
            const altContainer = document.getElementById('modalAlternatives');
            if (data.alternatives && data.alternatives.length > 0) {
                altBlock.style.display = 'block';
                altContainer.innerHTML = data.alternatives.map(a => 
                    `<span class="prob-tag">${a.label} — ${a.probability}%</span>`
                ).join('');
            } else {
                altBlock.style.display = 'none';
            }

            // Гены: список
            const genesContainer = document.getElementById('modalGenes');
            if (data.top_genes && Object.keys(data.top_genes).length > 0) {
                genesContainer.innerHTML = Object.entries(data.top_genes)
                    .sort((a, b) => b[1] - a[1])
                    .map(([gene, shap]) => `
                        <span class="gene-trigger">
                            <span>${gene}</span>
                            <span class="gene-shap-value">${shap.toFixed(4)}</span>
                        </span>
                    `).join('');
                
                // 🔽 ОТРИСОВЫВАЕМ ДИАГРАММУ 🔽
                renderGenesPieChart(data.top_genes);
            } else {
                genesContainer.innerHTML = '<span class="empty-message">Данные о генах недоступны</span>';
                // Очищаем диаграмму, если нет данных
                if (genesChartInstance) {
                    genesChartInstance.destroy();
                    genesChartInstance = null;
                }
            }

            // Показываем модальное окно
            document.getElementById('predictionModal').style.display = 'flex';
            document.querySelector('#predictionModal .gene-card').style.display = 'block';
            document.body.style.overflow = 'hidden';
        })
        .catch(err => {
            console.error('Ошибка загрузки деталей:', err);
            alert('Не удалось загрузить детали предсказания.');
        });
}

// ===== ЗАКРЫТИЕ МОДАЛЬНОГО ОКНА =====
function closePredictionModal() {
    const modal = document.getElementById('predictionModal');
    if (modal) modal.style.display = 'none';
    
    const card = document.querySelector('#predictionModal .gene-card');
    if (card) card.style.display = 'none';
    
    // Очищаем диаграмму при закрытии
    if (genesChartInstance) {
        genesChartInstance.destroy();
        genesChartInstance = null;
    }
    
    document.body.style.overflow = '';
}