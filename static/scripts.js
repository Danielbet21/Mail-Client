let app = Vue.createApp({
    data() {
        return {};
    }
});

app.component('toolbar', {
    data() {
        return {
            selectedAll: false
        };
    },
    template: `
        <div class="toolbar">
            <button @click="toggleSelectAll">
                <i :class="selectedAll ? 'bi bi-check-square' : 'bi bi-square'"></i>
            </button>
            <button @click="trash"><i class="bi bi-trash3"></i></button>
        </div>
    `,
    methods: {
        toggleSelectAll() {
            this.selectedAll = !this.selectedAll;  
        },
        trash() {
            alert("Trash clicked");
        }
    }
});

app.component('daily_summary', {
    data() {
        return {
            isOpen: false
        };
    },
    template: `
        <div class="daily-summary">
            <button @click="toggleWindow"><i class="bi bi-clipboard-data"></i></button>
            <div v-if="isOpen" class="summary-window">
                <!-- Content of the daily summary window goes here -->
                <p><strong>Here is where GPT 4o will post your emails</strong></p>
                <button @click="toggleWindow">Close</button>
            </div>
        </div>
    `,
    methods: {
        toggleWindow() {
            this.isOpen = !this.isOpen;
        }
    }
});

app.mount('#app');
