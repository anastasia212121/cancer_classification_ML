document.addEventListener('DOMContentLoaded', function() {
    initResultsToggle();
    initFormLoading();
    initGeneCards();
});

function initResultsToggle() {
    const resultsContainer = document.getElementById('resultsContainer');
    const uploadContainer = document.getElementById('uploadContainer');
    
    if (resultsContainer && resultsContainer.classList.contains('active')) {
        if (uploadContainer) {
            uploadContainer.style.display = 'none';
        }
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
                const target = card.getAttribute('data-target');
                if (name === target) {
                    card.classList.add('active');
                }
            });
            
            document.body.style.overflow = 'hidden';
        });
    });
    
    
    genesPreview.addEventListener('click', function(e) {
        if (e.target === genesPreview) {
            closeGeneModal(genesPreview, geneCards);
        }
    });
    
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && genesPreview.style.display === 'flex') {
            closeGeneModal(genesPreview, geneCards);
        }
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
    if (uploadContainer) {
        uploadContainer.style.display = 'block';
    }
    
    window.scrollTo({ top: 0, behavior: 'smooth' });
}
