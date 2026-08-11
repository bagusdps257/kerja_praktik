// ===============================
// NOTIFICATION PANEL SYSTEM
// ===============================

class NotificationManager {
    constructor() {
        this.notifications = JSON.parse(localStorage.getItem('ocr_notifications') || '[]');
        this.maxNotifications = 20;
        this.lastProgressStatus = null;
        this.lastTotalGagal = null;

        // Notification preferences (synced from Settings page via /api/status)
        this.prefs = {
            notify_success: true,
            notify_failed: true,
            sound_notify: false
        };

        this.badgeEl = document.getElementById('notification-badge');
        this.listEl = document.getElementById('notification-list');

        this.init();
    }

    init() {
        this.render();
        this.startPolling();

        // Clear all button
        this.clearAllBtn = document.getElementById('clear-all-notifications');
        if (this.clearAllBtn) {
            this.clearAllBtn.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                this.clearAll();
            });
        }
    }

    addNotification(type, message, iconClass, iconBgClass) {
        const id = Date.now().toString();
        const timestamp = new Date().toISOString();

        this.notifications.unshift({
            id,
            type,
            message,
            iconClass,
            iconBgClass,
            timestamp,
            read: false
        });

        if (this.notifications.length > this.maxNotifications) {
            this.notifications.pop();
        }

        this.save();
        this.render();

        // Play sound if enabled
        if (this.prefs.sound_notify) {
            this.playNotificationSound();
        }
    }

    save() {
        localStorage.setItem('ocr_notifications', JSON.stringify(this.notifications));
    }

    getUnreadCount() {
        return this.notifications.filter(n => !n.read).length;
    }

    clearAll() {
        this.notifications = [];
        this.save();
        this.render();
    }

    // ===============================
    // AUDIO NOTIFICATION (Web Audio API)
    // ===============================
    playNotificationSound() {
        try {
            const ctx = new (window.AudioContext || window.webkitAudioContext)();

            // First tone
            const osc1 = ctx.createOscillator();
            const gain1 = ctx.createGain();
            osc1.type = 'sine';
            osc1.frequency.setValueAtTime(660, ctx.currentTime);
            gain1.gain.setValueAtTime(0.15, ctx.currentTime);
            gain1.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.3);
            osc1.connect(gain1);
            gain1.connect(ctx.destination);
            osc1.start(ctx.currentTime);
            osc1.stop(ctx.currentTime + 0.3);

            // Second tone (higher, delayed)
            const osc2 = ctx.createOscillator();
            const gain2 = ctx.createGain();
            osc2.type = 'sine';
            osc2.frequency.setValueAtTime(880, ctx.currentTime + 0.15);
            gain2.gain.setValueAtTime(0.01, ctx.currentTime);
            gain2.gain.setValueAtTime(0.12, ctx.currentTime + 0.15);
            gain2.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.5);
            osc2.connect(gain2);
            gain2.connect(ctx.destination);
            osc2.start(ctx.currentTime + 0.15);
            osc2.stop(ctx.currentTime + 0.5);

            // Cleanup
            setTimeout(() => ctx.close(), 600);
        } catch (e) {
            // Audio not supported or blocked by browser
        }
    }

    // ===============================
    // RELATIVE TIMESTAMPS
    // ===============================
    timeAgo(dateString) {
        const date = new Date(dateString);
        const now = new Date();
        const seconds = Math.floor((now - date) / 1000);

        if (seconds < 60) return "Just now";

        const minutes = Math.floor(seconds / 60);
        if (minutes < 60) return minutes + " minutes ago";

        const hours = Math.floor(seconds / 3600);
        if (hours < 24) return hours + " hours ago";

        const days = Math.floor(seconds / 86400);
        if (days < 30) return days + " days ago";

        const months = Math.floor(seconds / 2592000);
        if (months < 12) return months + " months ago";

        const years = Math.floor(seconds / 31536000);
        return years + " years ago";
    }

    // ===============================
    // RENDER NOTIFICATION LIST
    // ===============================
    render() {
        if (!this.listEl || !this.badgeEl) return;

        const unreadCount = this.getUnreadCount();

        if (unreadCount > 0) {
            this.badgeEl.textContent = unreadCount > 99 ? '99+' : unreadCount;
            this.badgeEl.classList.remove('d-none');
        } else {
            this.badgeEl.classList.add('d-none');
        }

        // Show/hide Clear all link
        if (this.clearAllBtn) {
            this.clearAllBtn.style.display = this.notifications.length > 0 ? '' : 'none';
        }

        this.listEl.innerHTML = '';

        if (this.notifications.length === 0) {
            this.listEl.innerHTML =
                '<div class="notification-empty">' +
                    '<i class="bi bi-bell-slash text-muted fs-4"></i>' +
                    '<p class="text-muted small mt-2 mb-0">No new notifications</p>' +
                '</div>';
            return;
        }

        this.notifications.forEach(n => {
            const item = document.createElement('div');
            item.className = 'notification-item' + (n.read ? '' : ' unread');

            item.innerHTML =
                '<div class="notification-icon ' + n.iconBgClass + '">' +
                    '<i class="' + n.iconClass + '"></i>' +
                '</div>' +
                '<div class="notification-content">' +
                    '<div class="notification-message">' + this.escapeHtml(n.message) + '</div>' +
                    '<div class="notification-time">' +
                        '<i class="bi bi-clock me-1"></i> ' + this.timeAgo(n.timestamp) +
                    '</div>' +
                '</div>';

            this.listEl.appendChild(item);
        });
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // ===============================
    // POLLING & DATA PROCESSING
    // ===============================
    async checkUpdates() {
        try {
            const [statusRes, progressRes] = await Promise.all([
                fetch('/api/status').catch(() => null),
                fetch('/progress').catch(() => null)
            ]);

            if (statusRes && statusRes.ok) {
                const statusData = await statusRes.json();

                // Sync notification preferences from Settings page
                if (statusData.notification_prefs) {
                    this.prefs = statusData.notification_prefs;
                }

                this.processStatusData(statusData);
            }

            if (progressRes && progressRes.ok) {
                const progressData = await progressRes.json();
                this.processProgressData(progressData);
            }
        } catch (error) {
            console.error('Error fetching data for notifications:', error);
        }
    }

    processStatusData(data) {
        if (!data || !data.stats) return;

        const currentTotalGagal = data.stats.total_gagal || 0;

        // Detect new failed documents (only if notify_failed is enabled)
        if (this.prefs.notify_failed) {
            if (this.lastTotalGagal !== null && currentTotalGagal > this.lastTotalGagal) {
                const diff = currentTotalGagal - this.lastTotalGagal;
                this.addNotification(
                    'error',
                    diff + ' document(s) failed processing.',
                    'bi bi-exclamation-octagon-fill',
                    'error'
                );
            }
        }

        this.lastTotalGagal = currentTotalGagal;

        // Storage warning (once per day max, always shown regardless of settings)
        if (data.total_ukuran && typeof data.total_ukuran === 'string') {
            if (data.total_ukuran.includes('GB')) {
                const val = parseFloat(data.total_ukuran);
                if (!isNaN(val) && val > 5) {
                    const lastWarn = localStorage.getItem('ocr_last_storage_warn');
                    const now = Date.now();
                    if (!lastWarn || (now - parseInt(lastWarn)) > 86400000) {
                        this.addNotification(
                            'warning',
                            'Storage is high (' + data.total_ukuran + '). Consider cleaning up.',
                            'bi bi-hdd-fill',
                            'warning'
                        );
                        localStorage.setItem('ocr_last_storage_warn', now.toString());
                    }
                }
            }
        }
    }

    processProgressData(data) {
        if (!data || !data.status) return;

        const currentStatus = data.status;

        // Detect status transitions
        if (this.lastProgressStatus !== null && this.lastProgressStatus !== currentStatus) {
            if (currentStatus === 'FINISHED' && this.prefs.notify_success) {
                this.addNotification(
                    'success',
                    'OCR processing completed successfully.',
                    'bi bi-check-circle-fill',
                    'success'
                );
            } else if (currentStatus === 'ERROR' && this.prefs.notify_failed) {
                this.addNotification(
                    'error',
                    'OCR processing encountered an error.',
                    'bi bi-x-circle-fill',
                    'error'
                );
            } else if (currentStatus === 'STOPPED' && this.prefs.notify_failed) {
                this.addNotification(
                    'warning',
                    'OCR processing was stopped.',
                    'bi bi-pause-circle-fill',
                    'warning'
                );
            }
        }

        this.lastProgressStatus = currentStatus;
    }

    startPolling() {
        // Initial check
        this.checkUpdates().then(() => {
            setInterval(() => {
                this.render(); // Update relative timestamps
                this.checkUpdates();
            }, 3000);
        });
    }
}

document.addEventListener('DOMContentLoaded', () => {
    window.notificationManager = new NotificationManager();
});
