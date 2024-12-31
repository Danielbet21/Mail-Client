let app = Vue.createApp({
    data() {
        return {};
    }
});

app.component('toolbar', {
    template: `
        <div class="toolbar">
            <button @click="toggleSelectAll" :title="selectedAll ? 'Unselect All' : 'Select All'">
                <i :class="selectedAll ? 'bi bi-check-square' : 'bi bi-square'"></i>
            </button>
            <button v-if="selectedAll" @click="trash" title="Move to Trash">
                <i class="bi bi-trash3"></i>
            </button>
        </div>
    `,
    data() {
        return {
            selectedAll: false
        };
    },
    
    methods: {
        toggleSelectAll() {
            this.selectedAll = !this.selectedAll;  
        },
        trash() {
            alert("Trash clicked");
        }
    }
});
// ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
app.component('window-daily-summary', {
    template: `
        <div class="daily-summary">
            <button @click="toggleWindow" title="AI Summary"><i class="bi bi-clipboard-data"></i></button>
            <div v-if="isOpen" class="summary-window">
                <p><strong>Daily Summaries</strong></p>
                <p v-if="loading">Loading summaries...</p>
                <p v-if="response"><strong>Summaries:</strong> {{ response }}</p>
                <button @click="toggleWindow" id="button-close-window">Close</button>
            </div>
        </div>
    `,
    data() {
        return {
            isOpen: false,
            loading: false,
            response: "",
            triggerDailySummary: false,  
            newEmails: []                
        };
    },  
    watch: {
        triggerDailySummary(brief_of_today_initial) {
            if (brief_of_today_initial) {
                this.getDailySummary();
            }
        }
    },
    methods: {
        toggleWindow() {
            this.isOpen = !this.isOpen;
        },

//         async fetchEmailsAndTriggerSummary() {
//             this.loading = true;

//             try {
//                 const response = await fetch("/api/v1/gmail/messages/brief_of_today");
//                 const data = await response.json();

//                 if (data.triggerDailySummary) {
//                     this.newEmails = data.messages;  // Update with new emails
//                     this.triggerDailySummary = true;  // Set the flag to true to trigger summary
//                 } else {
//                     this.response = "No new emails for today.";
//                 }
//             } catch (error) {
//                 this.response = "Error fetching email summaries.";
//             } finally {
//                 this.loading = false;
//             }
//         },

//         async getDailySummary() {
//             if (!this.newEmails || this.newEmails.length === 0) { 
//                 return; 
//             }

//             this.loading = true;
//             this.response = "";  // Clear previous response

//             try {
//                 const instruction = `Please summarize each email with the following format: [Sender Name] <[Sender Email]>
//                  sent you an email regarding [Email Subject] and mentioned: [Brief summary of the email’s main content].`;

//                 const emailSummaries = this.newEmails.map(email => `${email.senderName} <${email.senderEmail}>: ${email.content}`).join("\n");
//                 const full_input = `${instruction} ${emailSummaries}`;

//                 const chat_response = await fetch("/api/v1/chat", {
//                     method: "POST",
//                     headers: {
//                         "Content-Type": "application/json"
//                     },
//                     body: JSON.stringify({ message: full_input })
//                 });

//                 if (chat_response.ok) {
//                     const data = await chat_response.json();
//                     this.response = data.response;
//                 } else {
//                     this.response = "An error occurred. Please try again later.";
//                 }
//             } catch (error) {
//                 this.response = "An error occurred. Please try again later.";
//             } finally {
//                 this.loading = false;
//             }
//         }
//     },
//     created() {
//         this.fetchEmailsAndTriggerSummary();  // Automatically call this when the component is created
    }
});

app.mount('#app');
