import { CONFIG } from './config.js';
import { ApiService } from './api.js';
import { UIManager } from './ui.js';

document.addEventListener('DOMContentLoaded', () => {
    const params = new URLSearchParams(location.search);
    
    // State
    const state = {
        text: (params.get('text') || '').trim(),
        currentK: Number(params.get('k') || '6'),
        isLoading: false,
        isFull: false
    };

    // DOM Elements
    const elements = {
        headerH2: document.querySelector('.results-header h2'),
        cardsContainer: document.querySelector('.cards'),
        loader: document.querySelector('.loading-indicator'),
        headerInput: document.querySelector('.search-bar input'),
        headerBtn: document.querySelector('.search-bar button')
    };

    if (elements.headerInput) elements.headerInput.value = state.text;

    // --- MAIN LOGIC ---
    async function loadDataAndRender(isLoadMore = false) {
        if (!state.text) {
            elements.headerH2.textContent = '0 results';
            return;
        }

        if (!isLoadMore) {
            elements.headerH2.textContent = 'Loading...';
            elements.cardsContainer.innerHTML = '';
        } else {
            elements.loader.classList.add('active');
        }
        state.isLoading = true;

        try {
            const data = await ApiService.fetchRecommendations(state.text, state.currentK);
            const items = data.results || [];

            if (!isLoadMore) {
                elements.headerH2.textContent = `${items.length} results`;
                items.forEach(it => elements.cardsContainer.appendChild(UIManager.createCardElement(it)));
            } else {
                const oldLength = state.currentK - CONFIG.stepK;
                const newItems = items.slice(oldLength);

                if (newItems.length === 0) {
                    state.isFull = true;
                    elements.loader.textContent = "Đã hiển thị hết kết quả.";
                } else {
                    newItems.forEach(it => elements.cardsContainer.appendChild(UIManager.createCardElement(it)));
                    elements.headerH2.textContent = `${items.length} results`;
                }
            }

            const ratings = await ApiService.fetchUserRatings();
            UIManager.applyUserRatings(ratings);

        } catch (e) {
            console.error(e);
            if (!isLoadMore) {
                elements.headerH2.textContent = 'Error loading data';
                elements.cardsContainer.innerHTML = `<div style="color:red; padding:10px">${e.message}</div>`;
            }
        } finally {
            state.isLoading = false;
            elements.loader.classList.remove('active');
        }
    }

    // --- EVENTS ---
    function triggerSearch() {
        const q = (elements.headerInput?.value || '').trim();
        if (!q) return;
        const newParams = new URLSearchParams();
        newParams.set('text', q);
        newParams.set('k', '6');
        window.location.search = newParams.toString();
    }

    elements.headerBtn?.addEventListener('click', triggerSearch);
    elements.headerInput?.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') triggerSearch();
    });

    window.addEventListener('scroll', () => {
        if (state.isLoading || state.isFull) return;
        if ((window.innerHeight + window.scrollY) >= document.body.offsetHeight - 100) {
            state.currentK += CONFIG.stepK;
            loadDataAndRender(true);
        }
    });

    // Start
    loadDataAndRender(false);
});