import { CONFIG } from './config.js';

export const ApiService = {
    getHeaders() {
        const token = localStorage.getItem('token');
        const headers = { 'Content-Type': 'application/json' };
        if (token) headers['Authorization'] = `Bearer ${token}`;
        return headers;
    },

    async sendRating(placeId, interactionType) {
        const token = localStorage.getItem('token');
        if (!token) throw { status: 401, message: "Unauthorized" };

        const res = await fetch(`${CONFIG.apiBase}/api/v1/user/rate`, {
            method: 'POST',
            headers: this.getHeaders(),
            body: JSON.stringify({ place_id: placeId, interaction_type: interactionType })
        });

        if (!res.ok) throw res;
        return await res.json();
    },

    async fetchRecommendations(text, kValue) {
        const res = await fetch(`${CONFIG.apiBase}/api/v1/recommend`, {
            method: 'POST',
            headers: this.getHeaders(),
            body: JSON.stringify({ user_text: text, top_k: kValue })
        });

        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return await res.json();
    },

    async fetchUserRatings() {
        const token = localStorage.getItem('token');
        if (!token) return null;

        const res = await fetch(`${CONFIG.apiBase}/api/v1/user/my-ratings`, {
            method: 'GET',
            headers: this.getHeaders()
        });

        if (res.ok) return await res.json();
        return null;
    }
};