/**
 * Rating Service - Frontend implementation of the user-place scoring algorithm
 * 
 * Handles:
 * - Automatic search appearance tracking (via backend)
 * - Watch time tracking with periodic updates
 * - Like/Dislike interactions
 * - Score management and display
 */

import { CONFIG } from './config.js';

export class RatingService {
    constructor() {
        this.watchTimers = new Map(); // Store active timers: placeId -> { startTime, interval, lastUpdate }
        this.updateInterval = 10000; // Update every 10 seconds
    }

    /**
     * Get auth headers with token
     */
    getHeaders() {
        const token = localStorage.getItem('token');
        const headers = { 'Content-Type': 'application/json' };
        if (token) headers['Authorization'] = `Bearer ${token}`;
        return headers;
    }

    /**
     * Check if user is logged in
     */
    isLoggedIn() {
        return !!localStorage.getItem('token');
    }

    /**
     * Track general interaction (like, dislike, watch_time)
     */
    async trackInteraction(placeId, interactionType, watchTimeSeconds = null) {
        if (!this.isLoggedIn()) {
            console.log('User not logged in - skipping interaction tracking');
            return null;
        }

        try {
            const body = {
                place_id: placeId,
                interaction_type: interactionType
            };

            // Add watch_time_seconds for watch_time interaction
            if (interactionType === 'watch_time' && watchTimeSeconds !== null) {
                body.watch_time_seconds = watchTimeSeconds;
            }

            const response = await fetch(`${CONFIG.apiBase}/api/v1/rating/interact`, {
                method: 'POST',
                headers: this.getHeaders(),
                body: JSON.stringify(body)
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const data = await response.json();
            console.log(`✅ Tracked ${interactionType} for place ${placeId}:`, data);
            return data;
        } catch (error) {
            console.error('Error tracking interaction:', error);
            return null;
        }
    }

    /**
     * Track watch time using dedicated endpoint
     */
    async trackWatchTime(placeId, watchTimeSeconds) {
        if (!this.isLoggedIn()) {
            return null;
        }

        try {
            const response = await fetch(`${CONFIG.apiBase}/api/v1/rating/watch-time`, {
                method: 'POST',
                headers: this.getHeaders(),
                body: JSON.stringify({
                    place_id: placeId,
                    watch_time_seconds: watchTimeSeconds
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const data = await response.json();
            console.log(`⏱️ Watch time updated for place ${placeId}: ${watchTimeSeconds}s, score: ${data.score}`);
            return data;
        } catch (error) {
            console.error('Error tracking watch time:', error);
            return null;
        }
    }

    /**
     * Start tracking watch time for a place (when user opens detail page)
     */
    startWatchTimeTracking(placeId) {
        // Don't track if user is not logged in
        if (!this.isLoggedIn()) {
            console.log('User not logged in - watch time tracking disabled');
            return;
        }

        // Stop existing timer if any
        this.stopWatchTimeTracking(placeId);

        const startTime = Date.now();
        let lastUpdate = 0;

        // Update watch time every 10 seconds
        const interval = setInterval(() => {
            const elapsedSeconds = Math.floor((Date.now() - startTime) / 1000);
            
            // Only update if at least 10 seconds have passed since last update
            if (elapsedSeconds - lastUpdate >= 10) {
                this.trackWatchTime(placeId, elapsedSeconds);
                lastUpdate = elapsedSeconds;
            }
        }, this.updateInterval);

        // Store timer info
        this.watchTimers.set(placeId, {
            startTime,
            interval,
            lastUpdate
        });

        console.log(`▶️ Started watch time tracking for place ${placeId}`);
    }

    /**
     * Stop tracking watch time (when user leaves page)
     */
    stopWatchTimeTracking(placeId) {
        const timer = this.watchTimers.get(placeId);
        
        if (timer) {
            clearInterval(timer.interval);
            
            // Send final watch time
            const finalSeconds = Math.floor((Date.now() - timer.startTime) / 1000);
            if (finalSeconds > 0) {
                this.trackWatchTime(placeId, finalSeconds);
            }

            this.watchTimers.delete(placeId);
            console.log(`⏹️ Stopped watch time tracking for place ${placeId} (${finalSeconds}s total)`);
        }
    }

    /**
     * Stop all active watch time tracking
     */
    stopAllWatchTimeTracking() {
        for (const [placeId, _] of this.watchTimers) {
            this.stopWatchTimeTracking(placeId);
        }
    }

    /**
     * Track like interaction
     */
    async trackLike(placeId) {
        return await this.trackInteraction(placeId, 'like');
    }

    /**
     * Track dislike interaction
     */
    async trackDislike(placeId) {
        return await this.trackInteraction(placeId, 'dislike');
    }

    /**
     * Get all user's ratings
     */
    async getUserRatings() {
        if (!this.isLoggedIn()) {
            return null;
        }

        try {
            const response = await fetch(`${CONFIG.apiBase}/api/v1/rating/my-ratings`, {
                method: 'GET',
                headers: this.getHeaders()
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const data = await response.json();
            return data;
        } catch (error) {
            console.error('Error fetching user ratings:', error);
            return null;
        }
    }

    /**
     * Get rating for a specific place
     */
    async getPlaceRating(placeId) {
        if (!this.isLoggedIn()) {
            return null;
        }

        try {
            const response = await fetch(`${CONFIG.apiBase}/api/v1/rating/rating/${placeId}`, {
                method: 'GET',
                headers: this.getHeaders()
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const data = await response.json();
            return data;
        } catch (error) {
            console.error('Error fetching place rating:', error);
            return null;
        }
    }

    /**
     * Get user's ratings as a map: placeId -> score
     */
    async getUserRatingsMap() {
        const ratings = await this.getUserRatings();
        if (!ratings || !ratings.ratings) {
            return {};
        }

        const map = {};
        ratings.ratings.forEach(rating => {
            map[rating.place_id] = rating.score;
        });

        return map;
    }

    /**
     * Update UI to show user's rating for a place
     */
    updateRatingUI(placeId, score) {
        // Update like/dislike buttons based on score
        const likeButtons = document.querySelectorAll(`[data-place-id="${placeId}"] .like-btn`);
        const dislikeButtons = document.querySelectorAll(`[data-place-id="${placeId}"] .dislike-btn`);

        likeButtons.forEach(btn => {
            if (score >= 7.0) {
                btn.classList.add('active');
                btn.style.color = '#2ecc71';
            } else {
                btn.classList.remove('active');
                btn.style.color = '';
            }
        });

        dislikeButtons.forEach(btn => {
            if (score <= 2.0) {
                btn.classList.add('active');
                btn.style.color = '#e74c3c';
            } else {
                btn.classList.remove('active');
                btn.style.color = '';
            }
        });
    }

    /**
     * Apply all user ratings to the current page
     */
    async applyUserRatings() {
        const ratingsMap = await this.getUserRatingsMap();
        
        for (const [placeId, score] of Object.entries(ratingsMap)) {
            this.updateRatingUI(placeId, score);
        }

        return ratingsMap;
    }
}

// Create singleton instance
export const ratingService = new RatingService();

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    ratingService.stopAllWatchTimeTracking();
});

// Cleanup on visibility change (when user switches tabs)
document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
        // User switched away from tab - pause all timers
        for (const [placeId, timer] of ratingService.watchTimers) {
            clearInterval(timer.interval);
        }
    } else {
        // User came back to tab - resume timers
        for (const [placeId, timer] of ratingService.watchTimers) {
            const startTime = timer.startTime;
            let lastUpdate = timer.lastUpdate;

            const interval = setInterval(() => {
                const elapsedSeconds = Math.floor((Date.now() - startTime) / 1000);
                
                if (elapsedSeconds - lastUpdate >= 10) {
                    ratingService.trackWatchTime(placeId, elapsedSeconds);
                    lastUpdate = elapsedSeconds;
                }
            }, ratingService.updateInterval);

            timer.interval = interval;
        }
    }
});
